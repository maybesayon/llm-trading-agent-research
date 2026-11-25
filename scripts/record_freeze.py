#!/usr/bin/env python3
"""Record the model-instrument freeze values into protocol.lock.yaml (D.1).
RUN AFTER THE MODEL DOWNLOAD. Adds a `model:` line under `recorded:` and
removes the resolved `freeze_status.pending` entries; every other line of
the lock (frozen rules, comments, amendments) is left byte-for-byte intact.

Usage:
  python scripts/record_freeze.py --model-revision <hf_commit_hash> \
      --model-date YYYY-MM-DD --vllm-version x.y.z
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.hashing import hash_obj  # noqa: E402

RESOLVED = ("model.revision", "model.downloaded_date", "inference.framework_version")


def record(text: str, revision: str, date: str, vllm: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("--model-revision must be a 40-character commit hash")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        sys.exit("--model-date must be YYYY-MM-DD")
    lines = text.splitlines(keepends=True)
    try:
        start = next(i for i, ln in enumerate(lines) if ln.rstrip() == "recorded:")
    except StopIteration:
        sys.exit("protocol.lock.yaml has no `recorded:` block")
    if any(ln.startswith("  model:") for ln in lines[start:]):
        sys.exit("model values already recorded; the lock is append-only")
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].strip() and not lines[i].startswith((" ", "#"))), len(lines))
    while lines[end - 1].strip() == "":
        end -= 1
    entry = f"  model: {{ revision: {revision}, downloaded_date: \"{date}\", vllm_version: \"{vllm}\" }}\n"
    lines.insert(end, entry)
    lines = [ln for ln in lines if not (ln.lstrip().startswith("- ") and any(m in ln for m in RESOLVED))]
    return "".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-revision", required=True)
    ap.add_argument("--model-date", required=True)
    ap.add_argument("--vllm-version", required=True)
    args = ap.parse_args()

    lock_path = ROOT / "protocol.lock.yaml"
    new = record(lock_path.read_text(), args.model_revision, args.model_date, args.vllm_version)
    lock = yaml.safe_load(new)  # must still parse before anything is written
    lock_path.write_text(new)
    print("Recorded. Remaining pending items:")
    for p in lock["freeze_status"]["pending"]:
        print(f"  - {p}")
    print(f"Lock hash: {hash_obj(lock)[:16]} (final only when pending list is empty)")


if __name__ == "__main__":
    main()
