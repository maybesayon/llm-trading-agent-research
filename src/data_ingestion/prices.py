"""Price ingestion. Network sources are thin wrappers recorded in snapshot
metadata; unit tests use CSV fixtures only — no network in tests."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from src.integrity.checks import assert_no_duplicates, assert_no_missing

PRICE_COLUMNS = ["date", "ticker", "open", "close", "volume"]


def validate_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    missing_cols = [c for c in PRICE_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Price frame missing columns: {missing_cols}")
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    assert_no_missing(df, ["date", "ticker", "open", "close"])
    assert_no_duplicates(df, ["date", "ticker"])
    return df.sort_values(["ticker", "date"]).reset_index(drop=True)


class PriceSource(ABC):
    @abstractmethod
    def fetch(self, tickers, start, end) -> pd.DataFrame: ...

    def metadata(self) -> dict:
        return {"source": type(self).__name__}


class CSVPriceSource(PriceSource):
    """Fixture/offline source (also used for FNSPID price files)."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def fetch(self, tickers, start, end) -> pd.DataFrame:
        df = validate_price_frame(pd.read_csv(self.path))
        mask = (
            df["ticker"].isin(list(tickers))
            & (df["date"] >= pd.Timestamp(start))
            & (df["date"] <= pd.Timestamp(end))
        )
        return df[mask].reset_index(drop=True)

    def metadata(self) -> dict:
        return {"source": "csv", "path": str(self.path)}


class YFinancePriceSource(PriceSource):
    """Network wrapper. NEVER called from unit tests; used at pilot time.
    Library version is recorded for the snapshot manifest (§3.5, D.2)."""

    def fetch(self, tickers, start, end) -> pd.DataFrame:
        import yfinance as yf  # lazy import: not a test dependency

        frames = []
        for t in tickers:
            raw = yf.download(
                t, start=str(start), end=str(end), auto_adjust=True, progress=False
            )
            raw = raw.reset_index()
            raw.columns = [str(c[0] if isinstance(c, tuple) else c).lower() for c in raw.columns]
            raw = raw.rename(columns={"index": "date"})
            raw["ticker"] = t
            frames.append(raw[["date", "ticker", "open", "close", "volume"]])
        return validate_price_frame(pd.concat(frames, ignore_index=True))

    def metadata(self) -> dict:
        import yfinance as yf

        return {
            "source": "yfinance",
            "library_version": yf.__version__,
            "auto_adjust": True,
        }
