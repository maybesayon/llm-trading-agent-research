"""Frozen prompts, version A-1.0 (manuscript Appendix A; Freeze Document §1).

Do not edit these strings without an Amendment Log entry — the prompts are
part of the frozen instrument.
"""

PROMPTS_VERSION = "A-1.0"

SYSTEM = {
    "s5_scorer": (
        "You are a financial news analyst. Given the news items below about "
        "one company, output JSON {\"score\": s} where s is a number in "
        "[-1, 1] reflecting the net sentiment of the news for the company's "
        "near-term stock performance. Consider only the provided text. Do "
        "not use any other knowledge about the company."
    ),
    "s6_agent": (
        "You are a trading assistant managing a single-stock position. "
        "Inputs: recent news summaries (trailing 3 trading days), daily "
        "closing prices (trailing 60 trading days), current position "
        "(long/flat). Decide the position for the next session. Output JSON "
        "{\"action\": \"long\"|\"flat\", \"rationale\": one paragraph "
        "explaining the primary driver of your decision}. Base your "
        "decision only on the provided inputs."
    ),
    "rationale_classifier": (
        "Classify the primary driver stated in this trading rationale into "
        "exactly one of: sentiment, price_momentum, risk_management, "
        "mixed_other. Output JSON {\"label\": ...}. Judge only what the "
        "rationale states, not whether it is correct."
    ),
    "paraphrase_generator": (
        "Rewrite the following news text preserving all factual content, "
        "named entities, figures, and sentiment. Change only wording and "
        "sentence structure. Output the rewritten text only."
    ),
    "polarity_flip_generator": (
        "Rewrite the following news text keeping all named entities, "
        "figures, and event descriptions unchanged, but invert the "
        "evaluative language so the overall sentiment is reversed. Output "
        "the rewritten text only."
    ),
}


def s5_user_prompt(company_label: str, articles: list) -> str:
    body = "\n".join(f"- {a}" for a in articles)
    return f"Company: {company_label}\nNews items:\n{body}"


def s6_user_prompt(
    company_label: str, articles: list, closes: list, position: str
) -> str:
    news = "\n".join(f"- {a}" for a in articles) if articles else "(no recent news)"
    prices = ", ".join(f"{c:.2f}" for c in closes)
    return (
        f"Company: {company_label}\n"
        f"Recent news (trailing 3 trading days):\n{news}\n"
        f"Daily closes (oldest to newest, trailing {len(closes)} trading days): {prices}\n"
        f"Current position: {position}"
    )


def classifier_user_prompt(rationale: str) -> str:
    return f"Trading rationale:\n{rationale}"


def perturbation_user_prompt(text: str) -> str:
    return text
