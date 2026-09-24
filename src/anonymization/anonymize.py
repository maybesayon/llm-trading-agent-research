"""Anonymization instrument (§3.4, Appendix E, Freeze Document §4).

Curated per-firm alias dictionaries with regex replacement; placeholders
are consistent WITHIN a decision context (one calendar day) and
re-randomized ACROSS contexts (seeded), so cross-day identity cannot be
inferred. Includes the within-ticker date shuffler for the third
contamination condition. spaCy NER fallback is a pilot-time addition and
is deliberately not exercised in unit tests.
"""
from __future__ import annotations

import random
import re

import pandas as pd

URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)


def strip_urls(text: str) -> str:
    return URL_RE.sub(" ", text)


def compile_alias_patterns(alias_map: dict) -> dict:
    """ticker -> list of compiled word-boundary patterns, longest alias
    first so 'Apple Inc.' is replaced before 'Apple'."""
    compiled = {}
    for ticker, aliases in alias_map.items():
        names = sorted(set(list(aliases) + [ticker]), key=len, reverse=True)
        compiled[ticker] = [
            re.compile(r"(?<!\w)" + re.escape(a) + r"(?!\w)", re.IGNORECASE)
            for a in names
        ]
    return compiled


def placeholder_assignment(tickers, context_key: str, seed: int = 42) -> dict:
    """Deterministic per-context placeholder mapping, re-randomized across
    contexts via a context-keyed seeded RNG."""
    tickers = sorted(tickers)
    rng = random.Random(f"{seed}:{context_key}")
    indices = list(range(1, len(tickers) + 1))
    rng.shuffle(indices)
    return {t: f"Company_{i}" for t, i in zip(tickers, indices)}


def anonymize_text(text: str, compiled: dict, placeholders: dict) -> str:
    out = strip_urls(text)
    for ticker, patterns in compiled.items():
        for pat in patterns:
            out = pat.sub(placeholders[ticker], out)
    return out


def anonymize_news(
    news: pd.DataFrame,
    alias_map: dict,
    seed: int = 42,
    text_col: str = "headline",
) -> pd.DataFrame:
    """Anonymize all firm mentions (any universe firm, not only the row's
    ticker) with day-consistent, cross-day-re-randomized placeholders."""
    compiled = compile_alias_patterns(alias_map)
    out = news.copy()
    context_keys = pd.to_datetime(out["timestamp"]).dt.normalize().astype(str)
    mappings = {
        ck: placeholder_assignment(alias_map.keys(), ck, seed)
        for ck in context_keys.unique()
    }
    out[text_col] = [
        anonymize_text(text, compiled, mappings[ck])
        for text, ck in zip(out[text_col], context_keys)
    ]
    return out


def shuffle_dates(news: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Third contamination condition (§3.4): within-ticker permutation of
    timestamps; the article set is preserved exactly."""
    out = news.copy().reset_index(drop=True)
    for ticker, idx in out.groupby("ticker").groups.items():
        idx = list(idx)
        ts = list(out.loc[idx, "timestamp"])
        rng = random.Random(f"{seed}:{ticker}")
        rng.shuffle(ts)
        out.loc[idx, "timestamp"] = ts
    return out


class SpacyNERFallback:
    """Pilot-time fallback for residual ORG/PERSON/GPE entities the alias
    dictionaries miss (Freeze Document §4). Lazy import; version recorded.
    Not exercised in unit tests."""

    def __init__(self, model: str = "en_core_web_sm"):
        self.model_name = model
        self._nlp = None

    def _load(self):
        if self._nlp is None:
            import spacy  # lazy: not a test dependency

            self._nlp = spacy.load(self.model_name)
        return self._nlp

    def mask_residual_entities(self, text: str, replacement: str = "Entity") -> str:
        nlp = self._load()
        doc = nlp(text)
        out = text
        for ent in sorted(doc.ents, key=lambda e: -e.start_char):
            if ent.label_ in {"ORG", "PERSON", "GPE"}:
                out = out[: ent.start_char] + replacement + out[ent.end_char :]
        return out
