"""S3: sentiment threshold rule (§4.1) with the frozen calibration procedure.

Architecture: the SCORER is an interface. Unit tests use a deterministic
fake scorer; the FinBERT wrapper below is lazy-loaded and only exercised at
pilot time. The rule logic — windowing, thresholding, calibration — is
therefore fully testable with deterministic inputs and no model downloads.

Recorded conventions:
  * Ticker-days with no news in the trailing window have no sentiment and
    map to FLAT (no carry-forward of stale signals).
  * Threshold calibration (frozen, D.3): the threshold is the percentile of
    the POOLED calibration-window sentiment distribution, among
    {30, 40, 50, 60, 70}, that maximizes calibration-window Sharpe; ties
    break to the LOWEST percentile (deterministic).
  * S5 reuses this exact module with the LLM scorer plugged in — identical
    procedure, recalibrated on S5's own score scale (§4.1).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from src.backtest.engine import run_backtest
from src.preprocessing.alignment import articles_in_trailing_window, trading_days
from src.strategies.baselines import entry_decision_day, price_days

CALIBRATION_PERCENTILES = (30, 40, 50, 60, 70)


class SentimentScorer(ABC):
    """Maps texts to scores. Scale is scorer-specific; the calibration
    procedure is scale-free by construction (percentile-based)."""

    @abstractmethod
    def score_texts(self, texts: list) -> list: ...

    def metadata(self) -> dict:
        return {"scorer": type(self).__name__}


class FinBERTScorer(SentimentScorer):
    """ProsusAI/finbert wrapper. Lazy import; NEVER called in unit tests.
    Score = P(positive) - P(negative). Model revision recorded (D.3)."""

    def __init__(self, revision: str | None = None, batch_size: int = 32):
        self.revision = revision
        self.batch_size = batch_size
        self._pipe = None

    def _load(self):
        if self._pipe is None:
            from transformers import pipeline  # lazy: not a test dependency

            self._pipe = pipeline(
                "text-classification",
                model="ProsusAI/finbert",
                revision=self.revision,
                top_k=None,
            )
        return self._pipe

    def score_texts(self, texts: list) -> list:
        pipe = self._load()
        scores = []
        for i in range(0, len(texts), self.batch_size):
            for result in pipe(texts[i : i + self.batch_size]):
                probs = {r["label"].lower(): r["score"] for r in result}
                scores.append(probs.get("positive", 0.0) - probs.get("negative", 0.0))
        return scores

    def metadata(self) -> dict:
        return {
            "scorer": "FinBERT",
            "model": "ProsusAI/finbert",
            "revision": self.revision or "RECORD_AT_DOWNLOAD",
        }


def score_news(news: pd.DataFrame, scorer: SentimentScorer) -> pd.DataFrame:
    """Attach a `score` column. Each article scored exactly once."""
    out = news.copy()
    out["score"] = scorer.score_texts(list(out["headline"]))
    return out


def daily_sentiment(
    scored_news: pd.DataFrame,
    prices: pd.DataFrame,
    universe: list,
    window: int = 3,
    close_time: pd.Timedelta | None = None,
) -> pd.DataFrame:
    """Per (date, ticker): mean score over the trailing news window the
    strategies consume. NaN where the window holds no articles."""
    days = trading_days(prices)
    records = []
    for t in universe:
        for d in days:
            arts = articles_in_trailing_window(
                scored_news, t, d, days, window=window, close_time=close_time
            )
            records.append(
                {
                    "date": d,
                    "ticker": t,
                    "sentiment": float(arts["score"].mean()) if len(arts) else float("nan"),
                }
            )
    return pd.DataFrame(records)


def s3_signals(
    sentiment: pd.DataFrame,
    threshold: float,
    universe: list,
    window_start,
    window_end,
) -> pd.DataFrame:
    """Daily decisions: long next session iff trailing sentiment > threshold.
    Missing sentiment (no news) -> flat. Decision days: the entry day plus
    every trading day in [window_start, window_end)."""
    w_start = pd.Timestamp(window_start).normalize()
    w_end = pd.Timestamp(window_end).normalize()
    days = pd.DatetimeIndex(sorted(sentiment["date"].unique()))
    decision_days = [entry_decision_day(days, w_start)] + list(
        days[(days >= w_start) & (days < w_end)]
    )

    lookup = sentiment.set_index(["date", "ticker"])["sentiment"]
    rows = []
    for d in decision_days:
        for t in universe:
            s = lookup.get((d, t), float("nan"))
            is_long = bool(s == s and s > threshold)  # NaN-safe
            rows.append(
                {"decision_date": d, "ticker": t, "action": "long" if is_long else "flat"}
            )
    return pd.DataFrame(rows)


def calibrate_threshold(
    scored_news: pd.DataFrame,
    prices: pd.DataFrame,
    universe: list,
    cal_start,
    cal_end,
    window: int = 3,
    cost_bps: float = 10.0,
    rf_daily: float = 0.0,
    percentiles: tuple = CALIBRATION_PERCENTILES,
) -> dict:
    """Frozen calibration (D.3): evaluate each percentile of the pooled
    calibration-window sentiment distribution as a threshold; pick the
    calibration-window Sharpe maximizer; ties -> lowest percentile.

    Uses ONLY data within [cal_start, cal_end] — strictly pre-evaluation.
    """
    cal_start = pd.Timestamp(cal_start).normalize()
    cal_end = pd.Timestamp(cal_end).normalize()
    cal_prices = prices[
        (pd.to_datetime(prices["date"]) >= cal_start)
        & (pd.to_datetime(prices["date"]) <= cal_end)
    ].reset_index(drop=True)

    sentiment = daily_sentiment(scored_news, cal_prices, universe, window=window)
    days = price_days(cal_prices)
    if len(days) < 3:
        raise ValueError("Calibration window too short")
    eval_start, eval_end = days[1], days[-1]  # day 0 serves as entry decision day

    pooled = sentiment["sentiment"].dropna()
    if pooled.empty:
        raise ValueError("No sentiment observations in calibration window")

    diagnostics = {}
    best = None
    for p in percentiles:
        thr = float(pooled.quantile(p / 100.0))
        signals = s3_signals(sentiment, thr, universe, eval_start, eval_end)
        res = run_backtest(cal_prices, signals, universe, cost_bps=cost_bps, rf_daily=rf_daily)
        sharpe = res.summary["sharpe_ratio"]
        key = -float("inf") if sharpe != sharpe else sharpe  # NaN never wins
        diagnostics[p] = {"threshold": thr, "sharpe": sharpe}
        if best is None or key > best[0]:  # strict '>': ties keep lowest percentile
            best = (key, p, thr)

    return {
        "percentile": best[1],
        "threshold": best[2],
        "diagnostics": diagnostics,
    }
