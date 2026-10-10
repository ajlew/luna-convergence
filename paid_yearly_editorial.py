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


PAID_YEARLY_EDITORIAL_VERSION = "1.2-provider-fit"
DEFAULT_TIMEOUT_SECONDS = 180
TARGET_TOTAL_TOKENS = 5350
PREFERRED_COMPLETION_TOKENS = 2500
MIN_COMPLETION_TOKENS = 1800

_MARKER_RE = re.compile(
    r"(?m)^<<(?P<name>HEADLINE|DECK|READ_YEAR|CLOSING|ISSUE:\d+|MONTH:\d+)>>\s*$"
)


@dataclass(frozen=True)
class PaidYearlyIssue:
    number: int
    paragraphs: tuple[str, ...]


@dataclass(frozen=True)
class PaidYearlyMonth:
    number: int
    focus: str


@dataclass(frozen=True)
class PaidYearlyEditorial:
    headline: str
    deck: str
    read_year: tuple[str, ...]
    issues: tuple[PaidYearlyIssue, ...]
    closing: tuple[str, ...]
    word_count: int
    voice_complete: bool = True
    monthly_rounds: tuple[PaidYearlyMonth, ...] = ()

    def issue_for(self, number: int) -> PaidYearlyIssue | None:
        for issue in self.issues:
            if issue.number == int(number):
                return issue
        return None

    def month_for(self, number: int) -> PaidYearlyMonth | None:
        for month in self.monthly_rounds:
            if month.number == int(number):
                return month
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
        "start_state": str(game.get("start_state") or ""),
        "end_state": str(game.get("end_state") or ""),
        "question": str(game.get("question") or ""),
        "advantage": str(game.get("advantage") or ""),
        "risk": str(game.get("risk") or ""),
        "move": str(game.get("move") or ""),
        "dont": str(game.get("dont") or ""),
        "primary": _transit_material(primary) if isinstance(primary, dict) else {},
        "supporting": [
            _transit_material(row)
            for row in list(supporting or [])[:2]
            if isinstance(row, dict)
        ],
    }


_PLANET_NAMES = (
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "Ascendant", "Midheaven",
)


def _named_planets(*values: object) -> set[str]:
    text = " ".join(str(value or "") for value in values)
    found = set()
    for planet in _PLANET_NAMES:
        if re.search(rf"\b{re.escape(planet)}\b", text, flags=re.IGNORECASE):
            found.add(planet)
    return found


def _natal_resonance_for_issue(
    issue: dict[str, Any],
    natal: dict[str, Any],
) -> list[dict[str, Any]]:
    """Find supplied natal signatures that genuinely overlap the issue's named planets.

    This is a thematic bridge only. It does not claim a transit directly activates
    a natal aspect unless that direct target already exists in the calculated packet.
    """
    primary = dict(issue.get("primary") or {})
    supporting = [
        row for row in list(issue.get("supporting") or [])
        if isinstance(row, dict)
    ]
    issue_planets = _named_planets(
        primary.get("technical"),
        *[row.get("technical") for row in supporting],
    )
    if not issue_planets:
        return []

    matches = []
    for row in list(natal.get("strengths") or []):
        if not isinstance(row, dict):
            continue
        signature_planets = _named_planets(
            row.get("title"),
            row.get("evidence"),
            row.get("strength"),
            row.get("interpretation"),
        )
        overlap = sorted(issue_planets & signature_planets)
        if not overlap:
            continue
        matches.append(
            {
                "title": _clip(row.get("title"), 72),
                "evidence": _clip(row.get("evidence"), 90),
                "overlap": overlap,
            }
        )
    return matches[:2]


def _monthly_round_material(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "number": int(row.get("number") or index),
        "start": str(row.get("start") or ""),
        "end": str(row.get("end") or ""),
        "label": str(row.get("label") or ""),
        "phase": str(row.get("phase") or ""),
        "dominant_game_number": row.get("dominant_game_number"),
        "dominant_game_title": str(row.get("dominant_game_title") or ""),
        "dominant_life_area": str(row.get("dominant_life_area") or ""),
        "strongest_date": str(row.get("strongest_date") or ""),
        "strongest_kind": str(row.get("strongest_kind") or ""),
        "focus": str(row.get("focus") or ""),
    }


def build_paid_yearly_material(
    packet: YearPacket | dict[str, Any],
    *,
    snapshot: Any | None = None,
    main_focus: str = "",
    personal_question: str = "",
    shared_year_context: dict[str, Any] | None = None,
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

    natal = _snapshot_material(snapshot, value)
    major_issues = [
        _issue_material(game)
        for game in list(value.get("games") or [])
        if isinstance(game, dict)
    ]
    for issue in major_issues:
        issue["natal_resonance"] = _natal_resonance_for_issue(issue, natal)

    monthly_rounds = [
        _monthly_round_material(row, index)
        for index, row in enumerate(list(value.get("monthly_rounds") or []), start=1)
        if isinstance(row, dict)
    ]

    return {
        "period": dict(value.get("period") or {}),
        "reader_context": {
            "main_focus": str(main_focus or "General overview"),
            "personal_question": str(personal_question or "").strip(),
        },
        "natal": natal,
        "year_statistics": dict(value.get("year_statistics") or {}),
        "year_strip": year_strip,
        "monthly_rounds": monthly_rounds,
        "shared_year": dict(shared_year_context or {}),
        "major_issues": major_issues,
    }


def _clip(value: object, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: max(0, limit - 1)].rstrip() + "…"


def _compact_transit_for_voice(story: dict[str, Any], level: int, *, primary: bool) -> dict[str, Any]:
    """Compact duplicate wording while preserving every supplied transit, pass and date."""
    out = {
        "technical": story.get("technical"),
        "active_start": story.get("active_start"),
        "active_end": story.get("active_end"),
        "house": story.get("house"),
        "passes": list(story.get("passes") or []),
        "triggers": list(story.get("triggers") or []),
    }
    if primary:
        limits = ((300, 220, 180), (240, 180, 140), (190, 135, 110), (150, 110, 90))[level]
        out["summary"] = _clip(story.get("summary"), limits[0])
        out["move"] = _clip(story.get("move"), limits[1])
        out["watch"] = _clip(story.get("watch"), limits[2])
    elif level <= 1:
        out["summary"] = _clip(story.get("summary"), 180 if level == 0 else 120)
    return out


def _compact_paid_yearly_material(material: dict[str, Any], level: int) -> dict[str, Any]:
    """Fit one annual request without deleting selected Games, exact passes or dates."""
    level = max(0, min(3, int(level or 0)))
    natal = dict(material.get("natal") or {})
    strengths = [
        dict(item) for item in list(natal.get("strengths") or [])
        if isinstance(item, dict)
    ]
    strength_caps = (6, 4, 3, 2)
    natal["strengths"] = [
        {
            "title": _clip(item.get("title"), 72),
            "strength": _clip(item.get("strength") or item.get("interpretation"), (180, 135, 105, 82)[level]),
            "watch": _clip(item.get("watch"), (130, 100, 78, 62)[level]),
            "evidence": _clip(item.get("evidence"), 72),
        }
        for item in strengths[: strength_caps[level]]
    ]

    if level >= 2:
        core = dict(natal.get("core") or {})
        keep = ("Sun", "Moon", "Mercury", "Venus", "Mars") if level == 2 else ("Sun", "Moon", "Venus", "Mars")
        natal["core"] = {key: core[key] for key in keep if key in core}

    issues = []
    for issue in list(material.get("major_issues") or []):
        if not isinstance(issue, dict):
            continue
        item = {
            "number": issue.get("number"),
            "customer_title": issue.get("customer_title"),
            "strategic_frame": _clip(issue.get("strategic_frame"), 120),
            "life_area": _clip(issue.get("life_area"), 90),
            "polarity": issue.get("polarity"),
            "start": issue.get("start"),
            "end": issue.get("end"),
            "start_state": issue.get("start_state"),
            "end_state": issue.get("end_state"),
            "natal_resonance": [
                dict(row)
                for row in list(issue.get("natal_resonance") or [])[:2]
                if isinstance(row, dict)
            ],
            "question": _clip(issue.get("question"), (150, 120, 95, 80)[level]),
            "advantage": _clip(issue.get("advantage"), (180, 135, 105, 85)[level]),
            "risk": _clip(issue.get("risk"), (180, 135, 105, 85)[level]),
            "move": _clip(issue.get("move"), (180, 135, 105, 85)[level]),
            "dont": _clip(issue.get("dont"), (130, 100, 80, 65)[level]),
            "primary": _compact_transit_for_voice(
                dict(issue.get("primary") or {}),
                level,
                primary=True,
            ),
            "supporting": [
                _compact_transit_for_voice(dict(row), level, primary=False)
                for row in list(issue.get("supporting") or [])
                if isinstance(row, dict)
            ],
        }
        issues.append(item)

    output = {
        "period": dict(material.get("period") or {}),
        "reader_context": dict(material.get("reader_context") or {}),
        "natal": natal,
        "year_statistics": dict(material.get("year_statistics") or {}),
        "year_strip": list(material.get("year_strip") or []),
        "monthly_rounds": [
            {
                "number": row.get("number"),
                "label": _clip(row.get("label"), 42),
                "phase": row.get("phase"),
                "dominant_game_number": row.get("dominant_game_number"),
                "dominant_game_title": _clip(row.get("dominant_game_title"), 72),
                "dominant_life_area": _clip(row.get("dominant_life_area"), 72),
                "strongest_date": row.get("strongest_date"),
                "strongest_kind": row.get("strongest_kind"),
                "focus": _clip(row.get("focus"), (120, 95, 80, 65)[level]),
            }
            for row in list(material.get("monthly_rounds") or [])[:12]
            if isinstance(row, dict)
        ],
        "major_issues": issues,
    }
    if level <= 1 and material.get("shared_year"):
        output["shared_year"] = dict(material.get("shared_year") or {})
    return output


def build_paid_yearly_prompt(material: dict[str, Any]) -> str:
    issues = list(material.get("major_issues") or [])
    months = list(material.get("monthly_rounds") or [])

    month_markers = "\n".join(
        f"<<MONTH:{int(item.get('number') or index)}>>"
        for index, item in enumerate(months, start=1)
    )
    issue_markers = "\n".join(
        f"<<ISSUE:{int(item.get('number') or index)}>>"
        for index, item in enumerate(issues, start=1)
    )

    return (
        "Write Luna's PAID PERSONAL YEAR AHEAD. This is the finished paid product, "
        "not a preview, dashboard summary or transit catalogue.\n\n"

        "ROLE SPLIT: Python has already calculated every transit, exact contact, "
        "active window, return, boundary state, ranking, monthly dominant story and "
        "Game. You only translate that finished evidence into useful human language. "
        "Do not calculate, repair, re-rank or invent astrology.\n\n"

        "EDITORIAL MODEL: follow Luna's Paid Monthly hierarchy but scale it to a "
        "rolling year. The person comes first. Tell one connected strategic story, "
        "then deepen the 3-5 supplied major stories. The report should feel like a "
        "skilled narrator explaining a year of choices and changing conditions, not "
        "software describing its own output.\n\n"

        "HUMAN-FIRST RULE: start paragraphs with the lived situation, consequence, "
        "decision or change. Do not begin a paragraph with a transit name, aspect, "
        "house, active-window range or technical label. Do not say 'the first issue', "
        "'the second Game', 'this report', 'the packet' or similar report-meta language. "
        "Technical facts may be mentioned sparingly after the human meaning is clear.\n\n"

        "DATE / LOCALISATION RULE: exact timing is rendered separately by Python. In "
        "READ_YEAR and ISSUE prose, DO NOT print raw ISO dates such as 2027-02-27 and do "
        "not restate active-window date ranges. Use month names, 'later in the year', "
        "'in the second half of the year' or similar neutral timing only when supported "
        "by the supplied chronology. Do NOT use spring, summer, autumn/fall or winter "
        "unless a local season is explicitly supplied. Never invent or alter a year.\n\n"

        "NATAL BRIDGE: natal.strengths describe lifelong patterns. If an issue contains "
        "natal_resonance, connect that supplied natal pattern to the current story as a "
        "recurring lens: explain why the present pressure/opening may feel familiar or "
        "what old habit it tests. Do NOT claim a transit 'activates' a natal aspect unless "
        "the calculated transit target explicitly says so. If no resonance is supplied, "
        "do not force one. In READ_YEAR, make at least one clear natal-to-year bridge when "
        "the supplied resonance supports it.\n\n"

        "ONE CHRONOLOGY: move through the year once. A first exact contact, retrograde "
        "return and final contact are stages of ONE story. Explain the development: "
        "what first becomes visible, what returns for review/renegotiation, and what can "
        "finally be settled or integrated. Fast Sun/Mercury/Venus/Mars contacts are "
        "supporting moments only.\n\n"

        "MONTHLY ROUNDS: Python has supplied exactly twelve rolling rounds from the "
        "reader's chosen start date. For each MONTH marker write ONE distinct 12-24 word "
        "strategic sentence. Do not repeat the Game title, date or phase label because "
        "the interface already shows them. Make the sentence specific to that round's "
        "phase and supplied focus. When consecutive rounds share the same dominant_game_number, "
        "treat them as stages of one continuing story: the later line must show what has "
        "changed, what is being tested, revisited, consolidated or settled since the previous "
        "round. Never restart the story from zero and never reuse the same sentence in two months.\n\n"

        "MAJOR STORY CHAPTERS: for each ISSUE marker, write 2-3 substantial paragraphs. "
        "Paragraph 1 = what is changing in human terms. Paragraphs 2-3 = concrete ways "
        "this may show up in ordinary life, the trade-off/risk, and how the sequence of "
        "passes changes the decision. Treat the supplied life_area, strategic_frame, risk "
        "and move as the customer-facing context for this story; do not drag relationship, "
        "chemistry, money or career language into a different life area merely because a "
        "planet is associated with those themes. Do not repeat the customer title at the "
        "start. Do not recite active-window dates; the interface renders timing separately.\n\n"

        "READER CONTEXT: the customer's priority/question may influence emphasis only "
        "when the supplied astrology supports it. Do not force an answer.\n\n"

        "VOICE: direct second person throughout. Strategic, adult, specific and grounded. "
        "Preserve agency. Avoid fate, therapy-speak, manifestation claims, guaranteed "
        "outcomes and mystical padding. Prefer ordinary consequences: agreements, workload, "
        "money, reciprocity, visibility, responsibility, information, timing, openings and "
        "limits where the supplied life area supports them.\n\n"

        "DEPTH / BUDGET:\n"
        "- READ_YEAR: roughly 550-700 words in 5-7 substantial paragraphs.\n"
        "- EACH ISSUE: roughly 160-210 words in 2-3 substantial paragraphs.\n"
        "- EACH MONTH: one 12-24 word sentence.\n"
        "- CLOSING: roughly 90-120 words in 1-2 paragraphs.\n"
        "- Use density rather than repetition. Every paragraph must add a new consequence, "
        "choice, stage or manifestation.\n\n"

        "OUTPUT FORMAT: PLAIN TEXT ONLY. Use the exact internal markers below on their "
        "own lines. No Markdown headings, bullets, JSON or code fences. The markers are "
        "parsing boundaries and are not shown to the customer.\n\n"

        "<<HEADLINE>>\n"
        "One strong editorial headline, 8-18 words. Human and non-technical.\n"
        "<<DECK>>\n"
        "One or two sentences stating the strategic shape of the rolling year.\n"
        "<<READ_YEAR>>\n"
        "The connected annual narrative.\n"
        f"{month_markers}\n"
        "For each MONTH marker write exactly one short strategic sentence for that supplied round.\n"
        f"{issue_markers}\n"
        "For each ISSUE marker write the substantial human-first interpretation for that supplied story.\n"
        "<<CLOSING>>\n"
        "Final strategic synthesis: what to protect, pursue, stop carrying and carry forward.\n\n"

        "Before returning, silently check: chronology is forward-moving; no raw ISO dates "
        "appear in prose; no season name appears unless local season data was supplied; no "
        "supplied story title is redundantly repeated at the start of its own chapter; no "
        "monthly sentence is duplicated; and every example belongs to the stated life area.\n\n"

        "CALCULATED YEAR:\n"
        + json.dumps(material, ensure_ascii=False, separators=(",", ":"), default=str)
    )


def build_paid_yearly_ultra_prompt(material: dict[str, Any]) -> str:
    """Provider-fit fallback prompt.

    Same editorial contract as the full prompt, but stripped of repeated explanation.
    Used only after the YearPacket itself has already been ultra-compacted.
    """
    issues = list(material.get("major_issues") or [])
    months = list(material.get("monthly_rounds") or [])

    month_markers = "\n".join(
        f"<<MONTH:{int(item.get('number') or index)}>>"
        for index, item in enumerate(months, start=1)
    )
    issue_markers = "\n".join(
        f"<<ISSUE:{int(item.get('number') or index)}>>"
        for index, item in enumerate(issues, start=1)
    )

    return (
        "Write Luna's finished PAID PERSONAL YEAR AHEAD from CALCULATED YEAR below. "
        "Python owns every astrology fact, date, pass, ranking, boundary and monthly story. "
        "Do not calculate, repair, rank or invent anything.\n\n"

        "VOICE: direct second person, adult, strategic, human-first. Start with lived "
        "situations, choices and consequences, not transit names. Technical astrology may "
        "support meaning after the human point is clear. Preserve agency; no fate or mystical padding.\n\n"

        "TIMING: do not print raw ISO dates or active-window ranges in READ_YEAR/ISSUE prose. "
        "Use month names or neutral phrases such as 'later in the year'. Do not use season "
        "names unless local season data is supplied. Never invent or alter a year.\n\n"

        "NATAL: if natal_resonance exists, use it only as a familiar lifelong lens. "
        "Do not claim a transit activates a natal aspect unless the supplied target proves it.\n\n"

        "CHRONOLOGY: one forward-moving year. First contact, retrograde return and final "
        "contact are stages of one developing story. Fast-planet contacts are supporting moments.\n\n"

        "MONTHS: write one unique 12-22 word strategic sentence per MONTH marker. "
        "Do not repeat title/date/phase. If consecutive months share a story, show progression "
        "rather than restarting it.\n\n"

        "ISSUES: 2 substantial paragraphs per ISSUE. Paragraph 1: what changes in ordinary "
        "life. Paragraph 2: concrete manifestations, risk/trade-off and how the pass sequence "
        "changes the decision. Use the supplied life_area/strategic_frame/risk/move; do not "
        "import relationship, money or career language into the wrong life area.\n\n"

        "SIZE: READ_YEAR about 500-650 words in 5-6 paragraphs; each ISSUE about 140-190 "
        "words; CLOSING about 80-110 words. Be dense, not repetitive.\n\n"

        "PLAIN TEXT ONLY. Use these exact markers on their own lines. No Markdown, bullets, "
        "JSON or code fences:\n"
        "<<HEADLINE>>\n"
        "<<DECK>>\n"
        "<<READ_YEAR>>\n"
        f"{month_markers}\n"
        f"{issue_markers}\n"
        "<<CLOSING>>\n\n"

        "Silently check: no invented dates, no season names, no duplicate monthly sentence, "
        "no report-meta language, and every example fits its life area.\n\n"

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


def _ultra_compact_paid_yearly_material(material: dict[str, Any]) -> dict[str, Any]:
    """Last pre-call compression: keep every major issue and primary pass/date."""
    natal = dict(material.get("natal") or {})
    core = dict(natal.get("core") or {})
    natal_min = {
        "birth_time_known": bool(natal.get("birth_time_known")),
        "core": {
            key: core[key]
            for key in ("Sun", "Moon", "Venus", "Mars")
            if key in core
        },
        "dominant_element": natal.get("dominant_element"),
        "dominant_modality": natal.get("dominant_modality"),
        "strengths": [
            {
                "title": _clip(item.get("title"), 64),
                "strength": _clip(item.get("strength") or item.get("interpretation"), 82),
                "evidence": _clip(item.get("evidence"), 64),
            }
            for item in list(natal.get("strengths") or [])[:2]
            if isinstance(item, dict)
        ],
    }

    issues = []
    for issue in list(material.get("major_issues") or []):
        if not isinstance(issue, dict):
            continue
        primary = dict(issue.get("primary") or {})
        issues.append(
            {
                "number": issue.get("number"),
                "customer_title": _clip(issue.get("customer_title"), 72),
                "strategic_frame": _clip(issue.get("strategic_frame"), 92),
                "life_area": _clip(issue.get("life_area"), 72),
                "start": issue.get("start"),
                "end": issue.get("end"),
                "start_state": issue.get("start_state"),
                "end_state": issue.get("end_state"),
                "natal_resonance": [
                    {
                        "title": _clip(row.get("title"), 64),
                        "evidence": _clip(row.get("evidence"), 72),
                        "overlap": list(row.get("overlap") or []),
                    }
                    for row in list(issue.get("natal_resonance") or [])[:1]
                    if isinstance(row, dict)
                ],
                "primary": {
                    "technical": primary.get("technical"),
                    "active_start": primary.get("active_start"),
                    "active_end": primary.get("active_end"),
                    "house": primary.get("house"),
                    "passes": [
                        {
                            "pass_number": row.get("pass_number"),
                            "pass_label": row.get("pass_label"),
                            "date": row.get("date"),
                            "time": row.get("time"),
                            "retrograde": bool(row.get("retrograde")),
                        }
                        for row in list(primary.get("passes") or [])
                        if isinstance(row, dict)
                    ],
                    "triggers": [
                        {
                            "planet": row.get("planet"),
                            "date": row.get("date"),
                            "label": _clip(row.get("label"), 72),
                            "activates_pass_number": row.get("activates_pass_number"),
                        }
                        for row in list(primary.get("triggers") or [])[:2]
                        if isinstance(row, dict)
                    ],
                },
                "supporting": [
                    {
                        "technical": row.get("technical"),
                        "active_start": row.get("active_start"),
                        "active_end": row.get("active_end"),
                    }
                    for row in list(issue.get("supporting") or [])[:2]
                    if isinstance(row, dict)
                ],
            }
        )

    return {
        "period": dict(material.get("period") or {}),
        "reader_context": dict(material.get("reader_context") or {}),
        "natal": natal_min,
        "monthly_rounds": [
            {
                "number": row.get("number"),
                "phase": row.get("phase"),
                "dominant_game_number": row.get("dominant_game_number"),
                "strongest_date": row.get("strongest_date"),
                "strongest_kind": row.get("strongest_kind"),
                "focus": _clip(row.get("focus"), 60),
            }
            for row in list(material.get("monthly_rounds") or [])[:12]
            if isinstance(row, dict)
        ],
        "major_issues": issues,
    }


def _prepare_request(material: dict[str, Any]) -> tuple[str, int, int]:
    """Fit one Paid Yearly call inside the same safe envelope proven by Paid Monthly."""
    for level in range(4):
        compact = _compact_paid_yearly_material(material, level)
        prompt = build_paid_yearly_prompt(compact)
        estimated_input = math.ceil(
            (_estimate_tokens(SYSTEM_PROMPT) + _estimate_tokens(prompt) + 100) * 1.15
        )
        if estimated_input + PREFERRED_COMPLETION_TOKENS <= TARGET_TOTAL_TOKENS:
            return prompt, PREFERRED_COMPLETION_TOKENS, estimated_input

    compact = _ultra_compact_paid_yearly_material(material)
    prompt = build_paid_yearly_ultra_prompt(compact)
    estimated_input = math.ceil(
        (_estimate_tokens(SYSTEM_PROMPT) + _estimate_tokens(prompt) + 100) * 1.15
    )
    completion = min(
        PREFERRED_COMPLETION_TOKENS,
        TARGET_TOTAL_TOKENS - estimated_input,
    )
    if completion < MIN_COMPLETION_TOKENS:
        raise RuntimeError(
            "Paid Yearly preflight still exceeds the provider-safe token envelope "
            f"after ultra compaction ({estimated_input} estimated input tokens)."
        )
    return prompt, int(completion), estimated_input


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


_ISO_DATE_TOKEN_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def _calculated_dates(material: dict[str, Any]) -> set[str]:
    dates: set[str] = set()

    def add(value: object) -> None:
        text = str(value or "").strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            dates.add(text)

    period = dict(material.get("period") or {})
    add(period.get("start"))
    add(period.get("end"))

    for month in list(material.get("monthly_rounds") or []):
        if not isinstance(month, dict):
            continue
        add(month.get("start"))
        add(month.get("end"))
        add(month.get("strongest_date"))

    for issue in list(material.get("major_issues") or []):
        if not isinstance(issue, dict):
            continue
        add(issue.get("start"))
        add(issue.get("end"))
        for story in [dict(issue.get("primary") or {})] + [
            dict(row)
            for row in list(issue.get("supporting") or [])
            if isinstance(row, dict)
        ]:
            add(story.get("active_start"))
            add(story.get("active_end"))
            for row in list(story.get("passes") or []):
                if isinstance(row, dict):
                    add(row.get("date"))
            for row in list(story.get("triggers") or []):
                if isinstance(row, dict):
                    add(row.get("date"))

    return dates


def _human_date(value: str) -> str:
    try:
        from datetime import date as _date
        return _date.fromisoformat(value).strftime("%d %B %Y").lstrip("0")
    except ValueError:
        return value


def _sanitize_generated_dates(text: str, allowed_dates: set[str]) -> str:
    """Drop any sentence containing an invented ISO date; humanise supplied dates.

    Exact timing is already rendered deterministically elsewhere. This guard never
    repairs astrology or calls the model again.
    """
    parts = re.split(r"(?<=[.!?])\s+", str(text or "").strip())
    kept: list[str] = []

    for sentence in parts:
        tokens = _ISO_DATE_TOKEN_RE.findall(sentence)
        if tokens and any(token not in allowed_dates for token in tokens):
            continue
        for token in tokens:
            sentence = sentence.replace(token, _human_date(token))
        sentence = " ".join(sentence.split()).strip()
        if sentence:
            kept.append(sentence)

    return " ".join(kept).strip()


def _strip_repeated_title(text: str, title: str) -> str:
    value = " ".join(str(text or "").split()).strip()
    title = " ".join(str(title or "").split()).strip()
    if not value or not title:
        return value

    pattern = re.compile(
        rf"^{re.escape(title)}\s*(?:[:—–\-.]+\s*)?",
        flags=re.IGNORECASE,
    )
    return pattern.sub("", value, count=1).strip()


def parse_paid_yearly_editorial(
    value: Any,
    *,
    expected_issue_numbers: list[int] | tuple[int, ...] = (),
    expected_month_numbers: list[int] | tuple[int, ...] = (),
    issue_titles: dict[int, str] | None = None,
    allowed_dates: set[str] | None = None,
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

    allowed_dates = set(allowed_dates or ())
    issue_titles = dict(issue_titles or {})

    def safe(value: str) -> str:
        return _sanitize_generated_dates(value, allowed_dates) if allowed_dates else " ".join(str(value or "").split())

    headline = safe(sections.get("HEADLINE", "")).rstrip(".")
    deck = safe(sections.get("DECK", ""))

    read_year = tuple(
        safe(paragraph)
        for paragraph in _paragraphs(sections.get("READ_YEAR", ""))
        if safe(paragraph)
    )
    closing = tuple(
        safe(paragraph)
        for paragraph in _paragraphs(sections.get("CLOSING", ""))
        if safe(paragraph)
    )

    month_numbers = list(expected_month_numbers)
    if not month_numbers:
        month_numbers = sorted(
            int(name.split(":", 1)[1])
            for name in sections
            if name.startswith("MONTH:")
        )
    monthly_rounds: list[PaidYearlyMonth] = []
    for number in month_numbers:
        focus = safe(sections.get(f"MONTH:{int(number)}", ""))
        if focus:
            monthly_rounds.append(
                PaidYearlyMonth(
                    number=int(number),
                    focus=focus,
                )
            )

    issues: list[PaidYearlyIssue] = []
    issue_numbers = list(expected_issue_numbers)
    if not issue_numbers:
        issue_numbers = sorted(
            int(name.split(":", 1)[1])
            for name in sections
            if name.startswith("ISSUE:")
        )

    for number in issue_numbers:
        raw_paragraphs = _paragraphs(sections.get(f"ISSUE:{int(number)}", ""))
        cleaned: list[str] = []
        for index, paragraph in enumerate(raw_paragraphs):
            paragraph = safe(paragraph)
            if index == 0:
                paragraph = _strip_repeated_title(
                    paragraph,
                    issue_titles.get(int(number), ""),
                )
            if paragraph:
                cleaned.append(paragraph)
        if cleaned:
            issues.append(
                PaidYearlyIssue(
                    number=int(number),
                    paragraphs=tuple(cleaned),
                )
            )

    all_text = " ".join(
        [headline, deck, *read_year, *closing]
        + [month.focus for month in monthly_rounds]
        + [paragraph for issue in issues for paragraph in issue.paragraphs]
    )
    word_count = len(re.findall(r"\\b[\\w'-]+\\b", all_text))

    required_issue_count = len(list(expected_issue_numbers or ())) or len(issue_numbers)
    required_month_count = len(list(expected_month_numbers or ()))

    required_present = bool(
        headline
        and deck
        and read_year
        and closing
        and issues
        and len(issues) == required_issue_count
        and (
            not required_month_count
            or len(monthly_rounds) == required_month_count
        )
    )

    return PaidYearlyEditorial(
        headline=headline,
        deck=deck,
        read_year=read_year,
        issues=tuple(issues),
        closing=closing,
        word_count=word_count,
        voice_complete=required_present,
        monthly_rounds=tuple(monthly_rounds),
    )


def generate_paid_yearly_editorial(
    packet: YearPacket | dict[str, Any],
    *,
    snapshot: Any | None = None,
    main_focus: str = "",
    personal_question: str = "",
    shared_year_context: dict[str, Any] | None = None,
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
        shared_year_context=shared_year_context,
    )
    prompt, completion_tokens, _estimated_input = _prepare_request(material)
    issue_numbers = [
        int(item.get("number") or index)
        for index, item in enumerate(material.get("major_issues") or [], start=1)
    ]
    month_numbers = [
        int(item.get("number") or index)
        for index, item in enumerate(material.get("monthly_rounds") or [], start=1)
    ]
    issue_titles = {
        int(item.get("number") or index): str(item.get("customer_title") or "")
        for index, item in enumerate(material.get("major_issues") or [], start=1)
    }
    allowed_dates = _calculated_dates(material)

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
        expected_month_numbers=month_numbers,
        issue_titles=issue_titles,
        allowed_dates=allowed_dates,
    )
