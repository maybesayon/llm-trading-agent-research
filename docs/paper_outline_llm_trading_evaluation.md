# Research Paper Outline

## Working Title
**"How Much of LLM Trading-Agent Performance Survives Bias-Controlled Evaluation? An Independent Study with a Rationale Audit"**

*Alternative (shorter, for the finance audience):* "LLM Trading Agents Under Bias-Controlled Evaluation"

**Format target:** 8 pages ACL style (long paper), ≈ 6,700 words body text + references + appendix.
**Note on Results:** until experiments are run, §5–§6 are drafted as *analysis plan and expected findings*; numbers are inserted only from real runs. Nothing in the draft may state an empirical outcome that has not occurred.

---

## Abstract (~180 words)

**Purpose:** compress the entire paper — dispute, method, headline finding, implication — into one self-contained paragraph.
**Key arguments:** the literature contradicts itself on LLM trading alpha; we run the first pre-specified, bias-controlled comparison; we quantify memorization; we audit rationales.
**Evidence required:** final headline numbers (DSR of S6 vs S1, memorization gap, rationale-consistency rate).
**Sources:** none cited in abstract.
**Paragraph breakdown (single paragraph, 6 sentences):**
1. Context: LLM agents report market-beating backtests. 2. Problem: independent re-evaluations disagree; existing evidence is bias-prone. 3. Method: six strategies, identical data, pre-specified metrics, memorization protocol, out-of-cutoff validation. 4. Result slot A (RQ1): [numbers]. 5. Result slot B (RQ2): [rationale-audit finding]. 6. Implication + artifact release.

---

## 1. Introduction (~900 words)

**Purpose:** establish the contradiction, state thesis and contributions, preview design. The reader must know by the end of page 1 exactly what question is answered and how.
**Key arguments:** (a) the field's evidence base is split; (b) the split is plausibly explained by evaluation artifacts; (c) resolving it requires an independent, pre-specified evaluation, which nobody has done; (d) what agents *say* vs. *do* is a second, unexamined gap.
**Evidence required:** reported performance claims from agent papers; the contradicting re-evaluation result; documented backtest-fragility findings.
**Recommended source types:** the primary agent papers (FinMem, FinAgent, TradingAgents); the 2025 skeptical re-evaluation; the backtest-overfitting methodology literature; one LLM-rationale-unfaithfulness study.

**Paragraph breakdown:**
- **P1 — Hook via contradiction.** Objective: state that LLM trading agents report outperformance, and independent re-evaluation reverses the conclusion under bias controls. End with the tension in one sentence. *Evidence: specific claims from both sides.*
- **P2 — Why the contradiction is predictable.** Objective: connect to the known fragility of backtests (look-ahead, selection, multiple testing, costs) and the LLM-specific problem of training-data memorization. *Evidence: backtest-validity literature; memorization/look-ahead studies of GPT-based prediction.*
- **P3 — The gap.** Objective: argue that no existing study combines (i) pre-specified protocol, (ii) memorization quantification, (iii) full baseline ladder including supervised ML, (iv) out-of-cutoff validation. One sentence per missing element.
- **P4 — The second gap (RQ2).** Objective: introduce the rationale problem — agents produce natural-language reasons, but rationale faithfulness is known to be unreliable in LLMs, and nobody has audited trading rationales against trading behavior.
- **P5 — Thesis and research questions.** Objective: state RQ1, RQ2, and the falsifiable thesis verbatim from the proposal; state explicitly that both outcomes are informative and why.
- **P6 — Design preview.** Objective: two sentences on the six-strategy ladder and two-track data design. No detail — signpost to §3–§4.
- **P7 — Contributions.** Objective: the four numbered contributions from the proposal, one line each, phrased as completed acts ("We quantify…", "We release…").

---

## 2. Related Work / Literature Review (~900 words)

**Purpose:** position the paper at the intersection of four literatures and show that the intersection is empty — that is the originality claim.
**Key arguments:** each literature supplies one ingredient; none combines them.
**Evidence required:** representative works per literature, accurately characterized.
**Recommended source types listed per subsection below. Do not cite anything unread; keep [Citation Needed] markers until each source is verified.**

**Paragraph breakdown:**
- **P1 — §2.1 LLM trading agents.** Objective: taxonomy in three sentences (reflection-driven: FinMem/FinAgent; debate/multi-role: TradingAgents; RL-tuned: Trading-R1), then their shared evaluation weakness: self-evaluation on hand-picked tickers and windows. *Sources: the agent papers themselves and the field survey.*
- **P2 — §2.2 News sentiment and returns.** Objective: establish that sentiment→returns is an old, well-measured effect concentrated in small caps and short horizons, evolving from lexicons to FinBERT to LLM scoring. This justifies both baselines S3/S5 and the "conservative universe" interpretation. *Sources: landmark media-sentiment asset-pricing studies (2000s), the finance-lexicon paper, FinBERT, and the first LLM-return-prediction study.*
- **P3 — §2.3 Backtest validity and LLM memorization.** Objective: two sentences on classical corrections (multiple-testing, deflated performance metrics); two on LLM-specific look-ahead via memorized history; one on anonymization-based mitigation. This subsection *is* the methods justification. *Sources: backtest-overfitting canon; GPT look-ahead-bias study; anonymization-first evaluation paper.*
- **P4 — §2.4 Rationale faithfulness.** Objective: state the finding that LLM-stated reasons can misrepresent actual decision drivers; note that this has never been tested in a trading context. *Sources: chain-of-thought unfaithfulness literature (NLP interpretability).*
- **P5 — Synthesis and gap statement.** Objective: one paragraph, four literatures → one table-like sentence each → "no prior work combines A+B+C+D; we do." Optionally frame with efficient-vs-adaptive-markets theory to motivate regime analysis. *Sources: EMH and Adaptive Markets Hypothesis foundational works.*

---

## 3. Methodology I — Data and Bias Controls (~900 words)

**Purpose:** make the evaluation credible before any result is shown; every design choice pre-empts a named bias.
**Key arguments:** rule-based universe kills selection bias; timing rule kills look-ahead; anonymization protocol measures (not assumes away) memorization; Track B provides genuinely out-of-cutoff data.
**Evidence required:** dataset statistics (coverage, article counts, date ranges — computed from the actual data); universe list with the selection rule and date; verified delisting handling.
**Recommended source types:** the FNSPID dataset paper; the news-API documentation for Track B; the memorization-protocol methodology papers.

**Paragraph breakdown:**
- **P1 — Track A data.** Objective: describe FNSPID subset used (window 2022-01–2023-12, tickers, article volume). Table 1: universe + coverage stats. *[Numbers from real data only.]*
- **P2 — Universe rule.** Objective: state the rule (top-20 S&P 500 by market cap at 2021-12-31), why rule-based (selection bias), and how delistings are handled point-in-time. Acknowledge in one sentence that mega-caps are a deliberately conservative testbed, with forward-reference to Limitations.
- **P3 — Timing and cost model.** Objective: information set = data timestamped ≤ close of day *t*; execution at open of *t+1*; 10 bps per side with 5/25 bps sensitivity. One sentence on why each choice matters (look-ahead; realism).
- **P4 — Memorization-quantification protocol.** Objective: define the three conditions (real / anonymized entities / date-shuffled) and the memorization-gap estimand. State that Track A conclusions are conditioned on this measurement.
- **P5 — Track B.** Objective: describe the 2026-H1 forward window, its news source, its role (validation, secondary), and its known limitation (thinner coverage).

## 4. Methodology II — Strategies and Evaluation Protocol (~1,100 words)

**Purpose:** define the six strategies so precisely that a reader could re-implement them, and freeze the statistical protocol.
**Key arguments:** the baseline ladder isolates, step by step, where any value is added (market → momentum → classical sentiment → supervised ML → LLM scorer → LLM agent); pre-specification and DSR answer the multiple-testing critique the paper itself raises.
**Evidence required:** exact hyperparameters, prompts (appendix), model version, seed policy; the accounting identity for portfolio returns.
**Recommended source types:** deflated-Sharpe / multiple-testing methodology; factor-model data library documentation; the agent papers being simplified (for honest disclosure of differences).

**Paragraph breakdown:**
- **P1 — Ladder rationale.** Objective: one paragraph explaining why six strategies and what each rung isolates. This is the paper's key inferential design — write it as argument, not list.
- **P2 — S1–S2 (passive, momentum).** Objective: exact specifications in 3–4 sentences.
- **P3 — S3–S4 (FinBERT rule; gradient-boosted trees).** Objective: features, thresholds, training/validation split for S4 with explicit no-leakage statement.
- **P4 — S5 (LLM scorer).** Objective: prompt design summary, score→action rule identical to S3 (that identity is the ablation).
- **P5 — S6 (reference agent).** Objective: architecture (news summary + price history + portfolio state → long/flat + rationale); explicit disclosure that S6 is a simplified FinMem-style agent, with a sentence enumerating what was removed relative to the original systems and why conclusions are scoped to the class, not the brands.
- **P6 — Portfolio accounting.** Objective: the return identity (equal-weight long positions; flat capital at T-bill rate), turnover definition.
- **P7 — Statistical protocol.** Objective: primary metric (DSR vs S1 corrected for the full grid), secondaries (net return, drawdown, factor alpha), stationary-bootstrap CIs, all-runs-reported commitment, and the sentence "protocol frozen prior to experiments" with a pointer to the released pre-specification.
- **P8 — Reproducibility.** Objective: pinned open-weight model + version, temperature/seed policy, full call caching, code release.

---

## 5. Results (~1,000 words) — *drafted first as Expected Findings / Analysis Plan*

**Purpose:** answer RQ1. Until data exist, this section is drafted as the analysis plan with empty result slots; after experiments, each paragraph receives its numbers without structural change.
**Key arguments (conditional):** either (a) no strategy achieves significant DSR over S1 → thesis confirmed, or (b) some rung does → the ladder identifies exactly which ingredient produced it.
**Evidence required:** all numbers from actual runs; no exceptions.
**Recommended source types:** none new — internal results plus comparisons to numbers reported in the agent papers.

**Paragraph breakdown:**
- **P1 — Main table walkthrough.** Objective: Table 2 (six strategies × {net return, Sharpe, DSR, drawdown, turnover, FF3 alpha}); text states the RQ1 answer in the first sentence. *[Slot.]*
- **P2 — Ladder attribution.** Objective: interpret adjacent rungs (S3 vs S5: does LLM scoring beat FinBERT? S5 vs S6: does agency add anything over scoring? S4 vs S5/S6: does any LLM rung beat supervised ML?). *[Slots.]*
- **P3 — Memorization effect.** Objective: report the real-vs-anonymized-vs-shuffled gap; state what fraction of apparent performance it explains. This paragraph is contribution 2 and stands regardless of RQ1's direction. *[Slot.]*
- **P4 — Cost sensitivity.** Objective: report how conclusions move at 5/25 bps; one paragraph, one figure. *[Slot.]*
- **P5 — Track B validation.** Objective: do Track A conclusions hold out-of-cutoff? State agreement/disagreement plainly. *[Slot.]*
- **P6 — Comparison to published claims.** Objective: place our S6 results next to the numbers reported by FinMem/FinAgent and the skeptical re-evaluation; attribute differences to named design deltas, not innuendo.

## 6. Rationale Audit (~700 words) — *drafted first as Analysis Plan*

**Purpose:** answer RQ2; give the paper a contribution that is informative even under a null RQ1.
**Key arguments:** stated drivers can be classified reliably; perturbation tests reveal whether decisions track stated reasons; consistency varies by regime (descriptive).
**Evidence required:** rationale taxonomy counts, inter-annotator or classifier-agreement figure, perturbation flip rates, regime splits.
**Recommended source types:** NLP interpretability/faithfulness methodology for metric definitions.

**Paragraph breakdown:**
- **P1 — Taxonomy and prevalence.** Objective: what drivers the agent claims, in what proportions; how classification reliability was established. *[Slot.]*
- **P2 — Robustness test.** Objective: neutral-paraphrase flip rate (should be ≈ 0); interpret deviations. *[Slot.]*
- **P3 — Sensitivity test.** Objective: polarity-flip agreement rate; acknowledge residual content confounds in one sentence. *[Slot.]*
- **P4 — Consistency and regimes.** Objective: agreement between stated driver and behavioral response; descriptive regime breakdown with explicit small-n caveat. *[Slot.]*

---

## 7. Discussion (~500 words)

**Purpose:** interpret, don't repeat. Answer: what should the field now believe, and who should change their behavior?
**Key arguments:** what the ladder localizes; what the memorization gap implies for every historical LLM backtest; what rationale (in)consistency implies for agent deployment and for reviewers of agent papers.
**Evidence required:** none new; synthesis only.

**Paragraph breakdown:**
- **P1 — RQ1 verdict in context.** Objective: reconcile our result with both prior camps; state which prior claims survive.
- **P2 — Methodological implication.** Objective: argue the memorization protocol should become standard practice for any historical LLM backtest; one sentence on cost of adoption (near zero).
- **P3 — RQ2 implication.** Objective: what rationale-behavior consistency means for trusting agent explanations; connect back to the faithfulness literature.
- **P4 — Theory link.** Objective: read regime-dependence through the adaptive-markets lens in 3–4 sentences; flag as interpretive, not tested.

## 8. Limitations (~300 words)

**Purpose:** pre-empt reviewers; scope claims honestly.
**Paragraph breakdown:**
- **P1:** design limits — mega-cap conservative universe; simplified reference agent (not brand replication); US-only; daily frequency.
- **P2:** inference limits — backtest ≠ live trading; regime analysis descriptive; Track B short and thin; residual content confounds in polarity flips; results tied to one pinned model.

## 9. Future Work (~120 words)

**Purpose:** convert every deferred scope decision into a roadmap.
**Single paragraph:** mid-/small-cap universes where sentiment effects should be stronger; multiple model families; longer live evaluation; faithful full replications of named agents; extension of the rationale audit to multi-agent debate systems.

## 10. Conclusion (~130 words)

**Purpose:** restate thesis verdict and contributions in past tense; end on the artifact release.
**Single paragraph, 5 sentences:** question → method in one clause → RQ1 answer → RQ2 answer → what we release and what the field should do differently.

---

## Appendices (not counted in 8 pages)
- A: full prompts for S5/S6; B: hyperparameters; C: per-ticker results (all runs); D: pre-specified protocol as frozen; E: anonymization procedure details.

## Word-count summary

| Section | Words |
|---|---|
| Abstract | 180 |
| 1 Introduction | 900 |
| 2 Related Work | 900 |
| 3 Data & Bias Controls | 900 |
| 4 Strategies & Protocol | 1,100 |
| 5 Results | 1,000 |
| 6 Rationale Audit | 700 |
| 7 Discussion | 500 |
| 8 Limitations | 300 |
| 9 Future Work | 120 |
| 10 Conclusion | 130 |
| **Total body** | **≈ 6,730** |
