#!/usr/bin/env python3
"""Download the evaluation reference series and Track B prices (Freeze
Document §6 / D.2 items ii–vi), then snapshot each with a content hash.

Series come from configs/data.yaml -> sources:
  risk_free  FRED DTB3 (3-month T-bill, daily)
  sp500_tr   Yahoo ^SP500TR (S&P 500 total return)
  vix        Yahoo ^VIX
  factors    Kenneth French library, F-F_Research_Data_Factors_daily
  prices     universe tickers over the Track B window (yfinance, auto-adjusted)

Raw files go to data/raw/reference/ (local); hashes to data/snapshots/manifest.json.

Usage:
  python scripts/fetch_reference_data.py
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_ingestion.prices import YFinancePriceSource  # noqa: E402
from src.data_ingestion.snapshots import write_snapshot  # noqa: E402
from src.utils.hashing import hash_file  # noqa: E402

OUT = ROOT / "data/raw/reference"
START = "2019-01-02"                       # calibration start
END_EXCL = "2026-07-01"                    # Track B end (2026-06-30), exclusive
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
FRENCH = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{file}_CSV.zip"


def now() -> str:
    return pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def fred(series: str) -> pd.DataFrame:
    r = requests.get(FRED.format(series=series), timeout=60)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")  # "." marks holidays
    return df[(df["date"] >= START) & (df["date"] < END_EXCL)].reset_index(drop=True)


def yahoo_index(symbol: str) -> pd.DataFrame:
    import yfinance as yf

    raw = yf.download(symbol, start=START, end=END_EXCL, auto_adjust=True, progress=False).reset_index()
    raw.columns = [str(c[0] if isinstance(c, tuple) else c).lower() for c in raw.columns]
    return raw[["date", "open", "close"]]


def french(file: str) -> tuple[pd.DataFrame, bytes]:
    r = requests.get(FRENCH.format(file=file), timeout=120)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        text = z.read(z.namelist()[0]).decode("latin-1")
    lines = text.splitlines()
    head = next(i for i, ln in enumerate(lines) if ln.strip().startswith(",Mkt-RF"))
    body = []
    for ln in lines[head + 1:]:
        if not ln.strip() or not ln.strip()[0].isdigit():
            break
        body.append(ln)
    df = pd.read_csv(io.StringIO("\n".join([lines[head]] + body)))
    df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"].astype(str).str.strip(), format="%Y%m%d")
    return df[(df["date"] >= START) & (df["date"] < END_EXCL)].reset_index(drop=True), r.content


def main():
    src = yaml.safe_load((ROOT / "configs/data.yaml").read_text())
    tickers, win_b = src["universe"]["tickers"], src["windows"]["track_b"]
    s = src["sources"]
    OUT.mkdir(parents=True, exist_ok=True)
    record = {}

    frames = {
        "risk_free_dtb3": (fred(s["risk_free"]["series"]), {"provider": "FRED", "series": s["risk_free"]["series"]}),
        "sp500_tr": (yahoo_index(s["sp500_tr"]["symbol"]), {"provider": "yahoo", "symbol": s["sp500_tr"]["symbol"]}),
        "vix": (yahoo_index(s["vix"]["symbol"]), {"provider": "yahoo", "symbol": s["vix"]["symbol"]}),
    }
    ff, ff_zip = french(s["factors"]["file"])
    (OUT / f"{s['factors']['file']}_CSV.zip").write_bytes(ff_zip)
    frames["ff_factors_daily"] = (ff, {"provider": "french_data_library", "file": s["factors"]["file"],
                                       "zip_sha256": hash_file(OUT / f"{s['factors']['file']}_CSV.zip")})

    src_b = YFinancePriceSource()
    end_b = (pd.Timestamp(win_b["end"]) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")  # yfinance end is exclusive
    frames["prices_track_b"] = (src_b.fetch(tickers, win_b["start"], end_b),
                                {**src_b.metadata(), "window": [win_b["start"], win_b["end"]]})

    import yfinance as yf

    for name, (df, meta) in frames.items():
        meta = {**meta, "retrieved_utc": now(), "yfinance": yf.__version__, "stage": "reference"}
        df.to_csv(OUT / f"{name}.csv", index=False)
        entry = write_snapshot(df, name, ROOT / "data/snapshots", meta=meta)
        d = pd.to_datetime(df["date"])
        record[name] = {"rows": len(df), "first": str(d.min().date()), "last": str(d.max().date()),
                        "sha256_content": entry["sha256_content"][:16]}
    (OUT / "record.json").write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
