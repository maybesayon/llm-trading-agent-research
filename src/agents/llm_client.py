"""Cached, transport-agnostic LLM client (§4.7, D.1, D.8).

Design:
  * TRANSPORT is a callable (system, user, params) -> {"text": str,
    "usage": dict}. Production uses an OpenAI-compatible local vLLM
    endpoint; unit tests use a fake transport. No network in tests.
  * Every call is cached by SHA-256 of (model, prompts version, role,
    system, user, generation params, seed, attempt). Cache entries are
    release artifacts: they allow exact reconstruction of every LLM
    decision without re-running inference.
  * Malformed-output policy (frozen): retry once with a corrective
    suffix, then ABSTAIN. Abstentions are returned explicitly and counted
    by the caller (S6 abstention = hold position, §4.7).
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from src.agents.prompts import PROMPTS_VERSION, SYSTEM

RETRY_SUFFIX = "\n\nYour previous reply was not valid JSON. Return ONLY valid JSON."


class SchemaError(ValueError):
    """Raised by validators on structurally invalid model output."""


# ---------- frozen output validators ----------

def validate_score(payload: dict) -> dict:
    s = payload.get("score")
    if not isinstance(s, (int, float)) or not (-1.0 <= float(s) <= 1.0):
        raise SchemaError(f"score out of schema: {payload!r}")
    return {"score": float(s)}


def validate_action(payload: dict) -> dict:
    action = payload.get("action")
    rationale = payload.get("rationale")
    if action not in ("long", "flat") or not isinstance(rationale, str) or not rationale.strip():
        raise SchemaError(f"action/rationale out of schema: {payload!r}")
    return {"action": action, "rationale": rationale.strip()}


def validate_label(payload: dict) -> dict:
    label = payload.get("label")
    if label not in ("sentiment", "price_momentum", "risk_management", "mixed_other"):
        raise SchemaError(f"label out of schema: {payload!r}")
    return {"label": label}


VALIDATORS = {
    "s5_scorer": validate_score,
    "s6_agent": validate_action,
    "rationale_classifier": validate_label,
}


class CachedLLMClient:
    def __init__(
        self,
        transport,
        cache_dir: str | Path,
        model_id: str,
        generation: dict,
        prompts_version: str = PROMPTS_VERSION,
    ):
        self.transport = transport
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.model_id = model_id
        self.generation = generation  # temperature, top_p, max_tokens per role
        self.prompts_version = prompts_version
        self.stats = {"transport_calls": 0, "cache_hits": 0, "abstentions": 0}

    # ---------- cache ----------

    def _key(self, role: str, system: str, user: str, params: dict, attempt: int) -> str:
        payload = json.dumps(
            {
                "model": self.model_id,
                "prompts_version": self.prompts_version,
                "role": role,
                "system": system,
                "user": user,
                "params": params,
                "attempt": attempt,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    # ---------- calls ----------

    def _params_for(self, role: str, seed: int) -> dict:
        return {
            "temperature": self.generation["temperature"],
            "top_p": self.generation["top_p"],
            "max_tokens": self.generation["max_tokens"][role],
            "seed": seed,
        }

    def call_text(self, role: str, user: str, seed: int, attempt: int = 1) -> dict:
        """Raw cached call. Returns the full cache entry."""
        system = SYSTEM[role]
        if attempt > 1:
            user = user + RETRY_SUFFIX
        params = self._params_for(role, seed)
        key = self._key(role, system, user, params, attempt)
        path = self._cache_path(key)
        if path.exists():
            self.stats["cache_hits"] += 1
            return json.loads(path.read_text())

        self.stats["transport_calls"] += 1
        t0 = time.time()
        result = self.transport(system, user, params)
        entry = {
            "key": key,
            "role": role,
            "system": system,
            "user": user,
            "params": params,
            "attempt": attempt,
            "text": result["text"],
            "usage": result.get("usage", {}),
            "latency_s": round(time.time() - t0, 3),
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        path.write_text(json.dumps(entry, indent=2))
        return entry

    def call_json(self, role: str, user: str, seed: int) -> dict:
        """Schema-validated call with the frozen retry-once-then-abstain
        policy. Returns {"ok": True, "value": ..., "entry": ...} or
        {"ok": False, "abstained": True, "entry": ...}."""
        validator = VALIDATORS[role]
        for attempt in (1, 2):
            entry = self.call_text(role, user, seed, attempt=attempt)
            try:
                value = validator(_parse_json(entry["text"]))
                return {"ok": True, "value": value, "entry": entry}
            except (SchemaError, ValueError):
                continue
        self.stats["abstentions"] += 1
        return {"ok": False, "abstained": True, "entry": entry}


def _parse_json(text: str) -> dict:
    """Extract the first JSON object from model output (models sometimes
    wrap JSON in prose or code fences)."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise SchemaError(f"no JSON object in output: {text[:80]!r}")
    return json.loads(text[start : end + 1])


def openai_compatible_transport(base_url: str, model: str, api_key: str = "EMPTY"):
    """Production transport for a LOCAL vLLM server (user's machine).
    Lazy import; never used in unit tests."""
    def transport(system: str, user: str, params: dict) -> dict:
        import requests  # local inference server only

        resp = requests.post(
            f"{base_url.rstrip('/')}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": params["temperature"],
                "top_p": params["top_p"],
                "max_tokens": params["max_tokens"],
                "seed": params["seed"],
                "chat_template_kwargs": {"enable_thinking": False},
            },
            timeout=300,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "text": data["choices"][0]["message"]["content"],
            "usage": data.get("usage", {}),
        }

    return transport
