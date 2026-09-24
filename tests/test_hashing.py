"""Content-hash determinism: identical content => identical hash,
regardless of row/column order; any content change => different hash."""
from src.utils.hashing import hash_frame, hash_obj


def test_hash_invariant_to_row_and_column_order(synthetic_prices):
    baseline = hash_frame(synthetic_prices)
    shuffled_rows = synthetic_prices.sample(frac=1.0, random_state=7)
    reversed_cols = synthetic_prices[list(reversed(synthetic_prices.columns))]
    assert hash_frame(shuffled_rows) == baseline
    assert hash_frame(reversed_cols) == baseline


def test_hash_changes_on_content_change(synthetic_prices):
    baseline = hash_frame(synthetic_prices)
    tweaked = synthetic_prices.copy()
    tweaked.loc[0, "close"] += 0.01
    assert hash_frame(tweaked) != baseline


def test_hash_obj_key_order_independent():
    a = {"x": 1, "y": [1, 2], "z": {"a": True}}
    b = {"z": {"a": True}, "y": [1, 2], "x": 1}
    assert hash_obj(a) == hash_obj(b)
    assert hash_obj({**a, "x": 2}) != hash_obj(a)
