# Appendix D: Frozen Experimental Protocol — Checklist

Every item below must have a recorded value before the first full-scale experiment. Items marked **[FREEZE]** require a value at protocol freeze; items marked **[PILOT→PARAM]** receive their value from the pilot via a rule fixed here, and are recorded as protocol parameters, never adjusted after results are seen. Any post-freeze change is logged in the Amendment Record (D.8) with date and rationale, and analyses affected by amendments are disclosed in the paper.

## D.1 Model Instrument
- [FREEZE] Model name and exact checkpoint/weights revision (e.g., repository revision hash)
- [FREEZE] Parameter count and context length
- [FREEZE] Inference framework and version
- [FREEZE] Quantization settings (or none)
- [FREEZE] Temperature and all generation parameters (top-p, max tokens, stop sequences) — **temperature 0.7, top_p 0.8 per Amendment A-001 (D.8)**
- [FREEZE] System prompt version for every role: S5 scorer, S6 agent, rationale classifier (§6.2), paraphrase generator (§6.3), polarity-flip generator (§6.4)
- [FREEZE] Random seeds (three, per §4.7)
- Rule: no model substitution after seeing results; any run with another model is labeled exploratory.

## D.2 Data Snapshots
- [FREEZE] FNSPID repository commit hash and download date
- [FREEZE] Universe: the twenty tickers produced by the §3.1 rule, listed explicitly with the market-cap source and as-of date (2021-12-31)
- [FREEZE] Track A window (2022-01-03 to 2023-12-29, trading days)
- [FREEZE] Track B window and news-source query parameters (Finnhub endpoints/parameters; GDELT query filters), with retrieval dates
- [FREEZE] Price source query parameters (yfinance version, adjustment settings); independent second price source for the §3.3 cross-check
- [FREEZE] Risk-free series identifier (FRED) and retrieval date
- [FREEZE] S&P 500 total-return index data source
- [FREEZE] Fama–French factor file version/download date

## D.3 Strategy Parameters
- [FREEZE] S2: momentum lookback (12 months, skip most recent), rebalance schedule
- [FREEZE] S3/S5: threshold-calibration procedure on pre-window data; calibration window dates; sensitivity quantile grid (30/40/50/60/70th percentiles, §5.8)
- [FREEZE] S4: feature list, training window, hyperparameter search space, cross-validation scheme (all pre-window), final selection rule
- [FREEZE] S6: full agent prompt, news-summary construction, price-history window length, position-state encoding

## D.4 Evaluation Grid and Statistics
- [FREEZE] Cost settings: 5/10/25 bps per side
- [FREEZE] Contamination conditions: original / anonymized / anonymized+shuffled dates (§3.4); anonymization procedure specification
- [FREEZE] DSR trial count: number of strategy-cost-condition combinations in the grid
- [FREEZE] Bootstrap: stationary bootstrap, block-length selection rule, number of resamples, 95% intervals
- [FREEZE] Regime definitions: bear = month-end close >20% below running peak; VIX terciles (§4.6)

## D.5 Audit Parameters (§6)
- [FREEZE] Audit budget (currency amount or GPU-hour cap)
- [PILOT→PARAM] Audit sample size: largest regime-stratified seeded sample fitting the budget while maintaining representation across market conditions (rule fixed; N recorded after pilot cost measurement)
- [PILOT→PARAM] Human-validation subsample N for rationale classification (same budget rule)
- [FREEZE] Rationale taxonomy: {sentiment-driven, price/momentum-driven, risk-management-driven, mixed/other}
- [FREEZE] Kappa reporting: continuous κ with bootstrap CI; κ = 0.70 as interpretive guideline triggering the human-labels fallback (§6.2)
- [FREEZE] Spot-check fraction: 10% of audited decisions, seeded, regime-stratified (§6.3–§6.4)

## D.6 Pilot (§3.5)
- [FREEZE] Pilot scope: two tickers, three-month sub-window; ticker selection rule (seeded random draw from universe)
- Verification targets: FNSPID news density; timestamp granularity; delisting/corporate-action handling; Track B coverage and firm-level precision; per-decision cost and latency
- [FREEZE] News-density adequacy criterion (§3.5): M1 = fraction of trading days with ≥1 timestamp-valid article in trailing 3 trading days, pass ≥ 0.90; M2 = fraction of articles with ≥ daily-granularity timestamps, pass ≥ 0.95; ticker exclusion on failure (reported); >5/20 failures → protocol amendment (augment sources or halt). Thresholds frozen pre-pilot; never tuned on outcomes. Criterion measures availability only, not signal quality.
- Rule: pilot outcomes may amend the protocol only via the Amendment Record, before full-scale runs; pilot trading performance is never reported as evidence

## D.7 Release Artifacts
- Code repository (harness, strategies, analysis scripts), config-as-code run files, cached LLM calls (prompts + outputs), labeled rationale subsample (§6.2), processed-data reconstruction scripts

## D.8 Amendment Record
- Append-only log: date, item changed, old value → new value, rationale, affected analyses
- **A-001 (2026-07-09)** — instrument configuration correction. generation.temperature 0.0 → 0.7; generation.top_p 1.0 → 0.8. Reason: model validity — Qwen3 documentation advises against greedy decoding; the documented non-thinking-mode inference configuration provides a more valid evaluation of the instrument. Reproducibility remains enforced through fixed seeds, full prompt/output caching, model revision pinning, and experiment logging. Not triggered by any experimental outcome (no experiments have run). Affected analyses: all LLM-based runs (none executed yet).
