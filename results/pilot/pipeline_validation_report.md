# Pipeline Validation Report (Phase 3 pilot)

Generated: 2026-09-25T01:06:20Z

- **Protocol:** lock hash (provisional): 47f2b996deeebe8c
- **Pilot scope:** tickers ['AAPL', 'AMZN'], sub-window 2022-01-03..2022-03-31 (seeded)
- **Ingestion:** prices rows=25160, news rows=87689 [PASS]
- **Snapshots:** prices 3ee7c2d69bfe, news e52a75ccd132 [PASS]
- **Granularity:** news timestamps are 'intraday' -> record in protocol.lock; apply 16:00 close cutoff
- **Density (M1/M2):** 14/20 tickers fail (threshold: >5 triggers amendment); failing=['AAPL', 'MSFT', 'AMZN', 'TSLA', 'META', 'UNH', 'JPM', 'JNJ', 'HD', 'PG', 'BAC', 'MA', 'PFE', 'AVGO'] [FAIL]
- **Reconciliation:** S1: engine vs reference final equity match [PASS]
- **Reconciliation:** S2: engine vs reference final equity match [PASS]
- **LLM:** skipped (--skip-llm); rerun with vLLM up before freeze completion

*This report validates infrastructure. No trading outcome herein is evidence for or against any hypothesis (protocol §3.5).*
