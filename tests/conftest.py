"""Synthetic fixtures. No network, no LLM, known answers throughout."""
import pandas as pd
import pytest

TICKERS = ["AAA", "BBB"]


@pytest.fixture
def synthetic_prices() -> pd.DataFrame:
    """10 business days x 2 tickers, deterministic values."""
    days = pd.bdate_range("2022-01-03", periods=10)
    rows = []
    for t in TICKERS:
        base = 100.0 if t == "AAA" else 50.0
        for i, d in enumerate(days):
            rows.append(
                {
                    "date": d,
                    "ticker": t,
                    "open": base + i,
                    "close": base + i + 0.5,
                    "volume": 1000 + i,
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture
def synthetic_news(synthetic_prices) -> pd.DataFrame:
    """AAA: articles on trading days 1, 4, 7 (10:00). BBB: every day (09:30).

    Known M1 answers with window=3 over 10 trading days:
      AAA -> 9/10 (only the last day's trailing window {8,9,10} is empty)
      BBB -> 10/10
    """
    days = sorted(synthetic_prices["date"].unique())
    rows = []
    for idx in (0, 3, 6):
        d = pd.Timestamp(days[idx])
        rows.append(
            {
                "timestamp": d + pd.Timedelta(hours=10),
                "ticker": "AAA",
                "headline": f"AAA news {idx}",
            }
        )
    for idx, d in enumerate(days):
        rows.append(
            {
                "timestamp": pd.Timestamp(d) + pd.Timedelta(hours=9, minutes=30),
                "ticker": "BBB",
                "headline": f"BBB news {idx}",
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture
def last_day_close(synthetic_prices) -> pd.Timestamp:
    return pd.Timestamp(max(synthetic_prices["date"])) + pd.Timedelta(hours=16)
