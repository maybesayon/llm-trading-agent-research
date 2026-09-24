"""Mechanical integrity assertions (protocol §3.2–§3.3).

Design rule: guards *raise loudly* instead of silently filtering. The
backtest harness must route every decision-input batch through
`guard_decision_batch`; `InformationSet` provides the point-in-time view
and re-validates its own output (defense in depth).
"""
from __future__ import annotations

import pandas as pd


class IntegrityError(Exception):
    """Base class for all integrity violations."""


class LookaheadError(IntegrityError):
    """A record's timestamp postdates the decision time (§3.2)."""


class MissingDataError(IntegrityError):
    """Required fields contain nulls."""


class DuplicateRecordError(IntegrityError):
    """Duplicate records on a key that must be unique."""


def assert_no_lookahead(df: pd.DataFrame, timestamp_col: str, decision_time) -> None:
    ts = pd.to_datetime(df[timestamp_col])
    violating = ts > pd.Timestamp(decision_time)
    if bool(violating.any()):
        raise LookaheadError(
            f"{int(violating.sum())} record(s) postdate decision time "
            f"{pd.Timestamp(decision_time)} (latest: {ts[violating].max()})"
        )


def assert_no_missing(df: pd.DataFrame, cols) -> None:
    null_counts = df[list(cols)].isnull().sum()
    bad = null_counts[null_counts > 0]
    if not bad.empty:
        raise MissingDataError(f"Null values found: {bad.to_dict()}")


def assert_no_duplicates(df: pd.DataFrame, subset) -> None:
    dup = df.duplicated(subset=list(subset))
    if bool(dup.any()):
        raise DuplicateRecordError(
            f"{int(dup.sum())} duplicate record(s) on key {list(subset)}"
        )


def timestamp_granularity(df: pd.DataFrame, timestamp_col: str) -> str:
    """'intraday' if any timestamp has a time-of-day component, else 'date_only'.

    Determines which §3.2 execution convention applies ([PILOT->PARAM]).
    """
    ts = pd.to_datetime(df[timestamp_col], errors="coerce").dropna()
    if ts.empty:
        return "empty"
    return "date_only" if bool((ts.dt.normalize() == ts).all()) else "intraday"


def guard_decision_batch(
    news: pd.DataFrame,
    prices: pd.DataFrame,
    decision_time,
    *,
    news_ts_col: str = "timestamp",
    price_date_col: str = "date",
) -> None:
    """Run every mechanical assertion on one decision's input batch."""
    assert_no_lookahead(news, news_ts_col, decision_time)
    assert_no_lookahead(prices, price_date_col, decision_time)
    assert_no_missing(prices, ["open", "close"])
    assert_no_duplicates(prices, [price_date_col, "ticker"])


class InformationSet:
    """Point-in-time view over news and prices with a hard cutoff (§3.2).

    Accessors return only records timestamped at or before the cutoff;
    `decision_batch` re-validates the filtered result through
    `guard_decision_batch` so no later code path can widen the view.
    """

    def __init__(
        self,
        news: pd.DataFrame,
        prices: pd.DataFrame,
        cutoff,
        *,
        news_ts_col: str = "timestamp",
        price_date_col: str = "date",
    ):
        self.news = news
        self.prices = prices
        self.cutoff = pd.Timestamp(cutoff)
        self.news_ts_col = news_ts_col
        self.price_date_col = price_date_col

    def visible_news(self, ticker: str | None = None) -> pd.DataFrame:
        df = self.news
        if ticker is not None:
            df = df[df["ticker"] == ticker]
        ts = pd.to_datetime(df[self.news_ts_col])
        return df[ts <= self.cutoff]

    def visible_prices(self, ticker: str | None = None) -> pd.DataFrame:
        df = self.prices
        if ticker is not None:
            df = df[df["ticker"] == ticker]
        dt = pd.to_datetime(df[self.price_date_col])
        return df[dt <= self.cutoff]

    def decision_batch(self, ticker: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        news = self.visible_news(ticker)
        prices = self.visible_prices(ticker)
        guard_decision_batch(
            news,
            prices,
            self.cutoff,
            news_ts_col=self.news_ts_col,
            price_date_col=self.price_date_col,
        )
        return news, prices
