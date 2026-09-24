"""S1/S2 signal-generation tests: timing, rebalancing frequency, sizing,
cash handling, and window edges (Phase 2 Step 4)."""
import numpy as np
import pandas as pd
import pytest

from src.backtest.engine import run_backtest
from src.strategies.baselines import (
    entry_decision_day,
    momentum_signal,
    month_end_days,
    price_days,
    s1_buy_and_hold,
    s2_momentum,
)


def make_history(n_days: int, formulas: dict, start="2021-01-04") -> pd.DataFrame:
    """Deterministic synthetic history; formulas: ticker -> f(i) -> price."""
    days = pd.bdate_range(start, periods=n_days)
    rows = []
    for t, f in formulas.items():
        for i, d in enumerate(days):
            p = float(f(i))
            assert p > 0, f"non-positive synthetic price for {t} at {i}"
            rows.append(
                {"date": d, "ticker": t, "open": p, "close": p, "volume": 100}
            )
    return pd.DataFrame(rows)


@pytest.fixture
def history():
    # AAA: steady uptrend. CCC: uptrend until day 255, then decline.
    return make_history(
        320,
        {
            "AAA": lambda i: 100.0 + 0.2 * i,
            "CCC": lambda i: 150.0 + 0.2 * min(i, 255) - 2.2 * max(i - 255, 0),
        },
    )


def window_of(history):
    days = price_days(history)
    return days[270], days[-1]  # window start, end


# ---------- signal timing ----------

def test_s1_decides_on_last_prewindow_day(history):
    w_start, _ = window_of(history)
    days = price_days(history)
    sig = s1_buy_and_hold(history, ["AAA", "CCC"], w_start)
    assert set(sig["decision_date"]) == {days[269]}  # strictly before window
    assert set(sig["action"]) == {"long"}
    assert len(sig) == 2  # one row per universe ticker


def test_s1_position_effective_first_window_day(history):
    w_start, _ = window_of(history)
    days = price_days(history)
    frame = history[history["date"] >= days[269]]  # entry day through end
    sig = s1_buy_and_hold(history, ["AAA", "CCC"], w_start)
    res = run_backtest(frame, sig, ["AAA", "CCC"], cost_bps=0.0)
    assert (res.positions.loc[days[269]] == 0.0).all()   # decision day: still cash
    assert (res.positions.loc[w_start] == 1.0).all()     # start of window: invested


def test_entry_requires_prewindow_history(history):
    days = price_days(history)
    with pytest.raises(ValueError, match="No trading day before"):
        entry_decision_day(days, days[0])


# ---------- rebalancing frequency ----------

def test_s2_decision_schedule_is_entry_plus_month_ends(history):
    w_start, w_end = window_of(history)
    days = price_days(history)
    sig = s2_momentum(history, ["AAA", "CCC"], w_start, w_end)
    expected = {days[269]} | {
        d for d in month_end_days(days) if w_start <= d < w_end
    }
    assert set(sig["decision_date"]) == expected
    assert len(expected) >= 3  # entry + at least two in-window month-ends


def test_s2_positions_change_only_after_decision_days(history):
    w_start, w_end = window_of(history)
    days = price_days(history)
    frame = history[history["date"] >= days[269]]
    sig = s2_momentum(history, ["AAA", "CCC"], w_start, w_end)
    res = run_backtest(frame, sig, ["AAA", "CCC"], cost_bps=0.0)

    decision_days = set(sig["decision_date"])
    pos = res.positions
    changes = pos.diff().abs().sum(axis=1)
    change_days = set(pos.index[changes > 0])
    # a change on day d must follow a decision on the previous trading day
    day_list = list(pos.index)
    for d in change_days:
        prev = day_list[day_list.index(d) - 1]
        assert prev in decision_days


# ---------- momentum rule ----------

def test_momentum_signal_hand_cases():
    up = pd.Series([100.0 + i for i in range(300)])
    down = pd.Series([400.0 - i for i in range(300)])
    assert momentum_signal(up, 299) is True
    assert momentum_signal(down, 299) is False
    assert momentum_signal(up, 100) is None  # < 252 days of history


def test_s2_uptrend_long_crashed_flat(history):
    """CCC crashes from day 255; momentum at the last in-window month-end
    (close[d-21] vs close[d-252]) must have turned negative -> flat, while
    AAA stays long throughout."""
    w_start, w_end = window_of(history)
    sig = s2_momentum(history, ["AAA", "CCC"], w_start, w_end)
    by = sig.set_index(["decision_date", "ticker"])["action"]

    days_sorted = sorted(set(sig["decision_date"]))
    first, last = days_sorted[0], days_sorted[-1]
    assert by[(first, "AAA")] == "long"
    assert by[(first, "CCC")] == "long"   # crash not yet visible past skip window
    assert by[(last, "AAA")] == "long"
    assert by[(last, "CCC")] == "flat"    # crash dominates the lookback


# ---------- sizing, cash, and window edges ----------

def test_equal_weight_sizing_and_cash_handling(history):
    w_start, w_end = window_of(history)
    days = price_days(history)
    frame = history[history["date"] >= days[269]]
    sig = s2_momentum(history, ["AAA", "CCC"], w_start, w_end)
    res = run_backtest(frame, sig, ["AAA", "CCC"], cost_bps=0.0, rf_daily=0.001)

    # when CCC is flat, its slot must sit in cash: cash_weight = 0.5
    flat_days = res.daily.index[res.daily["cash_weight"] == 0.5]
    assert len(flat_days) > 0
    # and on those days half the rf accrues
    aaa_ret = (
        frame.pivot(index="date", columns="ticker", values="open")["AAA"]
        .pct_change()
        .shift(-1)
    )
    d = flat_days[0]
    expected = 0.5 * aaa_ret.loc[d] + 0.5 * 0.001
    assert np.isclose(res.daily.loc[d, "net_return"], expected)


def test_no_signals_after_window_end(history):
    w_start, w_end = window_of(history)
    sig = s2_momentum(history, ["AAA", "CCC"], w_start, w_end)
    assert (pd.to_datetime(sig["decision_date"]) < w_end).all()
