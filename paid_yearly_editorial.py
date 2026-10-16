from __future__ import annotations

"""Year Ahead prose engine. Python owns every destination and evidence packet.

Each provider completion writes prose for exactly one Python-assigned section.
No section delimiters, LLM-authored labels, response parsing or editorial gates.
"""

from dataclasses import dataclass
import json
import math
import os
import re
import time
import threading
from collections import deque
from typing import Any

import requests

from year_ahead import YearPacket


PAID_YEARLY_EDITORIAL_VERSION = "1.5-python-owned-prose-bounded-truncation"
# Per-worker token accounting. External Groq clients and other workers are not visible.
_YEARLY_DAILY_LOCK = threading.Lock()
_YEARLY_DAILY_RESERVATIONS = deque()
_YEARLY_PROVIDER_DAILY_BLOCKED_UNTIL = 0.0
_YEARLY_PROVIDER_DAILY_DETAIL = ""


def _reserve_yearly_daily_tokens(tokens: int, *, budget: int, window: float) -> None:
    """Fail before sending a request when this worker knows daily headroom is absent."""
    global _YEARLY_PROVIDER_DAILY_BLOCKED_UNTIL
    with _YEARLY_DAILY_LOCK:
        now = time.time()
        if now < _YEARLY_PROVIDER_DAILY_BLOCKED_UNTIL:
            raise RuntimeError(
                "Groq daily token allowance exhausted (TPD). "
                + _YEARLY_PROVIDER_DAILY_DETAIL
                + " Wait for the provider quota reset; do not resubmit the report yet."
            )
        while _YEARLY_DAILY_RESERVATIONS and now - _YEARLY_DAILY_RESERVATIONS[0][0] >= window:
            _YEARLY_DAILY_RESERVATIONS.popleft()
        reserved = sum(amount for _, amount in _YEARLY_DAILY_RESERVATIONS)
        if tokens > budget or reserved + tokens > budget:
            raise RuntimeError(
                f"Year Ahead daily token preflight: this worker reserved {reserved:,} "
                f"of {budget:,} configured tokens; next job requires up to {tokens:,}. "
                "Wait for the daily budget window or configure the verified Groq allowance."
            )
        _YEARLY_DAILY_RESERVATIONS.append((now, tokens))


def _remember_yearly_daily_429(error: Exception, *, window: float) -> None:
    """Learn from Groq's actual TPD error without re-calling the model."""
    global _YEARLY_PROVIDER_DAILY_BLOCKED_UNTIL, _YEARLY_PROVIDER_DAILY_DETAIL
    message = str(error)
    if not re.search(r"tokens per day|\bTPD\b", message, re.I):
        return
    used = re.search(r"Used\s+(\d+)", message, re.I)
    limit = re.search(r"Limit\s+(\d+)", message, re.I)
    requested = re.search(r"Requested\s+(\d+)", message, re.I)
    detail = (f"Provider reports used {int(used.group(1)):,} / {int(limit.group(1)):,} "
              f"tokens; attempted {int(requested.group(1)):,}. "
              if used and limit and requested else "Provider explicitly reported TPD exhaustion. ")
    with _YEARLY_DAILY_LOCK:
        # Conservative local cooldown, not a claim about the provider reset time.
        _YEARLY_PROVIDER_DAILY_BLOCKED_UNTIL = time.time() + window
        _YEARLY_PROVIDER_DAILY_DETAIL = detail


DEFAULT_TIMEOUT_SECONDS = 180
TARGET_TOTAL_TOKENS = 5350
PREFERRED_COMPLETION_TOKENS = 2500
MIN_COMPLETION_TOKENS = 1800


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
    annual_phases: tuple[tuple[str, str, str], ...] = ()
    natal_portrait: tuple[str, ...] = ()

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


def _estimate_tokens(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(str(text or "")))
    except Exception:
        return max(1, math.ceil(len(str(text or "")) / 4.0))


def _paragraphs(text: str) -> tuple[str, ...]:
    return tuple(
        part.strip()
        for part in re.split(r"\n\s*\n+", str(text or "").strip())
        if str(part or "").strip()
    )


_ISO_DATE_TOKEN_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def _annual_act_evidence(material: dict[str, Any], month_slice: list[dict[str, Any]], *, game_number: int | None = None) -> list[dict[str, Any]]:
    """Deterministic exact-contact ledger for the four rolling months in an act.

    Include only computed contacts that actually occur during that act. A Game
    spanning multiple acts is context, not licence to move its exact date.
    """
    intervals = []
    for row in month_slice:
        start, end = str(row.get("start") or "")[:10], str(row.get("end") or "")[:10]
        if start and end:
            intervals.append((start, end, row.get("number")))
    if not intervals:
        return []
    found = {}
    for game in material.get("major_issues") or []:
        if game_number is not None and int(game.get("number") or 0) != game_number:
            continue
        for transit in [game.get("primary") or {}, *(game.get("supporting") or [])]:
            technical = str(transit.get("technical") or "").strip()
            if not technical:
                continue
            for passage in transit.get("passes") or []:
                day = str(passage.get("date") or "")[:10]
                for start, end, number in intervals:
                    if start <= day <= end:
                        key = (day, technical, "exact")
                        found[key] = {"date": day, "month_number": number, "contact": technical,
                                      "kind": "exact pass", "stage": passage.get("pass_label")}
                        break
            # Supporting trigger rows may carry a date without a complete,
            # appendix-backed aspect identity. They cannot authorise narrated
            # exact planetary claims. The appendix and narrator use the same
            # primary/supporting exact-pass source of truth.
    return sorted(found.values(), key=lambda item: (item["date"], item["contact"]))



def _game_voice_evidence(game: dict[str, Any], month_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build one Game's dated narrative contract from Python-computed records.

    Only full named exact passes are permitted as planetary assertions. Unnamed
    triggers do not supply an aspect identity and cannot authorise a named claim.
    Dates outside the customer rolling year are context, not narrative dates.
    """
    months = sorted((r for r in month_rows if r.get('start') and r.get('end')),
                    key=lambda r: str(r['start']))
    if not months:
        raise RuntimeError('Year Ahead Game has no calculated rolling months')
    year_start, year_end = str(months[0]['start'])[:10], str(months[-1]['end'])[:10]
    game_start = str(game.get('start') or '')[:10]
    game_end = str(game.get('end') or '')[:10]
    if not game_start or not game_end or game_start > game_end:
        raise RuntimeError('Year Ahead Game is missing calculated active boundaries')
    narrative_start = max(year_start, game_start)
    narrative_end = min(year_end, game_end)
    if narrative_start > narrative_end:
        raise RuntimeError('Year Ahead Game does not overlap the rolling year')
    contacts = {}
    for transit in [game.get('primary') or {}, *(game.get('supporting') or [])]:
        technical = str(transit.get('technical') or '').strip()
        if not technical:
            continue
        for passage in transit.get('passes') or []:
            day = str(passage.get('date') or '')[:10]
            if narrative_start <= day <= narrative_end:
                contacts[(day, technical)] = {
                    'date': day, 'contact': technical, 'stage': passage.get('pass_label') or '',
                }
    affected = [
        {'number': m.get('number'), 'start': m.get('start'), 'end': m.get('end'),
         'phase': m.get('phase'), 'focus': m.get('focus')}
        for m in months
        if str(m['start'])[:10] <= narrative_end and str(m['end'])[:10] >= narrative_start
    ]
    return {
        'active_start': game_start, 'active_end': game_end,
        'narrative_start': narrative_start, 'narrative_end': narrative_end,
        'allowed_exact_contacts': sorted(contacts.values(), key=lambda x: (x['date'], x['contact'])),
        'overlapping_months': affected,
    }


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
    secondary_base: str = "", secondary_model: str = "", secondary_key: str = "",
) -> PaidYearlyEditorial:
    """Generate bounded yearly sections using calculated evidence, without canned prose."""
    if not str(base_url or "").strip() or not str(model or "").strip() or not str(api_key or "").strip():
        raise RuntimeError("Paid Yearly voice provider is not configured.")

    material = build_paid_yearly_material(
        packet,
        snapshot=snapshot,
        main_focus=main_focus,
        personal_question=personal_question,
        shared_year_context=shared_year_context,
    )
    from paid_voice_router import VoiceProvider, completion, cached_completion
    # Every job has one preassigned destination and its own calculated evidence.
    compact=_compact_paid_yearly_material(material,2)
    issue_numbers=[int(row.get('number') or i) for i,row in enumerate(material.get('major_issues') or [],1)]
    month_numbers=[int(row.get('number') or i) for i,row in enumerate(material.get('monthly_rounds') or [],1)]
    issue_titles={int(row.get('number') or i):str(row.get('customer_title') or '') for i,row in enumerate(material.get('major_issues') or [],1)}
    primary=VoiceProvider(base_url,model,api_key)
    alternate=VoiceProvider(secondary_base,secondary_model,secondary_key) if all((secondary_base,secondary_model,secondary_key)) else None
    # Configurable provider budget: not a claim about the account's actual rate limit.
    total_budget = int(os.environ.get('LUNA_YEARLY_REQUEST_BUDGET_TOKENS', '7800'))
    # This is a *rolling* provider quota, distinct from per-request context size.
    # Set from the actual Groq account limit when known. Conservative free-tier
    # default; do not confuse requests/day with tokens/minute.
    minute_token_budget = int(os.environ.get('LUNA_YEARLY_TOKENS_PER_MINUTE', '8000'))
    rolling_window_seconds = float(os.environ.get('LUNA_YEARLY_TOKEN_WINDOW_SECONDS', '65'))
    pacing_enabled = os.environ.get('LUNA_YEARLY_PACE_REQUESTS', '1').strip() != '0'
    request_reservations = deque()
    daily_token_budget = int(os.environ.get('LUNA_YEARLY_TOKENS_PER_DAY', '200000'))
    daily_window_seconds = float(os.environ.get('LUNA_YEARLY_DAILY_WINDOW_SECONDS', '86400'))

    def reserve_provider_capacity(estimated_input: int, completion_cap: int) -> None:
        if not pacing_enabled:
            return
        requested = estimated_input + completion_cap
        if minute_token_budget <= 0 or requested > minute_token_budget:
            raise RuntimeError(
                'Year Ahead single voice job exceeds configured tokens/minute; '
                'reduce its Python packet or output allocation before contacting Groq.'
            )
        # Reserve potential usage, not merely observed completions. Sequential
        # calls cannot otherwise know how many thinking tokens were consumed.
        while True:
            now = time.monotonic()
            while request_reservations and now - request_reservations[0][0] >= rolling_window_seconds:
                request_reservations.popleft()
            used = sum(amount for _, amount in request_reservations)
            if used + requested <= minute_token_budget:
                request_reservations.append((now, requested))
                return
            pause = max(0.05, rolling_window_seconds - (now - request_reservations[0][0]))
            time.sleep(pause)
    # Keep the long annual essay separate from short framing and closing copy.
    # These are provider completion budgets, not hard-coded astrology or forecasts.
    annual_output = int(os.environ.get('LUNA_YEARLY_ANNUAL_OUTPUT_TOKENS', '1900'))
    framing_output = int(os.environ.get('LUNA_YEARLY_FRAMING_OUTPUT_TOKENS', '1200'))
    def section(job_name, packet, output_limit, *, instruction=""):
        """One predetermined Python slot per prose-only completion.

        There is no LLM-owned section delimiter, title, JSON envelope, or marker
        parser. Checkpoint identity is a Python internal identifier.
        """
        prompt = (
            "Write ONLY the finished customer-facing prose for the single section "
            "defined by the following instructions. Do not generate structural "
            "labels, section identifiers, headings, JSON or markdown. "
            "Python has already assigned the destination and calculated the evidence. "
            "Never calculate or invent an astrological fact, date, aspect or pass. "
            "Write clear personal interpretation, not instructions or a plan. "
            + instruction + "\nCALCULATED EVIDENCE: "
            + json.dumps(packet, ensure_ascii=False, separators=(',', ':'))
        )
        estimated = math.ceil((_estimate_tokens(prompt)+_estimate_tokens(SYSTEM_PROMPT)+100)*1.15)
        if estimated + output_limit > total_budget:
            raise RuntimeError(
                f'Year Ahead {job_name} packet over configured token budget: '
                f'input={estimated}, output={output_limit}, budget={total_budget}'
            )
        messages = [{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':prompt}]
        checkpoint_id = 'yearly:prose_slots_v3135:' + job_name
        result = cached_completion(messages, primary=primary,
                                   checkpoint_id=checkpoint_id, max_output=output_limit)
        if result is None:
            # A finish_reason=length is a technical truncation, not an editorial
            # judgment. Retry it at most once with more room for GPT-OSS hidden
            # reasoning. Preserve completed checkpoints and all prose verbatim.
            # Routine successful sections still cost exactly one provider call.
            caps = [output_limit]
            # An explicit retry cap is never used unless the first completion
            # actually reached its limit. Never exceed the configured TPM or
            # per-request budget; otherwise fail with the Python section name.
            retry_cap = min(total_budget - estimated,
                            minute_token_budget - estimated,
                            max(output_limit + 600, int(output_limit * 1.6)))
            if retry_cap > output_limit:
                caps.append(retry_cap)
            for attempt, cap in enumerate(caps):
                _reserve_yearly_daily_tokens(estimated + cap,
                                             budget=daily_token_budget,
                                             window=daily_window_seconds)
                reserve_provider_capacity(estimated, cap)
                try:
                    result = completion(messages, primary=primary, secondary=alternate,
                                        max_output=cap, timeout=timeout,
                                        checkpoint_id=checkpoint_id)
                    break
                except Exception as exc:
                    _remember_yearly_daily_429(exc, window=daily_window_seconds)
                    truncated = 'completion limit reached' in str(exc).lower()
                    if truncated and attempt + 1 < len(caps):
                        continue
                    if truncated:
                        raise RuntimeError(
                            f'Year Ahead {job_name}: Groq completion truncated '
                            f'(last max_completion_tokens={cap}; '
                            f'estimated input tokens={estimated}). '
                            'The section was not accepted or rewritten.'
                        ) from exc
                    raise RuntimeError(f'Year Ahead {job_name}: {exc}') from exc
        prose = str(result or '').strip()
        if not prose:
            raise RuntimeError(f'Year Ahead {job_name} provider returned no text')
        return prose
    base={k:compact.get(k) for k in ('period','reader_context','natal')}
    written_slots={}
    intro_packet={**base,'major_issues':[{'number':g.get('number'),'title':g.get('customer_title'),'primary':g.get('primary')} for g in compact.get('major_issues') or []],
        'monthly_rounds':[{'number':m.get('number'),'phase':m.get('phase'),'strongest_date':m.get('strongest_date')} for m in compact.get('monthly_rounds') or []]}
    # Construct four Python-owned chronological phases.
    # GPT-OSS completion tokens include hidden reasoning; generating a 650-word
    # essay in one response can exhaust the cap before the prose is complete.
    # The renderer receives the same assembled dataclass contract.
    year_segments = []
    phase_metadata = []
    for chunk_index, start_month in enumerate((1, 4, 7, 10), 1):
        month_slice = [row for row in compact.get('monthly_rounds') or []
                       if start_month <= int(row.get('number') or 0) < start_month + 3]
        if not month_slice:
            raise RuntimeError(f'Year Ahead annual section {chunk_index} has no calculated month evidence')
        # Construct the act from the full, calculated material, not just month
        # headings plus all-year Game dates. Only this act's exact contacts can
        # be cited as occurring now; later Games supply undated thematic context.
        full_month_slice = [row for row in material.get('monthly_rounds') or []
                            if start_month <= int(row.get('number') or 0) < start_month + 3]
        ledger = _annual_act_evidence(material, full_month_slice)
        period_months = [
            {'number': row.get('number'), 'start': row.get('start'), 'end': row.get('end'),
             'phase': row.get('phase'), 'focus': row.get('focus'),
             'dominant_game_number': row.get('dominant_game_number')}
            for row in full_month_slice
        ]
        # A Read-the-Year act gets only its own four months and the exact
        # ephemeris-backed contacts in those months. No all-year Game catalogue:
        # future dated evidence must not leak into the earlier act's prose.
        act_start = str(full_month_slice[0].get('start') or '')[:10]
        act_end = str(full_month_slice[-1].get('end') or '')[:10]
        if not (act_start and act_end and act_start <= act_end):
            raise RuntimeError('Year Ahead calculated act boundaries are missing')
        segment_packet = {
            'period': {'start': act_start, 'end': act_end},
            'reader_context': base.get('reader_context'),
            'natal': base.get('natal'),
            'act_start_date': act_start,
            'act_end_date': act_end,
            'monthly_rounds': period_months,
            'allowed_exact_contacts': ledger,
        }
        # The four bounded calls form consecutive PHASES of a single article,
        # not three independent mini-articles. Subsequent acts receive the end
        # of the prior act to prevent restarts without replaying the full essay.
        stage = ('opening phase', 'second phase', 'third phase', 'final phase')[chunk_index - 1]
        # Do not relay prior Groq prose as factual input: earlier prose may
        # contain an invented aspect that would be amplified in a later act.
        # Calculated month phases provide continuity without fact contamination.
        continuity = (
            'Open with the first supplied monthly phase.' if chunk_index == 1 else
            'Continue the annual narrative without recapping earlier phases. '
            'The only facts permitted are in this act evidence packet.'
        )
        ending = (
            'Finish with an open transition to the next period, not a conclusion.'
            if chunk_index < 4 else
            'Finish the final act without a separate concluding paragraph; '
            'the report already has a dedicated closing synthesis.'
        )
        instruction = (
            'Write one continuous chronological READ_YEAR article in four bounded phases. '
            f'This request writes ONLY the {stage}, phase {chunk_index} of 4. '
            'Write 125–175 words of finished customer-facing narrative in 2–3 paragraphs, '
            'not a list, outline, report summary or numbered Games. '
            f'ACT DATE BOUNDARY: {act_start} through {act_end}, inclusive. '
            'Narrate only this time window, month by month, in the supplied order. '
            'Do not name an event, month, contact or event date outside this act. '
            'ASTROLOGICAL FACT WHITELIST: allowed_exact_contacts is the ONLY authority '
            'for naming a transiting planet, aspect, natal target AND exact date. '
            'You may ONLY name an exact planetary contact listed in that array. '
            'Copy its contact identity and date faithfully; never expand an unnamed trigger. '
            'The technical appendix uses the SAME pass ledger. Do not invent, assume, interpolate, relabel or transfer an unlisted '
            'conjunction, sextile, square, trine or opposition, including Sun, Venus, '
            'Mercury and other fast-moving planets. '
            'Do not infer a planet or aspect from strongest_date, phase, Game title, '
            'natal placements, or an incomplete generic trigger. '
            'When a month has no allowed named contact, interpret its supplied '
            'phase and focus in human terms, without creating a planetary claim. '
            'Do not use Game numbering or section language such as "first game", '
            '"second game", "Major Story", or internal planning headings. '
            'Do not restart the year, recap an earlier act, repeat the headline/deck, '
            'introduce generic scenario lists or summarize other chapters. '
            'Use actual named calculated transit evidence from the supplied packet '
            'for every important shift, with concrete but conditional real-life choices. '
            'Avoid season names unless supplied and verified for the reader timezone. '
            + ending + ' ' + continuity
        )
        prose = section(f'annual_{chunk_index}', segment_packet, annual_output,
                        instruction=instruction)
        year_segments.append(prose)
        phase_metadata.append((act_start, act_end, prose))
        # No generated prose is passed to a later Groq call.
    written_slots['read_year'] = '\n\n'.join(year_segments)
    # The natal portrait uses Python-calculated natal evidence.
    intro_packet['natal'] = compact.get('natal')
    framing_instruction = (
        'For NATAL_PROFILE write 145–200 words in two personalised second-person paragraphs. '
        'Describe how the calculated Sun, Moon, Ascendant (only when available), '
        'Mercury, Venus and Mars placements interact with the calculated Strengths '
        'and their natal aspects/orbs. Translate those patterns into recognisable '
        'habits, assets, blind spots and everyday examples, with alternatives rather '
        'than claims about private biography. Explain how strengths can become traps '
        'under pressure. Never invent a placement, house, orb or aspect. '
        'Explain the four supplied Strengths through recognisable daily-life behaviours: a benefit, a possible excess, and a choice the person can notice. Avoid mechanical definitions and do not invent aspects. '
        'Do not repeat the four Strengths verbatim or promise life outcomes.'
    )
    # Framing has four independent Python-owned destinations. A single free-form
    # response cannot contain four reliably recoverable sections without asking
    # the model to do formatting or introducing a post-LLM delimiter parser.
    framing_jobs = (
        ('headline', 'Write one short, distinctive customer-facing headline. One line only.', 190),
        ('deck', 'Write a concise personalised introductory deck (two sentences).', 260),
        ('natal_portrait', framing_instruction.replace('For NATAL_PROFILE write', 'Write'),
         max(framing_output, int(os.environ.get('LUNA_YEARLY_NATAL_PORTRAIT_TOKENS', '1100')))),
        ('closing', 'Write a 90–130 word closing synthesis grounded only in the calculated annual themes.', 650),
    )
    for slot, instruction, cap in framing_jobs:
        written_slots[slot] = section('framing_' + slot, intro_packet, cap, instruction=instruction)
    full_games = {int(g.get('number') or 0): g for g in material.get('major_issues') or []}
    # Individually bounded monthly slots are necessary for strict prose-only
    # output. Four free-form monthly texts cannot be separated deterministically
    # without provider-authored separators or post-response heuristics.
    for month in material.get('monthly_rounds') or []:
        number = int(month['number'])
        game_number = int(month.get('dominant_game_number') or 0)
        game = full_games.get(game_number) or {}
        allowed = _annual_act_evidence(material, [month], game_number=game_number)
        evidence = {
            'start': month.get('start'), 'end': month.get('end'),
            'number': number,
            'phase': month.get('phase'), 'focus': month.get('focus'),
            'dominant_game_number': game_number,
            'dominant_game_title': game.get('customer_title'),
            'dominant_life_area': game.get('life_area'),
            # Do not expose a separate transit catalogue with extra dates:
            # exact passes in allowed_exact_contacts are the sole date authority.
            'allowed_exact_contacts': allowed,
        }
        instruction = (
            f'Write 45–65 useful words for the single month from {evidence["start"]} '
            f'through {evidence["end"]}, inclusive. The dominant Game is the central subject. '
            'Do not import another month or unrelated Game. Only name an exact contact '
            'and date if supplied in allowed_exact_contacts. Never name a transiting '
            'planetary contact missing from this list; if empty, describe only the Game '
            'theme and the choice without attaching an aspect or date. Use conditional, specific '
            'real-life choices, not guaranteed outcomes.'
        )
        written_slots[f'month_{number}'] = section(
            f'month_{number}', {**base, 'monthly_evidence': evidence}, 460,
            instruction=instruction)
    games=compact.get('major_issues') or []
    full_games = {int(g.get('number') or 0): g for g in material.get('major_issues') or []}
    for first in range(len(games)):
        group=games[first:first+1]
        game_number=int(group[0]['number'])
        scope=_game_voice_evidence(full_games[game_number], material.get('monthly_rounds') or [])
        raw_game=group[0]
        # Keep strategic vocabulary, but exclude overlapping raw transit/triggers
        # and undated supporting events that invite reconstructed aspects/dates.
        game_theme={k:raw_game.get(k) for k in (
            'number','customer_title','strategic_frame','life_area','question',
            'advantage','risk','move','dont','start_state','end_state')}
        game_packet={**base, 'major_issues':[game_theme], 'game_evidence_contract':scope}
        game_instructions=(
            'Write ONLY the named Game in major_issues, not another twelve-month forecast. '
            'game_evidence_contract is the authoritative calculated timeline. '
            'Its narrative_start and narrative_end are absolute boundaries for this Game. '
            'Do not narrate a month or date outside these bounds or treat the annual '
            'report start as the Game start. Do not describe every overlapping month: '
            'focus on the actual calculated pass sequence, the human tension, two '
            'conditional real-life scenarios, meaningful trade-offs, and a concrete move. '
            'Only name exact planetary contacts present in game_evidence_contract.allowed_exact_contacts; '
            'copy their date, planet, aspect and natal target without alterations. '
            'Never infer Sun, Venus, Mercury, Mars or another aspect from a generic '
            'trigger, natal placement or a Game heading. If the list is empty, '
            'describe the active window without inventing exact passes. '
            'The Game heading and evidence will be rendered by Python; write prose only.'
        )
        written_slots[f'game_{game_number}'] = section(
            f'game_{game_number}', game_packet, 1700, instruction=game_instructions)
    # Assemble from Python-owned destinations; never inspect, split, rewrite,
    # or validate the editorial content of a provider completion.
    headline = written_slots['headline']
    deck = written_slots['deck']
    read_year = _paragraphs(written_slots['read_year'])
    closing = _paragraphs(written_slots['closing'])
    natal_portrait = _paragraphs(written_slots['natal_portrait'])
    monthly_rounds = tuple(
        PaidYearlyMonth(number=n, focus=written_slots[f'month_{n}'])
        for n in month_numbers
    )
    issues = tuple(
        PaidYearlyIssue(number=n, paragraphs=_paragraphs(written_slots[f'game_{n}']))
        for n in issue_numbers
    )
    all_text = ' '.join(written_slots.values())
    return PaidYearlyEditorial(
        headline=headline, deck=deck, read_year=read_year,
        issues=issues, closing=closing,
        word_count=len(all_text.split()), voice_complete=True,
        monthly_rounds=monthly_rounds, annual_phases=tuple(phase_metadata),
        natal_portrait=natal_portrait,
    )
