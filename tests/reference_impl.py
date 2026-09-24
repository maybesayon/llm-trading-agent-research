"""Independent reference implementation of the §4.3 accounting identity.

Purpose (§3.5): reconcile the vectorized engine against a SEPARATE code
path. This is a pure-Python, day-by-day loop using plain dicts and floats —
no pandas vectorization, no code shared with src/backtest/engine.py.

It implements the SAME frozen rules (identity, timing, cost model); it is
independent in implementation, not in specification. Disagreement beyond
floating-point noise indicates an implementation error in one of the two.
"""
from __future__ import annotations

import pandas as pd


def reference_backtest(
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    universe: list,
    cost_bps: float = 10.0,
    rf_daily: float = 0.0,
) -> dict:
    n = len(universe)
    cost_rate = cost_bps / 10_000.0

    # --- plain-python data structures ---------------------------------
    days = sorted({pd.Timestamp(d).normalize() for d in prices["date"]})
    open_of = {}
    for rec in prices.to_dict("records"):
        open_of[(pd.Timestamp(rec["date"]).normalize(), rec["ticker"])] = float(
            rec["open"]
        )

    sig_by_day: dict = {}
    for rec in signals.to_dict("records"):
        d = pd.Timestamp(rec["decision_date"]).normalize()
        sig_by_day.setdefault(d, []).append((rec["ticker"], rec["action"]))

    # --- positions: decided day t-1, effective day t, persist ---------
    positions_per_day = []
    current = {t: 0.0 for t in universe}
    for i, day in enumerate(days):
        if i > 0:
            for ticker, action in sig_by_day.get(days[i - 1], []):
                current[ticker] = 1.0 if action == "long" else 0.0
        positions_per_day.append(dict(current))

    # --- day-by-day accounting -----------------------------------------
    net_list, turnover_list, cost_list = [], [], []
    equity = 1.0
    for i in range(len(days) - 1):
        pos = positions_per_day[i]
        prev = positions_per_day[i - 1] if i > 0 else {t: 0.0 for t in universe}

        turnover = sum(abs(pos[t] - prev[t]) for t in universe) / n
        gross = 0.0
        for t in universe:
            r = open_of[(days[i + 1], t)] / open_of[(days[i], t)] - 1.0
            gross += pos[t] * r
        gross /= n
        cash_weight = 1.0 - sum(pos.values()) / n
        gross += cash_weight * rf_daily

        cost = turnover * cost_rate
        net = gross - cost
        equity *= 1.0 + net

        net_list.append(net)
        turnover_list.append(turnover)
        cost_list.append(cost)

    return {
        "net": net_list,
        "turnover": turnover_list,
        "cost": cost_list,
        "final_equity": equity,
        "cumulative_return": equity - 1.0,
        "total_cost": sum(cost_list),
    }
