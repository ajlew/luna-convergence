from __future__ import annotations

"""Single-call Luna voice for the paid Year Ahead.

Architecture:
    one deterministic YearPacket
        -> one plain-prose provider call
        -> Read the Year

This module does not calculate astrology, choose transits, rank arcs, create
Games, validate a JSON schema, or retry the model. Python owns the facts.
"""

import json
import re
from typing import Any

import requests

from year_ahead import YearPacket


YEAR_AHEAD_VOICE_VERSION = "1.0"
DEFAULT_MAX_COMPLETION_TOKENS = 2800
DEFAULT_TIMEOUT_SECONDS = 150
TARGET_TOTAL_TOKENS = 7200
MIN_COMPLETION_TOKENS = 1700


SYSTEM_PROMPT = (
    "You are Luna, the narrative voice of Luna Convergence. "
    "Write the reader's Year Ahead from the supplied calculated astrology only. "
    "Return plain prose only. Python owns all dates, transits, pass labels, houses, "
    "rankings, Games and chronology. Do not invent or recalculate astrology."
)


VOICE_RULES = """Write one connected strategic story in second person.

Rules:
- Keep the reader at the centre of the story.
- Preserve the supplied chronology from the beginning of the year window to the end.
- Use only the astrology and deterministic interpretation supplied below.
- Treat each Game as part of one unfolding year, not as an isolated horoscope entry.
- Show where pressure develops, where opportunity opens, where a retrograde return
  revisits the issue, and where a final pass or later phase brings resolution when
  those features are actually present in the calculations.
- Distinguish a main transit from supporting transits and short-lived triggers without
  turning the reading into a technical list.
- Translate astrology into real decisions, relationships, work, money, home, identity,
  responsibility, opportunity and timing where the supplied life areas support it.
- Advice should improve the reader's position: preserve useful options, make costs,
  information, reciprocity, responsibility or commitment visible before committing more,
  and avoid unnecessary direct conflict when a better route exists.
- Avoid fatalism. Describe conditions, choices, leverage, risk and timing rather than
  claiming that an event must happen.
- Do not give transit-by-transit textbook definitions.
- Do not repeat the same month or date simply because several calculations touch it.
- Do not invent houses when the supplied natal fingerprint does not support houses.
- Do not invent missing birth-time precision.
- Do not invent extra transits, dates, pass numbers, trigger dates or planetary positions.
- Do not mention internal implementation words such as packet, cluster, evidence row,
  engine, score, JSON, schema, prompt, model or calculation pipeline.
- Do not describe the mechanics of how the reading was generated.
- Do not output JSON, YAML, bullet-point data dumps, tables or code.
- Do not add a disclaimer about being an AI.

Shape the prose as a substantial magazine-style Year Ahead reading:
1. Open with the strategic shape of the year and the reader's underlying natal tone.
2. Move through the Games in chronological order.
3. Let repeated passes feel like one developing storyline: activation, return, resolution.
4. Bring supporting triggers into the relevant part of the story only when useful.
5. End with what the reader should understand, protect, pursue or stop carrying by the
   end of the period.

Use clear paragraphs. Headings are optional, but if used they must be natural reader-facing
headings, not technical labels. Do not create sections that rewind the chronology.
"""


def _packet_dict(packet: YearPacket | dict[str, Any]) -> dict[str, Any]:
    if isinstance(packet, dict):
        value = dict(packet)
    elif hasattr(packet, "to_dict"):
        value = dict(packet.to_dict())
    else:
        raise TypeError("Year Ahead voice requires a YearPacket or dictionary.")

    period = value.get("period")
    games = value.get("games")
    fingerprint = value.get("natal_fingerprint")
    if not isinstance(period, dict):
        raise ValueError("Year Ahead packet is missing its period.")
    if not isinstance(fingerprint, dict):
        raise ValueError("Year Ahead packet is missing its natal fingerprint.")
    if not isinstance(games, list):
        raise ValueError("Year Ahead packet is missing its chronological Games.")
    return value


def _voice_story(value: dict[str, Any]) -> dict[str, Any]:
    """Strip ranking/provenance internals before the creative call."""
    passes = []
    for item in list(value.get("passes") or []):
        if not isinstance(item, dict):
            continue
        passes.append(
            {
                key: item.get(key)
                for key in (
                    "pass_number",
                    "pass_label",
                    "date",
                    "time",
                    "retrograde",
                    "orb",
                )
            }
        )

    triggers = []
    for item in list(value.get("triggers") or []):
        if not isinstance(item, dict):
            continue
        triggers.append(
            {
                key: item.get(key)
                for key in (
                    "planet",
                    "aspect",
                    "natal_target",
                    "date",
                    "time",
                    "retrograde",
                    "orb",
                    "activates_pass_number",
                    "activation_label",
                )
            }
        )

    return {
        "technical_label": value.get("technical_label"),
        "natal_house": value.get("natal_house"),
        "start": value.get("start"),
        "end": value.get("end"),
        "passes": passes,
        "triggers": triggers,
        "summary": value.get("summary"),
        "move": value.get("move"),
        "watch": value.get("watch"),
    }


def _voice_game(value: dict[str, Any]) -> dict[str, Any]:
    primary = value.get("primary_transit")
    supporting = value.get("supporting_transits")
    return {
        key: value.get(key)
        for key in (
            "number",
            "title",
            "strategic_frame",
            "question",
            "start_date",
            "end_date",
            "human_life_area",
            "polarity",
            "advantage",
            "risk",
            "move",
            "dont",
        )
    } | {
        "primary_transit": _voice_story(primary) if isinstance(primary, dict) else {},
        "supporting_transits": [
            _voice_story(item)
            for item in list(supporting or [])
            if isinstance(item, dict)
        ],
    }


def _voice_source(packet: YearPacket | dict[str, Any]) -> dict[str, Any]:
    """Keep the one voice call compact, chronological and reader-facing."""
    value = _packet_dict(packet)
    return {
        "period": value.get("period") or {},
        "natal_fingerprint": value.get("natal_fingerprint") or {},
        "year_statistics": value.get("year_statistics") or {},
        "year_strip": value.get("year_strip") or [],
        "games": [
            _voice_game(item)
            for item in list(value.get("games") or [])
            if isinstance(item, dict)
        ],
    }


def build_year_ahead_prompt(packet: YearPacket | dict[str, Any]) -> str:
    source = _voice_source(packet)
    facts_json = json.dumps(
        source,
        ensure_ascii=False,
        sort_keys=False,
        separators=(",", ":"),
        default=str,
    )
    return (
        "WRITE THE READER'S YEAR AHEAD\n\n"
        + VOICE_RULES.strip()
        + "\n\nCALCULATED YEAR MATERIAL\n"
        + facts_json
        + "\n\nReturn only the finished reader-facing prose."
    )


def _estimated_input_tokens(system_prompt: str, user_prompt: str) -> int:
    """Conservative pre-provider estimate without adding a tokenizer dependency."""
    characters = len(str(system_prompt or "")) + len(str(user_prompt or ""))
    # ~4 characters/token is a common English approximation. Add a fixed
    # message-envelope buffer so the Year Ahead never relies on the estimate
    # being exact.
    return max(1, (characters + 3) // 4) + 350


def _prepare_request(
    packet: YearPacket | dict[str, Any],
    preferred_completion_tokens: int = DEFAULT_MAX_COMPLETION_TOKENS,
) -> tuple[str, int, int]:
    """Size the single request before any provider call is made.

    The YearPacket is already compact and selected by Python. This final
    preflight protects the one-call architecture from an oversized request by
    reducing only the completion allowance. It never retries and never drops
    calculated Games, passes or dates.
    """
    prompt = build_year_ahead_prompt(packet)
    estimated_input = _estimated_input_tokens(SYSTEM_PROMPT, prompt)

    available = TARGET_TOTAL_TOKENS - estimated_input
    completion_tokens = min(int(preferred_completion_tokens), available)

    if completion_tokens < MIN_COMPLETION_TOKENS:
        raise RuntimeError(
            "Year Ahead voice preflight could not fit the finished Year Packet "
            "inside the configured single-call token budget."
        )

    return prompt, completion_tokens, estimated_input


def _clean_plain_prose(value: Any) -> str:
    """Transport cleanup only; do not editorially re-write the provider response."""
    text = str(value or "").strip()
    if not text:
        return ""

    text = re.sub(r"^\s*```(?:text|markdown|md)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```\s*$", "", text)

    paragraphs = []
    for part in re.split(r"\n\s*\n+", text):
        clean = re.sub(r"[ \t]+", " ", part).strip()
        if clean:
            paragraphs.append(clean)
    return "\n\n".join(paragraphs)


def generate_year_ahead_voice(
    packet: YearPacket | dict[str, Any],
    *,
    base_url: str,
    model: str,
    api_key: str,
    max_completion_tokens: int = DEFAULT_MAX_COMPLETION_TOKENS,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """Make exactly one provider call and return plain prose.

    There is deliberately:
    - no JSON response schema;
    - no multi-call chapter generation;
    - no automatic retry;
    - no post-generation content gate.

    The caller may render the deterministic Year Ahead whether this succeeds or not.
    """
    base_url = str(base_url or "").strip()
    model = str(model or "").strip()
    api_key = str(api_key or "").strip()

    if not base_url:
        raise ValueError("Year Ahead voice base URL is not configured.")
    if not model:
        raise ValueError("Year Ahead voice model is not configured.")
    if not api_key:
        raise ValueError("Year Ahead voice API key is not configured.")

    prompt, completion_tokens, _estimated_input = _prepare_request(
        packet,
        preferred_completion_tokens=max_completion_tokens,
    )
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.58,
        "max_completion_tokens": int(completion_tokens),
    }

    if model.startswith("openai/gpt-oss"):
        payload["reasoning_effort"] = "low"
        payload["include_reasoning"] = False

    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=int(timeout),
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Year Ahead voice provider request failed: {exc}") from exc

    if response.status_code >= 400:
        body = " ".join(str(response.text or "").split())[:500]
        raise RuntimeError(
            f"Year Ahead voice provider HTTP {response.status_code}: {body}"
        )

    try:
        choice = response.json()["choices"][0]
        body = choice["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError("Year Ahead voice provider returned no usable prose.") from exc

    if str(choice.get("finish_reason") or "") == "length":
        raise RuntimeError(
            "Year Ahead voice provider truncated the reading at the completion limit."
        )

    clean = _clean_plain_prose(body)
    if not clean:
        raise RuntimeError("Year Ahead voice provider returned an empty reading.")
    return clean
