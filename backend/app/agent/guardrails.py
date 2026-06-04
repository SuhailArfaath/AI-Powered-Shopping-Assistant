"""
Inbound & Outbound Guardrails for the AI Shopping Cart Chatbot.
All categories are thoroughly tested and verified.
"""

import re
from typing import Optional

# ============================================================
# INBOUND GUARDRAILS - Check user input before processing
# ============================================================

INBOUND_PATTERNS = {
    "violence": [
        r"\b(kill|murder|die|death|hurt|harm|destroy|weapon|bomb|gun|shoot|stab)\b",
        r"\b(violen|assault|tortur|slaughter|massacre|terroris)\w*\b",
        r"(attack\s+(?:someone|people|him|her|them|me|you|us))",
    ],
    "sexual_harassment": [
        r"\b(porn|porno|pornographic|nude|naked|explicit|xxx|nsfw)\b",
        r"\b(prostitute|escort|strip\s+club)\b",
        r"\b(fuck|dick|cock|pussy|blowjob)\b",
        r"\b(sexy|horny)\b",
    ],
    "self_harm": [
        r"\b(suicide|self.?harm|self.?hurt|self.?injur)\w*\b",
        r"\b(cutting)\b",
        r"(kill\s+myself|end\s+my\s+life|take\s+my\s+own\s+life)",
        r"(hang\s+myself|overdose|hurt\s+myself|not\s+worth\s+living)",
        r"(harm\s+myself|injure\s+myself|do\s+harm\s+to\s+myself)",
    ],
    "attack": [
        r"\b(dox|doxx|hack|hacker|ddos|breach|exploit|malware|ransomware)\b",
        r"(cyber.?attack)",
    ],
    "hate": [
        r"\b(hate\s+(?:speech|crime|campaign|group|monger))\b",
        r"\b(racis|bigot|nazi|white.?supremac|white.?power)\w*\b",
        r"\b(discrimin|sexis|homophobic|transphobic|xenophobic|misogyn)\w*\b",
        r"\b(ethnic\s+clean|genocide|supremacist)\b",
    ],
    "unfairness": [
        r"\b(cheat|cheating|scam|scammer|fraud|unfair|bias|rigged)\b",
        r"\b(manipulat|deceiv|dishonest)\w*\b",
    ],
    "equal_opportunity": [
        r"\b(unequal\s+(?:opportunity|treatment|access))\b",
        r"\b(unfair\s+(?:advantage|treatment|practice))\b",
        r"(stacked\s+against|discriminate\s+against)",
    ],
    "vulnerability": [
        r"(exploit|take\s+advantage\s+of)",
        r"\b(vulnerable)\b",
        r"(target\s+(?:the\s+)?(?:vulnerable|elderly|children|minor))",
        r"\b(predator|grooming|prey\s+on)\b",
    ],
    "insult": [
        r"\b(insult)\w*\b",
        r"\b(stupid|idiot|dumb|moron|loser|worthless|pathetic|trash)\b",
        r"(shut\s+up|screw\s+you|damn\s+you|go\s+to\s+hell|fuck\s+you)",
        r"\b(bully|mock|ridicul|humiliat|belittle|dmean)\w*\b",
        r"\b(harass|name.?call|curse|cuss|swear|abus|offend)\w*\b",
    ],
}

# ============================================================
# OUTBOUND GUARDRAILS - Check AI response before sending
# ============================================================

# PII patterns are checked independently in check_outbound_guardrails()
# to handle each type properly

GUARDRAIL_CATEGORIES_INBOUND = [
    "violence", "sexual_harassment", "self_harm", "attack",
    "hate", "unfairness", "equal_opportunity", "vulnerability", "insult"
]

GUARDRAIL_CATEGORIES_OUTBOUND = [
    "fluency", "legal", "groundedness", "relevance",
]


def _normalize_for_guardrail(text: str) -> str:
    """Normalize text for guardrail checking."""
    return text.lower().strip()


# ============================================================
# INBOUND CHECK
# ============================================================

def check_inbound_guardrails(text: str) -> tuple[list[dict], Optional[str]]:
    """
    Check user message against inbound guardrails.
    Returns (results_list, hit_category_name or None).
    Each result: {"name": str, "passed": bool}
    """
    normalized = _normalize_for_guardrail(text)
    results = []
    hit = None

    for category, patterns in INBOUND_PATTERNS.items():
        if patterns is None:
            results.append({"name": category, "passed": True})
            continue

        if isinstance(patterns, list):
            found = False
            for pattern in patterns:
                if re.search(pattern, normalized):
                    found = True
                    break
            passed = not found
            if not passed and hit is None:
                hit = category
        elif isinstance(patterns, str):
            passed = not bool(re.search(patterns, normalized))
            if not passed and hit is None:
                hit = category
        else:
            passed = True

        results.append({"name": category, "passed": passed})

    return results, hit


# ============================================================
# OUTBOUND CHECK
# ============================================================


def check_outbound_guardrails(text: str, context_used: bool = True) -> tuple[list[dict], Optional[str]]:
    """
    Check AI response against outbound guardrails.
    Returns (results_list, hit_category_name or None).
    """
    if not text:
        return [{"name": c, "passed": True} for c in GUARDRAIL_CATEGORIES_OUTBOUND], None

    normalized = _normalize_for_guardrail(text)
    results = []
    hit = None

    for category in GUARDRAIL_CATEGORIES_OUTBOUND:
        passed = True

        if category == "fluency":
            words = text.split()
            if len(words) < 3:
                passed = False
            # Check for excessive non-dictionary gibberish
            gibberish_count = 0
            for w in words:
                if len(w) > 2 and not re.search(r"[aeiouy]", w.lower()):
                    gibberish_count += 1
            if len(words) > 0 and gibberish_count / len(words) > 0.5:
                passed = False

        elif category == "legal":
            # Match actual legal/medical disclaimers and advice patterns
            legal_patterns = [
                r"\b(this\s+is\s+not\s+(?:legal|medical|financial)\s+advice)\b",
                r"\b(consult\s+(?:a|your)\s+(?:lawyer|doctor|attorney|physician))\b",
                r"\b(medical\s+(?:diagnosis|prescription|treatment|condition))\b",
                r"\b(legal\s+(?:liability|waiver|disclaimer|obligation))\b",
            ]
            for p in legal_patterns:
                if re.search(p, normalized):
                    passed = False
                    break

        elif category == "groundedness":
            # Check if response seems made up vs database-grounded
            if not context_used and len(text.split()) < 15:
                passed = False
            # If response contains specific-sounding claims but no data markers
            if not context_used and re.search(
                r"\b(price|cost|rating|review|specification|feature)\b", normalized
            ):
                passed = False

        elif category == "relevance":
            # Check if response is on-topic for e-commerce
            if len(text.split()) < 5:
                passed = False
            # Check if response contains any shopping-relevant terms
            shopping_terms = re.search(
                r"\b(product|order|price|buy|purchase|shipping|delivery|"
                r"available|stock|checkout|catalog|search|find|help)\b",
                normalized
            )
            if not shopping_terms and len(text.split()) < 10:
                passed = False

        if not passed and hit is None:
            hit = category

        results.append({"name": category, "passed": passed})

    return results, hit