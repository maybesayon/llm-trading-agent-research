# 4. Strategies and Evaluation Protocol

Where Section 3 established that the data can be trusted, this section establishes that the comparison is fair. The design principle is that all strategies operate under identical conditions — the same universe, window, information set, execution rules, cost assumptions, and portfolio constraints — so that observed performance differences are attributable to the decision rule and to nothing else. All statements in this section describe procedures to be executed; no empirical outcome is asserted.

## 4.1 Strategy Definitions

The six strategies form a graded ladder in which each adjacent pair differs, as far as practicable, in a single ingredient. This structure is the study's central inferential device: rather than asking only whether the most complex system outperforms the simplest benchmark, it asks *where along the ladder* any added value enters — with the price signal, the text signal, the learning algorithm, the language model, or the agent architecture. Strategies S1–S4 are baselines, S5 is an ablation variant, and S6 is the system under test. No ordering of expected performance is implied.

**S1 — Equal-weight buy-and-hold (passive benchmark).** All twenty universe stocks are bought in equal weights at the start of the window and held. S1 answers the question every active strategy must face: does the decision rule add anything over doing nothing?

**S2 — Time-series momentum (classical price baseline).** A stock is held long when its trailing twelve-month return, excluding the most recent month, is positive, and moved to cash otherwise, with signals refreshed monthly. The specification follows the momentum evidence of Jegadeesh and Titman (1993), including its conventional monthly signal frequency; the resulting difference in rebalancing frequency relative to the daily strategies is a property of the strategy itself, is charged costs under the identical per-trade model, and is made visible through the turnover metric (§4.3). S2 asks whether a decades-old price-only anomaly explains any advantage attributed to more elaborate systems.

**S3 — FinBERT sentiment rule (classical NLP baseline).** Each trading day, all universe-relevant articles are scored by FinBERT (Araci, 2019), averaged per ticker, and a stock is held long the following session if its trailing sentiment exceeds a threshold calibrated on pre-window data only. S3 asks whether pre-LLM sentiment technology suffices to capture the text signal.

**S4 — Gradient-boosted trees (supervised-ML baseline).** A gradient-boosted tree classifier is trained — on data strictly preceding the evaluation window — to predict next-day direction from the same FinBERT sentiment features plus standard technical features (lagged returns, moving-average ratios, realized volatility, volume). Its predictions map to the same long/flat action space. S4 is the ladder's critical control: without it, any advantage of S5 or S6 over S3 could not be attributed to the language model rather than to statistical learning in general.

**S5 — LLM sentiment scorer (ablation variant).** The pinned open-weight LLM (§4.7) assigns each ticker-day a sentiment score from the same news inputs, and the score feeds a threshold rule calibrated by the identical procedure as S3 — on pre-window data only — since the two scorers' output scales differ and sharing a numeric threshold would not yield a fair comparison. The S3–S5 pair isolates measurement technology (transformer classifier versus generative LLM); the S5–S6 pair isolates agency (scoring versus autonomous decision-making).

**S6 — LLM reference agent (system under test).** Each trading day, per ticker, the same LLM receives a prompt containing recent news summaries, a price-history window, and the current position, and outputs a long/flat decision together with a natural-language rationale, which is logged for the audit of Section 6. S6 is a deliberately simplified single-agent design in the style of FinMem (Yu et al., 2023): it omits fine-tuning, multimodal inputs, and multi-agent debate. Conclusions therefore attach to this reference class, not to any named published system; published systems' reported results are discussed as context in Section 5.

## 4.2 Experimental Controls

The following are held constant across all six strategies: the universe and its selection rule (§3.1); the evaluation window; the news corpus and the information-set rule (§3.2); the long/flat action space with no shorting and no leverage; equal-weight position sizing; execution at the next session's open; the transaction-cost model (§4.3); the treatment of uninvested capital, which earns the risk-free rate, proxied by the three-month US Treasury bill rate from the FRED database (Federal Reserve Bank of St. Louis, n.d.; exact series identifier recorded at protocol freeze); and the contamination conditions of §3.4, which apply to the LLM-based strategies. Strategies differ only in the mapping from the shared information set to the daily action vector.

## 4.3 Portfolio Accounting, Execution, and Transaction Costs

Daily portfolio return is defined by a single accounting identity applied to every strategy: the equal-weighted mean of open-to-open returns over stocks held long, plus the risk-free return on the cash weight, minus transaction costs incurred by that day's position changes. Turnover is the sum of absolute weight changes at each rebalancing, reported annualized. Costs are modeled as a proportional charge of 10 basis points per side, intended to cover commissions, half-spread, and slippage jointly; because any single number is contestable, all headline analyses are repeated at 5 and 25 basis points and reported in full. Market impact is assumed negligible, an assumption we consider defensible only because the universe consists of the most liquid US equities and the notional portfolio is assumed small relative to their daily volume; this assumption is restated as a limitation in Section 8. No commission-free execution is assumed to justify a zero-cost setting, since spread and slippage costs exist regardless of commission structure.

## 4.4 Evaluation Metrics

We report, for each strategy and condition: **cumulative return** and **annualized return**, the quantities most prior work emphasizes, included for comparability; **annualized volatility**, without which return figures are uninterpretable; the **Sharpe ratio** (Sharpe, 1966), which provides a risk-adjusted performance measure, subject to the limitations that it treats upside and downside variability symmetrically and that it overstates skill when many configurations are trialed — the latter being the reason it is not our primary endpoint; **maximum drawdown** and **downside deviation** (the standard deviation of negative daily returns), which capture the asymmetric loss experience that volatility alone misses and which prior work identifies as a specific weakness of LLM strategies in bear markets (Li et al., 2025); and a **factor-adjusted alpha** from a Fama–French three-factor regression (Fama & French, 1993), using factor data from the Kenneth French data library (French, n.d.), because a strategy can appear to add value while merely loading on known risk factors, and outperformance claims should survive that adjustment. Benchmark comparisons are made against S1 and against the S&P 500 total-return index (data source recorded at protocol freeze); outperformance will be assessed relative to these benchmarks, not asserted in advance. S1 answers whether a strategy beats passive holding of the identical universe under identical assumptions — the strictest like-for-like comparison — while the index comparison contextualizes results against the broad-market alternative an investor actually faces; using both avoids the unfair advantage of comparing a twenty-stock strategy only against a benchmark it does not track.

## 4.5 Statistical Protocol and Precision Statement

The primary endpoint is the **deflated Sharpe ratio** (DSR) of each active strategy relative to S1 (Bailey & López de Prado, 2014), computed with the number of trials set to the count of all strategy–cost–condition combinations actually executed under the pre-specified grid (six strategies at three cost settings, with the three contamination conditions of §3.4 applied to the LLM-based strategies), so that the correction reflects everything run, not only what is highlighted. Uncertainty for Sharpe-ratio differences is quantified with stationary-bootstrap confidence intervals (Politis & Romano, 1994), chosen over the i.i.d. bootstrap because daily returns exhibit serial dependence that resampling must preserve. All runs in the grid are reported; no ticker, window, or configuration is dropped after results are seen.

We state the study's precision limits in advance. With twenty assets over a two-year primary window, statistical power against modest performance differences is limited: confidence intervals are expected to be wide, and the absence of a statistically significant difference will be interpreted as the absence of evidence, not as evidence of equivalence. All point estimates are reported with uncertainty, and no claim of outperformance or underperformance will be made from point estimates alone.

## 4.6 Regime Analysis

Because the sentiment literature finds predictive content concentrated in particular market conditions (García, 2013), and the adaptive markets hypothesis predicts time-varying strategy profitability (Lo, 2004), performance is additionally reported within market regimes. Regimes are defined by rules fixed before any experiment: (i) *bear* versus *non-bear* months, where a month is bear if the S&P 500 closes that month more than 20% below its prior running peak, and (ii) volatility terciles of the evaluation window based on the Cboe VIX index level (Cboe Global Markets, n.d.), with the in-window construction of terciles acknowledged as a descriptive convenience. The regime analysis is exploratory and descriptive: per-regime observation counts are too small to support hypothesis testing, no per-regime significance claims will be made, and regime definitions will not be revised after results are seen. Its role is to characterize *when* strategies succeed or fail, generating hypotheses for confirmatory testing in future work rather than testing them here.

## 4.7 Reproducibility

All LLM-based strategies use a single pinned open-weight model, run locally, with the exact model identifier, weights revision, quantization, and inference parameters recorded in the frozen protocol; the model is selected and fixed before experiments begin. Decoding uses temperature zero where supported; because inference may remain non-deterministic, each LLM-based configuration is run with three fixed seeds and the across-seed dispersion is reported. Every model call — prompt, parameters, and output — is cached and released, allowing exact reconstruction of all LLM decisions without re-running inference. Experiments are driven by version-controlled configuration files; each run logs its configuration hash, data version identifiers (§3.5), and outputs to an append-only record. The full protocol, including prompts, thresholds, hyperparameter search spaces for S4, and this evaluation grid, is frozen and archived before the first full-scale experiment, and any post-freeze amendment is documented with its rationale.

---

## References (Section 4 additions)

Cboe Global Markets. (n.d.). *VIX Index*. Retrieved July 9, 2026, from https://www.cboe.com/

Fama, E. F., & French, K. R. (1993). Common risk factors in the returns on stocks and bonds. *Journal of Financial Economics, 33*(1), 3–56.

Federal Reserve Bank of St. Louis. (n.d.). *FRED economic data* [Database]. Retrieved July 9, 2026, from https://fred.stlouisfed.org/

French, K. R. (n.d.). *Data library*. Retrieved July 9, 2026, from https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html

Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers: Implications for stock market efficiency. *The Journal of Finance, 48*(1), 65–91. https://doi.org/10.1111/j.1540-6261.1993.tb04702.x

Politis, D. N., & Romano, J. P. (1994). The stationary bootstrap. *Journal of the American Statistical Association, 89*(428), 1303–1313. https://doi.org/10.1080/01621459.1994.10476870

Sharpe, W. F. (1966). Mutual fund performance. *The Journal of Business, 39*(1), 119–138.

*(Previously listed: Araci, 2019; Bailey & López de Prado, 2014; García, 2013; Li et al., 2025; Lo, 2004; Yu et al., 2023.)*
