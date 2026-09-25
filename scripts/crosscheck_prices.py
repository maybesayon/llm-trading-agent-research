#!/usr/bin/env python3
"""Cross-check the primary price file against a second source (runbook step 3,
protocol §3.3: corporate actions, missing histories, adjustment errors).

Compares daily close-to-close returns of adjusted closes, not levels: later
splits and dividends rescale historical levels but leave past returns intact.

Sources:
  fnspid  FNSPID Stock_price/full_history.zip (Yahoo-derived, saved 2023-12-30):
          a revision check of the primary vendor, not an independent source.
  tiingo  Tiingo EOD API; reads the key from the TIINGO_API_KEY env variable.

Usage:
  python scripts/crosscheck_prices.py --source fnspid|tiingo
Writes results/pilot/price_crosscheck_<source>.csv
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import zipfile
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
START, END = "2019-01-02", "2023-12-29"
FNSPID_NAMES = {"META": "FB"}  # FNSPID file name where it differs from the universe ticker


def load_primary(tickers) -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data/raw/prices_track_a.csv", parse_dates=["date"])
    return df[df["ticker"].isin(tickers)][["date", "ticker", "close"]]


def load_fnspid(tickers) -> pd.DataFrame:
    zf = zipfile.ZipFile(ROOT / "data/raw/fnspid/Stock_price/full_history.zip")
    members = {Path(n).stem.upper(): n for n in zf.namelist() if n.startswith("full_history/") and n.endswith(".csv")}
    frames = []
    for t in tickers:
        name = members.get(FNSPID_NAMES.get(t, t).upper())
        if name is None:
            continue
        raw = pd.read_csv(io.BytesIO(zf.read(name)), parse_dates=["date"])
        frames.append(pd.DataFrame({"date": raw["date"], "ticker": t, "close": raw["adj close"]}))
    return pd.concat(frames, ignore_index=True)


def load_tiingo(tickers) -> pd.DataFrame:
    import requests

    key = os.environ.get("TIINGO_API_KEY")
    if not key:
        sys.exit("set TIINGO_API_KEY first")
    frames = []
    for t in tickers:
        r = requests.get(
            f"https://api.tiingo.com/tiingo/daily/{t}/prices",
            params={"startDate": START, "endDate": END, "token": key},
            timeout=60,
        )
        r.raise_for_status()
        raw = pd.DataFrame(r.json())
        frames.append(pd.DataFrame({
            "date": pd.to_datetime(raw["date"]).dt.tz_localize(None).dt.normalize(),
            "ticker": t,
            "close": raw["adjClose"],
        }))
    return pd.concat(frames, ignore_index=True)


def compare(primary: pd.DataFrame, second: pd.DataFrame, tickers) -> pd.DataFrame:
    rows = []
    for t in tickers:
        a = primary[primary["ticker"] == t].set_index("date")["close"].sort_index()
        b = second[second["ticker"] == t].set_index("date")["close"].sort_index()
        b = b[(b.index >= START) & (b.index <= END)]
        if b.empty:
            rows.append({"ticker": t, "second_source_days": 0})
            continue
        common = a.index.intersection(b.index)
        ra, rb = a[common].pct_change().dropna(), b[common].pct_change().dropna()
        diff = (ra - rb).abs()
        rows.append({
            "ticker": t,
            "primary_days": len(a),
            "second_source_days": len(b),
            "common_days": len(common),
            "second_last_date": b.index.max().date(),
            "missing_in_second": len(a.index.difference(b.index)),
            "missing_in_primary": len(b.index.difference(a.index)),
            "max_abs_return_diff_bp": round(diff.max() * 1e4, 3),
            "days_diff_over_1bp": int((diff > 1e-4).sum()),
            "days_diff_over_10bp": int((diff > 1e-3).sum()),
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["fnspid", "tiingo"], required=True)
    args = ap.parse_args()
    tickers = yaml.safe_load((ROOT / "configs/data.yaml").read_text())["universe"]["tickers"]
    second = {"fnspid": load_fnspid, "tiingo": load_tiingo}[args.source](tickers)
    rep = compare(load_primary(tickers), second, tickers)
    out = ROOT / f"results/pilot/price_crosscheck_{args.source}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rep.to_csv(out, index=False)
    print(rep.to_string(index=False))
    print(f"\nwritten to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
