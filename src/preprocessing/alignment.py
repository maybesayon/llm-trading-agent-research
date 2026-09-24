"""News-to-trading-day alignment and the §3.5 density metrics (M1/M2)."""
from __future__ import annotations

import pandas as pd


def trading_days(prices: pd.DataFrame, date_col: str = "date") -> pd.DatetimeIndex:
    days = pd.to_datetime(prices[date_col]).dt.normalize().drop_duplicates().sort_values()
    return pd.DatetimeIndex(days)


def articles_in_trailing_window(
    news: pd.DataFrame,
    ticker: str,
    day,
    days: pd.DatetimeIndex,
    window: int = 3,
    ts_col: str = "timestamp",
    close_time: pd.Timedelta | None = None,
) -> pd.DataFrame:
    """Articles for `ticker` dated within the trailing `window` trading days
    ending at `day` (inclusive), timestamped no later than the day-`day`
    cutoff.

    Cutoff convention ([PILOT->PARAM], §3.2): `close_time=None` applies the
    date-only convention (an article dated `day` is assumed available by that
    day's close, hence usable for the decision executing at the next open).
    If the pilot finds intraday timestamps, pass the exchange close (e.g.,
    `pd.Timedelta(hours=16)`) so same-day articles published after the close
    are excluded from the day's decision.

    This is the exact news window the text-based strategies consume, so the
    M1 criterion measures what the strategies actually read (§3.5).
    """
    day = pd.Timestamp(day).normalize()
    i = days.get_loc(day)
    lo = max(0, i - window + 1)
    window_days = set(days[lo : i + 1])

    cutoff = day + (
        close_time
        if close_time is not None
        else pd.Timedelta(hours=23, minutes=59, seconds=59)
    )

    df = news[news["ticker"] == ticker]
    ts = pd.to_datetime(df[ts_col], errors="coerce")
    valid = ts.notna()
    dated = ts.dt.normalize().isin(window_days)
    close_ok = ts <= cutoff
    return df[valid & dated & close_ok]


def compute_m1(
    news: pd.DataFrame,
    prices: pd.DataFrame,
    ticker: str,
    window: int = 3,
    ts_col: str = "timestamp",
    date_col: str = "date",
) -> float:
    """M1: fraction of trading days with >=1 timestamp-valid article in the
    trailing `window` trading days (§3.5 availability metric)."""
    days = trading_days(prices, date_col)
    if len(days) == 0:
        return 0.0
    covered = sum(
        1
        for d in days
        if len(articles_in_trailing_window(news, ticker, d, days, window, ts_col)) > 0
    )
    return covered / len(days)


def compute_m2(news: pd.DataFrame, ticker: str, ts_col: str = "timestamp") -> float:
    """M2: fraction of a ticker's articles with a usable (parseable) timestamp."""
    df = news[news["ticker"] == ticker]
    if len(df) == 0:
        return 0.0
    ts = pd.to_datetime(df[ts_col], errors="coerce")
    return float(ts.notna().mean())


def density_report(
    news: pd.DataFrame,
    prices: pd.DataFrame,
    tickers,
    m1_threshold: float = 0.90,
    m2_threshold: float = 0.95,
    window: int = 3,
) -> pd.DataFrame:
    """Per-ticker M1/M2 against the frozen thresholds. Availability only —
    deliberately blind to signal quality (§3.5)."""
    rows = []
    for t in tickers:
        m1 = compute_m1(news, prices, t, window)
        m2 = compute_m2(news, t)
        rows.append(
            {
                "ticker": t,
                "m1": m1,
                "m2": m2,
                "passes": bool(m1 >= m1_threshold and m2 >= m2_threshold),
            }
        )
    return pd.DataFrame(rows)
