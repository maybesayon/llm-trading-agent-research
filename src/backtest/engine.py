"""Backtest engine implementing the §4.3 accounting identity.

Contract (§3.2/§4.3):
  * A signal carries a *decision date* t (information set: <= close of t).
  * The position becomes effective at the NEXT session's open, open(t+1),
    and earns the open-to-open return open(t+1) -> open(t+2).
  * Look-ahead is prevented structurally: a decision dated t cannot, by
    construction, touch any price before open(t+1).

Accounting identity (per §4.3):
  daily net return = (1/N) * sum_i pos_i * r_i  +  (cash_weight * rf_daily)
                     - turnover * cost_rate
  where N is the universe size (equal-weight slots), pos_i in {0, 1}
  (long/flat, no shorting, no leverage), turnover = (1/N) * sum_i |Δpos_i|,
  and cost_rate = cost_bps / 10,000 charged per side (each slot change is
  one trade).

Signals whose decision date is the final trading day execute outside the
window and are counted in `summary["ignored_signals"]`, never silently
dropped.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.evaluation.metrics import TRADING_DAYS_PER_YEAR, summarize
from src.integrity.checks import MissingDataError

ACTIONS = {"long": 1.0, "flat": 0.0}


@dataclass
class BacktestResult:
    daily: pd.DataFrame  # per return-bearing day: gross, cost, net, turnover, cash_weight
    positions: pd.DataFrame  # per execution day x ticker (0/1)
    equity: pd.Series  # cumulative growth of 1.0
    summary: dict


def _open_matrix(prices: pd.DataFrame, universe: list) -> pd.DataFrame:
    mat = (
        prices.assign(date=pd.to_datetime(prices["date"]).dt.normalize())
        .pivot(index="date", columns="ticker", values="open")
        .sort_index()
    )
    missing = [t for t in universe if t not in mat.columns]
    if missing:
        raise ValueError(f"Universe tickers missing from prices: {missing}")
    mat = mat[list(universe)]
    if bool(mat.isnull().any().any()):
        raise MissingDataError("Null open prices in backtest window")
    return mat


def build_positions(
    signals: pd.DataFrame, days: pd.DatetimeIndex, universe: list
) -> tuple[pd.DataFrame, int]:
    """Map decision-dated signals to per-execution-day positions.

    Positions persist until changed. Day 0 starts all-cash (flat).
    Returns (positions frame, count of ignored signals).
    """
    sig = signals.copy()
    sig["decision_date"] = pd.to_datetime(sig["decision_date"]).dt.normalize()

    unknown_actions = set(sig["action"]) - set(ACTIONS)
    if unknown_actions:
        raise ValueError(f"Unknown actions: {unknown_actions}")
    unknown_tickers = set(sig["ticker"]) - set(universe)
    if unknown_tickers:
        raise ValueError(f"Signals for tickers outside universe: {unknown_tickers}")
    off_calendar = set(sig["decision_date"]) - set(days)
    if off_calendar:
        raise ValueError(
            f"Signal decision dates are not trading days: {sorted(off_calendar)}"
        )

    ignored = int((sig["decision_date"] == days[-1]).sum())  # executes beyond window

    by_day = dict(tuple(sig.groupby("decision_date")))
    pos = pd.DataFrame(0.0, index=days, columns=list(universe))
    current = {t: 0.0 for t in universe}
    for i, day in enumerate(days):
        if i > 0:
            decided = by_day.get(days[i - 1])
            if decided is not None:
                for _, row in decided.iterrows():
                    current[row["ticker"]] = ACTIONS[row["action"]]
        pos.iloc[i] = [current[t] for t in universe]
    return pos, ignored


def run_backtest(
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    universe: list,
    cost_bps: float = 10.0,
    rf_daily: float = 0.0,
) -> BacktestResult:
    """Run the §4.3 accounting over one window.

    `signals` columns: decision_date, ticker, action ('long'|'flat').
    `rf_daily` is a constant daily risk-free rate (a series variant is a
    pilot-phase extension; the identity is unchanged).
    """
    opens = _open_matrix(prices, universe)
    days = opens.index
    if len(days) < 2:
        raise ValueError("Need at least two trading days for one return")
    n = len(universe)
    cost_rate = cost_bps / 10_000.0

    pos, ignored = build_positions(signals, days, universe)

    # Open-to-open return earned by positions held on day i (entered at open i).
    rets = (opens.shift(-1) / opens - 1.0).iloc[:-1]
    pos_active = pos.iloc[:-1]

    turnover = pos.diff().abs().sum(axis=1)
    turnover.iloc[0] = pos.iloc[0].abs().sum()  # entry from all-cash
    turnover = (turnover / n).iloc[:-1]  # final-open changes earn nothing in-window

    long_weight = pos_active.sum(axis=1) / n
    cash_weight = 1.0 - long_weight
    gross = (pos_active * rets).sum(axis=1) / n + cash_weight * rf_daily
    cost = turnover * cost_rate
    net = gross - cost

    equity = (1.0 + net).cumprod()
    daily = pd.DataFrame(
        {
            "gross_return": gross,
            "cost": cost,
            "net_return": net,
            "turnover": turnover,
            "cash_weight": cash_weight,
        }
    )

    summary = summarize(net, rf_daily=rf_daily)  # single source of truth (§4.4)
    summary.update(
        {
            "annualized_turnover": float(turnover.mean() * TRADING_DAYS_PER_YEAR),
            "total_cost": float(cost.sum()),
            "ignored_signals": ignored,
            "n_return_days": int(len(net)),
        }
    )
    return BacktestResult(daily=daily, positions=pos, equity=equity, summary=summary)
