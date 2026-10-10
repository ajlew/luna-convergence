from __future__ import annotations

"""Luna Paid Yearly editorial engine.

Fresh implementation for the paid Year Ahead only.

The deterministic YearPacket remains the authority for astrology. This module
turns that finished packet into one substantial paid reading in ONE provider
call. The model does not calculate, select, rank, date, group or correct
astrology.

Response format is plain text with simple internal section markers so a single
call can supply:
- the paid editorial headline;
- the short deck beneath it;
- one long chronological "Read the year" article;
- a substantial interpretation for every selected major annual issue;
- a short closing synthesis.

No JSON response format. No schema. No automatic retry.
"""

from dataclasses import dataclass
import json
import math
import re
from typing import Any

import requests

from year_ahead import YearPacket


PAID_YEARLY_EDITORIAL_VERSION = "1.0"
DEFAULT_TIMEOUT_SECONDS = 180
TARGET_TOTAL_TOKENS = 14500
PREFERRED_COMPLETION_TOKENS = 7600
MIN_COMPLETION_TOKENS = 5600

_MARKER_RE = re.compile(
    r"(?m)^<<(?P<name>HEADLINE|DECK|READ_YEAR|CLOSING|ISSUE:\d+)>>\s*$"
)


@dataclass(frozen=True)
class PaidYearlyIssue:
    number: int
    paragraphs: tuple[str, ...]


@dataclass(frozen=True)
class PaidYearlyEditorial:
    headline: str
    deck: str
    read_year: tuple[str, ...]
    issues: tuple[PaidYearlyIssue, ...]
    closing: tuple[str, ...]
    word_count: int
    voice_complete: bool = True

    def issue_for(self, number: int) -> PaidYearlyIssue | None:
        for issue in self.issues:
            if issue.number == int(number):
                return issue
        return None


SYSTEM_PROMPT = (
    "You are Luna, the editorial voice of a paid personal astrology report. "
    "Python has already calculated and selected the astrology. Interpret only "
    "the supplied natal and transit facts. Never calculate, infer, rank, group, "
    "correct or invent astrology."
)


def _packet_dict(packet: YearPacket | dict[str, Any]) -> dict[str, Any]:
    value = dict(packet) if isinstance(packet, dict) else packet.to_dict()
    if not isinstance(value.get("period"), dict):
        raise ValueError("Paid Yearly requires a finished YearPacket period.")
    if not isinstance(value.get("games"), list):
        raise ValueError("Paid Yearly requires selected annual issues.")
    return value


def _snapshot_material(snapshot: Any | None, packet: dict[str, Any]) -> dict[str, Any]:
    """Build the same kind of natal baseline Paid Monthly puts before the story."""
    if snapshot is None:
        return dict(packet.get("natal_fingerprint") or {})

    by_planet: dict[str, dict[str, Any]] = {}
    for item in list(getattr(snapshot, "positions", ()) or ()):
        planet = str(getattr(item, "planet", "") or "")
        if not planet:
            continue
        by_planet[planet] = {
            "sign": str(getattr(item, "sign", "") or ""),
            "degree": round(float(getattr(item, "degree", 0.0) or 0.0), 2),
            "house": getattr(item, "house", None),
        }

    strengths = []
    for item in list(getattr(snapshot, "signatures", ()) or ())[:6]:
        strengths.append(
            {
                "title": str(getattr(item, "title", "") or ""),
                "interpretation": str(getattr(item, "text", "") or ""),
                "strength": str(getattr(item, "strength", "") or ""),
                "watch": str(getattr(item, "watch", "") or ""),
                "question": str(getattr(item, "question", "") or ""),
                "evidence": str(getattr(item, "evidence", "") or ""),
            }
        )

    return {
        "birth_time_known": bool(getattr(snapshot, "birth_time_known", False)),
        "core": {
            planet: by_planet.get(planet)
            for planet in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")
            if by_planet.get(planet)
        },
        "ascendant": (
            {
                "sign": str(getattr(snapshot.ascendant, "sign", "") or ""),
                "degree": round(float(getattr(snapshot.ascendant, "degree", 0.0) or 0.0), 2),
            }
            if getattr(snapshot, "ascendant", None) is not None
            else None
        ),
        "midheaven": (
            {
                "sign": str(getattr(snapshot.midheaven, "sign", "") or ""),
                "degree": round(float(getattr(snapshot.midheaven, "degree", 0.0) or 0.0), 2),
            }
            if getattr(snapshot, "midheaven", None) is not None
            else None
        ),
        "dominant_element": str(getattr(snapshot, "dominant_element", "") or ""),
        "dominant_modality": str(getattr(snapshot, "dominant_modality", "") or ""),
        "strengths": strengths,
    }


def _pass_material(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "pass_number": int(row.get("pass_number") or 1),
        "pass_label": str(row.get("pass_label") or ""),
        "date": str(row.get("date") or ""),
        "time": str(row.get("time") or ""),
        "retrograde": bool(row.get("retrograde")),
        "orb": row.get("orb"),
    }


def _trigger_material(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "planet": str(row.get("planet") or ""),
        "aspect": str(row.get("aspect") or ""),
        "target": str(row.get("natal_target") or ""),
        "date": str(row.get("date") or ""),
        "time": str(row.get("time") or ""),
        "retrograde": bool(row.get("retrograde")),
        "orb": row.get("orb"),
        "activates_pass_number": row.get("activates_pass_number"),
        "label": str(row.get("activation_label") or row.get("technical_label") or ""),
    }


def _transit_material(story: dict[str, Any]) -> dict[str, Any]:
    return {
        "technical": str(story.get("technical_label") or ""),
        "active_start": str(story.get("start") or ""),
        "active_end": str(story.get("end") or ""),
        "house": story.get("natal_house"),
        "summary": str(story.get("summary") or ""),
        "move": str(story.get("move") or ""),
        "watch": str(story.get("watch") or ""),
        "passes": [
            _pass_material(row)
            for row in list(story.get("passes") or [])
            if isinstance(row, dict)
        ],
        "triggers": [
            _trigger_material(row)
            for row in list(story.get("triggers") or [])
            if isinstance(row, dict)
        ],
    }


def _issue_material(game: dict[str, Any]) -> dict[str, Any]:
    primary = game.get("primary_transit")
    supporting = game.get("supporting_transits")
    return {
        "number": int(game.get("number") or 0),
        "customer_title": str(game.get("title") or ""),
        "strategic_frame": str(game.get("strategic_frame") or ""),
        "life_area": str(game.get("human_life_area") or ""),
        "polarity": str(game.get("polarity") or ""),
        "start": str(game.get("start_date") or ""),
        "end": str(game.get("end_date") or ""),
        "question": str(game.get("question") or ""),
        "advantage": str(game.get("advantage") or ""),
        "risk": str(game.get("risk") or ""),
        "move": str(game.get("move") or ""),
        "dont": str(game.get("dont") or ""),
        "primary": _transit_material(primary) if isinstance(primary, dict) else {},
        "supporting": [
            _transit_material(row)
            for row in list(supporting or [])
            if isinstance(row, dict)
        ],
    }


def build_paid_yearly_material(
    packet: YearPacket | dict[str, Any],
    *,
    snapshot: Any | None = None,
    main_focus: str = "",
    personal_question: str = "",
) -> dict[str, Any]:
    value = _packet_dict(packet)
    year_strip = []
    for row in list(value.get("year_strip") or []):
        if not isinstance(row, dict):
            continue
        year_strip.append(
            {
                "month": str(row.get("month") or ""),
                "phase": str(row.get("phase") or "QUIET"),
                "intensity": round(float(row.get("intensity") or 0.0), 3),
            }
        )

    return {
        "period": dict(value.get("period") or {}),
        "reader_context": {
            "main_focus": str(main_focus or "General overview"),
            "personal_question": str(personal_question or "").strip(),
        },
        "natal": _snapshot_material(snapshot, value),
        "year_statistics": dict(value.get("year_statistics") or {}),
        "year_strip": year_strip,
        "major_issues": [
            _issue_material(game)
            for game in list(value.get("games") or [])
            if isinstance(game, dict)
        ],
    }


def build_paid_yearly_prompt(material: dict[str, Any]) -> str:
    issues = list(material.get("major_issues") or [])
    issue_markers = "\n".join(
        f"<<ISSUE:{int(item.get('number') or index)}>>"
        for index, item in enumerate(issues, start=1)
    )

    return (
        "Write Luna's PAID PERSONAL YEAR AHEAD. This is a finished paid report, "
        "not a preview, dashboard summary or list of transit definitions.\n\n"

        "EDITORIAL MODEL: follow the same logic as Luna's Paid Monthly. The "
        "person comes first, then one continuous chronological reading. The "
        "annual version must feel substantially deeper because it covers a full "
        "rolling year. Give the customer a strong editorial headline and a short "
        "deck, then a long Read the Year article, then a substantial chapter for "
        "each supplied major annual issue.\n\n"

        "DEPTH BENCHMARK: serious annual transit reports spend several paragraphs "
        "on important long-running transits. Match that usefulness and seriousness "
        "without copying any outside wording. For each annual issue explain the "
        "human situation, ordinary-life manifestations, opportunity, pressure, "
        "risk, trade-off, useful action, and how repeated passes change the story "
        "over time. Do not reduce an issue to a one-paragraph card.\n\n"

        "NATAL BASELINE: use natal.core and natal.strengths the way Paid Monthly "
        "uses the Natal Player: as the person's baseline. Use it to explain why "
        "the same transit may matter differently to this person. Do not pad the "
        "forecast with generic personality description. If birth_time_known is "
        "false, never imply an Ascendant, Midheaven or house not explicitly supplied.\n\n"

        "ONE CHRONOLOGY: the major issues are already selected and ordered by "
        "Python. Move through the year once from start to finish. A direct hit, "
        "retrograde return and final pass are stages of ONE story. Explain how "
        "the question changes from first contact to return to resolution. Fast "
        "Sun/Mercury/Venus/Mars triggers are supporting dates only; mention them "
        "when they sharpen an already-active major issue.\n\n"

        "DATE LOCK: Python owns every date, pass number, motion state, aspect, "
        "planet, natal target and house. If you name one, copy it exactly. Never "
        "invent a transit, exact date, house, return, station or placement. Never "
        "turn an active window into a new exact event.\n\n"

        "READER CONTEXT: the customer's priority/question may influence emphasis "
        "only when the supplied astrology supports it. Do not force the year to "
        "answer a question the calculations do not support.\n\n"

        "VOICE: direct second person throughout: you, your, yours. Strategic, "
        "adult, specific and grounded. Preserve choice and agency. Avoid fate, "
        "therapy-speak, manifestation claims, guaranteed outcomes and mystical "
        "padding. Translate astrology into real decisions, relationships, work, "
        "money, commitments, information, timing, pressure, openings and limits "
        "where the supplied life area supports those themes.\n\n"

        "CONTENT SIZE:\n"
        "- READ_YEAR: roughly 1,600-2,000 words in 10-14 substantial paragraphs.\n"
        "- EACH ISSUE: roughly 450-650 words in 3-5 substantial paragraphs.\n"
        "- CLOSING: 2 concise paragraphs, roughly 180-260 words total.\n"
        "- Total target: approximately 3,800-5,000 words depending on number of issues.\n\n"

        "OUTPUT FORMAT: return PLAIN TEXT ONLY using the exact internal markers "
        "below on their own lines. Do not use Markdown headings, bullets, JSON or "
        "code fences. The markers are parsing boundaries and will not be shown "
        "to the customer.\n\n"
        "<<HEADLINE>>\n"
        "One strong editorial headline, 8-18 words. Human, specific, not technical.\n"
        "<<DECK>>\n"
        "One or two sentences that state the strategic shape of this rolling year.\n"
        "<<READ_YEAR>>\n"
        "The long continuous annual reading.\n"
        f"{issue_markers}\n"
        "For each ISSUE marker, write the substantial interpretation of that "
        "numbered supplied issue in chronological context. Do not repeat the "
        "customer title as a heading; the interface supplies it.\n"
        "<<CLOSING>>\n"
        "Two final synthesis paragraphs: what to protect, what to pursue, what "
        "to stop carrying, and what the year ultimately asks the person to understand.\n\n"

        "Before returning, silently proofread chronology, exact dates, natal "
        "placements and repeated claims.\n\n"
        "CALCULATED YEAR:\n"
        + json.dumps(material, ensure_ascii=False, separators=(",", ":"), default=str)
    )


def _estimate_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(str(text or "")))
    except Exception:
        return max(1, math.ceil(len(str(text or "")) / 4.0))


def _prepare_request(material: dict[str, Any]) -> tuple[str, int, int]:
    prompt = build_paid_yearly_prompt(material)
    estimated_input = math.ceil(
        (_estimate_tokens(SYSTEM_PROMPT) + _estimate_tokens(prompt) + 120) * 1.10
    )
    completion = min(PREFERRED_COMPLETION_TOKENS, TARGET_TOTAL_TOKENS - estimated_input)
    if completion < MIN_COMPLETION_TOKENS:
        raise RuntimeError(
            "Paid Yearly preflight could not fit the finished annual material "
            "inside the configured single-call token budget."
        )
    return prompt, completion, estimated_input


def _clean_text(value: Any) -> str:
    text = str(value or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].lstrip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return re.sub(r"\*{1,3}|_{2,3}|`+", "", text).strip()


def _paragraphs(text: str) -> tuple[str, ...]:
    return tuple(
        " ".join(part.split())
        for part in re.split(r"\n\s*\n+", str(text or "").strip())
        if str(part or "").strip()
    )


def parse_paid_yearly_editorial(
    value: Any,
    *,
    expected_issue_numbers: list[int] | tuple[int, ...] = (),
) -> PaidYearlyEditorial:
    clean = _clean_text(value)
    if not clean:
        raise RuntimeError("Voice provider returned an empty Paid Yearly response.")

    matches = list(_MARKER_RE.finditer(clean))
    if not matches:
        raise RuntimeError("Paid Yearly response did not contain the required plain-text sections.")

    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(clean)
        sections[match.group("name")] = clean[start:end].strip()

    headline = " ".join(sections.get("HEADLINE", "").split()).strip().rstrip(".")
    deck = " ".join(sections.get("DECK", "").split()).strip()
    read_year = _paragraphs(sections.get("READ_YEAR", ""))
    closing = _paragraphs(sections.get("CLOSING", ""))

    issues: list[PaidYearlyIssue] = []
    issue_numbers = list(expected_issue_numbers)
    if not issue_numbers:
        issue_numbers = sorted(
            int(name.split(":", 1)[1])
            for name in sections
            if name.startswith("ISSUE:")
        )
    for number in issue_numbers:
        paragraphs = _paragraphs(sections.get(f"ISSUE:{int(number)}", ""))
        if paragraphs:
            issues.append(PaidYearlyIssue(number=int(number), paragraphs=paragraphs))

    all_text = " ".join(
        [headline, deck, *read_year, *closing]
        + [paragraph for issue in issues for paragraph in issue.paragraphs]
    )
    word_count = len(re.findall(r"\b[\w'-]+\b", all_text))

    required_present = bool(headline and deck and read_year and issues)
    return PaidYearlyEditorial(
        headline=headline,
        deck=deck,
        read_year=read_year,
        issues=tuple(issues),
        closing=closing,
        word_count=word_count,
        voice_complete=required_present,
    )


def generate_paid_yearly_editorial(
    packet: YearPacket | dict[str, Any],
    *,
    snapshot: Any | None = None,
    main_focus: str = "",
    personal_question: str = "",
    base_url: str,
    model: str,
    api_key: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> PaidYearlyEditorial:
    """One provider call. Plain text. No JSON schema. No retry loop."""
    if not str(base_url or "").strip() or not str(model or "").strip() or not str(api_key or "").strip():
        raise RuntimeError("Paid Yearly voice provider is not configured.")

    material = build_paid_yearly_material(
        packet,
        snapshot=snapshot,
        main_focus=main_focus,
        personal_question=personal_question,
    )
    prompt, completion_tokens, _estimated_input = _prepare_request(material)
    issue_numbers = [
        int(item.get("number") or index)
        for index, item in enumerate(material.get("major_issues") or [], start=1)
    ]

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.58,
        "max_completion_tokens": int(completion_tokens),
    }
    if str(model).startswith("openai/gpt-oss"):
        payload["reasoning_effort"] = "low"
        payload["include_reasoning"] = False

    try:
        response = requests.post(
            f"{str(base_url).rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=int(timeout),
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Voice provider request failed: {exc}") from exc

    if response.status_code >= 400:
        body = " ".join(str(response.text or "").split())[:600]
        raise RuntimeError(f"Voice provider HTTP {response.status_code}: {body}")

    try:
        choice = response.json()["choices"][0]
        body = choice["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError("Voice provider returned no usable Paid Yearly prose.") from exc

    if str(choice.get("finish_reason") or "") == "length":
        raise RuntimeError("Voice provider truncated the Paid Yearly report at the completion limit.")

    return parse_paid_yearly_editorial(
        body,
        expected_issue_numbers=issue_numbers,
    )
