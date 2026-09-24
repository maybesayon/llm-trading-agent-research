"""Anonymization instrument tests (§3.4, Freeze Document §4)."""
import pandas as pd

from src.anonymization.anonymize import (
    anonymize_news,
    anonymize_text,
    compile_alias_patterns,
    placeholder_assignment,
    shuffle_dates,
    strip_urls,
)

ALIASES = {
    "AAPL": ["Apple Inc.", "Apple", "iPhone", "Tim Cook"],
    "MSFT": ["Microsoft Corporation", "Microsoft", "Windows", "Satya Nadella"],
}


def make_news(rows):
    return pd.DataFrame(
        [
            {"timestamp": pd.Timestamp(ts), "ticker": t, "headline": h}
            for ts, t, h in rows
        ]
    )


def test_all_aliases_removed_case_insensitive():
    text = (
        "APPLE beats estimates as Tim Cook touts iPhone sales; "
        "Microsoft's Windows revenue slips, says Satya Nadella."
    )
    compiled = compile_alias_patterns(ALIASES)
    placeholders = placeholder_assignment(ALIASES.keys(), "2022-01-03")
    out = anonymize_text(text, compiled, placeholders)
    for aliases in ALIASES.values():
        for a in aliases:
            assert a.lower() not in out.lower()
    assert "Company_" in out


def test_longest_alias_first_no_residue():
    compiled = compile_alias_patterns(ALIASES)
    placeholders = {"AAPL": "Company_1", "MSFT": "Company_2"}
    out = anonymize_text("Apple Inc. announced Microsoft Corporation deal", compiled, placeholders)
    assert "Inc" not in out and "Corporation" not in out
    assert out.count("Company_1") == 1 and out.count("Company_2") == 1


def test_placeholders_consistent_within_day_rerandomized_across_days():
    news = make_news(
        [(f"2022-01-{d:02d} 10:00", "AAPL", "Apple rises; Microsoft flat") for d in range(3, 21)]
    )
    out = anonymize_news(news, ALIASES, seed=42)
    # within one day: identical mapping across articles
    same_day = make_news(
        [
            ("2022-01-03 09:00", "AAPL", "Apple up"),
            ("2022-01-03 15:00", "MSFT", "Apple down"),
        ]
    )
    out2 = anonymize_news(same_day, ALIASES, seed=42)
    assert out2["headline"].iloc[0].split()[0] == out2["headline"].iloc[1].split()[0]
    # across days: the AAPL placeholder is not the same every day
    aapl_tokens = {h.split()[0] for h in out["headline"]}
    assert len(aapl_tokens) > 1


def test_anonymize_deterministic():
    news = make_news([("2022-01-03 10:00", "AAPL", "Apple and Microsoft news")])
    a = anonymize_news(news, ALIASES, seed=42)
    b = anonymize_news(news, ALIASES, seed=42)
    assert a.equals(b)


def test_url_stripping_happens_before_alias_pass():
    out = strip_urls("see https://news.example.com/apple-story now")
    assert "https" not in out and "apple-story" not in out


def test_shuffle_dates_preserves_article_set():
    rows = [
        (f"2022-01-{d:02d} 10:00", t, f"{t} headline {d}")
        for d in range(3, 28)
        for t in ("AAPL", "MSFT")
    ]
    news = make_news(rows)
    shuffled = shuffle_dates(news, seed=42)

    assert len(shuffled) == len(news)
    # article content untouched, per-ticker timestamp MULTISET preserved
    assert sorted(shuffled["headline"]) == sorted(news["headline"])
    for t in ("AAPL", "MSFT"):
        assert sorted(shuffled[shuffled["ticker"] == t]["timestamp"]) == sorted(
            news[news["ticker"] == t]["timestamp"]
        )
    # but the time alignment is actually destroyed
    assert (shuffled["timestamp"] != news["timestamp"]).any()
    # and the permutation is seeded/deterministic
    assert shuffle_dates(news, seed=42).equals(shuffled)
    assert not shuffle_dates(news, seed=7).equals(shuffled)
