"""Config loading and the machine-readable protocol lock (§4.7).

Every run must log `protocol_lock_hash()` so config drift is detectable.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from src.utils.hashing import hash_obj

CONFIG_FILES = ["model.yaml", "data.yaml", "strategies.yaml", "evaluation.yaml"]
LOCK_FILE = "protocol.lock.yaml"


def load_yaml(path: str | Path) -> dict:
    with open(path) as fh:
        return yaml.safe_load(fh)


def load_configs(configs_dir: str | Path) -> dict:
    configs_dir = Path(configs_dir)
    return {
        f.removesuffix(".yaml"): load_yaml(configs_dir / f) for f in CONFIG_FILES
    }


def load_protocol_lock(project_root: str | Path) -> tuple[dict, str]:
    """Return (lock contents, lock hash). The hash is only final once
    `freeze_status.pending` is empty."""
    lock = load_yaml(Path(project_root) / LOCK_FILE)
    return lock, hash_obj(lock)


def assert_frozen(lock: dict) -> None:
    """Raise if any [FREEZE] item is still pending. No full-scale experiment
    may run while this raises."""
    pending = (lock.get("freeze_status") or {}).get("pending") or []
    if pending:
        raise RuntimeError(
            f"Protocol not frozen; pending items: {pending}. "
            "Experiments must not run (Freeze Document, final checklist)."
        )
