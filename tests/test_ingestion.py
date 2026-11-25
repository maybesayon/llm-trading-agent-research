"""Ingestion validation: schema enforcement and offline CSV round-trips."""
import pandas as pd
import pytest

from src.data_ingestion.news import CSVNewsSource, validate_news_frame
from src.data_ingestion.prices import CSVPriceSource, validate_price_frame
from src.integrity.checks import DuplicateRecordError


def test_csv_price_source_roundtrip(tmp_path, synthetic_prices):
    path = tmp_path / "prices.csv"
    synthetic_prices.to_csv(path, index=False)
    got = CSVPriceSource(path).fetch(["AAA"], "2022-01-03", "2022-01-07")
    assert set(got["ticker"]) == {"AAA"}
    assert len(got) == 5  # 5 business days in range
    assert got["date"].is_monotonic_increasing


def test_price_validation_rejects_missing_column(synthetic_prices):
    with pytest.raises(ValueError, match="missing columns"):
        validate_price_frame(synthetic_prices.drop(columns=["open"]))


def test_price_validation_rejects_duplicates(synthetic_prices):
    doubled = pd.concat([synthetic_prices, synthetic_prices.iloc[[0]]], ignore_index=True)
    with pytest.raises(DuplicateRecordError):
        validate_price_frame(doubled)


def test_news_column_map_and_timestamp_parsing(tmp_path, synthetic_news):
    raw = synthetic_news.rename(
        columns={"timestamp": "Date", "ticker": "Stock_symbol", "headline": "Article_title"}
    )
    path = tmp_path / "news.csv"
    raw.to_csv(path, index=False)
    got = CSVNewsSource(
        path,
        column_map={"Date": "timestamp", "Stock_symbol": "ticker", "Article_title": "headline"},
    ).fetch()
    assert list(got.columns) == ["timestamp", "ticker", "headline"]
    assert pd.api.types.is_datetime64_any_dtype(got["timestamp"])
    assert len(got) == len(synthetic_news)


def test_news_unparseable_timestamp_becomes_nat_not_error(synthetic_news):
    broken = pd.concat(
        [
            synthetic_news,
            pd.DataFrame(
                [{"timestamp": "not-a-date", "ticker": "AAA", "headline": "bad ts"}]
            ),
        ],
        ignore_index=True,
    )
    got = validate_news_frame(broken)  # NaT feeds M2, not an exception
    assert got["timestamp"].isna().sum() == 1


def test_news_utc_labelled_timestamps_keep_their_date():
    # FNSPID format: date-only records stamped "00:00:00 UTC"
    raw = pd.DataFrame(
        {
            "timestamp": ["2022-01-04 00:00:00 UTC", "2022-01-03 20:00:00 UTC"],
            "ticker": ["AAA", "AAA"],
            "headline": ["dated jan 4", "dated jan 3"],
        }
    )
    got = validate_news_frame(raw)
    assert got["timestamp"].dt.tz is None  # comparable with exchange dates
    assert list(got["timestamp"].dt.date.astype(str)) == ["2022-01-03", "2022-01-04"]


def test_news_mixed_timestamp_formats_all_parse():
    # merged corpus: FNSPID "... UTC" rows alongside unlabelled rows
    raw = pd.DataFrame(
        {
            "timestamp": ["2022-01-03 00:00:00 UTC", "2022-01-04 00:00:00 UTC",
                          "2022-01-03 12:15:00", "2022-01-04 09:30:00"],
            "ticker": ["AAA"] * 4,
            "headline": ["a", "b", "c", "d"],
        }
    )
    got = validate_news_frame(raw)
    assert got["timestamp"].notna().all()
    assert sorted(got["timestamp"].astype(str)) == [
        "2022-01-03 00:00:00", "2022-01-03 12:15:00",
        "2022-01-04 00:00:00", "2022-01-04 09:30:00",
    ]


def test_news_duplicate_rejection(synthetic_news):
    doubled = pd.concat([synthetic_news, synthetic_news.iloc[[0]]], ignore_index=True)
    with pytest.raises(DuplicateRecordError):
        validate_news_frame(doubled)
