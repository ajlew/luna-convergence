from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from luna_voice_provider import generate_openai_compatible_json


GUIDED_VOICE_SCHEMA_VERSION = "1.0"

_PRODUCT_RULES = {
    "daily": "Be quick and sharp. Use 2-3 short story paragraphs and 120-220 words.",
    "monthly": "Tell a developing story. Use 3-5 paragraphs and 260-450 words.",
    "yearly": "Map the strategic arc. Use 4-6 paragraphs and 380-650 words.",
    "natal": "Explain the person as one integrated character. Use 3-5 paragraphs and 280-500 words.",
}
_PLANETS = {
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto", "True Node",
}
_PROHIBITED = (
    "perfect alignment",
    "automatic luck",
    "guaranteed",
    "guarantees",
    "will definitely",
    "will certainly",
    "the worst is over",
    "destined to",
    "fated to",
    "karmic and highly aligned",
)
_IMPERATIVES = {
    "act", "allow", "answer", "ask", "build", "change", "check", "choose",
    "clarify", "complete", "contain", "decide", "define", "delay", "do",
    "finish", "give", "hold", "keep", "let", "make", "move", "name",
    "notice", "pause", "protect", "put", "release", "review", "set", "state",
    "stop", "test", "trust", "use", "verify", "wait", "watch", "write",
}


def facts_hash(product: str, facts: dict[str, Any]) -> str:
    payload = json.dumps(
        {"product": product, "facts": facts},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_guided_voice_prompt(product: str, facts: dict[str, Any]) -> str:
    product_rule = _PRODUCT_RULES.get(product, _PRODUCT_RULES["monthly"])
    return (
        "You are Luna. The JSON below contains calculations owned by Luna's deterministic astrology engine. "
        "Do not recalculate, correct or invent astrology. Interpret only the supplied planets, aspects, signs, "
        "houses, phases, dates, orbs and timing. You may explain what the pattern can feel like and connect its parts.\n\n"
        "Select the dominant calculated event or character thread. Connect the remaining factors into one emotional "
        "narrative. Explain why the period matters in ordinary language. Give the reader earned hope, agency and a "
        "useful direction. Affirm without flattering, guaranteeing, diagnosing or promising an outcome.\n\n"
        "Luna is imperative-led, intimate, emotionally intelligent, consequence-first and dryly cheeky. Include no "
        "more than one tongue-in-cheek line. Avoid vague spiritual padding, jargon lists, emojis and closing questions. "
        + product_rule
        + "\n\nReturn JSON only with exactly these keys: headline, opening, story, affirmation, your_move, facts_hash. "
        "story must be an array of paragraphs. Copy facts_hash exactly. Begin your_move with an imperative verb.\n\n"
        "Do not claim perfect alignment, automatic luck, guarantees, destiny, karmic inevitability, manifestation as "
        "fact, or that the worst is over.\n\n"
        "CALCULATED FACTS:\n"
        + json.dumps(
            {
                "schema_version": GUIDED_VOICE_SCHEMA_VERSION,
                "product": product,
                "facts_hash": facts_hash(product, facts),
                "facts": facts,
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


def validate_guided_voice_copy(
    product: str,
    copy: Any,
    facts: dict[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    errors: list[str] = []
    if not isinstance(copy, dict):
        return False, ("The provider response is not a JSON object.",)
    expected = {"headline", "opening", "story", "affirmation", "your_move", "facts_hash"}
    if set(copy) != expected:
        errors.append("The response fields do not match the guided Luna schema.")
    if copy.get("facts_hash") != facts_hash(product, facts):
        errors.append("The response does not belong to these calculated facts.")

    for key, limit in (("headline", 14), ("opening", 80), ("affirmation", 50), ("your_move", 65)):
        value = " ".join(str(copy.get(key) or "").split())
        if not value:
            errors.append(f"{key} is missing.")
        elif len(value.split()) > limit:
            errors.append(f"{key} exceeds its word limit.")

    story = copy.get("story")
    minimum, maximum = {"daily": (2, 3), "monthly": (3, 5), "yearly": (4, 6), "natal": (3, 5)}.get(
        product, (3, 5)
    )
    if not isinstance(story, list):
        errors.append("story must be an array.")
        story = []
    if not minimum <= len(story) <= maximum:
        errors.append(f"story must contain {minimum}-{maximum} paragraphs.")

    texts = [copy.get("headline"), copy.get("opening"), *(story or []), copy.get("affirmation"), copy.get("your_move")]
    combined = "\n".join(" ".join(str(value or "").split()) for value in texts)
    if "?" in combined:
        errors.append("Luna copy must not end by asking the reader for more information.")
    for phrase in _PROHIBITED:
        if phrase in combined.lower():
            errors.append(f"Prohibited certainty claim: {phrase}.")

    facts_text = json.dumps(facts, ensure_ascii=False, default=str)
    for planet in sorted(_PLANETS):
        if re.search(rf"\b{re.escape(planet)}\b", combined, flags=re.IGNORECASE) and not re.search(
            rf"\b{re.escape(planet)}\b", facts_text, flags=re.IGNORECASE
        ):
            errors.append(f"The response invented an unsupplied planet: {planet}.")

    supplied_numbers = set(re.findall(r"\b\d+(?:\.\d+)?(?::\d+)?\b", facts_text))
    output_numbers = set(re.findall(r"\b\d+(?:\.\d+)?(?::\d+)?\b", combined))
    invented = sorted(output_numbers - supplied_numbers)
    if invented:
        errors.append("The response invented numeric evidence: " + ", ".join(invented) + ".")

    move = " ".join(str(copy.get("your_move") or "").split())
    if move:
        first = re.sub(r"[^a-z]", "", move.split()[0].lower())
        if first not in _IMPERATIVES:
            errors.append("your_move is not clearly imperative.")

    normalized = [re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip() for value in texts if value]
    if len(normalized) != len(set(normalized)):
        errors.append("The response duplicates its own prose.")
    return not errors, tuple(dict.fromkeys(errors))


def generate_guided_voice_copy(
    product: str,
    facts: dict[str, Any],
    *,
    base_url: str,
    model: str,
    api_key: str,
) -> dict[str, Any]:
    copy = generate_openai_compatible_json(
        build_guided_voice_prompt(product, facts),
        base_url=base_url,
        model=model,
        api_key=api_key,
    )
    valid, errors = validate_guided_voice_copy(product, copy, facts)
    if not valid:
        raise ValueError("Guided Luna copy failed validation: " + " | ".join(errors))
    return copy
