#!/usr/bin/env python3
"""A-002 news-source survey (docs/amendments/A-002_source_selection_rule.md).

Measures availability only (M1/M2 over Track A, FNSPID ∪ candidate). Never
computes returns, sentiment, signals, or strategy outputs.

Usage:
  python scripts/a002_survey.py c1|c2|c3|c4        # build a candidate (C3/C4 need API keys in .env)
  python scripts/a002_survey.py measure <name>     # M1/M2 for fnspid ∪ data/raw/a002/<name>.csv
  python scripts/a002_survey.py measure baseline   # FNSPID alone
  python scripts/a002_survey.py sample <name>      # 100-article precision sample (seed 2026)

Candidate files use the subset schema: Date, Stock_symbol, Article_title, Url, source_file.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_ingestion.news import validate_news_frame  # noqa: E402
from src.preprocessing.alignment import density_report  # noqa: E402

RAW = ROOT / "data/raw/a002"
OUT = ROOT / "results/a002"
TRACK_A = ("2022-01-03", "2023-12-29")
WINDOW = ("2019-01-01", "2023-12-31")
KEY = ["Date", "Stock_symbol", "Article_title"]
COLUMN_MAP = {"Date": "timestamp", "Stock_symbol": "ticker", "Article_title": "headline"}

# Fixed in the A-002 rule document; do not edit after measurement starts.
ALIASES = {
    "AAPL": ["Apple"], "MSFT": ["Microsoft"], "GOOGL": ["Alphabet", "Google"],
    "AMZN": ["Amazon"], "TSLA": ["Tesla"], "META": ["Meta Platforms", "Meta", "Facebook"],
    "NVDA": ["Nvidia"], "BRK-B": ["Berkshire"], "UNH": ["UnitedHealth"], "V": ["Visa"],
    "JPM": ["JPMorgan", "JP Morgan", "J.P. Morgan"], "JNJ": ["Johnson & Johnson", "J&J"],
    "HD": ["Home Depot"], "WMT": ["Walmart"], "PG": ["Procter & Gamble", "P&G"],
    "BAC": ["Bank of America", "BofA"], "MA": ["Mastercard"], "PFE": ["Pfizer"],
    "DIS": ["Disney"], "AVGO": ["Broadcom"],
}


def alias_pattern(names) -> re.Pattern:
    # word boundaries that also work next to '&' and '.' inside an alias
    alts = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return re.compile(rf"(?<![\w&.])(?:{alts})(?![\w&])", re.I)


def fnspid_subset() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data/raw/fnspid_news_subset.csv", dtype=str)


def build_c1():
    pats = {t: alias_pattern(a) for t, a in ALIASES.items()}
    files = ["Stock_news/All_external.csv", "Stock_news/nasdaq_exteral_data.csv"]
    parts = []
    for f in files:
        cols = ["Date", "Article_title", "Stock_symbol", "Url"]
        for ch in pd.read_csv(ROOT / "data/raw/fnspid" / f, usecols=cols, dtype=str, chunksize=500_000):
            day = ch["Date"].fillna("").str[:10]
            ch = ch[(day >= WINDOW[0]) & (day <= WINDOW[1]) & ch["Article_title"].notna()]
            for t, p in pats.items():
                hit = ch[ch["Article_title"].str.contains(p)]
                if len(hit):
                    parts.append(pd.DataFrame({
                        "Date": hit["Date"], "Stock_symbol": t, "Article_title": hit["Article_title"],
                        "Url": hit["Url"], "source_file": f"c1:{Path(f).name}",
                        "tagged_symbol": hit["Stock_symbol"],
                    }))
        print(f"{f}: scanned", flush=True)
    c1 = pd.concat(parts, ignore_index=True).drop_duplicates(subset=KEY)
    RAW.mkdir(parents=True, exist_ok=True)
    c1.to_csv(RAW / "c1.csv", index=False)
    print(f"C1 rows: {len(c1)}")
    print(c1["Stock_symbol"].value_counts().sort_index().to_string())


GKG_URL = "https://data.gdeltproject.org/gdeltv2/{ts}.gkg.csv.zip"
TITLE = re.compile(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>", re.S)


def _c2_day(day: str) -> tuple[str, list, int]:
    """All 96 GKG batches of one UTC day -> rows whose Organizations field
    (GKG 2.1 column 14) names a firm alias. Date = GKG DATE (batch time, UTC)."""
    import io
    import time
    import zipfile

    import requests

    pats = {t: alias_pattern(a) for t, a in ALIASES.items()}
    anyp = alias_pattern([n for a in ALIASES.values() for n in a])
    rows, missing = [], 0
    for ts in pd.date_range(day, periods=96, freq="15min").strftime("%Y%m%d%H%M%S"):
        for attempt in range(4):
            try:
                r = requests.get(GKG_URL.format(ts=ts), timeout=120)
                break
            except requests.RequestException:
                time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError(f"GKG {ts}: download failed")
        if r.status_code == 404:
            missing += 1
            continue
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            text = z.read(z.namelist()[0]).decode("utf-8", errors="replace")
        for line in text.split("\n"):
            c = line.split("\t")
            if len(c) < 27 or not anyp.search(c[13]):
                continue
            m = TITLE.search(c[26])
            title = m.group(1).strip() if m and m.group(1).strip() else None
            d = c[1]
            stamp = f"{d[:4]}-{d[4:6]}-{d[6:8]} {d[8:10]}:{d[10:12]}:{d[12:14]}"
            for t, p in pats.items():
                if p.search(c[13]):
                    rows.append((stamp, t, title or c[4], c[4], "c2:gdelt_gkg", "page_title" if title else "url"))
    return day, rows, missing


def build_c2(workers: int = 8):
    from concurrent.futures import ProcessPoolExecutor, as_completed

    cols = ["Date", "Stock_symbol", "Article_title", "Url", "source_file", "title_source"]
    days_dir = RAW / "c2_days"
    days_dir.mkdir(parents=True, exist_ok=True)
    days = [d.strftime("%Y-%m-%d") for d in pd.date_range(*TRACK_A, freq="D")]
    todo = [d for d in days if not (days_dir / f"{d}.csv").exists()]
    print(f"C2: {len(days)} days, {len(todo)} to fetch", flush=True)
    with ProcessPoolExecutor(workers) as ex:
        futs = [ex.submit(_c2_day, d) for d in todo]
        for i, f in enumerate(as_completed(futs), 1):
            day, rows, missing = f.result()
            with open(days_dir / "missing_batches.tsv", "a") as fh:
                fh.write(f"{day}\t{missing}\n")
            pd.DataFrame(rows, columns=cols).to_csv(days_dir / f"{day}.csv", index=False)
            if i % 10 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)} days done (last {day}: {len(rows)} rows, {missing} missing batches)", flush=True)
    missing = pd.read_csv(days_dir / "missing_batches.tsv", sep="\t", names=["day", "n"])
    print(f"missing GKG batches: {int(missing.drop_duplicates('day', keep='last')['n'].sum())} of {96 * len(days)}")
    c2 = pd.concat([pd.read_csv(p, dtype=str) for p in sorted(days_dir.glob("*.csv"))], ignore_index=True)
    c2 = c2.drop_duplicates(subset=KEY)
    c2.to_csv(RAW / "c2.csv", index=False)
    print(f"C2 rows: {len(c2)}")
    print(c2["Stock_symbol"].value_counts().sort_index().to_string())


def _cached_get(cache: Path, url: str, params: dict, wait: float) -> dict:
    """GET with an on-disk JSON cache (the key is never part of the cache name)."""
    import json
    import time

    import requests

    if cache.exists():
        return json.loads(cache.read_text())
    where = url.split("?")[0]  # errors must never echo the query string (it holds the key)
    try:
        r = requests.get(url, params=params, timeout=120)
    except requests.RequestException as e:
        raise RuntimeError(f"request to {where} failed: {type(e).__name__}") from None
    if not r.ok:
        raise RuntimeError(f"HTTP {r.status_code} from {where}: {r.text[:200]}")
    data = r.json()
    time.sleep(wait)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data))
    return data


def build_c3():
    """Alpha Vantage NEWS_SENTIMENT, one call per ticker-month over Track A."""
    from src.utils.env import get_key

    key = get_key("ALPHAVANTAGE_API_KEY") or sys.exit("ALPHAVANTAGE_API_KEY not set (environment or .env)")
    rows, capped = [], []
    months = pd.period_range(TRACK_A[0], TRACK_A[1], freq="M")
    for t in ALIASES:
        for m in months:
            cache = RAW / "c3_raw" / t / f"{m}.json"
            data = _cached_get(cache, "https://www.alphavantage.co/query", {
                "function": "NEWS_SENTIMENT", "tickers": t, "sort": "EARLIEST", "limit": 1000,
                "time_from": m.start_time.strftime("%Y%m%dT0000"), "time_to": m.end_time.strftime("%Y%m%dT2359"),
                "apikey": key}, wait=1.0)
            if "feed" not in data:  # rate-limit or error notice: drop it so a rerun retries
                cache.unlink(missing_ok=True)
                sys.exit(f"Alpha Vantage stopped at {t} {m}: {list(data)[:1]} — rerun later to resume")
            if len(data["feed"]) >= 1000:
                capped.append(f"{t} {m}")
            for a in data["feed"]:
                if any(s.get("ticker") == t for s in a.get("ticker_sentiment", [])):
                    p = a["time_published"]
                    rows.append((f"{p[:4]}-{p[4:6]}-{p[6:8]} {p[9:11]}:{p[11:13]}:{p[13:15]}",
                                 t, a["title"], a["url"], "c3:alphavantage"))
    _write_candidate("c3", rows, capped)


def build_c4():
    """Polygon ticker news over Track A, all pages."""
    from src.utils.env import get_key

    key = get_key("POLYGON_API_KEY") or sys.exit("POLYGON_API_KEY not set (environment or .env)")
    rows, capped = [], []
    for t in ALIASES:
        url, params, page = "https://api.polygon.io/v2/reference/news", {
            "ticker": t, "published_utc.gte": TRACK_A[0], "published_utc.lte": f"{TRACK_A[1]}T23:59:59Z",
            "order": "asc", "sort": "published_utc", "limit": 1000, "apiKey": key}, 0
        while url:
            data = _cached_get(RAW / "c4_raw" / t / f"page{page:04d}.json", url, params, wait=12.5)  # free tier: 5/min
            for a in data.get("results", []):
                p = a["published_utc"]
                rows.append((f"{p[:10]} {p[11:19]}", t, a["title"], a["article_url"], "c4:polygon"))
            url, params, page = data.get("next_url"), {"apiKey": key}, page + 1
    _write_candidate("c4", rows, capped)


def _write_candidate(name: str, rows: list, capped: list):
    cols = ["Date", "Stock_symbol", "Article_title", "Url", "source_file"]
    df = pd.DataFrame(rows, columns=cols).drop_duplicates(subset=KEY)
    RAW.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW / f"{name}.csv", index=False)
    print(f"{name.upper()} rows: {len(df)}; calls at the 1000-article cap: {capped or 'none'}")
    print(df["Stock_symbol"].value_counts().reindex(list(ALIASES), fill_value=0).to_string())


def contributed(cand: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    """Candidate rows not already in the FNSPID subset (exact key)."""
    k = base[KEY].drop_duplicates()
    m = cand.merge(k, on=KEY, how="left", indicator=True)
    return m[m["_merge"] == "left_only"].drop(columns="_merge")


def measure(name: str):
    cfg = yaml.safe_load((ROOT / "configs/data.yaml").read_text())
    tickers, crit = cfg["universe"]["tickers"], cfg["density_criterion"]
    base = fnspid_subset()
    news = base[KEY]
    if name != "baseline":
        cand = pd.read_csv(RAW / f"{name}.csv", dtype=str)
        news = pd.concat([news, contributed(cand, base)[KEY]], ignore_index=True)
    news = validate_news_frame(news.rename(columns=COLUMN_MAP)[["timestamp", "ticker", "headline"]])
    prices = pd.read_csv(ROOT / "data/raw/prices_track_a.csv", parse_dates=["date"])
    prices = prices[(prices["date"] >= TRACK_A[0]) & (prices["date"] <= TRACK_A[1])]
    rep = density_report(news, prices, tickers, m1_threshold=crit["m1_threshold"],
                         m2_threshold=crit["m2_threshold"], window=crit["trailing_window_trading_days"])
    OUT.mkdir(parents=True, exist_ok=True)
    rep.to_csv(OUT / f"{name}_density_track_a.csv", index=False)
    print(rep.to_string(index=False))
    print(f"\n{name}: {int(rep['passes'].sum())}/{len(rep)} tickers pass over Track A "
          f"(failing: {rep.loc[~rep['passes'], 'ticker'].tolist()})")


def sample(name: str):
    cand = pd.read_csv(RAW / f"{name}.csv", dtype=str)
    pool = contributed(cand, fnspid_subset())
    s = pool.sample(n=min(100, len(pool)), random_state=2026)[["Stock_symbol", "Date", "Article_title", "Url"]]
    s = s.assign(about_firm="")  # author fills yes/no
    OUT.mkdir(parents=True, exist_ok=True)
    s.to_csv(OUT / f"{name}_precision_sample.csv", index=False)
    print(f"{len(s)} of {len(pool)} contributed rows -> {OUT.relative_to(ROOT)}/{name}_precision_sample.csv")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "c1":
        build_c1()
    elif cmd == "c2":
        build_c2()
    elif cmd == "c3":
        build_c3()
    elif cmd == "c4":
        build_c4()
    elif cmd in ("measure", "sample") and len(sys.argv) == 3:
        (measure if cmd == "measure" else sample)(sys.argv[2])
    else:
        sys.exit(__doc__)
