from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from luna_voice_provider import VoiceProviderError, generate_openai_compatible_json


GUIDED_VOICE_SCHEMA_VERSION = "1.0"
GUIDED_COLLECTION_SCHEMA_VERSION = "1.0"

_PRODUCT_RULES = {
    "daily": "Be quick and sharp. Use 2-3 short story paragraphs and 120-220 words.",
    "weekly": "Tell one connected weekly story. Use 3-5 paragraphs and 230-380 words.",
    "weekly_sign": "Translate the weekly pattern through the supplied houses. Use 2-3 short paragraphs and 140-240 words.",
    "monthly": "Tell a developing story. Use 3-5 paragraphs and 260-450 words.",
    "yearly": "Map the strategic arc. Use 4-6 paragraphs and 380-650 words.",
    "natal": "Explain the person as one integrated character. Use 3-5 paragraphs and 280-500 words.",
    "solar": "Explain the current solar phase as a practical seasonal instruction. Use 2-3 short paragraphs and 140-240 words.",
}

_COLLECTION_RULES = {
    "weekly_days": "Write one vivid 55-95 word daily reading per supplied day.",
    "weekly_signs": "Write one distinctive 90-150 word weekly reading per supplied sign. Use its supplied houses and life areas.",
    "monthly_events": "Write one useful 70-120 word interpretation per calculated date.",
    "natal_signatures": "Write one 80-130 word behavioural interpretation per calculated natal signature.",
    "yearly_transits": "Write one strategic 100-170 word interpretation per calculated personal transit.",
    "personal_events": "Write one 75-130 word interpretation per calculated event contacting the natal chart.",
}
_PLANETS = {
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto", "True Node",
}
_PROHIBITED = (
    "perfect alignment",
    "automatic luck",
    "will definitely",
    "will certainly",
    "the worst is over",
    "destined to",
    "fated to",
    "karmic and highly aligned",
)
_GUARANTEE_WORD = re.compile(r"\bguarantee(?:d|s|ing)?\b", flags=re.IGNORECASE)
_GUARANTEE_NEGATORS = {
    "no", "not", "never", "nothing", "neither", "without", "cannot",
    "can't", "isn't", "aren't", "doesn't", "don't",
}
_IMPERATIVES = {
    "accept", "act", "allow", "answer", "apply", "ask", "begin", "build",
    "change", "check", "choose", "clarify", "complete", "contain", "cut",
    "decide", "define", "delay", "do", "drop", "end", "face", "feel",
    "finish", "follow", "give", "hold", "keep", "lead", "lean", "let",
    "listen", "look", "make", "move", "name", "notice", "open", "pause",
    "pick", "protect", "put", "read", "release", "remember", "reset",
    "review", "say", "send", "set", "slow", "start", "state", "stay",
    "step", "stop", "take", "test", "treat", "trust", "turn", "use",
    "verify", "wait", "watch", "write",
}
_SECTION_LABEL = re.compile(
    r"(?:^|[.!?]\s+)(?:your\s+move|remember|affirmation)\s*(?::|·|-)",
    flags=re.IGNORECASE,
)


def _contains_move(story: str, move: str) -> bool:
    normalized_story = re.sub(r"[^a-z0-9]+", " ", story.lower()).strip()
    normalized_move = re.sub(r"[^a-z0-9]+", " ", move.lower()).strip()
    return bool(len(normalized_move.split()) >= 4 and normalized_move in normalized_story)


def _has_unnegated_guarantee(text: str) -> bool:
    """Reject promises while allowing clear disclaimers such as 'nothing is guaranteed'."""
    for match in _GUARANTEE_WORD.finditer(str(text or "")):
        prefix = str(text or "")[: match.start()]
        sentence = re.split(r"[.!?\n]+", prefix)[-1]
        words = re.findall(r"[a-z]+(?:'[a-z]+)?", sentence.lower())[-5:]
        if not any(word in _GUARANTEE_NEGATORS for word in words):
            return True
    return False


def facts_hash(product: str, facts: dict[str, Any]) -> str:
    payload = json.dumps(
        {"product": product, "facts": facts},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _guided_voice_response_format(product: str, facts: dict[str, Any]) -> dict[str, Any]:
    """Groq strict schema for one complete Luna reading."""
    minimum, maximum = {
        "daily": (2, 3),
        "monthly": (3, 5),
        "yearly": (4, 6),
        "natal": (3, 5),
        "solar": (2, 3),
        "weekly_sign": (2, 3),
    }.get(product, (3, 5))
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "luna_guided_voice",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "headline": {"type": "string"},
                    "opening": {"type": "string"},
                    "story": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": minimum,
                        "maxItems": maximum,
                    },
                    "affirmation": {"type": "string"},
                    "your_move": {"type": "string"},
                    "facts_hash": {"type": "string", "enum": [facts_hash(product, facts)]},
                },
                "required": [
                    "headline", "opening", "story", "affirmation", "your_move", "facts_hash"
                ],
                "additionalProperties": False,
            },
        },
    }


def build_guided_voice_prompt(product: str, facts: dict[str, Any]) -> str:
    product_rule = _PRODUCT_RULES.get(product, _PRODUCT_RULES["monthly"])
    return (
        "You are Luna. The JSON below contains calculations owned by Luna's deterministic astrology engine. "
        "Do not recalculate, correct or invent astrology. Interpret only the supplied planets, aspects, signs, "
        "houses, phases, dates, orbs and timing. You may explain what the pattern can feel like and connect its parts.\n\n"
        "Select the dominant calculated event or character thread. Connect the remaining factors into one emotional "
        "narrative. Explain why the period matters in ordinary language. Give the reader earned hope, agency and a "
        "useful direction. Affirm without flattering, guaranteeing, diagnosing or promising an outcome.\n\n"
        "Luna is imperative-led, intimate, emotionally intelligent, consequence-first and dryly cheeky. Name the "
        "human tension before explaining it. Use concrete ordinary-life examples when the supplied houses or life areas "
        "support them. Vary sentence rhythm. Include one memorable image or dry tongue-in-cheek observation, but no more "
        "than one. Make the affirmation credible and specific: recognise the reader's capacity without praising them or "
        "pretending the sky guarantees a reward. Avoid vague spiritual padding, jargon lists, emojis and closing questions. "
        + product_rule
        + "\n\nReturn JSON only with exactly these keys: headline, opening, story, affirmation, your_move, facts_hash. "
        "story must be an array of paragraphs. Copy facts_hash exactly. Begin your_move with one of these "
        "imperative verbs: " + ", ".join(sorted(_IMPERATIVES)) + ".\n\n"
        "Do not write section labels such as Your move, Remember or Affirmation inside story. Do not repeat the "
        "your_move sentence inside story; the application renders that field separately.\n\n"
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


def collection_facts_hash(product: str, facts: dict[str, Any]) -> str:
    payload = json.dumps(
        {"collection": product, "facts": facts},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _guided_collection_response_format(product: str, facts: dict[str, Any]) -> dict[str, Any]:
    """Groq strict schema for a bounded Luna collection batch."""
    source_ids = [str(item.get("source_id") or "") for item in facts.get("items") or []]
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "luna_guided_collection",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source_id": {"type": "string", "enum": source_ids},
                                "headline": {"type": "string"},
                                "story": {"type": "string"},
                                "affirmation": {"type": "string"},
                                "your_move": {"type": "string"},
                            },
                            "required": [
                                "source_id", "headline", "story", "affirmation", "your_move"
                            ],
                            "additionalProperties": False,
                        },
                    },
                    "facts_hash": {
                        "type": "string",
                        "enum": [collection_facts_hash(product, facts)],
                    },
                },
                "required": ["items", "facts_hash"],
                "additionalProperties": False,
            },
        },
    }


def build_guided_collection_prompt(product: str, facts: dict[str, Any]) -> str:
    rule = _COLLECTION_RULES.get(product, "Write one concise interpretation per supplied item.")
    shared_rule = (
        "The top-level shared_context is calculated evidence that applies to every item. Use it together with each "
        "item's own houses and life areas, without copying the same story between items.\n\n"
        if facts.get("shared_context")
        else ""
    )
    return (
        "You are Luna. The supplied JSON contains closed calculations from Luna's deterministic astrology engine. "
        "Never recalculate, repair or invent astrology. Interpret only the supplied items. Preserve every source_id "
        "exactly and return the items in their supplied order.\n\n"
        "Each item must feel written for a human, not assembled from a template. Name the recognisable emotional or "
        "practical tension, explain why it matters, connect pressure with any supplied support, offer earned hope or "
        "agency, and finish with a useful action. Luna is warm, incisive, intimate, imperative-led and dryly cheeky. "
        "Use ordinary language, varied sentence rhythm and at most one short cheeky observation per item. Do not use "
        "generic flattery, therapy slogans, mystical padding, emojis, jargon lists or closing questions. "
        + rule
        + "\n\n"
        + shared_rule
        + "Return JSON only with exactly these keys: items, facts_hash. Each items entry must contain exactly: "
        "source_id, headline, story, affirmation, your_move. story is one complete paragraph string. Copy facts_hash "
        "exactly. Begin every your_move with one of these imperative verbs: "
        + ", ".join(sorted(_IMPERATIVES))
        + ".\n\n"
        "Do not write section labels such as Your move, Remember or Affirmation inside story. Do not repeat an "
        "item's your_move sentence inside its story; the application renders that field separately.\n\n"
        "Never claim perfect alignment, automatic luck, guarantees, certainty, destiny, karmic inevitability, "
        "manifestation as fact, or that the worst is over.\n\n"
        "CALCULATED COLLECTION:\n"
        + json.dumps(
            {
                "schema_version": GUIDED_COLLECTION_SCHEMA_VERSION,
                "product": product,
                "facts_hash": collection_facts_hash(product, facts),
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
    if _has_unnegated_guarantee(combined):
        errors.append("Prohibited certainty claim: guarantee.")

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
    for paragraph in story:
        paragraph_text = " ".join(str(paragraph or "").split())
        if _SECTION_LABEL.search(paragraph_text):
            errors.append("story contains a reserved section label.")
        if move and _contains_move(paragraph_text, move):
            errors.append("story repeats the dedicated your_move field.")

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
    prompt = build_guided_voice_prompt(product, facts)
    output_budget = {
        "daily": 1400,
        "weekly": 2200,
        "weekly_sign": 1400,
        "monthly": 2600,
        "yearly": 3600,
        "natal": 3200,
        "solar": 1400,
    }.get(product, 2600)
    errors: tuple[str, ...] = ()
    best_errors: tuple[str, ...] = ()
    for attempt in range(3):
        copy = generate_openai_compatible_json(
            prompt,
            base_url=base_url,
            model=model,
            api_key=api_key,
            max_tokens=output_budget,
            response_format=_guided_voice_response_format(product, facts),
        )
        valid, errors = validate_guided_voice_copy(product, copy, facts)
        if valid:
            return copy
        repaired = _repair_guided_voice_structure(product, copy, facts=facts)
        repaired_valid, repaired_errors = validate_guided_voice_copy(
            product, repaired, facts
        )
        if repaired_valid:
            return repaired
        if not best_errors or len(repaired_errors) < len(best_errors):
            best_errors = repaired_errors
        if attempt < 2:
            prompt += (
                "\n\nCORRECTION REPORT: The previous draft was rejected. Return a complete replacement and fix: "
                + " | ".join(repaired_errors or errors)
            )
    if best_errors:
        errors = best_errors
    raise ValueError("Guided Luna copy failed validation: " + " | ".join(errors))


def _repair_guided_voice_structure(
    product: str,
    copy: dict[str, Any] | None,
    *,
    facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Repair presentation structure without changing or inventing astrology."""
    if not isinstance(copy, dict):
        return {}
    expected = {"headline", "opening", "story", "affirmation", "your_move", "facts_hash"}
    repaired = {key: value for key, value in copy.items() if key in expected}
    if facts is not None:
        # This is deterministic provenance metadata, not generated astrology.
        repaired["facts_hash"] = facts_hash(product, facts)
    minimum, maximum = {
        "daily": (2, 3),
        "monthly": (3, 5),
        "yearly": (4, 6),
        "natal": (3, 5),
        "solar": (2, 3),
        "weekly_sign": (2, 3),
    }.get(product, (3, 5))
    raw_story = repaired.get("story")
    if isinstance(raw_story, str):
        paragraphs = [" ".join(raw_story.split())]
    elif isinstance(raw_story, list):
        paragraphs = [" ".join(str(value or "").split()) for value in raw_story]
        paragraphs = [value for value in paragraphs if value]
    else:
        paragraphs = []

    while paragraphs and len(paragraphs) < minimum:
        index = max(range(len(paragraphs)), key=lambda item: len(paragraphs[item].split()))
        paragraph = paragraphs[index]
        sentences = [
            value.strip()
            for value in re.split(r"(?<=[.!?])\s+", paragraph)
            if value.strip()
        ]
        if len(sentences) >= 2:
            pivot = max(1, len(sentences) // 2)
            parts = [" ".join(sentences[:pivot]), " ".join(sentences[pivot:])]
        else:
            words = paragraph.split()
            if len(words) < 8:
                break
            pivot = len(words) // 2
            parts = [" ".join(words[:pivot]), " ".join(words[pivot:])]
        paragraphs[index:index + 1] = parts
    if len(paragraphs) > maximum:
        paragraphs = paragraphs[: maximum - 1] + [" ".join(paragraphs[maximum - 1:])]
    repaired["story"] = paragraphs

    move = " ".join(str(repaired.get("your_move") or "").split())
    if move:
        first = re.sub(r"[^a-z]", "", move.split()[0].lower())
        if first not in _IMPERATIVES:
            repaired["your_move"] = f"Do this: {move}"
    return repaired


def validate_guided_collection_copy(
    product: str,
    copy: Any,
    facts: dict[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    errors: list[str] = []
    if not isinstance(copy, dict):
        return False, ("The provider response is not a JSON object.",)
    if set(copy) != {"items", "facts_hash"}:
        errors.append("The response fields do not match the guided collection schema.")
    if copy.get("facts_hash") != collection_facts_hash(product, facts):
        errors.append("The response does not belong to these calculated collection facts.")

    supplied_items = list(facts.get("items") or [])
    expected_ids = [str(item.get("source_id") or "") for item in supplied_items]
    items = copy.get("items")
    if not isinstance(items, list):
        errors.append("items must be an array.")
        items = []
    returned_ids = [str(item.get("source_id") or "") for item in items if isinstance(item, dict)]
    if returned_ids != expected_ids or len(items) != len(expected_ids):
        errors.append("Source IDs are missing, duplicated, reordered or invented.")

    facts_text = json.dumps(facts, ensure_ascii=False, default=str)
    supplied_numbers = set(re.findall(r"\b\d+(?:\.\d+)?(?::\d+)?\b", facts_text))
    all_texts: list[str] = []
    story_texts: list[str] = []
    supplied_by_id = {str(item.get("source_id") or ""): item for item in supplied_items}
    shared_context = facts.get("shared_context") or {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"Item {index + 1} is not an object.")
            continue
        if set(item) != {"source_id", "headline", "story", "affirmation", "your_move"}:
            errors.append(f"Item {index + 1} fields do not match the collection schema.")
        item_texts = []
        for key, limit in (("headline", 14), ("story", 170), ("affirmation", 38), ("your_move", 45)):
            value = " ".join(str(item.get(key) or "").split())
            if not value:
                errors.append(f"Item {index + 1} {key} is missing.")
            elif len(value.split()) > limit:
                errors.append(f"Item {index + 1} {key} exceeds its word limit.")
            all_texts.append(value)
            item_texts.append(value)
            if key == "story" and value:
                story_texts.append(value)
        move = " ".join(str(item.get("your_move") or "").split())
        if move:
            first = re.sub(r"[^a-z]", "", move.split()[0].lower())
            if first not in _IMPERATIVES:
                errors.append(f"Item {index + 1} your_move is not clearly imperative.")
        story_value = " ".join(str(item.get("story") or "").split())
        if _SECTION_LABEL.search(story_value):
            errors.append(f"Item {index + 1} story contains a reserved section label.")
        if move and _contains_move(story_value, move):
            errors.append(f"Item {index + 1} story repeats its dedicated your_move field.")
        supplied_item_text = json.dumps(
            {
                "shared_context": shared_context,
                "item": supplied_by_id.get(str(item.get("source_id") or ""), {}),
            },
            ensure_ascii=False,
            default=str,
        )
        item_combined = "\n".join(item_texts)
        for planet in sorted(_PLANETS):
            if re.search(rf"\b{re.escape(planet)}\b", item_combined, flags=re.IGNORECASE) and not re.search(
                rf"\b{re.escape(planet)}\b", supplied_item_text, flags=re.IGNORECASE
            ):
                errors.append(f"Item {index + 1} invented an unsupplied planet: {planet}.")
        supplied_item_numbers = set(re.findall(r"\b\d+(?:\.\d+)?(?::\d+)?\b", supplied_item_text))
        item_numbers = set(re.findall(r"\b\d+(?:\.\d+)?(?::\d+)?\b", item_combined))
        item_invented = sorted(item_numbers - supplied_item_numbers)
        if item_invented:
            errors.append(
                f"Item {index + 1} invented numeric evidence: " + ", ".join(item_invented) + "."
            )

    combined = "\n".join(all_texts)
    if "?" in combined:
        errors.append("Luna collection copy must not ask the reader a question.")
    for phrase in _PROHIBITED:
        if phrase in combined.lower():
            errors.append(f"Prohibited certainty claim: {phrase}.")
    if _has_unnegated_guarantee(combined):
        errors.append("Prohibited certainty claim: guarantee.")
    for planet in sorted(_PLANETS):
        if re.search(rf"\b{re.escape(planet)}\b", combined, flags=re.IGNORECASE) and not re.search(
            rf"\b{re.escape(planet)}\b", facts_text, flags=re.IGNORECASE
        ):
            errors.append(f"The response invented an unsupplied planet: {planet}.")
    output_numbers = set(re.findall(r"\b\d+(?:\.\d+)?(?::\d+)?\b", combined))
    invented = sorted(output_numbers - supplied_numbers)
    if invented:
        errors.append("The response invented numeric evidence: " + ", ".join(invented) + ".")

    normalized_stories = [
        re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
        for value in story_texts
        if value
    ]
    if len(normalized_stories) != len(set(normalized_stories)):
        errors.append("The response duplicates a complete collection story.")
    return not errors, tuple(dict.fromkeys(errors))


def _generate_guided_collection_batch(
    product: str,
    facts: dict[str, Any],
    *,
    base_url: str,
    model: str,
    api_key: str,
) -> dict[str, Any]:
    """Generate and validate one collection batch."""
    prompt = build_guided_collection_prompt(product, facts)
    item_count = max(1, len(list(facts.get("items") or [])))
    # GPT-OSS spends part of the completion allowance on reasoning. Reserve
    # enough room for the complete JSON even when a batch contains one item.
    output_budget = min(4200, 1800 + item_count * 600)
    errors: tuple[str, ...] = ()
    for attempt in range(2):
        copy = generate_openai_compatible_json(
            prompt,
            base_url=base_url,
            model=model,
            api_key=api_key,
            max_tokens=output_budget,
            response_format=_guided_collection_response_format(product, facts),
        )
        valid, errors = validate_guided_collection_copy(product, copy, facts)
        if valid:
            return copy
        if attempt == 0:
            prompt += (
                "\n\nCORRECTION REPORT: The previous collection was rejected. Return a complete replacement and fix: "
                + " | ".join(errors)
            )
    raise ValueError("Guided Luna collection failed validation: " + " | ".join(errors))


def _collection_subset_facts(
    facts: dict[str, Any],
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    subset = {key: value for key, value in facts.items() if key != "items"}
    subset["items"] = items
    return subset


def _is_payload_too_large(error: Exception) -> bool:
    message = str(error).lower()
    return "413" in message or "payload too large" in message or "request too large" in message


def _generate_collection_partition(
    product: str,
    facts: dict[str, Any],
    *,
    base_url: str,
    model: str,
    api_key: str,
) -> list[dict[str, Any]]:
    """Generate one small partition and split again on 413 or validation failure."""
    try:
        generated = _generate_guided_collection_batch(
            product,
            facts,
            base_url=base_url,
            model=model,
            api_key=api_key,
        )
        return list(generated["items"])
    except (ValueError, VoiceProviderError) as batch_error:
        supplied_items = list(facts.get("items") or [])
        if len(supplied_items) <= 1:
            raise
        if isinstance(batch_error, VoiceProviderError) and not _is_payload_too_large(batch_error):
            raise
        midpoint = max(1, len(supplied_items) // 2)
        recovered: list[dict[str, Any]] = []
        for partition in (supplied_items[:midpoint], supplied_items[midpoint:]):
            recovered.extend(
                _generate_collection_partition(
                    product,
                    _collection_subset_facts(facts, partition),
                    base_url=base_url,
                    model=model,
                    api_key=api_key,
                )
            )
        return recovered


def generate_guided_collection_copy(
    product: str,
    facts: dict[str, Any],
    *,
    base_url: str,
    model: str,
    api_key: str,
) -> dict[str, Any]:
    """Generate bounded collection requests, then restore the original order and lock."""
    supplied_items = list(facts.get("items") or [])
    if not supplied_items:
        raise ValueError("Guided Luna collection contains no calculated items.")

    # Three items keeps input + reserved output safely below Groq's request cap.
    recovered_items: list[dict[str, Any]] = []
    for start in range(0, len(supplied_items), 3):
        partition = supplied_items[start:start + 3]
        recovered_items.extend(
            _generate_collection_partition(
                product,
                _collection_subset_facts(facts, partition),
                base_url=base_url,
                model=model,
                api_key=api_key,
            )
        )

    recovered_copy = {
        "items": recovered_items,
        "facts_hash": collection_facts_hash(product, facts),
    }
    valid, errors = validate_guided_collection_copy(product, recovered_copy, facts)
    if not valid:
        raise ValueError(
            "Guided Luna recombined collection failed validation: " + " | ".join(errors)
        )
    return recovered_copy
