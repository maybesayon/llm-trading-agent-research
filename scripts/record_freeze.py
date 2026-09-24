#!/usr/bin/env python3
"""Record download-time freeze values into protocol.lock.yaml (D.1/D.2).
RUN ON YOUR MACHINE after downloads. Appends values; never edits frozen rules.

Usage:
  python scripts/record_freeze.py \
      --model-revision <hf_commit_hash> --model-date 2026-07-XX \
      --fnspid-commit <hash> [--vllm-version x.y.z]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.utils.hashing import hash_obj  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-revision", required=True)
    ap.add_argument("--model-date", required=True)
    ap.add_argument("--fnspid-commit", required=True)
    ap.add_argument("--vllm-version", default=None)
    args = ap.parse_args()

    lock_path = ROOT / "protocol.lock.yaml"
    lock = yaml.safe_load(lock_path.read_text())

    lock["frozen"]["model"]["revision"] = args.model_revision
    lock["frozen"]["model"]["downloaded_date"] = args.model_date
    lock["frozen"]["fnspid_commit"] = args.fnspid_commit
    if args.vllm_version:
        lock["frozen"]["model"]["vllm_version"] = args.vllm_version

    resolved_markers = ("model.revision", "model.downloaded_date",
                        "inference.framework_version", "fnspid.commit")
    lock["freeze_status"]["pending"] = [
        p for p in lock["freeze_status"]["pending"]
        if not any(m in p for m in resolved_markers)
    ]

    lock_path.write_text(yaml.safe_dump(lock, sort_keys=False))
    print("Recorded. Remaining pending items:")
    for p in lock["freeze_status"]["pending"]:
        print(f"  - {p}")
    print(f"Lock hash: {hash_obj(lock)[:16]} (final only when pending list is empty)")


if __name__ == "__main__":
    main()
