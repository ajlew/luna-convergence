from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from astrology_engine import PLANET_WEIGHTS
from weekly_view import WeeklyDay, build_weekly_synthesis


VOICE_SCHEMA_VERSION = "1.0"
DEFAULT_GENERATED_ROOT = Path(__file__).parent / "generated" / "weekly"

_PRESSURE_ASPECTS = {"square", "opposition"}
_SUPPORT_ASPECTS = {"trine", "sextile"}
_PLANET_NAMES = {
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto", "True Node",
}
_PROHIBITED_CLAIMS = (
    "perfect alignment",
    "automatic luck",
    "guaranteed",
    "the worst is over",
    "working together perfectly",
    "will definitely",
    "will certainly",
    "destined to",
)
_TRAILING_FRAGMENTS = {
    "a", "an", "and", "as", "at", "before", "but", "for", "from", "in",
    "of", "on", "or", "the", "to", "with", "you", "your",
}
_IMPERATIVE_VERBS = {
    "act", "answer", "apply", "ask", "build", "change", "check", "choose",
    "complete", "contain", "convert", "cut", "decide", "define", "delay",
    "do", "end", "finish", "fix", "give", "hold", "keep", "let", "make",
    "move", "name", "pause", "preserve", "price", "protect", "put", "remove",
    "review", "send", "set", "stabilise", "state", "stop", "test", "use",
    "verify", "wait", "watch", "write",
}


@dataclass(frozen=True)
class VoiceValidation:
    valid: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class LoadedVoiceCandidate:
    copy: dict[str, Any] | None
    validation: VoiceValidation
    path: Path


def _clean(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _aspect_kind(day: WeeklyDay) -> str:
    aspect = _clean(day.aspect_name).lower()
    if aspect in {"conjunction", "square", "opposition", "trine", "sextile"}:
        return aspect
    evidence = f"{day.major_event_label} {day.evidence}".lower()
    for token, normalized in (
        ("conjunction", "conjunction"),
        ("conjunct", "conjunction"),
        ("opposition", "opposition"),
        ("opposite", "opposition"),
        ("square", "square"),
        ("trine", "trine"),
        ("sextile", "sextile"),
    ):
        if token in evidence:
            return normalized
    return aspect or "active"


def _aspect_role(day: WeeklyDay) -> str:
    aspect = _aspect_kind(day)
    if aspect in _PRESSURE_ASPECTS:
        return "pressure"
    if aspect in _SUPPORT_ASPECTS:
        return "opening" if "Jupiter" in day.planets else "support"
    if "Moon" in day.planets:
        return "emotional_trigger"
    return "active_condition"


def _source_id(day: WeeklyDay) -> str:
    pair = "-".join(sorted(planet.lower().replace(" ", "-") for planet in day.planets))
    aspect = _aspect_kind(day).replace(" ", "-")
    return f"{day.reading_date.isoformat()}:{pair}:{aspect}"


def _event_packet(day: WeeklyDay) -> dict[str, Any]:
    return {
        "source_id": _source_id(day),
        "date": day.reading_date.isoformat(),
        "weekday": day.weekday,
        "technical_label": _clean(day.major_event_label or day.evidence.split(" · ", 1)[0]),
        "evidence": _clean(day.evidence),
        "planets": list(day.planets),
        "aspect": _aspect_kind(day),
        "calculated_event_class": _clean(day.aspect_name),
        "phase": _clean(day.phase),
        "orb_degrees": round(float(day.orb), 5),
        "exact_time_label": _clean(day.exact_time_label),
        "role": _aspect_role(day),
        "approved_experience": _clean(day.line_one),
        "approved_meaning": _clean(day.line_two),
        "approved_move": _clean(day.action),
        "supporting_events": [_clean(item) for item in day.supporting_events],
    }


def _payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_weekly_voice_packet(
    days: tuple[WeeklyDay, ...],
    monday: date,
    timezone_name: str,
) -> dict[str, Any]:
    """Build a closed, deterministic packet. The model receives no raw natal data."""
    if len(days) != 7:
        raise ValueError("Weekly voice generation requires exactly seven calculated days.")
    if monday.weekday() != 0 or days[0].reading_date != monday:
        raise ValueError("Weekly voice generation must begin on the selected Monday.")

    events = [_event_packet(day) for day in days]
    counts = Counter(planet for event in events for planet in event["planets"])
    influence: Counter[str] = Counter()
    role_weight = {
        "pressure": 3.0,
        "opening": 4.0,
        "support": 2.0,
        "emotional_trigger": 2.0,
        "active_condition": 1.0,
    }
    for event in events:
        event_weight = role_weight[event["role"]]
        if event["phase"] == "exact today":
            event_weight += 1.0
        if event["calculated_event_class"] in {"opportunity", "ingress", "station", "eclipse"}:
            event_weight += 2.0
        for planet in event["planets"]:
            influence[planet] += event_weight * PLANET_WEIGHTS.get(planet, 1.0)
    highest = max(influence.values()) if influence else 0.0
    dominant = sorted(
        planet for planet, score in influence.items() if abs(score - highest) < 0.00001
    )
    existing = build_weekly_synthesis(days)
    packet = {
        "schema_version": VOICE_SCHEMA_VERSION,
        "week_start": monday.isoformat(),
        "week_end": days[-1].reading_date.isoformat(),
        "timezone": timezone_name,
        "guardrails": {
            "calculation_owner": "Luna deterministic engine",
            "model_role": "voice and synthesis only",
            "must_preserve_evidence_verbatim": True,
            "must_include_every_source_id_once": True,
            "must_not_add_aspects_times_or_houses": True,
            "must_not_ask_a_closing_question": True,
        },
        "calculated_pattern": {
            "planet_frequency": dict(sorted(counts.items())),
            "planet_influence_score": {
                planet: round(score, 3) for planet, score in sorted(influence.items())
            },
            "dominant_planets": dominant,
            "controlling_planet": dominant[0] if len(dominant) == 1 else "",
            "pressure_source_ids": [e["source_id"] for e in events if e["role"] == "pressure"],
            "support_source_ids": [e["source_id"] for e in events if e["role"] in {"support", "opening"}],
            "mixed_pressure_and_support": any(e["role"] == "pressure" for e in events)
            and any(e["role"] in {"support", "opening"} for e in events),
        },
        "existing_weekly_synthesis": {
            "headline": _clean(existing["headline"]),
            "paragraphs": [_clean(item) for item in existing["paragraphs"]],
            "rule": _clean(existing["rule"]),
        },
        "events": events,
    }
    packet["source_hash"] = _payload_hash(packet)
    return packet


def build_weekly_voice_prompt(packet: dict[str, Any]) -> str:
    """Return the complete voice-only contract for an OpenAI-compatible model."""
    return (
        "You are Luna's Convergence Composer. The supplied JSON is closed evidence. "
        "Do not calculate astrology, repair facts, add facts, infer houses, or change technical evidence.\n\n"
        "Your only job is synthesis and voice. Connect pressure, support, timing and opportunity. "
        "Write in Luna's imperative-led voice: short, consequence-first, dry, decisive, and lightly cheeky. "
        "Use no more than one tongue-in-cheek aside in a section. Do not use emojis. Do not ask a question. "
        "Do not claim perfect alignment, automatic luck, guarantees, destiny, or that the worst is over.\n\n"
        "Return JSON only with exactly these keys:\n"
        "headline: string; thesis: string; sections: array; closing_rule: string.\n"
        "Each section must contain exactly: source_id, evidence, headline, experience, meaning, move. "
        "Include every supplied source_id exactly once, in supplied order. Copy evidence verbatim. "
        "Keep each move complete and imperative. Do not truncate sentences.\n\n"
        "CLOSED EVIDENCE PACKET:\n"
        + json.dumps(packet, ensure_ascii=False, indent=2)
    )


def _all_text(copy: dict[str, Any]) -> list[str]:
    values = [copy.get("headline", ""), copy.get("thesis", ""), copy.get("closing_rule", "")]
    for section in copy.get("sections", []) if isinstance(copy.get("sections"), list) else []:
        if isinstance(section, dict):
            values.extend(section.get(key, "") for key in ("evidence", "headline", "experience", "meaning", "move"))
    return [_clean(item) for item in values if _clean(item)]


def _contains_unqualified_claim(text: str, phrase: str) -> bool:
    for match in re.finditer(re.escape(phrase), text, flags=re.IGNORECASE):
        prefix = text[max(0, match.start() - 32):match.start()]
        negated = re.search(
            r"\b(?:not|never|no|isn't|is not|doesn't|does not)\b(?:\W+\w+){0,2}\W*$",
            prefix,
            flags=re.IGNORECASE,
        )
        if not negated:
            return True
    return False


def validate_weekly_voice_copy(copy: Any, packet: dict[str, Any]) -> VoiceValidation:
    errors: list[str] = []
    if not isinstance(copy, dict):
        return VoiceValidation(False, ("The model response is not a JSON object.",))
    expected_top = {"headline", "thesis", "sections", "closing_rule"}
    if set(copy) != expected_top:
        errors.append("The response fields do not match the locked weekly voice schema.")

    for key, limit in (("headline", 14), ("thesis", 110), ("closing_rule", 35)):
        value = _clean(copy.get(key))
        if not value:
            errors.append(f"{key} is missing.")
        elif len(value.split()) > limit:
            errors.append(f"{key} exceeds the {limit}-word limit.")

    sections = copy.get("sections")
    events = packet.get("events", [])
    if not isinstance(sections, list):
        errors.append("sections must be an array.")
        sections = []
    if len(sections) != len(events):
        errors.append("Every calculated weekly event must appear exactly once.")

    expected_ids = [event["source_id"] for event in events]
    actual_ids = [section.get("source_id") for section in sections if isinstance(section, dict)]
    if actual_ids != expected_ids:
        errors.append("Source IDs are missing, duplicated, reordered or invented.")

    for index, event in enumerate(events):
        if index >= len(sections) or not isinstance(sections[index], dict):
            continue
        section = sections[index]
        expected_fields = {"source_id", "evidence", "headline", "experience", "meaning", "move"}
        if set(section) != expected_fields:
            errors.append(f"Section {index + 1} fields do not match the locked schema.")
        if section.get("evidence") != event["evidence"]:
            errors.append(f"Section {index + 1} changed its technical evidence.")
        for key, limit in (("headline", 14), ("experience", 55), ("meaning", 55), ("move", 28)):
            value = _clean(section.get(key))
            if not value:
                errors.append(f"Section {index + 1} {key} is missing.")
            elif len(value.split()) > limit:
                errors.append(f"Section {index + 1} {key} exceeds its word limit.")
        move = _clean(section.get("move"))
        if move:
            first = re.sub(r"[^a-z]", "", move.split()[0].lower())
            last = re.sub(r"[^a-z]", "", move.split()[-1].lower())
            if first not in _IMPERATIVE_VERBS:
                errors.append(f"Section {index + 1} move is not clearly imperative.")
            if last in _TRAILING_FRAGMENTS:
                errors.append(f"Section {index + 1} move appears truncated.")

    texts = _all_text(copy)
    combined = "\n".join(texts)
    lower = combined.lower()
    if "?" in combined:
        errors.append("Luna voice copy must not ask the reader a question.")
    for phrase in _PROHIBITED_CLAIMS:
        if _contains_unqualified_claim(lower, phrase):
            errors.append(f"Prohibited certainty claim: {phrase}.")

    supplied_planets = {planet for event in events for planet in event.get("planets", [])}
    for planet in sorted(_PLANET_NAMES - supplied_planets):
        if re.search(rf"\b{re.escape(planet)}\b", combined, flags=re.IGNORECASE):
            errors.append(f"The response invented an unsupplied planet reference: {planet}.")

    packet_numbers = set(re.findall(r"\b\d+(?:\.\d+)?(?::\d+)?\b", json.dumps(packet)))
    output_numbers = set(re.findall(r"\b\d+(?:\.\d+)?(?::\d+)?\b", combined))
    invented_numbers = sorted(output_numbers - packet_numbers)
    if invented_numbers:
        errors.append("The response invented numeric evidence: " + ", ".join(invented_numbers) + ".")

    editorial_texts = []
    for key in ("headline", "thesis", "closing_rule"):
        editorial_texts.append(_clean(copy.get(key)))
    for section in sections:
        if isinstance(section, dict):
            editorial_texts.extend(_clean(section.get(key)) for key in ("headline", "experience", "meaning", "move"))
    normalized = [re.sub(r"[^a-z0-9]+", " ", text.lower()).strip() for text in editorial_texts if text]
    if len(normalized) != len(set(normalized)):
        errors.append("The response duplicates editorial copy instead of synthesising it.")
    for text in texts:
        if text.count("(") > 1 or text.count(")") > 1:
            errors.append("A section contains more than one parenthetical aside.")
            break

    return VoiceValidation(not errors, tuple(dict.fromkeys(errors)))


def candidate_filename(monday: date, timezone_name: str) -> str:
    safe_timezone = re.sub(r"[^A-Za-z0-9._-]+", "-", timezone_name).strip("-")
    return f"{monday.isoformat()}_{safe_timezone}.json"


def candidate_path(
    monday: date,
    timezone_name: str,
    generated_root: Path = DEFAULT_GENERATED_ROOT,
) -> Path:
    return generated_root / candidate_filename(monday, timezone_name)


def make_candidate_document(
    copy: dict[str, Any],
    packet: dict[str, Any],
    *,
    provider: str,
    model: str,
) -> dict[str, Any]:
    validation = validate_weekly_voice_copy(copy, packet)
    if not validation.valid:
        raise ValueError("Weekly voice candidate failed validation: " + " | ".join(validation.errors))
    return {
        "schema_version": VOICE_SCHEMA_VERSION,
        "week_start": packet["week_start"],
        "timezone": packet["timezone"],
        "source_hash": packet["source_hash"],
        "provider": _clean(provider),
        "model": _clean(model),
        "copy": copy,
    }


def load_weekly_voice_candidate(
    days: tuple[WeeklyDay, ...],
    monday: date,
    timezone_name: str,
    generated_root: Path = DEFAULT_GENERATED_ROOT,
) -> LoadedVoiceCandidate:
    path = candidate_path(monday, timezone_name, generated_root)
    if not path.exists():
        return LoadedVoiceCandidate(None, VoiceValidation(False, ("No generated candidate exists for this week and timezone.",)), path)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return LoadedVoiceCandidate(None, VoiceValidation(False, (f"Candidate file could not be read: {exc}",)), path)

    packet = build_weekly_voice_packet(days, monday, timezone_name)
    envelope_errors = []
    for key in ("schema_version", "week_start", "timezone", "source_hash", "copy"):
        if key not in document:
            envelope_errors.append(f"Candidate is missing {key}.")
    if document.get("schema_version") != VOICE_SCHEMA_VERSION:
        envelope_errors.append("Candidate schema version does not match this app.")
    if document.get("week_start") != packet["week_start"]:
        envelope_errors.append("Candidate belongs to a different week.")
    if document.get("timezone") != packet["timezone"]:
        envelope_errors.append("Candidate belongs to a different timezone.")
    if document.get("source_hash") != packet["source_hash"]:
        envelope_errors.append("Calculated evidence changed after this candidate was generated.")
    if envelope_errors:
        return LoadedVoiceCandidate(None, VoiceValidation(False, tuple(envelope_errors)), path)

    validation = validate_weekly_voice_copy(document.get("copy"), packet)
    return LoadedVoiceCandidate(document.get("copy") if validation.valid else None, validation, path)
