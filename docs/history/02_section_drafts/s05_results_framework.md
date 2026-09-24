# 5. Results: Pre-Specified Reporting and Analysis Framework

*Status note: experiments have not yet been conducted. This section specifies, in advance of any experiment, what will be measured, how it will be calculated, how the outputs will be reported, and which interpretations the design does and does not license. Every table and figure below is a placeholder to be populated exclusively from executed runs. Nothing in this section states, estimates, or predicts an empirical outcome. The complete set of pre-committed analytic choices — hyperparameters, model versions and revisions, prompts, seeds, thresholds, dataset snapshots, and evaluation scripts — is archived in Appendix D (Frozen Experimental Protocol) before the first full-scale run, so that no analytic choice can be adjusted, consciously or otherwise, after results are seen.*

## 5.1 Primary Strategy Comparison

**Table 2: Strategy performance comparison, S1–S6 (to be populated after experiments).** Rows: the six strategies under the original-input condition at the 10-bps cost setting. Columns: cumulative return, annualized return, annualized volatility, Sharpe ratio, deflated Sharpe ratio versus S1, maximum drawdown, downside deviation, annualized turnover, and Fama–French three-factor alpha with its standard error. Every cell derives from the accounting identity of §4.3 applied to logged daily positions; no quantity is computed outside the harness. **Figure 1: Equity curves for S1–S6 with the S&P 500 total-return index (to be generated after experiments)**, plotted on a log scale over the Track A window with regime shading as defined in §4.6.

The first sentence of the populated section will state the answer to RQ1 in terms of the primary endpoint: whether any active strategy's deflated Sharpe ratio versus S1 is positive and statistically distinguishable from zero after the multiple-testing correction of §4.5. The evaluation will test whether the LLM-based strategies provide improved risk-adjusted performance relative to the baselines under the defined experimental conditions; the design treats improvement, equivalence, and deterioration as equally reportable outcomes.

## 5.2 Benchmark and Risk-Adjusted Comparison

Each active strategy will be compared against both benchmarks of §4.4. Interpretation follows pre-committed rules. A claim that a strategy "adds value" requires all three of: a positive DSR versus S1 after correction; a three-factor alpha distinguishable from zero; and survival of the result at the 25-bps cost setting. Failing any one, the result will be described in the specific terms of what was and was not observed (for example, positive raw Sharpe difference with a DSR indistinguishable from zero), without a value-added claim. Point estimates will never be interpreted without their interval estimates.

**Table 3: Bootstrap confidence intervals for Sharpe-ratio differences versus S1 (to be populated after experiments).** Stationary-bootstrap intervals (§4.5) at the 95% level, with block-length parameter recorded in Appendix D.

## 5.3 Ablation Analysis

The ladder contrasts of §4.1 will be reported as pairwise differences with intervals: S2−S1 (price anomaly), S3−S1 (classical text signal), S5−S3 (measurement technology: generative LLM versus FinBERT), S4 versus S5 (supervised learning versus LLM scoring on the same information set), and S6−S5 (agency versus scoring). Each contrast answers one attribution question, and conclusions will name the rung, not the paradigm: for example, a positive S6−S5 contrast would support a contribution of the agent architecture *given this model and window*, not a general claim that "agents work." Contrasts whose intervals include zero will be reported as uninformative on that rung.

## 5.4 Memorization and Contamination Results

**Table 4: LLM-based strategies under the three conditions of §3.4 — original inputs, anonymized inputs, and anonymized inputs with shuffled dates (to be populated after experiments).** For S5 and S6, all Table 2 metrics under each condition of §3.4, plus the pre-specified memorization-gap estimand: the difference in Sharpe ratio between original and anonymized conditions, with bootstrap intervals. Interpretation rules: a performance advantage present under original inputs but absent under anonymization will be attributed to memorization or entity-knowledge effects rather than to signal extraction, following the logic of Glasserman and Lin (2023); in the shuffled-dates condition, where no genuine time-aligned signal should exist, a Sharpe-ratio excess over S1 whose bootstrap interval excludes zero would indicate residual leakage and trigger a documented investigation before any Track A conclusion is drawn. This table stands as a contribution regardless of the direction of the RQ1 result.

## 5.5 Transaction-Cost Sensitivity

**Figure 2: Sharpe ratio and cumulative return of each strategy at 5, 10, and 25 bps per side (to be generated after experiments).** The populated text will report which, if any, qualitative conclusions of §5.1–§5.3 change across cost settings. A conclusion that holds only at the most favorable cost setting will be labeled cost-fragile and excluded from the paper's headline claims.

## 5.6 Out-of-Cutoff Validation (Track B)

Track B results will be reported in the same format as Table 2, clearly labeled as a short-window validation with limited power (§3.1). The pre-committed use is directional consistency, not significance: agreement in sign and approximate magnitude between Track A (anonymized condition) and Track B will be reported as supporting the adequacy of the anonymization protocol; disagreement will be reported as a finding about the protocol itself, and Track A conclusions will be correspondingly qualified. Track B will not be used to rescue or overturn Track A conclusions on its own.

## 5.7 Regime-Based Reporting

**Table 5: Per-regime descriptive performance (to be populated after experiments).** All strategies' returns, volatility, drawdown, and — for S6 — position frequencies, within the bear/non-bear and VIX-tercile partitions of §4.6, with per-regime observation counts stated in the table. Consistent with the precision statement of §4.5, this reporting is descriptive: no per-regime significance tests will be conducted, no per-regime claims will appear in the abstract or conclusions, and any regime pattern will be framed as hypothesis-generating, to be tested confirmatorily in future work. The populated text will note whether observed patterns are directionally consistent or inconsistent with the regime-dependence documented by García (2013) and with the bull/bear asymmetry reported by Li et al. (2025), without asserting confirmation of either.

## 5.8 Robustness Checks

Four pre-specified checks will be reported: across-seed dispersion for the LLM-based strategies (§4.7), with any configuration whose across-seed Sharpe range exceeds its bootstrap interval width flagged as unstable; per-ticker results for all strategies (Appendix C), reported in full to preclude selective emphasis; threshold-sensitivity analysis for S3 and S5, re-running each with thresholds set at the 30th, 40th, 50th, 60th, and 70th percentiles of the pre-window score distribution and reporting the full performance curve — a grid fixed before experiments and chosen over a multiplicative perturbation of the calibrated value because percentile placement is invariant to each scorer's arbitrary scale and remains meaningful when the calibrated threshold lies near zero, where a proportional perturbation would be negligible; and pilot-to-full consistency, confirming that no protocol amendment recorded under §3.5 altered any pre-specified analysis.

## 5.9 Statistical Framework and Limits of Inference

All interval estimates use the stationary bootstrap (Politis & Romano, 1994) on daily returns. The multiple-testing correction enters through the deflated Sharpe ratio (Bailey & López de Prado, 2014), applied as specified in §4.5 with the trial count fixed by the frozen grid; the trial count and all DSR inputs (skewness, kurtosis, sample length) will be reported so the calculation can be reproduced. Two limits are stated in advance. First, with approximately 500 trading days in Track A and twenty assets, the design has limited power against small true differences; wide intervals are the expected presentation, not a defect to be explained away. Second, all inference is conditional on the single evaluation window and universe; no statistical statement in this paper generalizes beyond them, and external validity rests on the design features (§3) rather than on the inferential statistics.

## 5.10 Interpreting Negative, Mixed, or Inconclusive Results

The study's value does not depend on any strategy outperforming. Pre-committed interpretations: if no LLM-based strategy achieves a corrected positive DSR versus S1, the result will be reported as an absence of evidence for bias-robust value-add in this setting — informative because the setting was designed to remove the artifacts that could manufacture such evidence — and explicitly not as proof that LLM strategies cannot add value elsewhere. If results are mixed across rungs (for example, an informative S5 contrast but an uninformative S6 contrast), the ladder localizes the finding and the paper will report rung-level conclusions only. If results are inconclusive throughout — intervals too wide to distinguish any pair — the paper will report this plainly, present the memorization table (§5.4) and the audit (Section 6) as its primary empirical contributions, and state the sample sizes future work would need. Under no outcome will post-hoc subgroups, alternative metrics, or unplanned configurations be introduced to obtain a reportable difference; any exploratory analysis conducted after unblinding will be labeled as such in a separate, clearly demarcated subsection.

## 5.11 Contextual Comparison with Published Results

The populated section will close by placing our S6 results alongside the performance reported for FinMem (Yu et al., 2023), FinAgent (Zhang et al., 2024), and the re-evaluation of Li et al. (2025). Because our reference agent, universe, window, and cost model differ from each of these by design, differences in outcomes will be attributed only to named design deltas (agent simplification, cost model, universe rule, contamination condition) and no claim of replication success or failure of any named system will be made.

---

*No new references are introduced in this section. All cited works appear in the reference lists of Sections 1–4.*
