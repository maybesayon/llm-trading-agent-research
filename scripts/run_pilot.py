#!/usr/bin/env python3
"""Phase 3 pilot orchestrator (protocol §3.5, D.6). RUN ON YOUR MACHINE.

Produces results/pilot/pipeline_validation_report.md. This script validates
the pipeline; it never reports trading performance as evidence.

Prerequisites (see RUNBOOK.md): FNSPID subset + prices downloaded into
data/raw/, universe tickers filled in configs/data.yaml, and (optionally,
for the LLM smoke test) a local vLLM server running Qwen3-14B.

Usage:
  python scripts/run_pilot.py [--skip-llm] [--vllm-url http://localhost:8000]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest.engine import run_backtest  # noqa: E402
from src.data_ingestion.news import CSVNewsSource  # noqa: E402
from src.data_ingestion.prices import CSVPriceSource  # noqa: E402
from src.data_ingestion.snapshots import write_snapshot  # noqa: E402
from src.integrity.checks import timestamp_granularity  # noqa: E402
from src.preprocessing.alignment import density_report  # noqa: E402
from src.strategies.baselines import price_days, s1_buy_and_hold, s2_momentum  # noqa: E402
from src.utils.config import load_configs, load_protocol_lock  # noqa: E402
from tests.reference_impl import reference_backtest  # noqa: E402

REPORT = []


def log(section: str, line: str, ok: bool | None = None):
    mark = "" if ok is None else (" [PASS]" if ok else " [FAIL]")
    REPORT.append(f"- **{section}:** {line}{mark}")
    print(f"{section}: {line}{mark}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-llm", action="store_true")
    ap.add_argument("--vllm-url", default="http://localhost:8000")
    args = ap.parse_args()

    cfg = load_configs(ROOT / "configs")
    lock, lock_hash = load_protocol_lock(ROOT)
    log("Protocol", f"lock hash (provisional): {lock_hash[:16]}")

    universe = cfg["data"]["universe"]["tickers"]
    if not universe:
        log("Universe", "configs/data.yaml universe.tickers is EMPTY — apply the "
            "2021-12-31 market-cap rule first (RUNBOOK step 3)", ok=False)
        _write_report()
        sys.exit(1)

    # ----- pilot scope: 2 tickers, 3 months, seeded draw (D.6) -----
    rng = random.Random(42)
    pilot_tickers = sorted(rng.sample(universe, 2))
    log("Pilot scope", f"tickers {pilot_tickers}, sub-window 2022-01-03..2022-03-31 (seeded)")

    # ----- ingestion -----
    prices_path = ROOT / "data/raw/prices_track_a.csv"
    news_path = ROOT / "data/raw/fnspid_news_subset.csv"
    for p in (prices_path, news_path):
        if not p.exists():
            log("Ingestion", f"missing {p.name} (RUNBOOK steps 2 and 4)", ok=False)
            _write_report()
            sys.exit(1)

    prices = CSVPriceSource(prices_path).fetch(universe, "2019-01-02", "2023-12-29")
    news = CSVNewsSource(news_path, cfg["data"]["sources"]["fnspid"]["news_column_map"]).fetch()
    log("Ingestion", f"prices rows={len(prices)}, news rows={len(news)}", ok=len(prices) > 0 and len(news) > 0)

    # ----- snapshots -----
    snap_p = write_snapshot(prices, "prices_track_a", ROOT / "data/snapshots", meta={"stage": "pilot"})
    snap_n = write_snapshot(news, "fnspid_news", ROOT / "data/snapshots", meta={"stage": "pilot"})
    log("Snapshots", f"prices {snap_p['sha256_content'][:12]}, news {snap_n['sha256_content'][:12]}", ok=True)

    # ----- timestamp granularity ([PILOT->PARAM], §3.2) -----
    gran = timestamp_granularity(news, "timestamp")
    log("Granularity", f"news timestamps are '{gran}' -> record in protocol.lock; "
        f"{'date-only convention applies' if gran == 'date_only' else 'apply 16:00 close cutoff'}")

    # ----- news-density criterion (frozen, §3.5) -----
    crit = cfg["data"]["density_criterion"]
    pilot_prices = prices[(prices["date"] >= "2022-01-03") & (prices["date"] <= "2022-03-31")]
    rep = density_report(news, pilot_prices, universe,
                         m1_threshold=crit["m1_threshold"], m2_threshold=crit["m2_threshold"],
                         window=crit["trailing_window_trading_days"])
    failing = rep[~rep["passes"]]["ticker"].tolist()
    (ROOT / "results/pilot").mkdir(parents=True, exist_ok=True)
    rep.to_csv(ROOT / "results/pilot/density_report.csv", index=False)
    log("Density (M1/M2)", f"{len(failing)}/{len(universe)} tickers fail "
        f"(threshold: >{crit['max_failing_tickers']} triggers amendment); failing={failing}",
        ok=len(failing) <= crit["max_failing_tickers"])

    # ----- S1/S2 reconciliation on REAL data -----
    days = price_days(prices)
    w_start = pd.Timestamp("2022-01-03")
    entry = days[days < w_start][-1]
    frame = prices[prices["date"] >= entry].reset_index(drop=True)
    for name, sig in (
        ("S1", s1_buy_and_hold(prices, universe, w_start)),
        ("S2", s2_momentum(prices, universe, w_start, days[-1])),
    ):
        eng = run_backtest(frame, sig, universe, cost_bps=10.0)
        ref = reference_backtest(frame, sig, universe, cost_bps=10.0)
        match = abs(eng.equity.iloc[-1] - ref["final_equity"]) < 1e-9
        log("Reconciliation", f"{name}: engine vs reference final equity match", ok=match)

    # ----- LLM smoke test + cost/latency ([PILOT->PARAM]) -----
    if args.skip_llm:
        log("LLM", "skipped (--skip-llm); rerun with vLLM up before freeze completion")
    else:
        from src.agents.llm_client import CachedLLMClient, openai_compatible_transport
        from src.agents.prompts import s5_user_prompt, s6_user_prompt

        gen = {
            "temperature": cfg["model"]["generation"]["temperature"],
            "top_p": cfg["model"]["generation"]["top_p"],
            "max_tokens": {
                "s5_scorer": cfg["model"]["generation"]["max_tokens"]["s5_scorer"],
                "s6_agent": cfg["model"]["generation"]["max_tokens"]["s6_agent"],
                "rationale_classifier": cfg["model"]["generation"]["max_tokens"]["rationale_classifier"],
            },
        }
        client = CachedLLMClient(
            openai_compatible_transport(args.vllm_url, cfg["model"]["model"]["hf_repository"]),
            ROOT / "results/pilot/llm_cache",
            cfg["model"]["model"]["hf_repository"],
            gen,
        )
        t0 = time.time()
        n_calls = 0
        sample_news = news[news["ticker"] == pilot_tickers[0]]["headline"].head(3).tolist()
        for seed in (11, 42, 2026):
            r = client.call_json("s5_scorer", s5_user_prompt(pilot_tickers[0], sample_news), seed=seed)
            n_calls += 1
            log("LLM S5", f"seed {seed}: ok={r['ok']} value={r.get('value')}", ok=r["ok"])
        closes = prices[prices["ticker"] == pilot_tickers[0]]["close"].tail(60).tolist()
        r = client.call_json("s6_agent", s6_user_prompt(pilot_tickers[0], sample_news, closes, "flat"), seed=42)
        n_calls += 1
        log("LLM S6", f"ok={r['ok']} action={r['value']['action'] if r['ok'] else None}", ok=r["ok"])
        per_call = (time.time() - t0) / n_calls
        log("Cost/latency", f"~{per_call:.1f}s per call -> record in D.5 budget calculation")

    _write_report()
    print("\nPipeline Validation Report written to results/pilot/pipeline_validation_report.md")


def _write_report():
    out = ROOT / "results/pilot"
    out.mkdir(parents=True, exist_ok=True)
    (out / "pipeline_validation_report.md").write_text(
        "# Pipeline Validation Report (Phase 3 pilot)\n\n"
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n\n"
        + "\n".join(REPORT)
        + "\n\n*This report validates infrastructure. No trading outcome herein is evidence "
        "for or against any hypothesis (protocol §3.5).*\n"
    )


if __name__ == "__main__":
    main()
