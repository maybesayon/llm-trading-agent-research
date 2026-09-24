"""Deterministic content hashing for dataset snapshots and configs.

Hashes canonical *content*, not files: row order, column order, and index
are normalized before hashing so that re-downloads of identical data
produce identical hashes (no false drift alarms).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


def canonicalize_frame(df: pd.DataFrame, sort_by: list | None = None) -> pd.DataFrame:
    """Return a canonical copy: sorted columns, stable row order, fresh index."""
    out = df.copy()
    out = out[sorted(out.columns)]
    sort_cols = sort_by if sort_by else list(out.columns)
    out = out.sort_values(by=sort_cols, kind="mergesort").reset_index(drop=True)
    return out


def hash_frame(df: pd.DataFrame, sort_by: list | None = None) -> str:
    """SHA-256 of a canonical serialization; invariant to row/column order."""
    canon = canonicalize_frame(df, sort_by)
    payload = canon.to_csv(index=False, float_format="%.10g").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def hash_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    """SHA-256 of raw file bytes (for archiving downloaded artifacts)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_obj(obj) -> str:
    """SHA-256 of a JSON-serializable object, key-order independent."""
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
