"""Backtest engine validated on synthetic signals with hand-computed
outcomes (Phase 2 step 3). No strategy logic, no LLM calls."""
import numpy as np
import pandas as pd
import pytest

from src.backtest.engine import build_positions, run_backtest
from src.integrity.checks import MissingDataError


def make_prices(opens_by_ticker: dict) -> pd.DataFrame:
    n = len(next(iter(opens_by_ticker.values())))
    days = pd.bdate_range("2022-01-03", periods=n)
    rows = []
    for t, opens in opens_by_ticker.items():
        for d, o in zip(days, opens):
            rows.append(
                {"date": d, "ticker": t, "open": o, "close": o, "volume": 100}
            )
    return pd.DataFrame(rows)


def sig(day, ticker, action):
    return {"decision_date": day, "ticker": ticker, "action": action}


def test_all_flat_earns_risk_free_only():
    prices = make_prices({"AAA": [100, 90, 80, 120]})
    signals = pd.DataFrame(columns=["decision_date", "ticker", "action"])
    res = run_backtest(prices, signals, ["AAA"], cost_bps=25.0, rf_daily=0.001)
    assert np.allclose(res.daily["net_return"], 0.001)  # cash earns rf, no costs
    assert res.summary["total_cost"] == 0.0
    assert res.summary["annualized_turnover"] == 0.0


def test_buy_and_hold_equity_equals_price_ratio_at_zero_cost():
    opens = [100.0, 101.0, 103.0, 99.0, 110.0]
    prices = make_prices({"AAA": opens})
    days = sorted(prices["date"].unique())
    signals = pd.DataFrame([sig(days[0], "AAA", "long")])  # decide day 1, enter open day 2
    res = run_backtest(prices, signals, ["AAA"], cost_bps=0.0, rf_daily=0.0)
    assert np.isclose(res.equity.iloc[-1], opens[-1] / opens[1])  # 110/101


def test_hand_computed_costs_round_trip():
    # O = [100, 100, 110, 110]; long decided d1 (enter open d2),
    # flat decided d2 (exit open d3); cost 100 bps per side.
    prices = make_prices({"AAA": [100.0, 100.0, 110.0, 110.0]})
    days = sorted(prices["date"].unique())
    signals = pd.DataFrame([sig(days[0], "AAA", "long"), sig(days[1], "AAA", "flat")])
    res = run_backtest(prices, signals, ["AAA"], cost_bps=100.0, rf_daily=0.0)
    expected_daily = [0.0, 0.10 - 0.01, 0.0 - 0.01]  # d1 flat; d2 +10% -1%; d3 exit cost
    assert np.allclose(res.daily["net_return"], expected_daily)
    assert np.isclose(res.equity.iloc[-1], 1.0 * 1.09 * 0.99)


def test_equal_weight_two_tickers_with_cash_slot():
    # AAA long from day 2 (+10% on d2), BBB never held -> its slot is cash.
    prices = make_prices({"AAA": [100, 100, 110], "BBB": [50, 50, 50]})
    days = sorted(prices["date"].unique())
    signals = pd.DataFrame([sig(days[0], "AAA", "long")])
    res = run_backtest(prices, signals, ["AAA", "BBB"], cost_bps=0.0, rf_daily=0.002)
    # d1: all cash -> 0.002; d2: 0.5*0.10 + 0.5*0.002
    assert np.allclose(res.daily["net_return"], [0.002, 0.05 + 0.001])


def test_decision_never_touches_same_day_open():
    # Structural look-ahead check: a huge same-day move must not be captured.
    # Decision on d2 (spike day) executes at open d3; return d3->d4 is flat.
    prices = make_prices({"AAA": [100.0, 100.0, 200.0, 200.0]})
    days = sorted(prices["date"].unique())
    signals = pd.DataFrame([sig(days[1], "AAA", "long")])
    res = run_backtest(prices, signals, ["AAA"], cost_bps=0.0)
    # d1: flat 0; d2: flat 0 (missed the +100% jump into d3); d3: long, 200->200 = 0
    assert np.allclose(res.daily["net_return"], [0.0, 0.0, 0.0])


def test_positions_persist_until_changed():
    prices = make_prices({"AAA": [1, 1, 1, 1, 1, 1]})
    days = sorted(prices["date"].unique())
    signals = pd.DataFrame([sig(days[1], "AAA", "long")])
    pos, ignored = build_positions(
        signals, pd.DatetimeIndex(pd.to_datetime(days)), ["AAA"]
    )
    assert list(pos["AAA"]) == [0, 0, 1, 1, 1, 1]  # effective d3 onward, persists
    assert ignored == 0


def test_last_day_signal_is_counted_not_silently_dropped():
    prices = make_prices({"AAA": [100, 101, 102]})
    days = sorted(prices["date"].unique())
    signals = pd.DataFrame([sig(days[-1], "AAA", "long")])
    res = run_backtest(prices, signals, ["AAA"], cost_bps=0.0)
    assert res.summary["ignored_signals"] == 1
    assert np.allclose(res.daily["net_return"], [0.0, 0.0])


def test_rejects_bad_inputs():
    prices = make_prices({"AAA": [100, 101, 102]})
    days = sorted(prices["date"].unique())
    with pytest.raises(ValueError, match="Unknown actions"):
        run_backtest(prices, pd.DataFrame([sig(days[0], "AAA", "short")]), ["AAA"])
    with pytest.raises(ValueError, match="outside universe"):
        run_backtest(prices, pd.DataFrame([sig(days[0], "ZZZ", "long")]), ["AAA"])
    with pytest.raises(ValueError, match="not trading days"):
        run_backtest(
            prices, pd.DataFrame([sig("2022-01-08", "AAA", "long")]), ["AAA"]
        )  # a Saturday
    broken = prices.copy()
    broken.loc[0, "open"] = None
    with pytest.raises(MissingDataError):
        run_backtest(broken, pd.DataFrame(columns=["decision_date", "ticker", "action"]), ["AAA"])


def test_summary_metrics_consistency():
    prices = make_prices({"AAA": [100.0, 100.0, 105.0, 102.9, 108.045]})
    days = sorted(prices["date"].unique())
    signals = pd.DataFrame([sig(days[0], "AAA", "long")])
    res = run_backtest(prices, signals, ["AAA"], cost_bps=0.0)
    assert np.isclose(
        res.summary["cumulative_return"], res.equity.iloc[-1] - 1.0
    )
    assert res.summary["max_drawdown"] <= 0.0
    assert res.summary["n_return_days"] == 4
