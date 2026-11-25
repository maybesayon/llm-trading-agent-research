#!/usr/bin/env python3
"""Extract the FNSPID news subset for the universe (runbook step 2, D.2).

Reads both FNSPID news files at the pinned dataset revision, keeps the
universe firms over 2019-01-01..2023-12-31, and writes
data/raw/fnspid_news_subset.csv plus a JSON record of every count.

Firm-level mapping: all FNSPID symbols for one firm (share classes, the FB ->
META rename) map to the firm's universe ticker. Exact (Date, firm, title)
duplicates are dropped and counted. Rows whose Date does not parse are kept:
they are what the M2 timestamp-validity metric measures (protocol §3.5).

Usage:
  python scripts/build_fnspid_subset.py [--tickers AAPL MSFT ...]
  (defaults to configs/data.yaml universe.tickers)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
FNSPID = ROOT / "data/raw/fnspid"
FILES = ["Stock_news/All_external.csv", "Stock_news/nasdaq_exteral_data.csv"]
OUT = ROOT / "data/raw/fnspid_news_subset.csv"
START, END = "2019-01-01", "2023-12-31"
USECOLS = ["Date", "Article_title", "Stock_symbol", "Url", "Publisher"]

# universe ticker -> FNSPID Stock_symbol labels for the same firm
SYMBOLS = {
    "GOOGL": ["GOOGL", "GOOG"],
    "META": ["META", "FB"],
    "BRK-B": ["BRK", "BRK.B", "BRK-B", "BRK/B", "BRKB", "BRK.A", "BRK-A", "BRK/A"],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="+")
    args = ap.parse_args()
    cfg = yaml.safe_load((ROOT / "configs/data.yaml").read_text())
    fnspid = cfg["sources"]["fnspid"]
    tickers = args.tickers or cfg["universe"]["tickers"]
    if not tickers:
        sys.exit("configs/data.yaml universe.tickers is empty — fill it first")
    label_to_firm = {lbl: t for t in tickers for lbl in SYMBOLS.get(t, [t])}

    record = {"fnspid_revision": fnspid["commit"], "window": [START, END],
              "firm_symbol_map": {t: SYMBOLS.get(t, [t]) for t in tickers}, "files": {}}
    parts = []
    for f in FILES:
        path = FNSPID / f
        digest = sha256(path)
        expected = fnspid["sha256"][f]
        if digest != expected:
            sys.exit(f"{f}: sha256 {digest} != published {expected}")
        kept = 0
        for ch in pd.read_csv(path, usecols=USECOLS, dtype=str, chunksize=500_000):
            sym = ch["Stock_symbol"].fillna("").str.strip().str.upper()
            ch = ch[sym.isin(label_to_firm)].copy()
            day = ch["Date"].fillna("").str[:10]
            parsed = pd.to_datetime(ch["Date"], errors="coerce").notna()
            ch = ch[~parsed | ((day >= START) & (day <= END))]
            ch["fnspid_symbol"] = ch["Stock_symbol"].str.strip().str.upper()
            ch["Stock_symbol"] = ch["fnspid_symbol"].map(label_to_firm)
            ch["source_file"] = Path(f).name
            kept += len(ch)
            parts.append(ch)
        record["files"][f] = {"sha256": digest, "rows_kept": kept}
        print(f"{f}: sha256 ok, {kept} rows kept", flush=True)

    df = pd.concat(parts, ignore_index=True)
    n_missing_title = int(df["Article_title"].isna().sum())
    df = df[df["Article_title"].notna()]
    n_before = len(df)
    df = df.drop_duplicates(subset=["Date", "Stock_symbol", "Article_title"], keep="first")
    df = df.sort_values(["Stock_symbol", "Date"], na_position="first")
    df.to_csv(OUT, index=False)

    record.update({
        "rows_written": len(df),
        "dropped_missing_title": n_missing_title,
        "dropped_exact_duplicates": n_before - len(df),
        "unparseable_dates": int(pd.to_datetime(df["Date"], errors="coerce").isna().sum()),
        "rows_per_ticker": df["Stock_symbol"].value_counts().sort_index().to_dict(),
        "rows_per_fnspid_symbol": df["fnspid_symbol"].value_counts().sort_index().to_dict(),
        "output_sha256": sha256(OUT),
    })
    (ROOT / "data/raw/fnspid_news_subset.meta.json").write_text(json.dumps(record, indent=2))
    print(json.dumps({k: v for k, v in record.items() if k != "firm_symbol_map"}, indent=2))


if __name__ == "__main__":
    main()
