# 2. Related Work

This study sits at the intersection of four literatures: LLM trading agents, news sentiment and asset returns, backtest validity, and the faithfulness of model-generated explanations. We review each in turn and identify the gap at their intersection.

## 2.1 LLM Trading Agents

Architectures in this area fall into three broad families. Memory- and reflection-driven single agents equip an LLM with structured storage and self-evaluation: FinMem combines a profiling module, layered memory, and a decision module aligned with the cognitive structure of human traders, and reports leading backtest performance against algorithmic baselines (Yu et al., 2023); FinAgent extends this design with multimodal inputs and dual-level reflection, reporting an average profit improvement of over 36% against twelve baselines across six datasets (Zhang et al., 2024). Multi-agent frameworks distribute reasoning across specialized roles: TradingAgents simulates a trading firm with fundamental, sentiment, and technical analysts, bull and bear researchers who debate market conditions, and a risk-management team, reporting improvements in cumulative return, Sharpe ratio, and maximum drawdown (Xiao et al., 2024). A third family fine-tunes the model itself: Trading-R1 aligns LLM reasoning with trading principles through supervised fine-tuning and a staged reinforcement-learning curriculum, reporting improved risk-adjusted returns on six equities and exchange-traded funds (Xiao et al., 2025). Across the field, however, the evaluation regime is thin: surveyed studies rely on generally short backtesting windows, are largely confined to US and Chinese equity markets, and rarely incorporate trading costs (Ding et al., 2024). When Li et al. (2025) re-evaluated LLM strategies over two decades and more than one hundred symbols within a unified framework, previously reported advantages deteriorated significantly, with strategies proving overly conservative in bull markets and overly aggressive in bear markets.

## 2.2 News Sentiment and Asset Returns

The proposition that textual sentiment carries return-relevant information predates LLMs by two decades. Tetlock (2007) showed that high media pessimism in a daily Wall Street Journal column predicts downward pressure on prices followed by reversion to fundamentals. Loughran and McDonald (2011) demonstrated that general-purpose sentiment dictionaries systematically misclassify financial text and constructed finance-specific word lists that became widely used for lexicon-based measurement. García (2013) found that the predictive content of news sentiment for daily returns is concentrated in recessions, establishing that sentiment effects are regime-dependent — a finding that directly motivates the regime analysis in the present study. Measurement technology has since advanced from lexicons to pretrained transformers, with FinBERT improving the state of the art on financial sentiment benchmarks (Araci, 2019), and most recently to general-purpose LLMs: Lopez-Lira and Tang (2023) showed that sentiment scores assigned by ChatGPT to news headlines predict subsequent daily stock returns. This progression supplies both the classical-NLP and LLM-scorer baselines in our strategy ladder, and its regime-dependence finding shapes our secondary research question.

## 2.3 Backtest Validity and LLM Memorization

A parallel literature documents why reported backtest performance so often fails to generalize. When many strategy configurations are evaluated and the best is reported, conventional performance statistics overstate skill; Bailey and López de Prado (2014) formalize the correction with the deflated Sharpe ratio, which adjusts for selection bias, backtest overfitting, and non-normality of returns. LLMs introduce an additional contamination channel absent from classical strategies. Glasserman and Lin (2023) distinguish two effects when a model's training corpus overlaps the backtest period: look-ahead bias, in which the model may possess direct knowledge of returns that followed a news article, and a distraction effect, in which background knowledge about the company interferes with the sentiment-measurement task itself; using an anonymization procedure to separate the two, they find the distraction effect to be the larger. Building on this logic, Jeon and Lee (2026) propose an anonymization-first evaluation framework in which tickers and company names are masked before LLM agents make portfolio decisions, addressing memorization bias from pre-training alongside survivorship bias in backtest construction. Our memorization-quantification protocol adapts these procedures, and our pre-specified statistical protocol applies the deflated Sharpe ratio that this literature prescribes but that developer-reported evaluations have not adopted.

## 2.4 Faithfulness of Model-Generated Explanations

Trading agents present natural-language rationales as an interpretability benefit of the paradigm (Yu et al., 2023). Whether such rationales can be trusted is a separate empirical question. Turpin et al. (2023) demonstrate that chain-of-thought explanations can systematically misrepresent the true basis of a model's prediction: when biasing features are introduced into inputs, models change their answers while producing plausible explanations that never mention the manipulation. This result implies that the stated rationale of a trading agent — for example, that a position was taken on the basis of news sentiment — cannot be assumed to reflect the actual driver of the decision. To our knowledge, no prior work has tested rationale–behavior consistency for trading agents by perturbing their inputs and observing whether decisions change in the manner the rationales imply; this is the audit our second research question supplies.

## 2.5 Synthesis

Classical finance theory frames what is at stake. Under the efficient markets hypothesis, publicly available news should be impounded into prices too quickly for a daily sentiment strategy to profit net of costs (Fama, 1970); the adaptive markets hypothesis instead predicts that profitability of any such strategy will vary with market conditions as competition and arbitrage evolve (Lo, 2004) — consistent with the regime-dependence documented by García (2013) and the bull/bear asymmetry found by Li et al. (2025). Each literature reviewed above supplies one ingredient of a credible adjudication: candidate systems (§2.1), validated signal sources and baselines (§2.2), bias controls and corrected statistics (§2.3), and constructs for auditing explanations (§2.4). No existing study combines them: developer evaluations lack the controls, the corrective re-evaluation of Li et al. (2025) applies neither memorization quantification nor a supervised-ML baseline on an identical information set, and the faithfulness literature has not reached trading. The present study occupies this intersection.

---

## References (Section 2 additions)

Araci, D. (2019). *FinBERT: Financial sentiment analysis with pre-trained language models* (arXiv:1908.10063). arXiv. https://doi.org/10.48550/arXiv.1908.10063

Fama, E. F. (1970). Efficient capital markets: A review of theory and empirical work. *The Journal of Finance, 25*(2), 383–417. https://doi.org/10.1111/j.1540-6261.1970.tb00518.x

García, D. (2013). Sentiment during recessions. *The Journal of Finance, 68*(3), 1267–1300. https://doi.org/10.1111/jofi.12027

Jeon, J., & Lee, H. (2026). *Can blindfolded LLMs still trade? An anonymization-first framework for portfolio optimization* (arXiv:2603.17692). arXiv. https://doi.org/10.48550/arXiv.2603.17692

Lo, A. W. (2004). The adaptive markets hypothesis: Market efficiency from an evolutionary perspective. *The Journal of Portfolio Management, 30*(5), 15–29.

Loughran, T., & McDonald, B. (2011). When is a liability not a liability? Textual analysis, dictionaries, and 10-Ks. *The Journal of Finance, 66*(1), 35–65.

Tetlock, P. C. (2007). Giving content to investor sentiment: The role of media in the stock market. *The Journal of Finance, 62*(3), 1139–1168. https://doi.org/10.1111/j.1540-6261.2007.01232.x

Xiao, Y., Sun, E., Chen, T., Wu, F., Luo, D., & Wang, W. (2025). *Trading-R1: Financial trading with LLM reasoning via reinforcement learning* (arXiv:2509.11420). arXiv. https://doi.org/10.48550/arXiv.2509.11420

*(Previously listed in Section 1: Bailey & López de Prado, 2014; Ding et al., 2024; Glasserman & Lin, 2023; Li et al., 2025; Lopez-Lira & Tang, 2023; Turpin et al., 2023; Xiao et al., 2024; Yu et al., 2023; Zhang et al., 2024.)*
