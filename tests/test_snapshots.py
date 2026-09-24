"""Snapshot write/verify round-trips and drift detection."""
import pandas as pd

from src.data_ingestion.snapshots import load_manifest, verify_snapshot, write_snapshot
from src.utils.hashing import hash_frame


def test_write_and_verify_roundtrip(tmp_path, synthetic_prices):
    entry = write_snapshot(
        synthetic_prices, "prices_test", tmp_path, meta={"source": "fixture"}
    )
    assert entry["rows"] == len(synthetic_prices)
    assert (tmp_path / entry["file"]).exists()
    assert verify_snapshot(synthetic_prices, entry)

    manifest = load_manifest(tmp_path)
    assert len(manifest) == 1 and manifest[0]["sha256_content"] == entry["sha256_content"]


def test_drift_is_detected(tmp_path, synthetic_prices):
    entry = write_snapshot(synthetic_prices, "prices_test", tmp_path)
    drifted = synthetic_prices.copy()
    drifted.loc[0, "volume"] += 1
    assert not verify_snapshot(drifted, entry)


def test_identical_redownload_same_hash(tmp_path, synthetic_prices):
    """Re-downloaded identical data in a different row order must produce
    the same content hash: no false drift alarms."""
    entry = write_snapshot(synthetic_prices, "prices_test", tmp_path)
    redownload = synthetic_prices.sample(frac=1.0, random_state=3)
    assert hash_frame(redownload) == entry["sha256_content"]


def test_snapshot_file_roundtrip_preserves_content(tmp_path, synthetic_prices):
    entry = write_snapshot(synthetic_prices, "prices_test", tmp_path)
    reloaded = pd.read_csv(tmp_path / entry["file"], parse_dates=["date"])
    assert verify_snapshot(reloaded, entry)
