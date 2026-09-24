"""M1/M2 density metrics against hand-computed answers (protocol §3.5)."""
import pandas as pd

from src.preprocessing.alignment import (
    articles_in_trailing_window,
    compute_m1,
    compute_m2,
    density_report,
    trading_days,
)


def test_m1_known_answers(synthetic_news, synthetic_prices):
    assert compute_m1(synthetic_news, synthetic_prices, "AAA", window=3) == 0.9
    assert compute_m1(synthetic_news, synthetic_prices, "BBB", window=3) == 1.0


def test_m2_counts_unparseable_timestamps(synthetic_news):
    assert compute_m2(synthetic_news, "AAA") == 1.0
    broken = pd.concat(
        [
            synthetic_news,
            pd.DataFrame(
                [{"timestamp": "not-a-date", "ticker": "AAA", "headline": "bad ts"}]
            ),
        ],
        ignore_index=True,
    )
    assert compute_m2(broken, "AAA") == 0.75  # 3 valid of 4


def test_trailing_window_excludes_articles_after_day(synthetic_news, synthetic_prices):
    days = trading_days(synthetic_prices)
    first_day = days[0]
    got = articles_in_trailing_window(synthetic_news, "AAA", first_day, days, window=3)
    assert len(got) == 1  # only the day-1 article; days 4 and 7 are in the future
    assert (pd.to_datetime(got["timestamp"]).dt.normalize() == first_day).all()


def test_density_report_applies_frozen_thresholds(synthetic_news, synthetic_prices):
    report = density_report(
        synthetic_news, synthetic_prices, ["AAA", "BBB"], m1_threshold=0.90
    )
    row = report.set_index("ticker")
    assert bool(row.loc["BBB", "passes"]) is True
    assert bool(row.loc["AAA", "passes"]) is True  # 0.9 >= 0.9 boundary passes
    strict = density_report(
        synthetic_news, synthetic_prices, ["AAA"], m1_threshold=0.95
    ).set_index("ticker")
    assert bool(strict.loc["AAA", "passes"]) is False
