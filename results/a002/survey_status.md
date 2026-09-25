# A-002 news-source survey — status (2026-09-25)

Rule: `docs/amendments/A-002_source_selection_rule.md` (committed before
measurement). Availability only; no returns, sentiment or strategy output.

| Candidate | Tickers passing M1/M2 over Track A | Precision (100-article sample) | Status |
|---|---|---|---|
| FNSPID alone (baseline) | 6/20 | — | measured |
| C1 FNSPID headline mentions | 12/20 (fail: UNH JNJ HD PG BAC MA PFE AVGO) | not labelled | measured |
| C2 GDELT GKG organizations | 18/20 (fail: JNJ, PG) | proposed 0.11 (Claude), awaiting author confirmation | measured |
| C3 Alpha Vantage | — | — | awaiting API key |
| C4 Polygon | — | — | awaiting API key |

## Notes
- **C2 build:** 726 Track A days, 69,696 GKG batches (259 missing on the
  GDELT server), 5,364,255 firm-matched rows; 2,346,116 (44%) are META via the
  "facebook" organization.
- **C2 precision:** most sampled rows name the firm only incidentally (e.g.
  social-media links on unrelated local news). Claude's proposed labels: 11/100
  about the firm (0.15 if all four borderline rows count). Below the 0.90
  eligibility bar either way, pending the author's confirmation.
- **C2 JNJ/PG = 0:** GKG writes organization names without "&"
  ("johnson johnson", "procter gamble"), so the fixed aliases cannot match.
  A matching artifact, not absence of coverage; aliases were not changed after
  measurement (rule). Moot if C2 is ineligible on precision.
- **C1 precision** only matters if C1 ends as the best eligible candidate; at
  12/20 (8 failing > 5) that outcome is the pre-registered halt either way.
- Found during the survey and fixed in the pipeline: mixed timestamp formats
  silently became NaT (`d9e697d`); cross-source duplicates are now compared as
  instants. Baseline and C1 results re-measured unchanged.
