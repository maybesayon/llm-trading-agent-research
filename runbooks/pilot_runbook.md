# Phase 3 Pilot Runbook — actions required on YOUR machine

Everything below involves downloads, APIs, or GPU inference and therefore
cannot run in the assistant's sandbox. Do the steps in order; nothing here
requires judgment calls that would touch the frozen protocol.

## 0. Environment
```
python 3.10+
pip install pandas pyyaml pytest lightgbm yfinance huggingface_hub requests transformers
cd research_project && python -m pytest   # must be 83/83 green before continuing
```

## 1. Universe (D.2) — one-time, rule-based
Obtain the 20 largest S&P 500 constituents by market capitalization **as of
2021-12-31** (any reputable point-in-time source; save the source URL/screenshot
into `data/raw/universe_source.txt`). Enter the 20 tickers into
`configs/data.yaml -> universe.tickers`. Do not deviate from the rule.

## 2. FNSPID news subset (D.2)
```
# the data lives at Zihan1004/FNSPID (the GitHub repo only links to it)
huggingface-cli download Zihan1004/FNSPID --repo-type dataset \
    --revision bf9189c41527198897d1af3e17b1a0095279fc45 --include "Stock_news/*" \
    --local-dir data/raw/fnspid
python scripts/build_fnspid_subset.py   # checks sha256s recorded in configs/data.yaml
```
- Record the dataset commit hash.
- Extract news for your 20 tickers, 2019-01-01..2023-12-31, into
  `data/raw/fnspid_news_subset.csv` (the script does this, verifying sha256).
- Confirm the real column names; if they differ from
  `configs/data.yaml -> sources.fnspid.news_column_map`, update the MAP
  (that is a data-integrity configuration, not a protocol change).

## 3. Prices (D.2)
```
python - <<'EOF'
import sys; sys.path.insert(0, '.')
from src.data_ingestion.prices import YFinancePriceSource
import yaml
cfg = yaml.safe_load(open('configs/data.yaml'))
df = YFinancePriceSource().fetch(cfg['universe']['tickers'], '2019-01-02', '2023-12-30')  # end is exclusive
df.to_csv('data/raw/prices_track_a.csv', index=False)
print(len(df), 'rows;', YFinancePriceSource().metadata())
EOF
```
Then cross-check against a second source (Stooq now blocks automated
downloads; Tiingo was fixed at pilot, key in TIINGO_API_KEY):
```
python scripts/crosscheck_prices.py --source tiingo   # independent vendor
python scripts/crosscheck_prices.py --source fnspid   # Yahoo vintage check
```
and note the source in `configs/data.yaml -> sources.prices_crosscheck`.

## 4. Model instrument (D.1) — the critical freeze item
Hardware: bf16 Qwen3-14B needs ~30+ GB VRAM (A100-40GB class; rentable). Then:
```
pip install vllm
vllm serve Qwen/Qwen3-14B          # note the resolved revision in the logs
# revision also via: huggingface-cli scan-cache | grep Qwen3-14B
```
Record: revision hash, download date, vLLM version.
(If only smaller hardware is available: STOP and tell me — the Q8 fallback
is an instrument amendment that must be logged before any run.)

## 5. FinBERT (S3 scorer)
```
python -c "from transformers import pipeline; p=pipeline('text-classification', model='ProsusAI/finbert'); print(p.model.config._commit_hash if hasattr(p.model.config,'_commit_hash') else 'see ~/.cache/huggingface')"
```
Record the revision.

## 6. Record freeze values
```
python scripts/record_freeze.py --model-revision <hash> --model-date YYYY-MM-DD \
    --vllm-version <x.y.z>
```
(Universe, FNSPID commit and cross-check source were recorded at the pilot,
under `recorded:` in protocol.lock.yaml.)

## 7. Run the pilot
```
python scripts/run_pilot.py                # with vLLM running
# or: python scripts/run_pilot.py --skip-llm   (data-side checks only, first pass)
```
Output: `results/pilot/pipeline_validation_report.md` + `density_report.csv`.

## 8. Send back to the assistant
- `pipeline_validation_report.md`
- `density_report.csv`
- the recorded revisions/commits (or updated `protocol.lock.yaml`)
- observed per-call latency and your GPU $/hour, for the D.5 budget math

Phase 3 assessment, any justified amendments, and the Phase 4 full-run
scripts follow from that report. **No full experiment before the report is
reviewed and every pending freeze item has a value.**

## Track B note (not needed for the pilot)
Finnhub requires a free API key (finnhub.io). Collect keys now if convenient;
Track B collection scripts arrive with Phase 4.
