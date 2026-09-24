"""S4: gradient-boosted trees on the identical information set (§4.1, D.3).

The ladder's critical control: supervised learning on the same sentiment +
technical features available to the LLM strategies. Frozen specification
(configs/strategies.yaml): LightGBM, seed 42, expanding-window CV,
log-loss selection, decision rule long iff P(up) > 0.5.

Leakage discipline: features at decision day d use ONLY data timestamped
<= d (day-d close is known at the close-of-d decision, §3.2). The label at
decision day d is the direction of the return that decision would earn:
open(d+1) -> open(d+2) (recorded convention D-S4-LABEL, matching the
engine's execution contract exactly).
"""
from __future__ import annotations

import itertools
import math

import numpy as np
import pandas as pd

from src.strategies.baselines import entry_decision_day

SEED = 42

FROZEN_SEARCH_SPACE = {
    "num_leaves": [15, 31, 63],
    "learning_rate": [0.01, 0.05, 0.1],
    "n_estimators": [100, 300, 500],
    "min_child_samples": [20, 50],
    "feature_fraction": [0.8, 1.0],
}

FEATURE_NAMES = [
    "ret_1",
    "ret_5",
    "ret_21",
    "ma_10_50",
    "ma_50_200",
    "vol_21",
    "volume_z_21",
    "sent_daily",
    "sent_3d",
]


def _pivot(prices: pd.DataFrame, col: str) -> pd.DataFrame:
    return (
        prices.assign(date=pd.to_datetime(prices["date"]).dt.normalize())
        .pivot(index="date", columns="ticker", values=col)
        .sort_index()
    )


def build_features(
    prices: pd.DataFrame, sentiment: pd.DataFrame | None = None
) -> pd.DataFrame:
    """Long frame indexed (date, ticker) with the frozen feature set.
    All rolling statistics end at day d — nothing after d is touched.
    Missing sentiment maps to 0.0 (neutral; recorded convention)."""
    closes = _pivot(prices, "close")
    volumes = _pivot(prices, "volume")

    ret_1 = closes.pct_change(1)
    ret_5 = closes.pct_change(5)
    ret_21 = closes.pct_change(21)
    ma_10_50 = closes.rolling(10).mean() / closes.rolling(50).mean() - 1.0
    ma_50_200 = closes.rolling(50).mean() / closes.rolling(200).mean() - 1.0
    vol_21 = closes.pct_change().rolling(21).std(ddof=1)
    v_mean = volumes.rolling(21).mean()
    v_std = volumes.rolling(21).std(ddof=1)
    volume_z_21 = (volumes - v_mean) / v_std
    # zero-variance window carries no information -> z = 0, not NaN
    # (warmup NaNs are preserved: v_std is NaN there, not zero)
    volume_z_21 = volume_z_21.mask(v_std == 0.0, 0.0)

    if sentiment is not None:
        sent_daily = (
            sentiment.assign(date=pd.to_datetime(sentiment["date"]).dt.normalize())
            .pivot(index="date", columns="ticker", values="sent_daily")
            .reindex(index=closes.index, columns=closes.columns)
        )
        sent_3d = sent_daily.rolling(3, min_periods=1).mean()
        sent_daily = sent_daily.fillna(0.0)
        sent_3d = sent_3d.fillna(0.0)
    else:
        sent_daily = pd.DataFrame(0.0, index=closes.index, columns=closes.columns)
        sent_3d = sent_daily.copy()

    parts = {
        "ret_1": ret_1,
        "ret_5": ret_5,
        "ret_21": ret_21,
        "ma_10_50": ma_10_50,
        "ma_50_200": ma_50_200,
        "vol_21": vol_21,
        "volume_z_21": volume_z_21,
        "sent_daily": sent_daily,
        "sent_3d": sent_3d,
    }
    stacked = {name: frame.stack(future_stack=True) for name, frame in parts.items()}
    out = pd.DataFrame(stacked)[FEATURE_NAMES]
    out.index.names = ["date", "ticker"]
    return out


def make_labels(prices: pd.DataFrame) -> pd.Series:
    """Label at decision day d: 1 iff open(d+2) > open(d+1) — the direction
    of the open-to-open return the decision earns. Last two days: NaN."""
    opens = _pivot(prices, "open")
    future = opens.shift(-2) / opens.shift(-1) - 1.0
    labels = (future > 0).astype(float).where(future.notna())
    out = labels.stack(future_stack=True)
    out.index.names = ["date", "ticker"]
    return out


def expanding_time_splits(dates: list, folds: int = 5):
    """Chronological expanding-window folds over unique sorted dates:
    fold k trains on blocks [0..k] and validates on block k+1."""
    dates = sorted(set(dates))
    blocks = np.array_split(np.array(dates), folds + 1)
    for k in range(folds):
        train_dates = np.concatenate(blocks[: k + 1])
        test_dates = blocks[k + 1]
        yield set(pd.Timestamp(d) for d in train_dates), set(
            pd.Timestamp(d) for d in test_dates
        )


def _log_loss(y_true: np.ndarray, p: np.ndarray) -> float:
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return float(-np.mean(y_true * np.log(p) + (1 - y_true) * np.log(1 - p)))


def _lgb_params(combo: dict, seed: int) -> dict:
    return {
        "objective": "binary",
        "num_leaves": combo["num_leaves"],
        "learning_rate": combo["learning_rate"],
        "min_data_in_leaf": combo["min_child_samples"],
        "feature_fraction": combo["feature_fraction"],
        "seed": seed,
        "feature_fraction_seed": seed,
        "bagging_seed": seed,
        "deterministic": True,
        "force_row_wise": True,
        "verbosity": -1,
    }


def grid_search_train(
    features: pd.DataFrame,
    labels: pd.Series,
    folds: int = 5,
    search_space: dict | None = None,
    seed: int = SEED,
) -> dict:
    """Frozen selection procedure (D.3): full grid, expanding-window CV,
    mean log-loss criterion; ties break to the first combination in the
    deterministic iteration order (sorted parameter names). Final model is
    refit on all supplied data with the winning parameters."""
    import lightgbm as lgb

    space = search_space or FROZEN_SEARCH_SPACE
    data = features.join(labels.rename("label"), how="inner").dropna()
    if data.empty:
        raise ValueError("No complete (feature, label) rows to train on")
    X = data[FEATURE_NAMES].to_numpy()
    y = data["label"].to_numpy()
    row_dates = data.index.get_level_values("date")

    keys = sorted(space)
    best = None
    for values in itertools.product(*(space[k] for k in keys)):
        combo = dict(zip(keys, values))
        losses = []
        for train_dates, test_dates in expanding_time_splits(row_dates, folds):
            tr = np.array([d in train_dates for d in row_dates])
            te = np.array([d in test_dates for d in row_dates])
            if tr.sum() == 0 or te.sum() == 0 or len(set(y[tr])) < 2:
                continue
            booster = lgb.train(
                _lgb_params(combo, seed),
                lgb.Dataset(X[tr], label=y[tr]),
                num_boost_round=combo["n_estimators"],
            )
            losses.append(_log_loss(y[te], booster.predict(X[te])))
        if not losses:
            continue
        mean_loss = float(np.mean(losses))
        if best is None or mean_loss < best["cv_logloss"]:  # strict '<': ties keep first
            best = {"params": combo, "cv_logloss": mean_loss}

    if best is None:
        raise ValueError("Grid search found no valid fold configuration")

    final = lgb.train(
        _lgb_params(best["params"], seed),
        lgb.Dataset(X, label=y),
        num_boost_round=best["params"]["n_estimators"],
    )
    return {
        "booster": final,
        "params": best["params"],
        "cv_logloss": best["cv_logloss"],
        "feature_names": list(FEATURE_NAMES),
        "seed": seed,
        "n_train_rows": int(len(data)),
    }


def s4_signals(
    model: dict,
    features: pd.DataFrame,
    universe: list,
    window_start,
    window_end,
    threshold: float = 0.5,
) -> pd.DataFrame:
    """Daily decisions: long iff P(up) > threshold (frozen 0.5). Rows with
    incomplete features -> flat (recorded convention)."""
    w_start = pd.Timestamp(window_start).normalize()
    w_end = pd.Timestamp(window_end).normalize()
    days = pd.DatetimeIndex(sorted(features.index.get_level_values("date").unique()))
    decision_days = [entry_decision_day(days, w_start)] + list(
        days[(days >= w_start) & (days < w_end)]
    )

    rows = []
    for d in decision_days:
        for t in universe:
            action = "flat"
            if (d, t) in features.index:
                x = features.loc[(d, t), FEATURE_NAMES]
                if not x.isna().any():
                    p = float(
                        model["booster"].predict(x.to_numpy().reshape(1, -1))[0]
                    )
                    action = "long" if p > threshold else "flat"
            rows.append({"decision_date": d, "ticker": t, "action": action})
    return pd.DataFrame(rows)
