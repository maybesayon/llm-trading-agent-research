"""News ingestion. FNSPID column mapping is configured in configs/data.yaml
and confirmed at pilot time ([PILOT->PARAM]); tests use CSV fixtures."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.integrity.checks import assert_no_duplicates, assert_no_missing

NEWS_COLUMNS = ["timestamp", "ticker", "headline"]


def validate_news_frame(
    df: pd.DataFrame, *, allow_unparsed_timestamps: bool = True
) -> pd.DataFrame:
    """Validate schema. Unparseable timestamps become NaT (they feed the M2
    metric, §3.5) unless `allow_unparsed_timestamps=False`."""
    missing_cols = [c for c in NEWS_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"News frame missing columns: {missing_cols}")
    df = df.copy()
    ts = pd.to_datetime(df["timestamp"], errors="coerce")
    if isinstance(ts.dtype, pd.DatetimeTZDtype):
        # Keep the source's wall-clock value; never shift across dates.
        # FNSPID stamps date-only records "00:00:00 UTC": converting to
        # exchange time would move them to the previous evening (look-ahead).
        # Dropping the label is conservative under either reading of the date.
        ts = ts.dt.tz_localize(None)
    df["timestamp"] = ts
    if not allow_unparsed_timestamps:
        assert_no_missing(df, ["timestamp"])
    assert_no_missing(df, ["ticker", "headline"])
    assert_no_duplicates(df, ["timestamp", "ticker", "headline"])
    return df.sort_values(["ticker", "timestamp"]).reset_index(drop=True)


class CSVNewsSource:
    """CSV-backed news source with configurable column mapping."""

    def __init__(self, path: str | Path, column_map: dict | None = None):
        self.path = Path(path)
        self.column_map = column_map or {}

    def fetch(self) -> pd.DataFrame:
        df = pd.read_csv(self.path)
        if self.column_map:
            df = df.rename(columns=self.column_map)
        return validate_news_frame(df)

    def metadata(self) -> dict:
        return {"source": "csv", "path": str(self.path), "column_map": self.column_map}


class FNSPIDNewsSource(CSVNewsSource):
    """FNSPID loader: a CSVNewsSource whose column_map comes from
    configs/data.yaml. Repository commit hash recorded at download (D.2)."""
