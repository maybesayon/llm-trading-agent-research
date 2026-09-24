"""S4 validation: hand-computed features/labels, a mutation-based leakage
test, chronological CV splits, and a separable-data learning check."""
import math

import numpy as np
import pandas as pd
import pytest

from src.strategies.ml_model import (
    FEATURE_NAMES,
    build_features,
    expanding_time_splits,
    grid_search_train,
    make_labels,
    s4_signals,
)

SMALL_SPACE = {
    "num_leaves": [15],
    "learning_rate": [0.1],
    "n_estimators": [60],
    "min_child_samples": [20],
    "feature_fraction": [1.0],
}


def make_prices(n_days, close_fn, open_fn=None, volume_fn=None, tickers=("AAA",)):
    days = pd.bdate_range("2020-01-02", periods=n_days)
    rows = []
    for t in tickers:
        for i, d in enumerate(days):
            c = float(close_fn(i, t))
            rows.append(
                {
                    "date": d,
                    "ticker": t,
                    "open": float(open_fn(i, t)) if open_fn else c,
                    "close": c,
                    "volume": float(volume_fn(i, t)) if volume_fn else 1000.0,
                }
            )
    return pd.DataFrame(rows), days


# ---------- features ----------

def test_feature_hand_calculations():
    prices, days = make_prices(260, lambda i, t: 100.0 + i, volume_fn=lambda i, t: 1000.0 + 10 * i)
    feats = build_features(prices)
    d = days[250]
    row = feats.loc[(d, "AAA")]
    # closes are 100+i: ret_1 at i=250 -> 350/349 - 1
    assert math.isclose(row["ret_1"], 350.0 / 349.0 - 1.0)
    assert math.isclose(row["ret_5"], 350.0 / 345.0 - 1.0)
    assert math.isclose(row["ret_21"], 350.0 / 329.0 - 1.0)
    # MA(10) at i ends 341..350 -> mean 345.5; MA(50) -> 325.5
    assert math.isclose(row["ma_10_50"], 345.5 / 325.5 - 1.0)
    # MA(50)=325.5, MA(200) ends 151..350 -> 250.5
    assert math.isclose(row["ma_50_200"], 325.5 / 250.5 - 1.0)
    # linear volume: z-score of the last point of a linear 21-window
    vols = np.array([1000.0 + 10 * j for j in range(230, 251)])
    assert math.isclose(row["volume_z_21"], (vols[-1] - vols.mean()) / vols.std(ddof=1))
    # no sentiment supplied -> neutral zeros
    assert row["sent_daily"] == 0.0 and row["sent_3d"] == 0.0


def test_features_nan_during_warmup():
    prices, days = make_prices(60, lambda i, t: 100.0 + i)
    feats = build_features(prices)
    assert np.isnan(feats.loc[(days[10], "AAA"), "ma_50_200"])  # needs 200 days
    assert not np.isnan(feats.loc[(days[30], "AAA"), "ret_21"])


# ---------- labels ----------

def test_label_alignment_hand_case():
    opens = [100.0, 101.0, 103.0, 102.0, 105.0]
    prices, days = make_prices(5, lambda i, t: 1.0, open_fn=lambda i, t: opens[i])
    labels = make_labels(prices)
    # label(d) = 1 iff open(d+2) > open(d+1)
    assert labels.loc[(days[0], "AAA")] == 1.0  # 103 > 101
    assert labels.loc[(days[1], "AAA")] == 0.0  # 102 < 103
    assert labels.loc[(days[2], "AAA")] == 1.0  # 105 > 102
    assert np.isnan(labels.loc[(days[3], "AAA")])
    assert np.isnan(labels.loc[(days[4], "AAA")])


# ---------- leakage (mutation test) ----------

def test_features_immune_to_future_mutation():
    """Multiply every price/volume strictly after a cutoff by 5; features at
    or before the cutoff must be bit-identical. If any rolling window peeks
    forward, this fails."""
    prices, days = make_prices(
        300,
        lambda i, t: 100.0 + i + 3 * math.sin(i / 5.0),
        volume_fn=lambda i, t: 1000.0 + 10 * i + 100 * math.sin(i / 3.0),
    )
    cutoff = days[250]
    mutated = prices.copy()
    after = pd.to_datetime(mutated["date"]) > cutoff
    mutated.loc[after, ["open", "close", "volume"]] *= 5.0

    f_orig = build_features(prices)
    f_mut = build_features(mutated)
    upto = f_orig.index.get_level_values("date") <= cutoff
    pd.testing.assert_frame_equal(f_orig[upto], f_mut[upto])


# ---------- CV splits ----------

def test_expanding_splits_are_chronological():
    dates = list(pd.bdate_range("2020-01-02", periods=120))
    folds = list(expanding_time_splits(dates, folds=5))
    assert len(folds) == 5
    prev_train_size = 0
    for train, test in folds:
        assert max(train) < min(test)          # strictly chronological
        assert len(train) > prev_train_size    # expanding
        prev_train_size = len(train)


# ---------- learning + signals on separable synthetic data ----------

@pytest.fixture
def separable_market():
    """Sentiment at day d deterministically drives the open(d+1)->open(d+2)
    move: +1 -> +1%, -1 -> -1%. A working pipeline must learn this."""
    n = 420
    rng = np.random.RandomState(42)
    sent = {t: rng.choice([-1.0, 1.0], size=n) for t in ("AAA", "BBB")}

    opens = {t: [100.0, 100.0] for t in ("AAA", "BBB")}
    for t in ("AAA", "BBB"):
        for i in range(2, n):
            drive = sent[t][i - 2]  # open(i)/open(i-1) driven by sentiment at i-2
            opens[t].append(opens[t][-1] * (1.01 if drive > 0 else 0.99))

    days = pd.bdate_range("2020-01-02", periods=n)
    price_rows, sent_rows = [], []
    for t in ("AAA", "BBB"):
        for i, d in enumerate(days):
            price_rows.append(
                {
                    "date": d,
                    "ticker": t,
                    "open": opens[t][i],
                    "close": opens[t][i],
                    "volume": 1000.0,
                }
            )
            sent_rows.append({"date": d, "ticker": t, "sent_daily": sent[t][i]})
    return pd.DataFrame(price_rows), pd.DataFrame(sent_rows), days


def test_s4_learns_separable_signal(separable_market):
    prices, sentiment, days = separable_market
    feats = build_features(prices, sentiment)
    labels = make_labels(prices)

    train_cut = days[330]
    train_mask = feats.index.get_level_values("date") <= train_cut
    model = grid_search_train(
        feats[train_mask], labels, folds=3, search_space=SMALL_SPACE
    )
    assert model["params"]["num_leaves"] == 15
    assert model["n_train_rows"] > 0

    # out-of-sample: predictions on dates after the training cutoff
    test_mask = (feats.index.get_level_values("date") > train_cut) & (
        ~feats.isna().any(axis=1)
    )
    X = feats[test_mask][FEATURE_NAMES].to_numpy()
    y = labels[feats[test_mask].index].dropna()
    p = model["booster"].predict(feats.loc[y.index, FEATURE_NAMES].to_numpy())
    accuracy = float(((p > 0.5).astype(float) == y.to_numpy()).mean())
    assert accuracy > 0.9  # the deterministic signal must be learned


def test_s4_signals_schedule_and_actions(separable_market):
    prices, sentiment, days = separable_market
    feats = build_features(prices, sentiment)
    labels = make_labels(prices)
    train_cut = days[330]
    model = grid_search_train(
        feats[feats.index.get_level_values("date") <= train_cut],
        labels,
        folds=3,
        search_space=SMALL_SPACE,
    )

    w_start, w_end = days[350], days[-1]
    sig = s4_signals(model, feats, ["AAA", "BBB"], w_start, w_end)
    # schedule: entry day + every trading day in [start, end)
    assert min(sig["decision_date"]) == days[349]
    assert max(sig["decision_date"]) < w_end
    assert set(sig["action"]) <= {"long", "flat"}
    # decisions should track the driving sentiment out of sample
    merged = sig.merge(
        sentiment.rename(columns={"date": "decision_date"}),
        on=["decision_date", "ticker"],
    )
    agree = ((merged["sent_daily"] > 0) == (merged["action"] == "long")).mean()
    assert agree > 0.9


def test_grid_search_deterministic(separable_market):
    prices, sentiment, days = separable_market
    feats = build_features(prices, sentiment)
    labels = make_labels(prices)
    # note: features are complete only after the 200-day ma_50_200 warmup,
    # so the cutoff must leave enough post-warmup rows for 3 folds
    sub = feats[feats.index.get_level_values("date") <= days[380]]
    m1 = grid_search_train(sub, labels, folds=3, search_space=SMALL_SPACE)
    m2 = grid_search_train(sub, labels, folds=3, search_space=SMALL_SPACE)
    assert m1["cv_logloss"] == m2["cv_logloss"]
    assert m1["params"] == m2["params"]
