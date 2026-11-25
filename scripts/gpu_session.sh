#!/usr/bin/env bash
# One-shot GPU session for the model-instrument freeze items (runbook steps 4, 6, 7).
# Run on a rented Linux GPU with >= 48 GB VRAM (bf16 Qwen3-14B, no quantization).
#
# Before running, copy the two local data files into the clone on the GPU box:
#   scp data/raw/prices_track_a.csv data/raw/fnspid_news_subset.csv <gpu-host>:llm-trading-agent-research/data/raw/
#
# It: pins the model revision, serves it with vLLM, runs the pilot with the LLM
# smoke test (per-call latency), and records revision/date/vLLM version in
# protocol.lock.yaml. Copy back results/pilot/ and protocol.lock.yaml afterwards.
set -euo pipefail

MODEL="Qwen/Qwen3-14B"
PORT=8000
# vLLM applies the model's generation_config.json defaults (e.g. top_k) unless
# told otherwise. A-001 fixes temperature 0.7 and top_p 0.8 only; which default
# governs the rest is an open instrument question for the author. "auto" keeps
# vLLM's default behaviour; "vllm" ignores the model's generation_config.
GEN_CONFIG="${GEN_CONFIG:-auto}"

cd "$(dirname "$0")/.."
for f in data/raw/prices_track_a.csv data/raw/fnspid_news_subset.csv; do
  [ -f "$f" ] || { echo "missing $f (copy it from your Mac first)"; exit 1; }
done
nvidia-smi --query-gpu=name,memory.total --format=csv

python3 -m venv .venv && . .venv/bin/activate
pip install -q -r requirements.txt vllm
VLLM_VERSION=$(python -c "import vllm; print(vllm.__version__)")

REV=$(python -c "from huggingface_hub import HfApi; print(HfApi().model_info('$MODEL').sha)")
python -c "from huggingface_hub import snapshot_download; snapshot_download('$MODEL', revision='$REV')"
DATE=$(date -u +%Y-%m-%d)
echo "model $MODEL @ $REV (downloaded $DATE), vLLM $VLLM_VERSION, generation-config $GEN_CONFIG" | tee results/gpu_session.txt

vllm serve "$MODEL" --revision "$REV" --dtype bfloat16 --port "$PORT" \
    --generation-config "$GEN_CONFIG" > results/vllm_server.log 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null || true' EXIT
until curl -sf "localhost:$PORT/v1/models" >/dev/null; do
  kill -0 $SERVER 2>/dev/null || { echo "vLLM exited; see results/vllm_server.log"; exit 1; }
  sleep 10
done

python scripts/run_pilot.py --vllm-url "http://localhost:$PORT" | tee -a results/gpu_session.txt
python scripts/record_freeze.py --model-revision "$REV" --model-date "$DATE" --vllm-version "$VLLM_VERSION"

echo "Done. Copy back: results/pilot/ results/gpu_session.txt results/vllm_server.log protocol.lock.yaml"
