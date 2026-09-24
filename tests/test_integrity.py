"""Integrity layer tests — failure paths first: the guards are validated
only when we prove they reject bad data loudly (protocol §3.5)."""
import pandas as pd
import pytest

from src.integrity.checks import (
    DuplicateRecordError,
    InformationSet,
    LookaheadError,
    MissingDataError,
    guard_decision_batch,
    timestamp_granularity,
)


def test_guard_passes_on_clean_batch(synthetic_news, synthetic_prices, last_day_close):
    guard_decision_batch(synthetic_news, synthetic_prices, last_day_close)


def test_injected_future_news_raises(synthetic_news, synthetic_prices, last_day_close):
    future_row = pd.DataFrame(
        [
            {
                "timestamp": last_day_close + pd.Timedelta(days=1),
                "ticker": "AAA",
                "headline": "from the future",
            }
        ]
    )
    poisoned = pd.concat([synthetic_news, future_row], ignore_index=True)
    with pytest.raises(LookaheadError):
        guard_decision_batch(poisoned, synthetic_prices, last_day_close)


def test_injected_future_price_raises(synthetic_news, synthetic_prices, last_day_close):
    future_row = pd.DataFrame(
        [
            {
                "date": last_day_close + pd.Timedelta(days=3),
                "ticker": "AAA",
                "open": 1.0,
                "close": 1.0,
                "volume": 1,
            }
        ]
    )
    poisoned = pd.concat([synthetic_prices, future_row], ignore_index=True)
    with pytest.raises(LookaheadError):
        guard_decision_batch(synthetic_news, poisoned, last_day_close)


def test_missing_price_raises(synthetic_news, synthetic_prices, last_day_close):
    broken = synthetic_prices.copy()
    broken.loc[0, "close"] = None
    with pytest.raises(MissingDataError):
        guard_decision_batch(synthetic_news, broken, last_day_close)


def test_duplicate_price_raises(synthetic_news, synthetic_prices, last_day_close):
    doubled = pd.concat(
        [synthetic_prices, synthetic_prices.iloc[[0]]], ignore_index=True
    )
    with pytest.raises(DuplicateRecordError):
        guard_decision_batch(synthetic_news, doubled, last_day_close)


def test_information_set_filters_future_records(synthetic_news, synthetic_prices):
    days = sorted(synthetic_prices["date"].unique())
    cutoff = pd.Timestamp(days[4]) + pd.Timedelta(hours=16)  # close of day 5

    info = InformationSet(synthetic_news, synthetic_prices, cutoff)
    news, prices = info.decision_batch("BBB")  # must not raise

    assert pd.to_datetime(news["timestamp"]).max() <= cutoff
    assert pd.to_datetime(prices["date"]).max() <= cutoff
    assert len(news) == 5  # BBB has one article per day, days 1-5
    assert len(prices) == 5


def test_granularity_detection(synthetic_news):
    assert timestamp_granularity(synthetic_news, "timestamp") == "intraday"
    date_only = synthetic_news.copy()
    date_only["timestamp"] = pd.to_datetime(date_only["timestamp"]).dt.normalize()
    assert timestamp_granularity(date_only, "timestamp") == "date_only"
