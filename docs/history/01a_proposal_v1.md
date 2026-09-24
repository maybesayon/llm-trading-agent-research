# Research Proposal

## Do LLM-Based Trading Agents Add Value? Sentiment-Driven Signals, Performance, and Interpretability on US Equities

**Author:** Sayon Upadhyay
**Status:** Proposal draft — July 2026

---

## 1. Research Question

**Primary:** Do LLM-based trading agents that consume news/social sentiment outperform simple baselines (buy-and-hold, momentum, classic sentiment models) on US equities after controlling for transaction costs and evaluation biases?

**Secondary:**
1. Which input matters more — the LLM's reasoning or the raw sentiment signal? (ablation)
2. Are the agent's stated reasons consistent with its actions? (interpretability/faithfulness)
3. Under what market regimes (bull/bear/high-volatility) does the agent fail?

**Why this is publishable:** Recent work shows contradictory results — FinAgent/FinMem report market-beating backtests, but bias-controlled re-evaluations ([Can LLM-based Financial Investing Strategies Outperform the Market in Long Run?](https://arxiv.org/pdf/2505.07078)) find the market baseline wins once look-ahead and selection biases are removed. A careful, honest replication + interpretability study directly addresses this open dispute. Negative results are publishable here.

## 2. Related Work (starting reading list)

| Paper | Role in your paper |
|---|---|
| [FinMem (2023)](https://arxiv.org/pdf/2311.13743) | Baseline agent #1 — layered memory design |
| [FinAgent (KDD 2024)](https://personal.ntu.edu.sg/boan/papers/KDD24_FinAgent.pdf) | Baseline agent #2 — multimodal, best reported results |
| [TradingAgents (2024)](https://arxiv.org/pdf/2412.20138) | Multi-agent role framework (analyst/risk roles) |
| [LLM Agents in Financial Trading: A Survey (2024)](https://arxiv.org/pdf/2408.06361) | Structure your related-work section |
| [Can LLM Strategies Outperform the Market? (2025)](https://arxiv.org/pdf/2505.07078) | The skeptical result you're testing |
| [Trading-R1 (2025)](https://arxiv.org/pdf/2509.11420) | Recent RL-tuned comparison point |
| [FNSPID dataset (2024)](https://arxiv.org/abs/2402.06698) | Primary data source |

Also skim the curated list: [Awesome-LLM-Quantitative-Trading-Papers](https://github.com/Tom-roujiang/Awesome-LLM-Quantitative-Trading-Papers).

## 3. Data (all free)

- **News + prices:** [FNSPID](https://github.com/Zdong104/FNSPID_Financial_News_Dataset) — 15.7M news articles time-aligned with prices for 4,775 S&P 500 companies, 1999–2023.
- **Prices (extension to 2024–2026):** `yfinance` (Yahoo Finance API).
- **Stock universe:** pick 10–20 large-cap tickers *by rule* (e.g., top-20 S&P 500 by market cap as of study start) — never hand-picked, to avoid selection bias.
- **Test period:** must be after the LLM's training cutoff to avoid memorization (e.g., use a 2025–2026 window with a model whose cutoff predates it, or explicitly test the memorization effect — that itself is a contribution).

## 4. Method

**Agents to compare:**

1. Buy-and-hold (market baseline — this is the one to beat)
2. Momentum / moving-average crossover (classic quant baseline)
3. FinBERT sentiment → threshold rule (classic NLP baseline)
4. LLM sentiment scoring → same threshold rule (isolates the LLM-as-scorer effect)
5. Full LLM agent: daily loop of {news summary + price history + portfolio state} → reasoned trade decision (buy/hold/sell) with stated rationale

**Evaluation:**

- Metrics: cumulative return, Sharpe ratio, max drawdown, turnover — all **net of transaction costs** (e.g., 10 bps per trade)
- Bias controls: no look-ahead (decisions use only data timestamped before decision time), rule-based ticker selection, multiple seeds/runs, report all tickers not cherry-picked winners
- Statistical tests: bootstrap confidence intervals on Sharpe differences

**Interpretability analysis (your differentiator):**

- Log every rationale the agent produces; classify rationales by type (sentiment-driven, momentum-driven, risk-driven)
- Faithfulness test: perturb the news input (neutral paraphrase, flipped sentiment) and measure whether decisions change consistently with stated reasons
- Regime analysis: split results by VIX tercile and bull/bear periods

**Estimated cost:** ~$50–200 in LLM API calls (GPT-4-class or open-weight Llama/Qwen locally for $0), one laptop, Python + `pandas`/`backtrader`.

## 5. Paper Outline (8 pages, ACL/FinNLP format)

1. **Introduction** — the dispute: agent papers claim alpha, re-evaluations disagree
2. **Related Work** — LLM trading agents; sentiment-based forecasting; backtest pitfalls
3. **Data & Experimental Setup** — FNSPID + yfinance; bias controls
4. **Agents & Baselines** — the 5 strategies above
5. **Results** — performance table; ablations (LLM-scorer vs full agent)
6. **Interpretability Analysis** — rationale faithfulness; regime failures
7. **Limitations** — backtest ≠ live trading; single-market; model-version sensitivity
8. **Conclusion**

## 6. Target Venues (in order)

1. **arXiv (q-fin.TR / cs.CL)** — post first for timestamp and feedback; no review barrier
2. **[FinNLP workshop @ EMNLP 2026](https://thefin.ai/finnlp-2026.html)** — direct submission deadline **Aug 11, 2026** (tight; a 4-page short paper might be feasible), otherwise the next edition (~Jan 2027, typically co-located with another *CL conference). Proceedings in ACL Anthology — real publication, student-friendly review
3. **[FNP workshop](https://wp.lancs.ac.uk/cfie/fnp2026/)** — alternative financial-NLP venue
4. Journals if extended: *Journal of Financial Data Science*, *Finance Research Letters*

## 7. Timeline (~14 weeks)

| Weeks | Milestone |
|---|---|
| 1–2 | Read the 7 core papers; finalize research question |
| 3–4 | Data pipeline: FNSPID subset + yfinance; backtest harness with cost model |
| 5–6 | Implement baselines 1–3; validate harness on known results |
| 7–9 | Implement LLM scorer + full agent; run experiments |
| 10–11 | Interpretability experiments (perturbations, regime splits) |
| 12–13 | Write paper; make figures |
| 14 | Internal review (advisor/peers), arXiv submission |

## 8. Risks & Mitigations

- **LLM memorization of test period** → use post-cutoff data or quantify the effect explicitly
- **Negative result (agent doesn't beat market)** → still publishable; frame as rigorous evaluation study
- **API cost creep** → use open-weight models locally; cache all LLM calls
- **Scope creep** → freeze the 5-strategy design; extensions go in "future work"

---

*Note: this study involves simulated backtesting only — no real-money trading. Backtest results are not investment advice or predictions.*
