# Pre-Submission Audit (Pre-Experiment)

Conducted July 9, 2026, against the six audit criteria. Verdict at end.

## A. Research question → method → metric → interpretation rule → overclaim guard

| RQ / Contribution | Method | Metric(s) | Interpretation rule | Overclaim guard |
|---|---|---|---|---|
| RQ1: does LLM trading value survive bias controls? | Six-strategy ladder (§4.1), two tracks (§3.1), three contamination conditions (§3.4) | DSR vs S1 (primary), bootstrap CIs on Sharpe differences, FF3 alpha, cost sensitivity (§4.4–4.5) | Value-add requires DSR+, alpha ≠ 0, survival at 25 bps (§5.2); three-outcome readings pre-committed (§7.1) | No generalization beyond universe/window/model/frequency; no live-trading claims (§5.9, §7.1, §8) |
| RQ1 attribution: where does value enter? | Ladder contrasts S2−S1, S3−S1, S5−S3, S4 vs S5, S6−S5 (§5.3) | Pairwise differences with intervals | Rung-level conclusions only; intervals incl. zero = uninformative (§5.3) | Conclusions name the rung, never the paradigm (§5.3) |
| Contribution 2: memorization quantification | Original / anonymized / anonymized+shuffled runs (§3.4) | Sharpe gap original−anonymized with CI; shuffled-dates negative control (§5.4) | Advantage absent under anonymization → memorization/entity effects; shuffled excess ≠ 0 → leakage investigation (§5.4) | Framed as adaptation of Glasserman & Lin / Jeon & Lee, difference in emphasis not new instrument (§3.4, §7.1) |
| RQ2: rationale–behavior consistency | Rationale logging + taxonomy (§6.2); paraphrase test (§6.3); polarity-flip test (§6.4) | Flip rate vs seed baseline; directional agreement (observable cases only, exclusions reported); consistency proportions; continuous κ with CI (§6.2–6.5) | High consistency → usable summaries in this setting; low → rationales a liability (§6.5, §7.3) | Consistency ≠ causation stated in §6.1; no general-faithfulness claims; single agent/model scope (§7.3, §8) |
| RQ2 regime variation | Regime partitions (§4.6) applied to Tables 5–7 | Descriptive proportions with counts | Descriptive only; hypothesis-generating (§4.6, §5.7) | No per-regime significance, no abstract/conclusion claims (§5.7) |

Every RQ maps to a method; every method has metrics; every metric has an interpretation rule; every rule carries a guard. **Pass**, with findings in D below.

## B. Overclaiming spot-checks (resolved during drafting)
Removed/softened during section reviews: fabricated KDD page numbers and a constructed DOI (§1); "pre-registered" → "pre-specified" (§1); "hand-selected tickers without protocols" corrected to survey-supported claim (§1); "outperforming traditional sentiment measures" trimmed (§2); "became the standard" softened (§2); Jeon & Lee two-door attribution corrected (§3); S5 threshold-sharing bug (§4); DSR false-factorial wording (§4); "chance-level" made operational (§5); ±25% perturbation replaced by quantile grid (§5.8); "only this study can isolate" corrected (§7); García size-effect misattribution corrected (§9).

## C. Citation verification register (all checked this session)
**Verified against primary records (arXiv/ACM/ACL/Wiley/journal listings):** Yu et al. 2023 (FinMem); Xiao et al. 2024 (TradingAgents, v1); Xiao et al. 2025 (Trading-R1); Zhang et al. 2024 (FinAgent, ACM DOI); Li et al. 2025 (FINSABER); Ding et al. 2024 (survey — full-text §4–§5 checked for the claims cited); Glasserman & Lin 2023; Jeon & Lee 2026; Lopez-Lira & Tang 2023; Turpin et al. 2023 (NeurIPS); Jacovi & Goldberg 2020 (ACL DOI); Dong et al. 2024 (FNSPID); Bailey & López de Prado 2014 (JPM 40(5), 94–107); Fama 1970; Fama & French 1993; Jegadeesh & Titman 1993; Tetlock 2007; Loughran & McDonald 2011; García 2013; Lo 2004; Politis & Romano 1994; Sharpe 1966; Leetaru & Schrodt 2013. **Web sources with retrieval dates:** Finnhub, FRED, French data library, Cboe.
**Open items:** (1) Lopez-Lira & Tang JFE final publication details unconfirmed — currently cited as arXiv working paper (correct until confirmed). (2) Tetlock 2007 and García 2013 findings verified at abstract/secondary level — read full texts before submission. (3) Sharpe 1966 pagination taken from the Ding et al. survey's reference list — confirm against the journal.

## D. Appendix D freeze status
**Rules frozen:** universe rule; timing/execution convention; cost grid; contamination conditions; DSR trial-count rule; regime definitions; audit sample-size rule; κ guideline with continuous reporting; 10% spot-check fraction; amendment procedure; no-model-substitution rule.
**Values still required before pilot/full run (audit findings):**
1. Model instrument: exact model, revision hash, framework, quantization, generation parameters, and all five role prompts (D.1) — most important open item.
2. Audit budget figure (D.5).
3. S4 feature list, search space, calibration-window dates (D.3).
4. S3/S5 calibration procedure specifics (D.3).
5. Anonymization procedure specification — entity detection method, replacement scheme (D.4).
6. Bootstrap: number of resamples and block-length selection rule (D.4) — currently named but not valued.
7. Data snapshot identifiers: FNSPID commit, FRED series ID, S&P 500 TR source, factor file version, Track B query parameters (D.2).
8. **Gap found:** pilot verification targets (§3.5) lack quantitative pass criteria for news density (what minimum article count per ticker-day/week makes Track A viable?). Define before pilot, or the density judgment becomes result-driven.
9. Editorial: harmonize table numbering (Table 1 in §3 vs Tables 2–7 in §5–6) and merge per-section reference lists at integration.

## E. Verdict
Structure, mapping, and interpretation discipline: **ready**. The paper may proceed to integration. Experiments must not begin until items D.1–D.8 hold recorded values; item D.8 (density criterion) and C's three citation open items are the only substantive gaps discovered by this audit.
