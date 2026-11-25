# A-002 — News-source augmentation: selection rule (fixed before the survey)

Status: RULE FIXED 2026-09-24, approved by the author. The survey it governs
has not started. When it concludes, A-002 is appended to
`protocol.lock.yaml → freeze_status.amendments` and the manuscript Amendment
Log, citing the commit that introduced this file.

## Trigger (data cause; not outcome-triggered)
Pilot of 2026-09-24 (`results/pilot/`): 14/20 universe tickers fail the frozen
news-density criterion (§3.5: M1 ≥ 0.90, M2 ≥ 0.95, 3-day trailing window) on
the pilot sub-window. More than five failures means Track A's news source is
inadequate and requires "a documented protocol amendment (source augmentation
or halt) before any strategy is run". Cause: FNSPID's ticker-tagged Nasdaq
coverage starts at staggered dates and is absent in 2022–23 for ten firms
(`results/pilot/pilot_notes.md`). No strategy has been evaluated.

## Candidates (fixed; none added or removed after measurement starts)
- **C1 — FNSPID headline mentions.** FNSPID articles (either news file, any
  `Stock_symbol`) whose `Article_title` names the firm, matched
  case-insensitively on word boundaries against the alias list below.
- **C2 — GDELT 2.0 GKG.** Articles whose organizations field contains a firm
  alias; date = GKG publication date.
- **C3 — Alpha Vantage `NEWS_SENTIMENT`.** Articles listing the firm's ticker
  in `ticker_sentiment` (any relevance score).
- **C4 — Polygon ticker news** (`/v2/reference/news?ticker=`). Articles
  returned for the ticker.

Aliases (C1, C2): AAPL Apple · MSFT Microsoft · GOOGL Alphabet, Google ·
AMZN Amazon · TSLA Tesla · META Meta Platforms, Meta, Facebook · NVDA Nvidia ·
BRK-B Berkshire · UNH UnitedHealth · V Visa · JPM JPMorgan, JP Morgan,
J.P. Morgan · JNJ Johnson & Johnson, J&J · HD Home Depot · WMT Walmart ·
PG Procter & Gamble, P&G · BAC Bank of America, BofA · MA Mastercard ·
PFE Pfizer · DIS Disney · AVGO Broadcom.

## Measurement
For each candidate: corpus = FNSPID subset ∪ candidate, exact
(date, ticker, headline) duplicates removed. Compute M1 and M2 per ticker
over the full Track A window (2022-01-03..2023-12-29) with
`src.preprocessing.alignment.density_report`, frozen thresholds, date-only
convention (§3.2). The FNSPID-only baseline is computed the same way.

Only availability is measured. No returns, sentiment scores, signals, or
strategy outputs are computed or inspected during the survey.

## Eligibility
- **Precision:** 100 candidate-contributed articles drawn at random
  (seed 2026, across all firms) are labelled "about the firm: yes/no" from
  headline and URL. Claude may propose labels; the author confirms each.
  Precision < 0.90 → ineligible.
- **Feasibility:** a candidate that cannot deliver 2022–23 data within the
  existing D.5 budget is recorded as infeasible and scores as FNSPID-only.
  Any paid access needs the author's approval before purchase.

## Choice rule
1. Most tickers passing M1 and M2 over Track A (FNSPID ∪ candidate).
2. Ties: licence permits releasing cached article metadata; then lower cost.
3. The chosen source augments **all 20 firms** over calibration and Track A
   (2019–2023), so calibration and evaluation share one information set.
4. If the best eligible candidate still leaves more than five tickers
   failing, Track A halts as pre-registered (§3.5). Otherwise tickers still
   failing (≤ 5) are excluded from the primary analysis and reported (§3.5).

## Disclosure
Before this rule was written, a diagnostic scan checking the FNSPID extraction
counted 2022–23 headline mentions of twelve missing-firm names in FNSPID
(e.g. "jpmorgan" 2,065). That touched C1's data. No M1/M2 was computed for
any candidate, and no other candidate source has been queried.
