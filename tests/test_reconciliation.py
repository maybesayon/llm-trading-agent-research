"""Engine vs. independent reference implementation (§3.5 reconciliation).

Both code paths implement the same frozen rules; any disagreement beyond
floating-point noise (1e-12) is an implementation error and blocks Phase 2.
"""
import math

import numpy as np
import pandas as pd
import pytest

from src.backtest.engine import run_backtest
from src.strategies.baselines import price_days, s1_buy_and_hold, s2_momentum
from tests.reference_impl import reference_backtest

UNIVERSE = ["AAA", "BBB", "CCC"]
COST_BPS = 10.0
RF_DAILY = 0.0001


@pytest.fixture
def market():
    """Deterministic 320-day market: trend + oscillation + one crash ticker
    so S2 produces in-window position changes (nontrivial turnover/costs)."""
    days = pd.bdate_range("2021-01-04", periods=320)
    formulas = {
        "AAA": lambda i: 100.0 + 0.05 * i + 2.0 * math.sin(i / 7.0),
        "BBB": lambda i: 55.0 + 0.03 * i + 1.5 * math.sin(i / 11.0 + 1.0),
        "CCC": lambda i: 150.0 + 0.2 * min(i, 255) - 2.2 * max(i - 255, 0),
    }
    rows = []
    for t, f in formulas.items():
        for i, d in enumerate(days):
            o = float(f(i))
            assert o > 0
            rows.append(
                {"date": d, "ticker": t, "open": o, "close": o * 1.001, "volume": 100}
            )
    return pd.DataFrame(rows)


def _frame_and_window(market):
    days = price_days(market)
    w_start, w_end = days[270], days[-1]
    frame = market[market["date"] >= days[269]].reset_index(drop=True)
    return frame, w_start, w_end


def _reconcile(frame, signals):
    engine = run_backtest(frame, signals, UNIVERSE, cost_bps=COST_BPS, rf_daily=RF_DAILY)
    ref = reference_backtest(frame, signals, UNIVERSE, cost_bps=COST_BPS, rf_daily=RF_DAILY)

    assert np.allclose(engine.daily["net_return"], ref["net"], atol=1e-12)
    assert np.allclose(engine.daily["turnover"], ref["turnover"], atol=1e-12)
    assert np.allclose(engine.daily["cost"], ref["cost"], atol=1e-12)
    assert math.isclose(
        float(engine.equity.iloc[-1]), ref["final_equity"], rel_tol=1e-12
    )
    assert math.isclose(
        engine.summary["cumulative_return"], ref["cumulative_return"], rel_tol=1e-12,
    )
    assert math.isclose(
        engine.summary["total_cost"], ref["total_cost"], rel_tol=1e-12
    )
    return engine


def test_s1_engine_matches_reference(market):
    frame, w_start, _ = _frame_and_window(market)
    signals = s1_buy_and_hold(market, UNIVERSE, w_start)
    engine = _reconcile(frame, signals)
    # sanity: S1 fully invested from window start, one entry cost, no more
    assert engine.summary["total_cost"] == pytest.approx(COST_BPS / 10_000.0)
    assert (engine.daily["cash_weight"].iloc[1:] == 0.0).all()


def test_s2_engine_matches_reference(market):
    frame, w_start, w_end = _frame_and_window(market)
    signals = s2_momentum(market, UNIVERSE, w_start, w_end)
    engine = _reconcile(frame, signals)
    # sanity: the crash ticker forces at least one in-window position change
    assert engine.daily["turnover"].iloc[1:].sum() > 0


def test_benchmark_relative_metrics_consistent(market):
    """S2-minus-S1 daily excess computed from both code paths agrees."""
    frame, w_start, w_end = _frame_and_window(market)
    s1 = s1_buy_and_hold(market, UNIVERSE, w_start)
    s2 = s2_momentum(market, UNIVERSE, w_start, w_end)

    e1 = run_backtest(frame, s1, UNIVERSE, cost_bps=COST_BPS, rf_daily=RF_DAILY)
    e2 = run_backtest(frame, s2, UNIVERSE, cost_bps=COST_BPS, rf_daily=RF_DAILY)
    r1 = reference_backtest(frame, s1, UNIVERSE, cost_bps=COST_BPS, rf_daily=RF_DAILY)
    r2 = reference_backtest(frame, s2, UNIVERSE, cost_bps=COST_BPS, rf_daily=RF_DAILY)

    excess_engine = e2.daily["net_return"].values - e1.daily["net_return"].values
    excess_ref = np.array(r2["net"]) - np.array(r1["net"])
    assert np.allclose(excess_engine, excess_ref, atol=1e-12)
