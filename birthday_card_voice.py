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
    poetry_style: str = "Homeric Epic",
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
        "poetry_style": poetry_style,
        "sun_sign_options": _safe_signs(snapshot, "Sun"),
        "moon_sign_options": _safe_signs(snapshot, "Moon"),
    }

    if snapshot.birth_time_known:
        ranked = sorted(getattr(snapshot, "aspects", ()), key=_aspect_rank)
        if ranked:
            best = ranked[0]
            facts["dominant_verified_strength"] = {
                "planet1": best.planet1, "aspect": best.name,
                "planet2": best.planet2, "orb": round(float(best.orb), 2),
            }
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

POEM VOICE AND STRUCTURE:
- Write exactly THREE short stanzas separated by blank lines, with a maximum of THIRTY words across all stanzas.
- Use mature, unrhymed free verse. Never use childish rhymes, sing-song metre, or forced end-rhyme.
- Match the chosen poetry_style: Homeric Epic (heroic mythic imagery), Shakespearean (elegant lyrical prose without rhyme), Ancient Oracle (spare enigmatic symbolism), or Modern Celebration (restrained warm contemporary language).
- Centre the imagery on the dominant_verified_strength if supplied; never invent an aspect.
- Begin with a concrete image drawn from the meaning of the calculated sky.
- Turn that image inward: the outer image should reveal something about identity, instinct, desire, tension, growth, or possibility.
- Let the final line create movement, release, emergence, recognition, or unresolved possibility.
- Prefer image and implication over explanation.
- Keep the language simple, vivid and emotionally resonant.
- Vary the syntax, verbs, nouns, imagery and line structure between generations.
- Do not imitate or reproduce any existing poem.
- Use the general poetic movement: outer or cosmic image -> inner human meaning -> final movement.

ASTROLOGICAL GROUNDING:
- The supplied calculated facts are authoritative. Never recalculate or contradict them.
- Translate the supplied Sun into identity, vitality or direction.
- Translate the supplied Moon into emotional need, instinct or inner response.
- When exact luminary aspects are supplied, let the strongest relevant aspect alter the imagery, tension or resolution.
- When either sign has two options, do not choose between them; use imagery compatible with both.
- The astrology must determine the poem's meaning, but the finished poem must not explain the astrology.
- Do not name planets, signs, astrology, zodiac, horoscope, the recipient, the birth date or birth year.
- Do not predict an event, promise an outcome, or use a quotation.
- Do not reuse a stock horoscope line. The poem must be newly written from this evidence packet.
- Use variation_key only to vary wording, imagery and cadence; it is not astrology evidence and must never appear in the poem.
- The evidence arrays and facts_hash must be copied exactly from the supplied values.
"""


def validate_birthday_poem(payload: dict[str, Any], facts: dict[str, Any]) -> str:
    """Structural response extraction only; never judge or rewrite returned prose."""
    if not isinstance(payload, dict):
        raise BirthdayPoemError("Provider did not return a JSON object.")
    poem = payload.get("poem")
    if not isinstance(poem, str) or not poem.strip():
        raise BirthdayPoemError("Provider returned no poem text.")
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
            rate_limit_retries=0,
        )
    except VoiceProviderError as exc:
        raise BirthdayPoemError(str(exc)) from exc
    return validate_birthday_poem(payload, facts)
