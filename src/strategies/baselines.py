"""S1 (buy-and-hold) and S2 (time-series momentum) signal generators (§4.1).

Strategies emit DECISIONS ONLY — frames of (decision_date, ticker, action).
Execution, costs, and accounting are exclusively the engine's job (§4.3).

Entry convention (implementation decision, recorded): strategies decide on
the last trading day BEFORE the evaluation window, so positions are
effective at the open of the window's first day — matching §4.1 'bought at
the start of the window'. The engine must therefore be run on prices from
that entry-decision day through the window end.
"""
from __future__ import annotations

import pandas as pd


def price_days(prices: pd.DataFrame, date_col: str = "date") -> pd.DatetimeIndex:
    days = pd.to_datetime(prices[date_col]).dt.normalize().drop_duplicates().sort_values()
    return pd.DatetimeIndex(days)


def entry_decision_day(days: pd.DatetimeIndex, window_start) -> pd.Timestamp:
    """Last trading day strictly before the evaluation window."""
    window_start = pd.Timestamp(window_start).normalize()
    prior = days[days < window_start]
    if len(prior) == 0:
        raise ValueError(
            f"No trading day before window start {window_start.date()}: "
            "provide pre-window price history for the entry decision."
        )
    return prior[-1]


def month_end_days(days: pd.DatetimeIndex) -> list:
    """Last trading day of each calendar month present in `days`."""
    s = pd.Series(days)
    return list(s.groupby([s.dt.year, s.dt.month]).max())


def s1_buy_and_hold(prices: pd.DataFrame, universe: list, window_start) -> pd.DataFrame:
    """S1: every universe stock long from the start of the window; held."""
    d0 = entry_decision_day(price_days(prices), window_start)
    return pd.DataFrame(
        [{"decision_date": d0, "ticker": t, "action": "long"} for t in universe]
    )


def momentum_signal(
    closes: pd.Series, i: int, lookback: int = 252, skip: int = 21
) -> bool | None:
    """Trailing 12-month return excluding the most recent month (frozen:
    lookback 252 trading days, skip 21 — configs/strategies.yaml).

    Returns True (long), False (flat), or None when history is insufficient.
    """
    if i - lookback < 0:
        return None
    past = float(closes.iloc[i - lookback])
    recent = float(closes.iloc[i - skip])
    return bool(recent / past - 1.0 > 0.0)


def s2_momentum(
    prices: pd.DataFrame,
    universe: list,
    window_start,
    window_end,
    lookback: int = 252,
    skip: int = 21,
) -> pd.DataFrame:
    """S2: long when trailing momentum is positive, else flat; decisions at
    the entry day and at each month-end within the window (monthly refresh,
    §4.1). Insufficient history maps to flat (recorded convention; real runs
    always have the 2019–2021 calibration history behind them)."""
    days = price_days(prices)
    w_start = pd.Timestamp(window_start).normalize()
    w_end = pd.Timestamp(window_end).normalize()

    decision_days = [entry_decision_day(days, w_start)] + [
        d for d in month_end_days(days) if w_start <= d < w_end
    ]

    close_mat = (
        prices.assign(date=pd.to_datetime(prices["date"]).dt.normalize())
        .pivot(index="date", columns="ticker", values="close")
        .sort_index()
    )

    rows = []
    for d in decision_days:
        i = close_mat.index.get_loc(d)
        for t in universe:
            m = momentum_signal(close_mat[t], i, lookback, skip)
            rows.append(
                {
                    "decision_date": d,
                    "ticker": t,
                    "action": "long" if m else "flat",
                }
            )
    return pd.DataFrame(rows)
