# Research Proposal (Revised)

## How Much of LLM Trading-Agent Performance Survives Bias-Controlled Evaluation? An Independent Study with a Rationale Audit

**Author:** Sayon Upadhyay
**Version:** 2.0 — July 2026

---

## 1. Motivation and Research Question

Large language model (LLM) trading agents such as FinMem ([Yu et al., 2023](https://arxiv.org/pdf/2311.13743)) and FinAgent ([Zhang et al., KDD 2024](https://personal.ntu.edu.sg/boan/papers/KDD24_FinAgent.pdf)) report backtests that outperform buy-and-hold benchmarks. Independent re-evaluation, however, finds that once look-ahead and selection biases are controlled, the market baseline outperforms these agents ([arXiv 2505.07078](https://arxiv.org/pdf/2505.07078)). This unresolved contradiction — combined with a quantitative-finance literature documenting the fragility of backtests under multiple testing and cost assumptions [Citation Needed: Bailey & López de Prado; Harvey & Liu] — means the field currently lacks a credible, independent, fully pre-specified evaluation of whether sentiment-driven LLM agents add value.

**Primary research question (RQ1).** How much of the reported outperformance of sentiment-driven LLM trading agents survives bias-controlled evaluation — rule-based universe selection, cost-adjusted next-open execution, memorization checks, and multiple-testing correction — on US large-cap equities?

**Secondary research question (RQ2).** Are the agents' stated trading rationales consistent with their trading behavior, and how does this consistency vary across market regimes?

**Thesis.** Reported outperformance of sentiment-driven LLM trading agents is substantially attributable to evaluation artifacts. Under the controls above, such agents will not deliver statistically significant risk-adjusted alpha over passive and classical baselines on US large-caps; however, their rationales will exhibit systematic, regime-dependent sensitivity patterns that inform when and why they fail. Both confirmation and refutation of this thesis are informative: confirmation establishes that current evidence for LLM trading alpha is an evaluation artifact; refutation would constitute the first bias-controlled demonstration of such alpha.

**Contributions.**
1. The first pre-specified, bias-controlled comparative evaluation of sentiment-driven LLM trading strategies against passive, classical-quant, classical-NLP, and supervised-ML baselines on identical data.
2. A quantification of LLM memorization effects in historical backtests via ticker anonymization and date-shuffling controls.
3. A decision-sensitivity and rationale audit linking what agents *say* to what they *do*, across market regimes.
4. Released code, cached model outputs, and evaluation harness for reproducibility.

## 2. Related Work

Four literatures frame this study. **(a) LLM trading agents:** FinMem, FinAgent, TradingAgents ([arXiv 2412.20138](https://arxiv.org/pdf/2412.20138)), Trading-R1 ([arXiv 2509.11420](https://arxiv.org/pdf/2509.11420)); surveyed in [Ding et al., 2024](https://arxiv.org/pdf/2408.06361). **(b) News sentiment and returns:** the classical finance literature on media sentiment and lexicon-based measures [Citation Needed: Tetlock 2007; Loughran & McDonald 2011; Garcia 2013], FinBERT [Citation Needed: Araci 2019], and LLM-based return prediction [Citation Needed: Lopez-Lira & Tang 2023]. **(c) Backtest validity:** multiple-testing and overfitting corrections [Citation Needed: Bailey & López de Prado (Deflated Sharpe Ratio); White 2000], and look-ahead/memorization bias specific to LLMs [Citation Needed: Glasserman & Lin 2023]; anonymization-first evaluation ([arXiv 2603.17692](https://arxiv.org/pdf/2603.17692)). **(d) Rationale faithfulness:** evidence that LLM-stated reasoning can misrepresent actual decision drivers [Citation Needed: Turpin et al. 2023]. The theoretical frame is the tension between the Efficient Markets Hypothesis and the Adaptive Markets Hypothesis [Citation Needed: Fama; Lo 2004], under which any sentiment alpha should be regime-dependent and decaying.

The evaluation-study framing follows precedent that independent negative or corrective results are publishable in this area, as demonstrated by [arXiv 2505.07078](https://arxiv.org/pdf/2505.07078) itself.

## 3. Data (two-track design)

**Track A — historical (primary).** [FNSPID](https://github.com/Zdong104/FNSPID_Financial_News_Dataset) ([Dong et al., 2024](https://arxiv.org/abs/2402.06698)): time-aligned news and prices for S&P 500 companies through 2023. Test window: 2022-01 to 2023-12. Because candidate LLMs have likely seen this period in training, Track A includes a **memorization-quantification protocol**: each experiment is repeated with (i) real inputs, (ii) anonymized tickers and entity names, and (iii) date-shuffled controls. The performance gap between (i) and (ii)/(iii) is reported as the memorization effect [method per Glasserman & Lin — Citation Needed; and arXiv 2603.17692].

**Track B — out-of-cutoff validation (secondary).** A 6-month forward window (2026-H1) using prices from Yahoo Finance and news from a free API (GDELT or Finnhub free tier [verify coverage]). Smaller scale; serves as a genuine out-of-sample check on Track A conclusions.

**Universe.** Top 20 S&P 500 constituents by market capitalization as of 2021-12-31, selected by rule, never by outcome. Delistings handled point-in-time [verify FNSPID delisting coverage]. This mega-cap universe is deliberately conservative: prior literature locates sentiment effects mainly in smaller, less-covered stocks [Citation Needed], so any alpha found here is strong evidence, and a null is interpreted accordingly in the Limitations.

## 4. Method

**Strategies (all on identical data and universe).**

| # | Strategy | Purpose |
|---|---|---|
| S1 | Equal-weight buy-and-hold of the universe | Passive benchmark |
| S2 | Momentum (12-1) / MA-crossover | Classical quant baseline |
| S3 | FinBERT daily sentiment → threshold rule | Classical NLP baseline |
| S4 | Gradient-boosted trees on FinBERT sentiment + technical features | Supervised-ML baseline (isolates "any model on same inputs") |
| S5 | LLM daily sentiment score → same threshold rule as S3 | Isolates LLM-as-scorer |
| S6 | Full LLM agent (simplified FinMem-style reference agent: news summary + price history + portfolio state → long/flat decision with stated rationale) | The system under test |

S6 is a disclosed simplification, not a claimed replication of FinMem/FinAgent; conclusions are scoped to this agent class, with the original systems' reported numbers discussed as context.

**Portfolio accounting.** Each strategy makes a daily long/flat decision per ticker. Portfolio return on day *t+1* = equal-weighted mean of returns on long positions; capital in flat positions earns the T-bill rate. Decisions use only information timestamped on or before the close of day *t*; execution occurs at the open of day *t+1*. Transaction costs: 10 bps per side (sensitivity analysis at 5 and 25 bps).

**Pre-specified evaluation.** Primary metric: Deflated Sharpe Ratio of each strategy vs. S1, correcting for the full strategy-and-configuration grid [Citation Needed: Bailey & López de Prado]. Secondary: net cumulative return, max drawdown, turnover, and Fama-French three-factor alpha [Citation Needed: Ken French data library]. Uncertainty: stationary-bootstrap confidence intervals. All runs are reported; no post-hoc strategy or ticker selection. Metrics, window, and universe are frozen in this proposal before any experiment is run.

**Reproducibility.** A pinned open-weight LLM (e.g., a Llama- or Qwen-family model, exact version recorded) run locally with fixed temperature and seeds; every model call cached and released with the code. This removes API model drift and bounds cost near zero.

**Decision-sensitivity and rationale audit (RQ2).** All S6 rationales are logged and classified by driver type (sentiment / momentum / risk). Two pre-specified perturbation tests: (i) *robustness* — neutral paraphrase of news should not change decisions; (ii) *sensitivity* — polarity-flipped news should change decisions in the stated direction, holding non-sentiment content fixed as far as possible (paraphrase-controlled construction; residual content confounds acknowledged). Consistency is measured as agreement between stated driver and observed behavioral change. Regime splits (VIX terciles, bull/bear) are **descriptive only**, given limited per-regime observations.

## 5. Paper Outline (8 pages, ACL format)

1. Introduction — the contradiction in the literature; thesis; contributions (mirroring §1)
2. Related Work — the four literatures of §2
3. Data and Bias Controls — two tracks; memorization protocol
4. Strategies and Evaluation Protocol — S1–S6; pre-specified metrics
5. Results — DSR table, factor alphas, memorization effect, Track B validation
6. Rationale Audit — consistency and sensitivity results; regime description
7. Limitations — mega-cap conservatism; simplified agent; backtest ≠ live; US-only
8. Conclusion

## 6. Venues

1. **arXiv (q-fin.TR + cs.CL)** upon completion — timestamp and feedback.
2. **FinNLP workshop** ([EMNLP 2026 edition](https://thefin.ai/finnlp-2026.html) deadline Aug 11, 2026 is not reachable on this timeline; target the following edition, historically ~6 months later) — ACL Anthology proceedings, appropriate scope and review standard.
3. **[FNP workshop](https://wp.lancs.ac.uk/cfie/fnp2026/)** as alternative; *Journal of Financial Data Science* or *Finance Research Letters* for an extended version.

## 7. Timeline (16 weeks)

| Weeks | Milestone |
|---|---|
| 1–2 | Close reading of core papers; freeze protocol (this document, §4) |
| 3–5 | Data pipeline (Track A subset; Track B collectors); backtest harness with cost model; validate S1–S2 against known benchmarks |
| 6–7 | S3–S4 baselines |
| 8–10 | S5–S6 with pinned local model; memorization protocol runs |
| 11–12 | Rationale audit experiments |
| 13–15 | Analysis, figures, paper drafting |
| 16 | Internal review; arXiv submission |

## 8. Risks and Mitigations

- **Memorization dominates Track A** → the memorization quantification is itself contribution 2; Track B provides clean validation.
- **Null result on RQ1** → informative under the thesis framing; the paper's identity is evaluation, not system-building.
- **Track B news API coverage is thin** → Track B is scoped as secondary; degrade gracefully to fewer tickers.
- **Scope creep** → protocol frozen at week 2; extensions (mid-caps, more agents) deferred to future work.

---

*This study uses simulated backtesting only; no live trading. Results are research findings, not investment advice.*
