# Experimental Freeze Document (v1.0 — July 9, 2026)

Companion to Appendix D. Each open item: decision required → options → trade-offs → recommendation → **frozen value**. Once signed off, this document is archived; changes go only through the Amendment Record (D.8). **No experiment begins until every [FREEZE] item below carries its value.**

---

## 1. D.1 Model Instrument

**Decision:** the single pinned open-weight model for all five roles (S5 scorer, S6 agent, rationale classifier, paraphrase generator, polarity-flip generator).

**Options.**
- **A — Qwen3-14B (Instruct).** Current leaderboards place the Qwen3 family as the standard mid-size open-weight choice; Apache-2.0; released April 2025, so its training data predates the Track B window (Jan–Jun 2026) — the design-critical property. Runs in bf16 on a single rented 48–80 GB GPU, or quantized on consumer hardware. *Con:* 14B reasoning is below frontier; S6 agent quality is bounded by it.
- **B — Llama-3.x-8B-Instruct.** Cheapest, most-replicated baseline; runs locally on 12–16 GB VRAM. *Con:* weakest instruction-following of the three; higher risk of malformed structured outputs, which inflates harness rejection handling.
- **C — 70B-class open model (rented multi-GPU).** Strongest reasoning; closest to what agent papers deploy. *Con:* 3–5× inference cost consumes the audit budget; multi-GPU inference adds nondeterminism and reproducibility friction.

**Recommendation: A.** Best quality-per-cost inside the budget; single-GPU bf16 avoids quantization nondeterminism; the pre-2026 cutoff preserves Track B validity; Apache-2.0 permits releasing cached outputs. The bounded capability is a scoped limitation (§8), not a validity threat — conclusions attach to the instrument by design.

**Frozen values:**
- Model: **Qwen3-14B, instruction-tuned variant**; exact Hugging Face repository ID and **weights revision hash recorded at download** (mechanical lookup, not a decision; recorded in D.1 before pilot).
- Parameters: 14B class; context window as shipped (recorded with revision).
- Inference framework: **vLLM (version pinned at download)**, single GPU, **bf16, no quantization**. Fallback if local-only hardware forces it: llama.cpp Q8_0 — allowed only via Amendment Record and labeled as instrument change.
- Generation: **temperature 0.7; top_p 0.8** *(Amendment A-001, 2026-07-09: instrument configuration correction — vendor documentation advises against greedy decoding; not outcome-triggered)*; **max_tokens 512 (S6), 64 (S5 scorer), 64 (classifier), 1024 (paraphrase/flip generators); fixed stop sequences; seeds {11, 42, 2026}**.
- Structured output: S5/S6/classifier responses constrained to JSON schemas; malformed outputs retried once, then logged as abstentions (S6 abstention = hold current position; count reported).
- **No model substitution after results are seen; any other model's runs are labeled exploratory.**

**Frozen system prompts (Appendix A, v1.0 — final wording archived at freeze):**
- **S5 scorer:** "You are a financial news analyst. Given the news items below about one company, output JSON {\"score\": s} where s ∈ [-1, 1] reflects the net sentiment of the news for the company's near-term stock performance. Consider only the provided text. Do not use any other knowledge about the company."
- **S6 agent:** "You are a trading assistant managing a single-stock position. Inputs: recent news summaries (trailing 3 trading days), daily closing prices (trailing 60 trading days), current position (long/flat). Decide the position for the next session. Output JSON {\"action\": \"long\"|\"flat\", \"rationale\": one paragraph explaining the primary driver of your decision}. Base your decision only on the provided inputs."
- **Rationale classifier:** "Classify the primary driver stated in this trading rationale into exactly one of: sentiment, price_momentum, risk_management, mixed_other. Output JSON {\"label\": ...}. Judge only what the rationale states, not whether it is correct."
- **Paraphrase generator:** "Rewrite the following news text preserving all factual content, named entities, figures, and sentiment. Change only wording and sentence structure. Output the rewritten text only."
- **Polarity-flip generator:** "Rewrite the following news text keeping all named entities, figures, and event descriptions unchanged, but invert the evaluative language so the overall sentiment is reversed. Output the rewritten text only."

## 2. Audit Budget and Sample-Size Rule

**Decision:** total inference budget and audit share. **Options:** $50 (cripples the audit), **$200**, $500 (exceeds a student project's defensible spend without changing conclusions' scope). **Recommendation/Frozen:** **total inference budget $200 (≈100 A100-hours at prevailing rental rates, or equivalent local GPU time); audit sub-budget 30% ($60)**. Sample-size rule as frozen in §6.6: largest regime-stratified seeded sample fitting the audit sub-budget; human-validation subsample: **min(200, 20% of audited rationales)**. N values recorded post-pilot as [PILOT→PARAM].

## 3. S4 Search Space and Calibration Windows

**Decision:** training data, features, model family, search procedure. **Options:** logistic regression (too weak to be the "any-ML" control), **LightGBM** (standard tabular choice, fast, deterministic with fixed seed), deep nets (unjustified for ~15k training rows). **Recommendation/Frozen:**
- **Training/calibration window: 2019-01-02 to 2021-12-31** (three years; includes the 2020 stress episode so calibration sees more than one regime; strictly pre-evaluation).
- **Features (per ticker-day):** lagged returns (1, 5, 21 d); MA ratios (10/50, 50/200); 21-day realized volatility; 21-day volume z-score; FinBERT daily mean sentiment and trailing 3-day mean.
- **Model: LightGBM classifier, fixed seed 42.** Search space: num_leaves {15, 31, 63}; learning_rate {0.01, 0.05, 0.1}; n_estimators {100, 300, 500}; min_child_samples {20, 50}; feature_fraction {0.8, 1.0}. Selection: 5-fold expanding-window time-series CV within the training window, log-loss criterion. Decision rule: long if predicted P(up) > 0.5.
- **S3/S5 threshold calibration (frozen):** threshold = the percentile of the calibration-window score distribution, among {30, 40, 50, 60, 70}, that maximizes calibration-window Sharpe — evaluated on pre-window data only, consistent with the §5.8 sensitivity grid.

## 4. Anonymization Procedure (Appendix E)

**Decision:** how entities are masked. **Options:** (a) automated NER only — scalable but misses tickers, product names, CEO names, colloquial aliases; (b) **curated per-firm alias dictionary + NER fallback** — feasible for exactly 20 firms and materially higher recall; (c) LLM-based masking — introduces the instrument into its own control condition; rejected. **Recommendation/Frozen: (b).**
- For each universe firm: curated list of company names, tickers, brands/products, executive names, headquarters city (compiled from public profiles; frozen pre-pilot).
- Replacement: consistent neutral placeholders within each decision context ("the Company", "the CEO", "Product A"); placeholder assignment re-randomized across decision days (seed 42) so cross-day identity cannot be inferred.
- spaCy NER (version pinned) as fallback for residual ORG/PERSON/GPE entities; URLs, bylines, and publication names stripped.
- **Date shuffling:** within-ticker permutation of article dates across the Track A window, seed 42, article set preserved.
- **Validation:** on the 10% spot-check sample, the annotator attempts firm identification from anonymized text; the identification rate is reported as a protocol-quality metric (not tuned against).

## 5. Bootstrap Parameters

**Decision:** resample count and block length. **Options:** B = 1,000 (unstable tail quantiles), **B = 10,000** (stable 95% CIs, trivial compute), B = 100,000 (waste). Block length: data-driven selection (adds an unverified methods citation) vs. **fixed expected block length with sensitivity**. **Recommendation/Frozen:** **B = 10,000; stationary bootstrap expected block length ℓ = 21 trading days (≈1 month, matching the persistence horizon of the monthly-refreshed signals); sensitivity at ℓ ∈ {5, 63} reported in appendix; RNG seed 2026.**

## 6. Data Snapshot Identifiers and Versioning

**Frozen procedure:** at download, record (i) FNSPID repository commit hash and file SHA-256 checksums; (ii) yfinance library version and query date; auto/back-adjustment settings (adjusted prices, dividends+splits); (iii) **FRED series DTB3** (3-month Treasury bill, secondary market, daily) with retrieval date; (iv) S&P 500 total-return via **^SP500TR** (Yahoo Finance) with retrieval date; (v) VIX daily closes via Cboe historical data or ^VIX (Yahoo), source recorded; (vi) Fama–French daily factors file name and download date from the French library; (vii) Finnhub/GDELT query parameters and retrieval timestamps (Track B, [PILOT→PARAM] for final configuration). All snapshots hashed and archived; the manuscript's "recorded at protocol freeze" placeholders are then replaced by these values.

## 7. Remaining Citation Items — Resolution

1. **Lopez-Lira & Tang JFE status:** searched again this session; final journal volume/pages remain unconfirmed. **Frozen action:** retain the arXiv working-paper citation; re-check once at submission time; update only the reference entry (no textual claims change).
2. **Tetlock (2007) / García (2013) full texts:** publicly posted PDFs exist (Columbia; Leeds faculty page). **Frozen action:** author reads both before submission and confirms the two sentences citing them; flagged as pre-submission checklist items — not blockers for experiments, since no experimental choice depends on them.
3. **Sharpe (1966) pagination:** 39(1), 119–138 corroborated by two independent sources this session; **resolved**, with a final glance at the journal record during proofreading.

---

## Final Frozen Protocol Checklist

**[FREEZE] — complete upon signing this document:** model family/variant, inference framework, precision, generation parameters, seeds, five system prompts (§1); budget figures and sample-size rules (§2); S4 window/features/search space, S3/S5 calibration rule (§3); anonymization and date-shuffle procedures (§4); bootstrap B and ℓ (§5); snapshot/versioning procedure and series identifiers (§6); plus all previously frozen items (universe rule; timing/execution; cost grid 5/10/25 bps; contamination conditions; DSR trial-count rule; regime definitions; news-density criterion M1/M2; κ guideline; 10% spot-check; amendment procedure).

**[FREEZE — mechanical, record at download, before pilot]:** exact HF repository ID + weights revision hash; vLLM/spaCy/yfinance versions; dataset commit hashes and checksums; factor-file version.

**Remaining [PILOT→PARAM] (values set by frozen rules + pilot measurements, never by results):** audit sample N and human-validation N (budget rule, §2); FNSPID timestamp-granularity determination → §3.2 convention selection; per-ticker M1/M2 outcomes → any exclusions; Track B final source configuration (Finnhub vs. GDELT weighting, query filters); per-decision cost/latency → full-run feasibility envelope.

**Confirmation: no experiment — pilot included beyond its validation purpose, and no strategy performance run — begins until every [FREEZE] item above carries its recorded value, and no [PILOT→PARAM] value may be influenced by any strategy's performance.**

---

## Pilot Implementation Plan (Phase 2)

**Purpose (per protocol):** pipeline validation only. The pilot produces a **Pipeline Validation Report**, not performance claims; its trading outcomes are never reported as evidence.

**Build order (≈2–3 weeks):**
1. **Data ingestion:** FNSPID subset loader (universe tickers, 2019–2023 for calibration + Track A); yfinance price fetch + second-source cross-check; snapshot hashing per §6.
2. **Alignment and integrity layer:** news↔price timestamp alignment; the §3.2 mechanical assertion (future-dated record injection test must fail loudly); M1/M2 computation per ticker (Table 1 inputs).
3. **Backtest harness:** accounting identity, cost model, turnover; unit tests on synthetic paths with known outcomes; S1/S2 reconciliation against an independent implementation.
4. **Inference wrapper:** vLLM serving with role prompts, JSON-schema validation, retry/abstention logic, full call caching keyed by (prompt hash, params, seed).
5. **Anonymization module:** alias dictionaries + NER fallback + date shuffler; identification-rate spot-check tooling.
6. **Pilot run:** two tickers (seeded random draw from universe), three-month sub-window, all six strategies, all three conditions for S5/S6, one seed; measure per-decision cost/latency.

**Pipeline Validation Report — required contents:** data ingestion pass/fail per source; timestamp correctness findings and granularity determination; price-alignment cross-check results; harness unit-test and reconciliation results; reproducibility check (two identical runs → byte-identical cached outputs); cost/latency per decision and full-run projection vs. budget; M1/M2 per pilot ticker; anonymization identification rate; list of any protocol amendments proposed (each mapped to a data/infrastructure cause — Phase 3 allows "coverage was insufficient, source configuration changed"; it forbids "strategy performed poorly, threshold changed").

**Phase gates:** Phase 3 (parameter updates from pilot) touches only [PILOT→PARAM] items through the Amendment Record; Phase 4 (full grid: Tables 2–7, Figures 1–2, ablations, audit) begins only after the Validation Report is archived and Appendix D shows no empty [FREEZE] fields.
