from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable

from luna_voice_provider import VoiceProviderError, generate_openai_compatible_json


class BirthdayPoemError(RuntimeError):
    pass


def _position_map(snapshot: Any) -> dict[str, Any]:
    return {item.planet: item for item in snapshot.positions}


def _safe_signs(snapshot: Any, planet: str) -> list[str]:
    uncertain = tuple(getattr(snapshot, f"{planet.lower()}_uncertain", ()) or ())
    if not snapshot.birth_time_known and uncertain:
        return list(dict.fromkeys(uncertain))
    return [_position_map(snapshot)[planet].sign]


def _aspect_rank(item: Any) -> tuple[float, float]:
    return (-float(getattr(item, "strength", 0.0)), float(getattr(item, "orb", 99.0)))


def build_birthday_poem_facts(
    *,
    snapshot: Any,
    variation_key: str,
) -> dict[str, Any]:
    """Expose only calculated facts the Birthday Card voice may interpret."""
    variation = re.sub(r"[^a-zA-Z0-9_-]+", "", str(variation_key or ""))[:32]
    if not variation:
        raise BirthdayPoemError("A non-personal variation key is required.")

    by_planet = _position_map(snapshot)
    facts: dict[str, Any] = {
        "product": "birthday_card_micro_poem",
        "variation_key": variation,
        "birth_time_known": bool(snapshot.birth_time_known),
        "sun_sign_options": _safe_signs(snapshot, "Sun"),
        "moon_sign_options": _safe_signs(snapshot, "Moon"),
    }

    if snapshot.birth_time_known:
        facts["exact_positions"] = {
            "Sun": {
                "sign": by_planet["Sun"].sign,
                "degree": round(float(by_planet["Sun"].degree), 2),
            },
            "Moon": {
                "sign": by_planet["Moon"].sign,
                "degree": round(float(by_planet["Moon"].degree), 2),
            },
        }
        relevant = [
            item
            for item in getattr(snapshot, "aspects", ())
            if "Sun" in {item.planet1, item.planet2} or "Moon" in {item.planet1, item.planet2}
        ]
        facts["strongest_luminary_aspects"] = [
            {
                "planet1": item.planet1,
                "aspect": item.name,
                "planet2": item.planet2,
                "orb": round(float(item.orb), 2),
            }
            for item in sorted(relevant, key=_aspect_rank)[:3]
        ]
    else:
        # Noon positions and exact aspects are not treated as birth facts when
        # the time is unknown. The voice receives only placements that remain
        # safe across the recipient's local calendar date.
        facts["exact_positions"] = None
        facts["strongest_luminary_aspects"] = []
    return facts


def facts_hash(facts: dict[str, Any]) -> str:
    canonical = json.dumps(facts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _prompt(facts: dict[str, Any]) -> str:
    fingerprint = facts_hash(facts)
    return f"""Write one original micro-poem for a Luna Birthday Sky Card.

CALCULATED FACTS - authoritative; never recalculate or contradict them:
{json.dumps(facts, ensure_ascii=False, sort_keys=True, indent=2)}

Return exactly one JSON object:
{{
  "facts_hash": "{fingerprint}",
  "sun_evidence": {json.dumps(facts['sun_sign_options'], ensure_ascii=False)},
  "moon_evidence": {json.dumps(facts['moon_sign_options'], ensure_ascii=False)},
  "poem": "..."
}}

POEM CONTRACT:
- One sentence of 10 to 18 words, ending with a period.
- Use this sentence architecture, not these words: [concrete subject] only [active verb] [abstract possibility] [movement toward emergence].
- Translate the supplied Sun into identity/direction and the supplied Moon into emotional need/instinct.
- When exact luminary aspects are supplied, let the strongest relevant aspect refine the connection.
- When either sign has two options, do not choose between them; use imagery valid for both.
- Use concrete imagery and elegant plain English.
- Do not name planets, signs, astrology, the recipient, the birth date or birth year.
- Do not predict an event, promise an outcome, use a quotation, or add a second sentence.
- Do not reuse a stock horoscope line. The poem must be newly written from this evidence packet.
- Use variation_key only to vary wording; it is not astrology evidence and must never appear in the poem.
- The evidence arrays and facts_hash must be copied exactly from the supplied values.
"""


def validate_birthday_poem(payload: dict[str, Any], facts: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        raise BirthdayPoemError("Birthday voice response must be one JSON object.")
    if str(payload.get("facts_hash", "")) != facts_hash(facts):
        raise BirthdayPoemError("Birthday voice response did not preserve the facts hash.")
    if payload.get("sun_evidence") != facts["sun_sign_options"]:
        raise BirthdayPoemError("Birthday voice response changed the Sun evidence.")
    if payload.get("moon_evidence") != facts["moon_sign_options"]:
        raise BirthdayPoemError("Birthday voice response changed the Moon evidence.")

    poem = " ".join(str(payload.get("poem", "") or "").split()).strip()
    words = re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)?", poem)
    if not 10 <= len(words) <= 18:
        raise BirthdayPoemError("Birthday poem must contain 10 to 18 words.")
    if not poem.endswith(".") or any(mark in poem[:-1] for mark in ".!?;:\n"):
        raise BirthdayPoemError("Birthday poem must be exactly one sentence ending with a period.")
    if " only " not in poem.lower():
        raise BirthdayPoemError("Birthday poem did not follow Luna's approved sentence architecture.")

    forbidden = {
        "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
        "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        "sun", "moon", "planet", "astrology", "zodiac", "horoscope",
        "guarantee", "destiny", "fated",
    }
    lowered_words = {word.lower().replace("’", "'") for word in words}
    if forbidden & lowered_words:
        raise BirthdayPoemError("Birthday poem exposed astrology jargon or an unsupported promise.")
    if str(facts["variation_key"]).lower() in poem.lower():
        raise BirthdayPoemError("Birthday poem exposed an internal variation key.")
    return poem


def generate_birthday_poem(
    facts: dict[str, Any],
    *,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    generate_json: Callable[..., dict[str, Any]] = generate_openai_compatible_json,
) -> str:
    prompt = _prompt(facts)
    last_validation_error: BirthdayPoemError | None = None
    for attempt in range(2):
        try:
            payload = generate_json(
                prompt,
                base_url=base_url,
                model=model,
                api_key=api_key,
                timeout=90,
                max_tokens=420,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "luna_birthday_poem",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["facts_hash", "sun_evidence", "moon_evidence", "poem"],
                            "properties": {
                                "facts_hash": {"type": "string"},
                                "sun_evidence": {"type": "array", "items": {"type": "string"}},
                                "moon_evidence": {"type": "array", "items": {"type": "string"}},
                                "poem": {"type": "string"},
                            },
                        },
                    },
                },
                rate_limit_retries=2,
            )
        except VoiceProviderError as exc:
            raise BirthdayPoemError(str(exc)) from exc
        try:
            return validate_birthday_poem(payload, facts)
        except BirthdayPoemError as exc:
            last_validation_error = exc
            if attempt == 0:
                prompt += (
                    "\nThe previous response failed validation: "
                    f"{exc} Return a corrected JSON object now."
                )
    raise last_validation_error or BirthdayPoemError("Birthday poem validation failed.")
