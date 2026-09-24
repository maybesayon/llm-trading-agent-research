"""LLM client tests with a fake transport — no network, no model."""
import json

import pytest

from src.agents.llm_client import (
    CachedLLMClient,
    SchemaError,
    validate_action,
    validate_label,
    validate_score,
)

GEN = {
    "temperature": 0.7,
    "top_p": 0.8,
    "max_tokens": {
        "s5_scorer": 64,
        "s6_agent": 512,
        "rationale_classifier": 64,
    },
}


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, system, user, params):
        self.calls.append({"system": system, "user": user, "params": params})
        return {"text": self.responses.pop(0), "usage": {"total_tokens": 10}}


def make_client(tmp_path, responses):
    transport = FakeTransport(responses)
    client = CachedLLMClient(transport, tmp_path / "cache", "Qwen/Qwen3-14B", GEN)
    return client, transport


def test_validators_accept_and_reject():
    assert validate_score({"score": 0.5}) == {"score": 0.5}
    with pytest.raises(SchemaError):
        validate_score({"score": 2.0})
    assert validate_action({"action": "long", "rationale": "news is positive"})[
        "action"
    ] == "long"
    with pytest.raises(SchemaError):
        validate_action({"action": "short", "rationale": "x"})
    assert validate_label({"label": "sentiment"}) == {"label": "sentiment"}
    with pytest.raises(SchemaError):
        validate_label({"label": "vibes"})


def test_cache_hit_avoids_transport(tmp_path):
    client, transport = make_client(tmp_path, ['{"score": 0.3}'])
    r1 = client.call_json("s5_scorer", "Company: X\nNews:\n- up", seed=42)
    r2 = client.call_json("s5_scorer", "Company: X\nNews:\n- up", seed=42)
    assert r1["ok"] and r2["ok"] and r1["value"] == r2["value"]
    assert len(transport.calls) == 1  # second call served from cache
    assert client.stats["cache_hits"] == 1


def test_different_seed_is_different_cache_entry(tmp_path):
    client, transport = make_client(tmp_path, ['{"score": 0.3}', '{"score": 0.3}'])
    client.call_json("s5_scorer", "same prompt", seed=11)
    client.call_json("s5_scorer", "same prompt", seed=42)
    assert len(transport.calls) == 2


def test_retry_then_abstain_policy(tmp_path):
    client, transport = make_client(
        tmp_path, ["not json at all", "still { broken"]
    )
    r = client.call_json("s6_agent", "decide", seed=42)
    assert r["ok"] is False and r["abstained"] is True
    assert len(transport.calls) == 2  # exactly one retry
    assert "ONLY valid JSON" in transport.calls[1]["user"]
    assert client.stats["abstentions"] == 1


def test_retry_recovers_when_second_attempt_valid(tmp_path):
    client, transport = make_client(
        tmp_path, ["oops", '{"action": "flat", "rationale": "no clear signal"}']
    )
    r = client.call_json("s6_agent", "decide", seed=42)
    assert r["ok"] and r["value"]["action"] == "flat"
    assert client.stats["abstentions"] == 0


def test_json_extraction_from_fenced_output(tmp_path):
    client, _ = make_client(tmp_path, ['```json\n{"score": -0.2}\n```'])
    r = client.call_json("s5_scorer", "x", seed=42)
    assert r["ok"] and r["value"]["score"] == -0.2


def test_cache_entries_are_release_artifacts(tmp_path):
    client, _ = make_client(tmp_path, ['{"score": 0.1}'])
    r = client.call_json("s5_scorer", "x", seed=42)
    cached = json.loads((tmp_path / "cache" / f"{r['entry']['key']}.json").read_text())
    for field in ("role", "system", "user", "params", "text", "usage", "created_utc"):
        assert field in cached  # everything needed to reconstruct the call
    assert cached["params"]["temperature"] == 0.7  # A-001 values in effect
    assert cached["params"]["top_p"] == 0.8
