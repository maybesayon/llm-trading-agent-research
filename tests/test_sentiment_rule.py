"""S3 rule logic validated with a deterministic fake scorer — no model
downloads, no network (Phase 2 discipline)."""
import numpy as np
import pandas as pd
import pytest

from src.backtest.engine import run_backtest
from src.preprocessing.alignment import articles_in_trailing_window, trading_days
from src.strategies.sentiment_rule import (
    SentimentScorer,
    calibrate_threshold,
    daily_sentiment,
    s3_signals,
    score_news,
)


class FakeScorer(SentimentScorer):
    """Deterministic keyword scorer: 'good' -> +1, 'bad' -> -1, else 0."""

    def score_texts(self, texts):
        out = []
        for t in texts:
            low = t.lower()
            out.append(1.0 if "good" in low else (-1.0 if "bad" in low else 0.0))
        return out


def make_market(n_days, opens, news_items):
    days = pd.bdate_range("2022-01-03", periods=n_days)
    prices = pd.DataFrame(
        [
            {"date": d, "ticker": "AAA", "open": o, "close": o, "volume": 100}
            for d, o in zip(days, opens)
        ]
    )
    news = pd.DataFrame(
        [
            {
                "timestamp": pd.Timestamp(days[i]) + pd.Timedelta(hours=10),
                "ticker": "AAA",
                "headline": text,
            }
            for i, text in news_items
        ]
    )
    return prices, news, days


@pytest.fixture
def simple_market():
    # good news day 1 (index 0), bad news day 5 (index 4), 10 flat days
    return make_market(10, [100.0] * 10, [(0, "good results"), (4, "bad outlook")])


def test_daily_sentiment_windows(simple_market):
    prices, news, days = simple_market
    scored = score_news(news, FakeScorer())
    sent = daily_sentiment(scored, prices, ["AAA"], window=3)
    s = sent.set_index("date")["sentiment"]
    assert s[days[0]] == 1.0 and s[days[1]] == 1.0 and s[days[2]] == 1.0
    assert np.isnan(s[days[3]])            # window {d2,d3,d4}: empty
    assert s[days[4]] == -1.0 and s[days[6]] == -1.0
    assert np.isnan(s[days[7]])            # bad article fell out of window


def test_s3_signal_actions_hand_computed(simple_market):
    prices, news, days = simple_market
    scored = score_news(news, FakeScorer())
    sent = daily_sentiment(scored, prices, ["AAA"], window=3)
    sig = s3_signals(sent, 0.0, ["AAA"], days[1], days[-1])
    actions = sig.set_index("decision_date")["action"]
    # long only while good news is in the trailing window (decisions d1-d3)
    expected_long = {days[0], days[1], days[2]}
    for d, a in actions.items():
        assert a == ("long" if d in expected_long else "flat")
    # NaN sentiment (d4) and negative sentiment (d5-d7) both map to flat
    assert actions[days[3]] == "flat" and actions[days[4]] == "flat"


def test_s3_through_engine_positions(simple_market):
    prices, news, days = simple_market
    scored = score_news(news, FakeScorer())
    sent = daily_sentiment(scored, prices, ["AAA"], window=3)
    sig = s3_signals(sent, 0.0, ["AAA"], days[1], days[-1])
    res = run_backtest(prices, sig, ["AAA"], cost_bps=0.0)
    held = [d for d in res.positions.index if res.positions.loc[d, "AAA"] == 1.0]
    assert held == [days[1], days[2], days[3]]  # decisions d1-d3 -> positions d2-d4


def test_intraday_close_time_cutoff():
    """Article published AFTER the close must not enter that day's decision
    when the intraday convention is active ([PILOT->PARAM], §3.2)."""
    prices, _, days = make_market(4, [100.0] * 4, [])
    news = pd.DataFrame(
        [
            {
                "timestamp": pd.Timestamp(days[1]) + pd.Timedelta(hours=17),  # 5pm
                "ticker": "AAA",
                "headline": "good after hours",
            }
        ]
    )
    tdays = trading_days(prices)
    after_close = articles_in_trailing_window(
        news, "AAA", days[1], tdays, close_time=pd.Timedelta(hours=16)
    )
    assert len(after_close) == 0  # excluded from day-2 decision
    next_day = articles_in_trailing_window(
        news, "AAA", days[2], tdays, close_time=pd.Timedelta(hours=16)
    )
    assert len(next_day) == 1  # usable the following day
    date_only = articles_in_trailing_window(news, "AAA", days[1], tdays)
    assert len(date_only) == 1  # date-only convention includes it


@pytest.fixture
def calibration_market():
    """Perfect-signal market: good news on days i%6==0 precedes a +2% move
    for the position entered off that signal; bad news on i%6==3; drift
    -0.1% otherwise. The Sharpe-maximizing threshold must admit good-news
    days and exclude everything else."""
    n = 60
    good = {i for i in range(n) if i % 6 == 0}
    bad = {i for i in range(n) if i % 6 == 3}
    opens = [100.0]
    for i in range(1, n):
        # Return ROW j = open(j+1)/open(j) is row i-1 here. The position
        # entered off good news dated g starts day g+1 and earns row g+1,
        # so the +2% must sit at row j = g+1, i.e. (i-1)-1 = i-2 in good.
        # (An earlier version keyed this to i-1: the move then coincided
        # with the news day itself and the engine — correctly — could not
        # reach it. The engine's look-ahead prevention caught the fixture.)
        r = 1.02 if (i - 2) in good else 0.999
        opens.append(opens[-1] * r)
    items = [(i, "good results") for i in sorted(good)] + [
        (i, "bad outlook") for i in sorted(bad)
    ]
    return make_market(n, opens, items)


def test_calibration_selects_sharpe_maximizer(calibration_market):
    prices, news, days = calibration_market
    scored = score_news(news, FakeScorer())
    result = calibrate_threshold(
        scored, prices, ["AAA"], days[0], days[-1], cost_bps=0.0
    )
    assert result["percentile"] in (30, 40, 50, 60, 70)
    assert set(result["diagnostics"].keys()) == {30, 40, 50, 60, 70}
    chosen = result["diagnostics"][result["percentile"]]["sharpe"]
    finite = [
        d["sharpe"] for d in result["diagnostics"].values() if d["sharpe"] == d["sharpe"]
    ]
    assert chosen == max(finite)
    assert chosen > 0  # economic sanity: the perfect signal is profitable
    # ties break to the LOWEST percentile (deterministic frozen rule)
    tied = [
        p for p, d in result["diagnostics"].items() if d["sharpe"] == chosen
    ]
    assert result["percentile"] == min(tied)


def test_calibration_deterministic(calibration_market):
    prices, news, days = calibration_market
    scored = score_news(news, FakeScorer())
    r1 = calibrate_threshold(scored, prices, ["AAA"], days[0], days[-1])
    r2 = calibrate_threshold(scored, prices, ["AAA"], days[0], days[-1])
    assert r1["percentile"] == r2["percentile"]
    assert r1["threshold"] == r2["threshold"]
    for p in r1["diagnostics"]:
        a, b = r1["diagnostics"][p]["sharpe"], r2["diagnostics"][p]["sharpe"]
        assert (a != a and b != b) or a == b  # NaN-aware equality


def test_calibration_requires_sentiment(simple_market):
    prices, _, days = simple_market
    empty = pd.DataFrame(columns=["timestamp", "ticker", "headline", "score"])
    with pytest.raises(ValueError, match="No sentiment"):
        calibrate_threshold(empty, prices, ["AAA"], days[0], days[-1])
