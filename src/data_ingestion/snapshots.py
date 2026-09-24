"""Content-hashed dataset snapshots with a JSON manifest (§3.5, D.2)."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

from src.utils.hashing import hash_frame

MANIFEST_NAME = "manifest.json"


def write_snapshot(
    df: pd.DataFrame,
    name: str,
    snapshots_dir: str | Path,
    meta: dict | None = None,
    sort_by: list | None = None,
) -> dict:
    snapshots_dir = Path(snapshots_dir)
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    content_hash = hash_frame(df, sort_by=sort_by)
    fname = f"{name}_{content_hash[:12]}.csv.gz"
    df.to_csv(snapshots_dir / fname, index=False, compression="gzip")

    entry = {
        "name": name,
        "file": fname,
        "rows": int(len(df)),
        "sha256_content": content_hash,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "meta": meta or {},
    }
    manifest_path = snapshots_dir / MANIFEST_NAME
    manifest = (
        json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    )
    manifest.append(entry)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return entry


def load_manifest(snapshots_dir: str | Path) -> list:
    manifest_path = Path(snapshots_dir) / MANIFEST_NAME
    return json.loads(manifest_path.read_text()) if manifest_path.exists() else []


def verify_snapshot(df: pd.DataFrame, entry: dict, sort_by: list | None = None) -> bool:
    """True iff `df` content-hashes to the manifest entry (drift detection)."""
    return hash_frame(df, sort_by=sort_by) == entry["sha256_content"]
