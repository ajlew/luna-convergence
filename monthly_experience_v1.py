from __future__ import annotations

from datetime import datetime, timedelta
from html import escape
import re
from typing import Iterable
from zoneinfo import ZoneInfo
from uuid import uuid4

from date_display import human_date, human_date_range
from luna_editorial_system import (
    DO_LABEL,
    DONT_LABEL,
    FOOTER_DISCLAIMER,
    GATEKEEPER_LINE,
    LUNA_SAYS_LABEL,
    SOLAR_LABEL,
    TECHNICAL_LABEL,
    TIMING_LABEL,
    VALIDATION_LINE,
    WHY_LUNA_LABEL,
    YOUR_MOVE_LABEL,
)
from monthly_narrative_v1 import MonthlyNarrative
from luna_voice import narrator_cue


PRINT_PAPERS = ("A4", "A3")
PRINT_ORIENTATIONS = ("portrait", "landscape")


ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

PUBLIC_LIFE_AREAS = {
    1: "identity, energy and personal direction",
    2: "income, possessions, pricing and personal security",
    3: "communication, decisions, learning and everyday movement",
    4: "home, family and private foundations",
    5: "romance, creativity, children and pleasure",
    6: "workload, wellbeing, routines and practical systems",
    7: "relationships, clients, agreements and significant partnerships",
    8: "shared money, trust, debt and joint responsibilities",
    9: "travel, education, publishing, law and the wider world",
    10: "career, reputation, authority and visible results",
    11: "friends, networks, audiences and future plans",
    12: "rest, closure, private matters and unfinished business",
}

SIGN_RULERS = {
    "Aries": ("Mars",),
    "Taurus": ("Venus",),
    "Gemini": ("Mercury",),
    "Cancer": ("Moon",),
    "Leo": ("Sun",),
    "Virgo": ("Mercury",),
    "Libra": ("Venus",),
    "Scorpio": ("Pluto", "Mars"),
    "Sagittarius": ("Jupiter",),
    "Capricorn": ("Saturn",),
    "Aquarius": ("Uranus", "Saturn"),
    "Pisces": ("Neptune", "Jupiter"),
}


def _whole_sign_name(sign: str, house: int | None) -> str:
    if house in (None, ""):
        return ""
    try:
        start = ZODIAC_SIGNS.index(str(sign))
        return ZODIAC_SIGNS[(start + int(house) - 1) % 12]
    except (ValueError, TypeError):
        return ""


def _plain_life_area(house: int | None) -> str:
    try:
        return PUBLIC_LIFE_AREAS[int(house)]
    except (KeyError, TypeError, ValueError):
        return "the active part of life"


def _plain_area_list(houses) -> str:
    values = []
    for house in houses or []:
        label = _plain_life_area(house)
        if label not in values:
            values.append(label)
    return "; ".join(values) if values else "—"


def _event_orb(event: dict) -> str:
    match = re.search(r"approximately\s+([0-9.]+)°", str(event.get("detail") or ""), flags=re.I)
    return f"~{match.group(1)}°" if match else ""


def _event_short(event: dict, *, include_date: bool = False) -> str:
    title = str(event.get("title") or "planetary contact")
    orb = _event_orb(event)
    text = f"{title}{f' ({orb})' if orb else ''}"
    if include_date and event.get("event_date"):
        text += f" on {human_date(event.get('event_date'))}"
    return text


def _beat_for_chapter(result: dict, chapter) -> dict:
    arc = result.get("monthly_arc") or {}
    beats = list(arc.get("beats") or [])
    title = str(chapter.title or "").strip()
    matching = [beat for beat in beats if str(beat.get("title") or "").strip() == title]
    if matching:
        # Prefer a beat with a real narrative house and the strongest score.
        return max(matching, key=lambda beat: (beat.get("narrative_house") not in (None, ""), float(beat.get("score", 0.0) or 0.0)))
    return {}


def _window_events(result: dict, beat: dict, *, lookback_days: int = 7) -> list[dict]:
    if not beat.get("start_date"):
        return []
    try:
        start = datetime.fromisoformat(str(beat.get("start_date"))).date() - timedelta(days=lookback_days)
        end = datetime.fromisoformat(str(beat.get("end_date") or beat.get("start_date"))).date()
    except ValueError:
        return []
    selected = []
    for event in result.get("events") or []:
        try:
            event_date = datetime.fromisoformat(str(event.get("event_date"))).date()
        except (TypeError, ValueError):
            continue
        if start <= event_date <= end and float(event.get("importance", 0.0) or 0.0) >= 5.2:
            if set(event.get("planets") or []) == {"Moon"} and event.get("kind") not in {"lunation", "eclipse"}:
                continue
            selected.append(event)
    return selected


def _month_to_date_focus_events(result: dict, beat: dict, narrative_house: int | None) -> list[dict]:
    if narrative_house in (None, "") or not beat.get("end_date"):
        return []
    try:
        end = datetime.fromisoformat(str(beat.get("end_date"))).date()
        month_start = end.replace(day=1)
    except ValueError:
        return []
    selected = []
    for event in result.get("events") or []:
        try:
            event_date = datetime.fromisoformat(str(event.get("event_date"))).date()
        except (TypeError, ValueError):
            continue
        if not month_start <= event_date <= end:
            continue
        if int(narrative_house) not in [int(value) for value in (event.get("houses") or [])]:
            continue
        if event.get("kind") not in {"ingress", "lunation", "eclipse", "station"}:
            continue
        if float(event.get("importance", 0.0) or 0.0) < 5.5:
            continue
        selected.append(event)
    return selected


def _chapter_context(result: dict, index: int, total: int) -> dict:
    arc = result.get("monthly_arc") or {}
    beats = {str(item.get("role") or "").lower(): dict(item) for item in (arc.get("beats") or [])}
    primary = arc.get("primary_house")
    secondary = arc.get("secondary_house")
    tertiary = arc.get("tertiary_house")

    if index == 0:
        selected = [beat for beat in (beats.get("inherited state"), beats.get("inciting event")) if beat]
        target_house = primary
        role = "opening"
    elif index == 1:
        selected = [beat for beat in (beats.get("complication"),) if beat]
        target_house = primary
        role = "complication"
    elif total >= 4 and index == 2:
        selected = [beat for beat in (beats.get("pivot"), beats.get("relationship test")) if beat]
        target_house = tertiary or (selected[0].get("narrative_house") if selected else secondary)
        role = "bridge"
    else:
        selected = [beat for beat in (beats.get("climax"), beats.get("resolution")) if beat]
        target_house = secondary
        role = "resolution"

    dates = [str(beat.get("start_date")) for beat in selected if beat.get("start_date")]
    ends = [str(beat.get("end_date") or beat.get("start_date")) for beat in selected if beat.get("start_date")]
    return {
        "role": role,
        "target_house": int(target_house) if target_house not in (None, "") else None,
        "start_date": min(dates) if dates else "",
        "end_date": max(ends) if ends else (min(dates) if dates else ""),
        "beats": selected,
    }


def _direct_story_event(result: dict, context: dict) -> dict:
    target_house = context.get("target_house")
    if target_house in (None, "") or not context.get("start_date"):
        return {}
    try:
        start = datetime.fromisoformat(str(context.get("start_date"))).date() - timedelta(days=7)
        end = datetime.fromisoformat(str(context.get("end_date") or context.get("start_date"))).date() + timedelta(days=2)
    except ValueError:
        return {}

    candidates = []
    for event in result.get("events") or []:
        try:
            event_date = datetime.fromisoformat(str(event.get("event_date"))).date()
        except (TypeError, ValueError):
            continue
        if not start <= event_date <= end:
            continue
        if int(target_house) not in [int(value) for value in (event.get("houses") or [])]:
            continue
        if float(event.get("importance", 0.0) or 0.0) < 5.2:
            continue
        if set(event.get("planets") or []) == {"Moon"} and event.get("kind") not in {"lunation", "eclipse"}:
            continue
        candidates.append(event)
    if not candidates:
        return {}

    role = str(context.get("role") or "")
    def key(event: dict):
        kind = str(event.get("kind") or "")
        polarity = str(event.get("polarity") or "")
        role_bonus = 0.0
        if role in {"complication", "resolution"} and kind in {"lunation", "eclipse"}:
            role_bonus += 1.2
        if role == "opening" and polarity in {"pressure", "opportunity"}:
            role_bonus += 0.4
        return float(event.get("importance", 0.0) or 0.0) + role_bonus
    return max(candidates, key=key)


def _context_for_evidence(context: dict, display_event: dict) -> dict:
    beats = list(context.get("beats") or [])
    best = max(beats, key=lambda beat: float(beat.get("score", 0.0) or 0.0)) if beats else {}
    return {
        "start_date": context.get("start_date") or display_event.get("event_date") or "",
        "end_date": context.get("end_date") or display_event.get("event_date") or "",
        "narrative_house": context.get("target_house"),
        "strategy_posture": best.get("strategy_posture") or "",
    }


def _sky_evidence_for_chapter(narrative: MonthlyNarrative, result: dict, chapter, *, context: dict | None = None) -> str:
    """Plain-language evidence placed beside the customer interpretation.

    House numbers stay internal. If Luna has verified a concentrated pattern, it
    states the count and names the planets/aspects instead of hiding behind vague
    phrases such as 'several signals'.
    """
    beat = dict(context or _beat_for_chapter(result, chapter) or {})
    if not beat:
        evidence = list(chapter.evidence or ())
        return "; ".join(evidence[:3])

    narrative_house = beat.get("narrative_house")
    area = _plain_life_area(narrative_house)
    zodiac_area = _whole_sign_name(narrative.sign, narrative_house)
    window_events = _window_events(result, beat)
    focus_events = _month_to_date_focus_events(result, beat, narrative_house)

    parts: list[str] = []
    if zodiac_area and narrative_house not in (None, ""):
        parts.append(
            f"For {narrative.sign}, {zodiac_area} describes {area}."
        )

    # If several bodies have accumulated in the same life area, say exactly how
    # many and name the events that establish the concentration.
    if len(focus_events) >= 3:
        planets = []
        for event in focus_events:
            for planet in event.get("planets") or []:
                if planet not in planets:
                    planets.append(str(planet))
        event_list = "; ".join(_event_short(event, include_date=True) for event in focus_events[-5:])
        parts.append(
            f"The concentration is visible in the sky: {len(planets)} planets are involved in {len(focus_events)} major movements in this same area by this point — {event_list}."
        )

    pressure = [
        event for event in window_events
        if event.get("kind") == "aspect" and str(event.get("polarity") or "") == "pressure"
    ]
    supportive = [
        event for event in window_events
        if event.get("kind") == "aspect" and str(event.get("polarity") or "") == "opportunity"
    ]

    if pressure:
        pressure_planets = []
        for event in pressure:
            for planet in event.get("planets") or []:
                if planet not in pressure_planets and planet not in {"Moon", "True Node"}:
                    pressure_planets.append(str(planet))
        examples = "; ".join(_event_short(event) for event in pressure[:4])
        noun = "pressure contact" if len(pressure) == 1 else "pressure contacts"
        parts.append(
            f"The pressure is explicit, not inferred: {len(pressure_planets)} planets are involved in {len(pressure)} exact {noun} in this build-up — {examples}."
        )

    if supportive:
        examples = "; ".join(_event_short(event) for event in supportive[:3])
        if pressure:
            parts.append(f"Support is present too — {examples}.")
        else:
            parts.append(f"The supportive evidence is equally concrete — {examples}.")

    rulers = set(SIGN_RULERS.get(narrative.sign, ()))
    ruler_events = [event for event in window_events if set(event.get("planets") or []) & rulers]
    if ruler_events:
        ruler_names = ", ".join(sorted(rulers & {str(p) for event in ruler_events for p in (event.get("planets") or [])}))
        if ruler_names:
            parts.append(f"{ruler_names}, the ruling planet{'s' if ',' in ruler_names else ''} for {narrative.sign}, {'are' if ',' in ruler_names else 'is'} part of the evidence in this window.")

    if not parts:
        evidence = list(chapter.evidence or ())
        return "; ".join(evidence[:3])
    return " ".join(parts)


def _chapter_strategy_label(result: dict, chapter, *, context: dict | None = None) -> str:
    beat = dict(context or _beat_for_chapter(result, chapter) or {})
    posture = str(beat.get("strategy_posture") or "").strip().upper() if beat else ""
    return posture


def _safe(value: object) -> str:
    return escape(str(value or ""), quote=True)


def _paragraphs(values: Iterable[str], maximum: int | None = None) -> str:
    selected = list(values)
    if maximum is not None:
        selected = selected[:maximum]
    return "".join(f"<p>{_safe(value)}</p>" for value in selected if value)


def _generated_report_details(narrative: MonthlyNarrative, result: dict) -> dict[str, str]:
    """Return stable, human-readable metadata embedded in the printable report.

    Browser print headers are inconsistent and can be disabled, so Luna places its
    own report identity inside the document. The timestamp is calculated in the
    report's selected/browser timezone rather than the Streamlit server timezone.
    """
    timezone_name = str(result.get("timezone_name") or "UTC")
    try:
        timezone = ZoneInfo(timezone_name)
    except Exception:
        timezone_name = "UTC"
        timezone = ZoneInfo("UTC")

    now = datetime.now(timezone)
    hour = now.strftime("%I").lstrip("0") or "0"
    minute = now.strftime("%M")
    meridiem = now.strftime("%p").lower()
    time_label = f"{hour}:{minute}{meridiem}"
    month_label = str(narrative.label)
    sign_label = str(narrative.sign)
    display_title = f"{sign_label} {time_label} {month_label}"

    # Preserve Luna's original, sortable monthly PDF naming convention.
    # Browser print-to-PDF uses the document title as the proposed filename,
    # so a Virgo report for August 2026 should prefill as:
    # 2026-08_Virgo_Monthly.pdf
    try:
        parsed_month = datetime.strptime(month_label, "%B %Y")
        period_key = parsed_month.strftime("%Y-%m")
    except Exception:
        try:
            period_key = datetime.fromisoformat(str(result.get("start", ""))).strftime("%Y-%m")
        except Exception:
            period_key = month_label.replace(" ", "-")
    safe_sign = "".join(ch for ch in sign_label if ch.isalnum() or ch in ("-", "_")) or "Report"
    file_title = f"{period_key}_{safe_sign}_Monthly"
    generated_date = f"{now.day} {now.strftime('%B %Y')}"
    zone_short = now.tzname() or timezone_name

    return {
        "sign": sign_label,
        "month": month_label,
        "time": time_label,
        "display_title": display_title,
        "file_title": file_title,
        "generated_date": generated_date,
        "timezone": f"{zone_short} · {timezone_name}",
    }


def _report_details_html(details: dict[str, str]) -> str:
    return f"""
<div class="luna-report-details" aria-label="Report details">
  <strong class="luna-report-identity">{_safe(details['display_title'])}</strong>
  <span class="luna-report-generated">Generated {_safe(details['generated_date'])} · {_safe(details['timezone'])}</span>
</div>
    """


def _key_date_cards(narrative: MonthlyNarrative) -> str:
    return "".join(
        f"""
<article class="luna-date-card">
  <span>{_safe(item.date_label)}</span>
  <strong>{_safe(item.consequence)}</strong>
  <p>{_safe(item.response)}</p>
  <small>{_safe(item.evidence)}</small>
</article>
        """
        for item in narrative.key_dates
    )


def _story_date_cards(narrative: MonthlyNarrative) -> str:
    dates = list(narrative.key_dates)
    if not dates:
        return ""

    if len(dates) <= 4:
        selected = dates
    else:
        indexes = (0, len(dates) // 2, max(len(dates) - 2, 0), len(dates) - 1)
        selected = []
        for index in indexes:
            item = dates[index]
            if item not in selected:
                selected.append(item)

    return "".join(
        f"""
<article class="luna-story-date-card">
  <span>{_safe(item.date_label)}</span>
  <strong>{_safe(item.consequence)}</strong>
  <p>{_safe(item.response)}</p>
</article>
        """
        for item in selected
    )


def _technical_rows(result: dict) -> str:
    rows = []
    for item in (result.get("dominant_houses") or [])[:6]:
        house = item.get("house")
        rows.append(
            "<tr>"
            f"<td>{_safe(_plain_life_area(house))}</td>"
            f"<td>{_safe(item.get('topic'))}</td>"
            f"<td>{float(item.get('weight', 0.0)):.1f}</td>"
            "</tr>"
        )
    return "".join(rows)


def _story_driver_rows(result: dict) -> str:
    arc = result.get("monthly_arc") or {}
    public_roles = {
        "inherited state", "inciting event", "complication", "pivot",
        "relationship test", "climax", "resolution",
    }
    rows = []
    for beat in arc.get("beats") or []:
        role = str(beat.get("role") or "").lower()
        if role not in public_roles or float(beat.get("score", 0.0) or 0.0) <= 0:
            continue
        direct = _plain_area_list(beat.get("direct_houses") or [])
        connected = _plain_area_list(beat.get("connected_houses") or [])
        narrative_house = beat.get("narrative_house")
        narrative = _plain_life_area(narrative_house) if narrative_house not in (None, "") else "—"
        path = f"{direct} → {narrative}"
        if connected != "—":
            path += f" · connected with {connected}"
        raw_reason = str(beat.get("connection_reason") or "direct event / cluster evidence")
        if raw_reason == "direct event house":
            reason = "directly activated by this event"
        elif "promoted through" in raw_reason:
            reason = "promoted because the wider event cluster connects this life area to the main story"
        else:
            reason = raw_reason.replace("house", "life area")
        rows.append(
            "<tr>"
            f"<td>{_safe(role.replace('_', ' ').title())}</td>"
            f"<td>{_safe(beat.get('title'))}</td>"
            f"<td>{_safe(path)}</td>"
            f"<td>{_safe(reason)}</td>"
            f"<td>{float(beat.get('score', 0.0)):.1f}</td>"
            "</tr>"
        )
    # Make the convergent bridge auditable in plain customer language.
    tertiary = arc.get("tertiary_house")
    if tertiary not in (None, ""):
        rows.append(
            "<tr>"
            "<td>Bridge</td>"
            f"<td>{_safe(_plain_life_area(tertiary))}</td>"
            f"<td>{_safe(_plain_life_area(arc.get('primary_house')))} → {_safe(_plain_life_area(tertiary))} → {_safe(_plain_life_area(arc.get('secondary_house')))}</td>"
            f"<td>{_safe('Promoted because this life area is present in both the opening and result event clusters, linking ' + _plain_life_area(arc.get('primary_house')) + ' with ' + _plain_life_area(arc.get('secondary_house')) + '.')}</td>"
            f"<td>{float(arc.get('convergence_score', 0.0) or 0.0):.1f}</td>"
            "</tr>"
        )
    return "".join(rows)


def _transition_rows(result: dict) -> str:
    rows = []
    for item in (result.get("major_transitions") or [])[:12]:
        rows.append(
            "<tr>"
            f"<td>{_safe(human_date(item.get('event_date')))}</td>"
            f"<td>{_safe(item.get('title'))}</td>"
            f"<td>{_safe(_plain_area_list(item.get('houses') or []))}</td>"
            "</tr>"
        )
    return "".join(rows)


def _decision_evidence_rows(result: dict) -> str:
    decision = dict(result.get("monthly_decision") or {})
    rows = (
        ("Overall climate", decision.get("climate_label", "n/a")),
        ("Support share", f"{float(decision.get('support_score', 0.0)):.1f}"),
        ("Friction share", f"{float(decision.get('friction_score', 0.0)):.1f}"),
        ("Uncertainty share", f"{float(decision.get('uncertainty_score', 0.0)):.1f}"),
        ("Support minus friction", f"{float(decision.get('evidence_balance', 0.0)):+.1f}"),
        ("Capacity", f"{decision.get('capacity_label', 'n/a')} ({float(decision.get('capacity_pressure', 0.0)):.1f}/100)"),
        ("Truth gate", f"{decision.get('action_truth', 'n/a')} · {decision.get('posture', 'n/a')}"),
        ("Portfolio strategy", decision.get("portfolio_posture", "n/a")),
    )
    return "".join(
        f"<tr><td>{_safe(label)}</td><td>{_safe(value)}</td></tr>" for label, value in rows
    )


def _retrograde_rows(result: dict) -> str:
    rows = []
    for item in (result.get("retrograde_cycles") or [])[:8]:
        rows.append(
            "<tr>"
            f"<td>{_safe(item.get('planet'))}</td>"
            f"<td>{_safe(human_date(item.get('retrograde_start')))}</td>"
            f"<td>{_safe(human_date(item.get('direct_date')))}</td>"
            f"<td>{_safe(_plain_area_list(item.get('houses') or []))}</td>"
            "</tr>"
        )
    return "".join(rows)


def _arc_evidence_path(result: dict) -> str:
    arc = result.get("monthly_arc") or {}
    beats = {
        str(item.get("role", "")).lower(): item
        for item in (arc.get("beats") or [])
    }

    beginning = beats.get("inherited state") or beats.get("inciting event")
    middle = beats.get("complication") or beats.get("pivot")
    relationship = beats.get("relationship test")
    ending_items = [
        item
        for key in ("pivot", "climax", "resolution")
        if (item := beats.get(key)) is not None
    ]

    anchors: list[tuple[str, str, str]] = []
    if beginning:
        anchors.append((
            "Starting condition",
            human_date_range(
                beginning.get("start_date"),
                beginning.get("end_date", beginning.get("start_date")),
            ),
            str(beginning.get("title", "Carryover trigger")),
        ))
    if middle:
        anchors.append((
            "Midmonth test",
            human_date_range(
                middle.get("start_date"),
                middle.get("end_date", middle.get("start_date")),
            ),
            str(middle.get("title", "Turning point")),
        ))
    if relationship:
        anchors.append((
            "Relationship test",
            human_date_range(
                relationship.get("start_date"),
                relationship.get("end_date", relationship.get("start_date")),
            ),
            str(relationship.get("title", "Attention meets standards")),
        ))
    if ending_items:
        first = ending_items[0]
        last = ending_items[-1]
        titles = []
        for item in ending_items:
            title = str(item.get("title", "")).strip()
            if title and title not in titles:
                titles.append(title)
        anchors.append((
            "Release and result",
            human_date_range(
                first.get("start_date"),
                last.get("end_date", last.get("start_date")),
            ),
            ", ".join(titles),
        ))

    return "".join(
        f"""
<div class="luna-evidence-anchor">
  <span>{_safe(label)}</span>
  <strong>{_safe(window)}</strong>
  <p>{_safe(title)}</p>
</div>
        """
        for label, window, title in anchors
    )

def _scenario_rows_html(result: dict) -> str:
    arc = result.get("monthly_arc") or {}
    rows = []
    for item in (arc.get("ranked_scenarios") or [])[:8]:
        examples = "; ".join(str(value) for value in (item.get("examples") or [])[:2])
        rows.append(
            "<tr>"
            f"<td>{_safe(item.get('label'))}</td>"
            f"<td>{_safe(item.get('confidence'))}</td>"
            f"<td>{_safe(examples)}</td>"
            "</tr>"
        )
    return "".join(rows)


def _carryover_rows_html(result: dict) -> str:
    arc = result.get("monthly_arc") or {}
    rows = []
    for item in arc.get("inherited_events") or []:
        rows.append(
            "<tr>"
            f"<td>{_safe(human_date(item.get('event_date')))}</td>"
            f"<td>{_safe(item.get('title'))}</td>"
            f"<td>{_safe(_plain_area_list(item.get('houses') or []))}</td>"
            "</tr>"
        )
    return "".join(rows)


def _chapter_cards(narrative: MonthlyNarrative, result: dict) -> str:
    prepared = []
    total = len(narrative.chapters)
    for index, chapter in enumerate(narrative.chapters):
        context = _chapter_context(result, index, total)
        display_event = _direct_story_event(result, context)
        evidence_context = _context_for_evidence(context, display_event)
        display_title = str(display_event.get("title") or chapter.title)
        exact_date = human_date(display_event.get("event_date")) if display_event.get("event_date") else ""
        window = chapter.date_range
        sky_evidence = _sky_evidence_for_chapter(narrative, result, chapter, context=evidence_context)
        strategy = _chapter_strategy_label(result, chapter, context=evidence_context)
        prepared.append({
            "chapter": chapter,
            "context": context,
            "display_title": display_title,
            "exact_date": exact_date,
            "window": window,
            "sky_evidence": sky_evidence,
            "strategy": strategy,
            "event_key": (str(display_event.get("event_date") or ""), display_title),
        })

    # If the bridge and resolution genuinely use the same astronomical event,
    # tell the story once and let the interpretation progress inside that card.
    merged = []
    for item in prepared:
        if merged and item["event_key"] != ("", "") and item["event_key"] == merged[-1]["event_key"]:
            previous = merged[-1]
            previous["paragraphs"].extend(list(item["chapter"].paragraphs))
            previous["actions"].append((item["strategy"], item["chapter"].action))
            previous_house = previous["context"].get("target_house")
            current_house = item["context"].get("target_house")
            if current_house not in (None, "") and current_house != previous_house:
                current_area = _plain_life_area(current_house)
                previous["sky_evidence"] += (
                    f" The same astronomical event also directly connects with {current_area}, "
                    "which is why Luna uses it again as the closing test rather than inventing a separate event."
                )
            continue
        merged.append({
            **item,
            "paragraphs": list(item["chapter"].paragraphs),
            "actions": [(item["strategy"], item["chapter"].action)],
        })

    acts = []
    for item in merged:
        chapter = item["chapter"]
        exact_date = item["exact_date"]
        if exact_date and exact_date != item["window"]:
            date_html = (
                f'<span>{_safe(exact_date)}</span>'
                f'<small>{_safe(item["display_title"])}</small>'
                f'<em>Influence window: {_safe(item["window"])}</em>'
            )
        else:
            date_html = (
                f'<span>{_safe(item["window"])}</span>'
                f'<small>{_safe(item["display_title"])}</small>'
            )

        action_lines = []
        seen_actions = set()
        for strategy, action in item["actions"]:
            key = (strategy, action)
            if key in seen_actions:
                continue
            seen_actions.add(key)
            move_label = f"Luna's move — {strategy}" if strategy else "Luna's move"
            action_lines.append(f'<p class="luna-chapter-move"><strong>{_safe(move_label)}:</strong> {_safe(action)}</p>')

        acts.append(
            f"""
<article class="luna-story-act">
  <div class="luna-story-date">
    {date_html}
  </div>
  <div class="luna-story-copy">
    {f'<div class="luna-sky-evidence"><span>Why Luna says this</span><p>{_safe(item["sky_evidence"])}</p></div>' if item["sky_evidence"] else ''}
    <h3>{_safe(chapter.hook)}</h3>
    {_paragraphs(item["paragraphs"])}
    {''.join(action_lines)}
  </div>
</article>
            """
        )
    return "".join(acts)


def _life_rows(narrative: MonthlyNarrative, result: dict) -> str:
    decisions = dict((result.get("monthly_decision") or {}).get("domain_decisions") or {})
    sections = (
        ("Love", "romance", narrative.love_hook, narrative.love_story[0]),
        ("Work", "work", narrative.work_hook, narrative.work_story[0]),
        ("Money", "money", narrative.money_hook, narrative.money_story[0]),
    )
    rows = []
    for label, key, hook, copy in sections:
        decision = dict(decisions.get(key) or {})
        strategy = " · ".join(
            value for value in (str(decision.get("action_truth", "")), str(decision.get("posture", ""))) if value
        )
        rows.append(
            f"""
<article class="luna-life-row">
  <span>{_safe(label)}{f'<small>{_safe(strategy)}</small>' if strategy else ''}</span>
  <h3>{_safe(hook)}</h3>
  <p>{_safe(copy)}</p>
</article>
            """
        )
    return "".join(rows)


def _print_controls(
    default_paper: str,
    default_orientation: str,
    instance_id: str,
) -> str:
    paper_options = "".join(
        f'<option value="{paper}"'
        + (" selected" if paper == default_paper else "")
        + f">{paper}</option>"
        for paper in PRINT_PAPERS
    )
    orientation_options = "".join(
        f'<option value="{orientation}"'
        + (" selected" if orientation == default_orientation else "")
        + f">{orientation.title()}</option>"
        for orientation in PRINT_ORIENTATIONS
    )
    return f"""
<div class="luna-print-controls">
  <div class="luna-print-field">
    <label for="{instance_id}-paper">Paper</label>
    <select id="{instance_id}-paper" data-luna-paper>{paper_options}</select>
  </div>
  <div class="luna-print-field">
    <label for="{instance_id}-orientation">Orientation</label>
    <select id="{instance_id}-orientation" data-luna-orientation>{orientation_options}</select>
  </div>
  <button id="{instance_id}-print" data-luna-print type="button">Print / Save PDF</button>
</div>
    """


def build_monthly_experience_html(
    narrative: MonthlyNarrative,
    result: dict,
    *,
    show_print: bool = True,
    preview: bool = False,
    order_reference: str = "",
    default_paper: str = "A4",
    default_orientation: str = "portrait",
) -> str:
    if default_paper not in PRINT_PAPERS:
        raise ValueError(f"Unsupported paper: {default_paper}")
    if default_orientation not in PRINT_ORIENTATIONS:
        raise ValueError(f"Unsupported orientation: {default_orientation}")

    instance_id = f"luna-monthly-{uuid4().hex}"
    chapters = _chapter_cards(narrative, result)
    life_rows = _life_rows(narrative, result)
    arc_evidence_path = _arc_evidence_path(result)
    scenario_rows = _scenario_rows_html(result)
    carryover_rows = _carryover_rows_html(result)

    relationship_test_section = ""
    if narrative.relationship_test:
        relationship_test_section = f"""
<section class="luna-monthly-section luna-relationship-test">
  <div class="luna-eyebrow">{_safe(narrator_cue("monthly", 1))}</div>
  <h2>{_safe(narrative.relationship_test[0])}</h2>
  {_paragraphs(narrative.relationship_test[1:])}
</section>
        """

    # v3.11: Romance remains in the domain map and, when Nature supports it,
    # appears inside the chronology as a countercurrent/relationship test.  The
    # old standalone "Romance and validation" block repeated generic copy and
    # could float free of the actual sky, so it is no longer customer-rendered.
    romance_section = ""

    focus_section = ""
    if (
        narrative.main_focus != "General overview"
        or narrative.personal_question
    ):
        question_html = (
            f'<blockquote class="luna-question">{_safe(narrative.personal_question)}</blockquote>'
            if narrative.personal_question
            else ""
        )
        focus_section = f"""
<section class="luna-monthly-section luna-focus-section">
  <div class="luna-eyebrow">{_safe(narrative.focus_title)}</div>
  {question_html}
  {_paragraphs(narrative.focus_answer, maximum=2)}
</section>
        """

    evidence = f"""
<section class="luna-evidence-stack">
  <details>
    <summary>{_safe(WHY_LUNA_LABEL)} <span>+</span></summary>
    <div class="luna-detail-body">
      <p>{_safe(narrative.central_storyline)}</p>
      <p><strong>Intensity:</strong> {_safe((result.get("monthly_arc") or {}).get("intensity_rating", "Steady"))}</p>
      {f'<p><strong>Trajectory:</strong> {_safe((result.get("monthly_trajectory") or {}).get("trajectory_reason", ""))}</p>' if result.get("monthly_trajectory") else ''}
      {f'<p><strong>Countercurrent:</strong> {_safe(((result.get("monthly_trajectory") or {}).get("countercurrent") or {}).get("summary", ""))}</p>' if ((result.get("monthly_trajectory") or {}).get("countercurrent") or {}) else ''}
      <h3>Evidence path</h3>
      <div class="luna-evidence-path">{arc_evidence_path}</div>
      <p><strong>Rule:</strong> {_safe(narrative.validation_rule)}</p>
    </div>
  </details>

  <details>
    <summary>Solar background <span>+</span></summary>
    <div class="luna-detail-body">
      <p class="luna-method-note"><strong>Background current:</strong> this slower solar movement adds context; it does not replace the event-led monthly story above.</p>
      <h3>{_safe(narrative.solar_title)}</h3>
      {_paragraphs(narrative.solar_paragraphs, maximum=2)}
      <div class="luna-evidence-grid">
        {''.join(
            f'<div><span>{_safe(label)}</span><strong>{_safe(value)}</strong></div>'
            for label, value in narrative.solar_rows
        )}
      </div>
      <p><strong>Opportunity:</strong> {_safe(narrative.solar_opportunity)}</p>
      <p><strong>Risk:</strong> {_safe(narrative.solar_risk)}</p>
      <p><strong>Response:</strong> {_safe(narrative.solar_action)}</p>
    </div>
  </details>


  <details>
    <summary>{_safe(TECHNICAL_LABEL)} <span>+</span></summary>
    <div class="luna-detail-body">
      <h3>Carryover evidence</h3>
      <div class="luna-table-wrap">
        <table>
          <thead><tr><th>Date</th><th>Evidence</th><th>Life areas</th></tr></thead>
          <tbody>{carryover_rows}</tbody>
        </table>
      </div>
      <h3>Narrative evidence ledger</h3>
      <p class="luna-method-note">Every event used publicly is traceable here. The direct area comes from the event itself; connected areas come from the wider event cluster; the story area is the life area Luna selected for that narrative role.</p>
      <div class="luna-table-wrap">
        <table>
          <thead><tr><th>Role</th><th>Event</th><th>Direct area → story area</th><th>Why connected</th><th>Score</th></tr></thead>
          <tbody>{_story_driver_rows(result)}</tbody>
        </table>
      </div>
      <h3>Decision evidence</h3>
      <p class="luna-method-note">Support, friction and uncertainty are normalized symbolic evidence shares, not probabilities. Capacity is a separate decision-load index.</p>
      <div class="luna-table-wrap">
        <table>
          <thead><tr><th>Decision measure</th><th>Result</th></tr></thead>
          <tbody>{_decision_evidence_rows(result)}</tbody>
        </table>
      </div>
      <h3>Major transitions</h3>
      <div class="luna-table-wrap">
        <table>
          <thead><tr><th>Date</th><th>Evidence</th><th>Life areas</th></tr></thead>
          <tbody>{_transition_rows(result)}</tbody>
        </table>
      </div>
      <h3>Retrograde climate</h3>
      <div class="luna-table-wrap">
        <table>
          <thead><tr><th>Planet</th><th>Retrograde</th><th>Direct</th><th>Life areas</th></tr></thead>
          <tbody>{_retrograde_rows(result)}</tbody>
        </table>
      </div>
      {f'<p><strong>Order reference:</strong> {_safe(order_reference)}</p>' if order_reference else ''}
    </div>
  </details>
</section>
    """

    body = ""
    if not preview:
        body = f"""
<section class="luna-monthly-section luna-opening-story">
  <div class="luna-eyebrow">{_safe(LUNA_SAYS_LABEL)}</div>
  <h2>{_safe(narrative.central_storyline)}</h2>
  <div class="luna-story-prose">
    {_paragraphs(narrative.luna_says)}
  </div>
  <div class="luna-do-dont luna-do-dont-light">
    <div><span>{_safe(DO_LABEL)}</span><strong>{_safe(narrative.do_line)}</strong></div>
    <div><span>{_safe(DONT_LABEL)}</span><strong>{_safe(narrative.dont_line)}</strong></div>
  </div>
</section>

{focus_section}

<section class="luna-monthly-section luna-story-section">
  <div class="luna-eyebrow">How {_safe(narrative.label.split()[0])} unfolds</div>
  <div class="luna-story-timeline">{chapters}</div>
</section>

{relationship_test_section}


{romance_section}

<section class="luna-monthly-section">
  <div class="luna-eyebrow">Where the story lands</div>
  <div class="luna-life-list">{life_rows}</div>
</section>

<section class="luna-monthly-section luna-next-move">
  <div>
    <div class="luna-eyebrow">{_safe(YOUR_MOVE_LABEL)}</div>
    <div class="luna-strategy-badge">{_safe(narrative.portfolio_posture or (narrative.decision_truth + ' · ' + narrative.strategic_posture))}</div>
    <h2>From reading the future to writing it.</h2>
    <p class="luna-strategy-rationale">{_safe(narrative.portfolio_rationale or narrative.strategic_rationale)}</p>
  </div>
  <ol>
    {''.join(f'<li>{_safe(action)}</li>' for action in narrative.action_plan)}
  </ol>
</section>

{evidence}
        """
    else:
        body = f"""
<section class="luna-monthly-section luna-opening-story">
  <div class="luna-eyebrow">{_safe(LUNA_SAYS_LABEL)}</div>
  <h2>{_safe(narrative.central_storyline)}</h2>
  {_paragraphs(narrative.luna_says, maximum=2)}
</section>
        """

    controls = (
        _print_controls(default_paper, default_orientation, instance_id)
        if show_print
        else ""
    )
    report_identity = _generated_report_details(narrative, result)
    report_details = _report_details_html(report_identity)
    print_file_title = report_identity["file_title"]

    return f"""
<div id="{instance_id}" class="luna-monthly-instance" data-luna-instance>
<style id="{instance_id}-page-size" data-luna-page-size>
@page {{ size: {default_paper} {default_orientation}; margin: 12mm; }}
</style>
<style>
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,400;6..96,500;6..96,600&family=IBM+Plex+Mono:wght@400;500;600&family=Josefin+Sans:wght@300;400;500;600;700&display=swap');

.luna-monthly-report {{
  --black:#050505;
  --white:#fff;
  --soft:#f5f5f2;
  --line:#d8d8d3;
  --muted:#696963;
  width:100%;
  max-width:900px;
  margin:0 auto;
  color:var(--black);
  background:var(--white);
  font-family:"Josefin Sans","Avenir Next","Century Gothic",Arial,sans-serif;
}}
.luna-monthly-report * {{ box-sizing:border-box; }}
.luna-monthly-report h1,
.luna-monthly-report h2,
.luna-monthly-report h3 {{
  font-family:"Bodoni MT","Bodoni 72","Bodoni Moda",Didot,Georgia,serif;
  font-weight:500;
  letter-spacing:-.035em;
}}
.luna-monthly-report p {{
  font-size:clamp(.98rem,1.35vw,1.12rem);
  line-height:1.58;
  margin:.4rem 0 .9rem;
}}
.luna-monthly-hero {{
  display:grid;
  gap:.85rem;
  min-height:0 !important;
  height:auto !important;
  max-height:none !important;
  padding:clamp(1.15rem,2.8vw,2rem);
  color:#fff !important;
  background:#050505 !important;
}}
.luna-monthly-meta {{
  display:flex;
  justify-content:space-between;
  gap:1rem;
  padding-bottom:.7rem;
  border-bottom:1px solid rgba(255,255,255,.28);
  color:#fff !important;
  font-family:"IBM Plex Mono",monospace;
  font-size:.65rem;
  letter-spacing:.045em;
  text-transform:uppercase;
}}
.luna-monthly-hero h1 {{
  display:block !important;
  visibility:visible !important;
  opacity:1 !important;
  position:relative;
  z-index:2;
  max-width:760px;
  margin:.45rem 0 .3rem;
  color:#fff !important;
  font-size:clamp(2.45rem,5.5vw,4.45rem);
  line-height:.95;
}}
.luna-hero-theme {{
  display:grid;
  grid-template-columns:auto 1fr;
  gap:.7rem;
  align-items:baseline;
  color:rgba(255,255,255,.78);
}}
.luna-hero-theme span,
.luna-says span,
.luna-eyebrow,
.luna-story-date span,
.luna-romance-grid span,
.luna-life-row > span {{
  font-family:"IBM Plex Mono",monospace;
  font-size:.65rem;
  letter-spacing:.05em;
  text-transform:uppercase;
}}
.luna-hero-theme strong {{
  font-size:.95rem;
  font-weight:400;
  line-height:1.35;
}}
.luna-monthly-section {{
  padding:clamp(2.25rem,5vw,4.3rem) clamp(1rem,4vw,3.2rem);
  border-bottom:1px solid var(--black);
}}
.luna-opening-story h2 {{
  max-width:780px;
  margin:.45rem 0 1.35rem;
  font-size:clamp(2.25rem,5vw,4.45rem);
  line-height:.98;
}}
.luna-story-prose {{
  max-width:760px;
}}
.luna-story-prose p {{
  font-size:clamp(1.03rem,1.5vw,1.18rem);
  line-height:1.68;
}}
.luna-do-dont {{
  display:grid;
  grid-template-columns:1fr 1fr;
  margin-top:1.35rem;
}}
.luna-do-dont div {{
  padding:.9rem .9rem .15rem 0;
}}
.luna-do-dont div + div {{
  padding-left:.9rem;
}}
.luna-do-dont span {{
  display:block;
  font-family:"IBM Plex Mono",monospace;
  font-size:.63rem;
  text-transform:uppercase;
  margin-bottom:.28rem;
}}
.luna-do-dont strong {{
  font-family:"Bodoni Moda",Georgia,serif;
  font-size:clamp(1.18rem,2vw,1.55rem);
  line-height:1.18;
}}
.luna-do-dont-light {{
  border-top:1px solid var(--black);
  border-bottom:1px solid var(--black);
}}
.luna-do-dont-light div + div {{
  border-left:1px solid var(--black);
}}
.luna-do-dont-light span {{
  color:var(--muted);
}}
.luna-story-timeline {{
  border-top:1px solid var(--black);
}}
.luna-story-act {{
  display:grid;
  grid-template-columns:minmax(7rem,.34fr) minmax(0,1fr);
  gap:clamp(1rem,4vw,3rem);
  padding:clamp(1.35rem,3vw,2.3rem) 0;
  border-bottom:1px solid var(--black);
}}
.luna-story-date {{
  display:flex;
  flex-direction:column;
  gap:.45rem;
}}
.luna-story-date small {{
  color:var(--muted);
  font-size:.85rem;
  line-height:1.4;
}}
.luna-story-date em {{
  color:var(--muted);
  font-size:.72rem;
  line-height:1.35;
  font-style:normal;
}}
.luna-story-copy {{
  max-width:700px;
}}
.luna-story-copy h3,
.luna-life-row h3 {{
  margin:0 0 .65rem;
  font-size:clamp(1.7rem,3vw,2.55rem);
  line-height:1.02;
}}
.luna-story-copy p {{
  margin:.35rem 0 .8rem;
  line-height:1.62;
}}
.luna-sky-evidence {{
  margin:0 0 1rem;
  padding:.8rem .95rem;
  border-left:3px solid var(--black);
  background:var(--soft);
}}
.luna-sky-evidence span {{
  display:block;
  margin-bottom:.35rem;
  font-family:"IBM Plex Mono",monospace;
  font-size:.62rem;
  letter-spacing:.055em;
  text-transform:uppercase;
}}
.luna-sky-evidence p {{
  margin:0;
  font-size:.93rem;
  line-height:1.52;
}}
.luna-chapter-move {{
  margin-top:1rem !important;
  padding-top:.75rem;
  border-top:1px solid var(--line);
  color:var(--muted);
}}
.luna-chapter-move strong {{ color:var(--black); }}
.luna-relationship-test {{
  background:var(--soft);
}}
.luna-relationship-test h2 {{
  max-width:760px;
  margin:.45rem 0 1rem;
  font-size:clamp(2.1rem,4.8vw,4rem);
  line-height:1;
}}
.luna-relationship-test p {{
  max-width:720px;
  font-size:clamp(1.02rem,1.45vw,1.16rem);
  line-height:1.62;
}}

.luna-story-dates-section h2 {{
  max-width:680px;
  margin:.45rem 0 1.35rem;
  font-size:clamp(2.1rem,4.5vw,3.8rem);
  line-height:.98;
}}
.luna-story-date-grid {{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  border-top:1px solid var(--black);
  border-left:1px solid var(--black);
}}
.luna-story-date-card {{
  padding:1rem;
  border-right:1px solid var(--black);
  border-bottom:1px solid var(--black);
}}
.luna-story-date-card span {{
  display:block;
  font-family:"IBM Plex Mono",monospace;
  font-size:.65rem;
  letter-spacing:.05em;
  text-transform:uppercase;
  margin-bottom:.55rem;
}}
.luna-story-date-card strong {{
  display:block;
  font-size:1.02rem;
  line-height:1.38;
}}
.luna-story-date-card p {{
  margin:.65rem 0 0;
  color:var(--muted);
}}
.luna-focus-section {{
  background:var(--soft);
}}
.luna-focus-section p {{
  max-width:760px;
}}
.luna-question {{
  max-width:760px;
  margin:1rem 0 1.4rem;
  padding-left:1rem;
  border-left:3px solid var(--black);
  font-family:"Bodoni Moda",Georgia,serif;
  font-size:clamp(1.35rem,2.4vw,2rem);
  line-height:1.22;
}}
.luna-romance-grid {{
  display:grid;
  grid-template-columns:1fr 1fr;
  border-top:1px solid var(--black);
  border-left:1px solid var(--black);
}}
.luna-romance-grid article {{
  padding:1rem;
  border-right:1px solid var(--black);
  border-bottom:1px solid var(--black);
}}
.luna-life-list {{
  border-top:1px solid var(--black);
}}
.luna-life-row {{
  display:grid;
  grid-template-columns:5rem minmax(12rem,.75fr) 1.4fr;
  gap:1rem;
  align-items:start;
  padding:1rem 0;
  border-bottom:1px solid var(--black);
}}
.luna-life-row > span small {{
  display:block;
  margin-top:.25rem;
  font-family:var(--luna-mono);
  font-size:.62rem;
  letter-spacing:.05em;
  opacity:.72;
}}
.luna-life-row h3,
.luna-life-row p {{
  margin:0;
}}
.luna-strategy-badge {{
  display: inline-block;
  margin: 0.55rem 0 0.8rem;
  padding: 0.28rem 0.55rem;
  border: 1px solid currentColor;
  font-family: var(--luna-mono);
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}
.luna-strategy-rationale {{
  max-width: 46rem;
  margin-top: 0.8rem;
}}

.luna-next-move {{
  display:grid;
  grid-template-columns:.8fr 1.2fr;
  gap:2rem;
}}
.luna-next-move h2 {{
  margin:.4rem 0 0;
  font-size:clamp(2.2rem,5vw,4.2rem);
  line-height:.98;
}}
.luna-next-move ol {{
  margin:0;
  padding-left:1.25rem;
}}
.luna-next-move li {{
  margin-bottom:.8rem;
  font-size:1.03rem;
  line-height:1.48;
}}
.luna-evidence-path {{
  border-top:1px solid var(--black);
  margin:1rem 0 1.35rem;
}}
.luna-evidence-anchor {{
  display:grid;
  grid-template-columns:minmax(7.5rem,.55fr) minmax(8rem,.7fr) minmax(0,1.5fr);
  gap:1rem;
  align-items:baseline;
  padding:.8rem 0;
  border-bottom:1px solid var(--line);
}}
.luna-evidence-anchor span {{
  font-family:"IBM Plex Mono",monospace;
  font-size:.62rem;
  text-transform:uppercase;
  color:var(--muted);
}}
.luna-evidence-anchor strong {{
  font-size:.9rem;
}}
.luna-evidence-anchor p {{
  margin:0;
  font-size:.95rem;
  line-height:1.4;
}}
.luna-method-note {{
  color:var(--muted);
  font-size:.82rem !important;
}}
.luna-evidence-stack details {{
  border-bottom:1px solid var(--black);
}}
.luna-evidence-stack summary {{
  list-style:none;
  display:flex;
  justify-content:space-between;
  align-items:center;
  min-height:3.8rem;
  cursor:pointer;
  padding:0 clamp(1rem,4vw,3.2rem);
  font-family:"IBM Plex Mono",monospace;
  font-size:.7rem;
  text-transform:uppercase;
}}
.luna-evidence-stack summary::-webkit-details-marker {{ display:none; }}
.luna-detail-body {{
  padding:.8rem clamp(1rem,4vw,3.2rem) 2.4rem;
}}
.luna-evidence-grid,
.luna-date-grid {{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  border-top:1px solid var(--black);
  border-left:1px solid var(--black);
}}
.luna-evidence-grid div,
.luna-date-card {{
  padding:.9rem;
  border-right:1px solid var(--black);
  border-bottom:1px solid var(--black);
}}
.luna-evidence-grid span,
.luna-date-card span,
.luna-date-card small {{
  display:block;
  font-family:"IBM Plex Mono",monospace;
  font-size:.63rem;
  text-transform:uppercase;
}}
.luna-date-card strong {{
  display:block;
  margin:.45rem 0;
}}
.luna-table-wrap {{ overflow-x:auto; margin-bottom:1.5rem; }}
.luna-monthly-report table {{
  width:100%;
  border-collapse:collapse;
}}
.luna-monthly-report th,
.luna-monthly-report td {{
  padding:.65rem .4rem;
  border-bottom:1px solid var(--line);
  text-align:left;
  vertical-align:top;
}}
.luna-monthly-report th {{
  font-family:"IBM Plex Mono",monospace;
  font-size:.63rem;
  text-transform:uppercase;
}}
.luna-report-footer {{
  padding:1.2rem clamp(1rem,4vw,3.2rem);
  color:var(--muted);
  font-size:.72rem;
  line-height:1.5;
  border-top:1px solid var(--line);
}}
.luna-report-details {{
  display:flex;
  align-items:baseline;
  justify-content:space-between;
  gap:.85rem 1.5rem;
  padding:.78rem clamp(1rem,4vw,3.2rem);
  border-bottom:1px solid var(--black);
  background:var(--soft);
}}
.luna-report-identity {{
  font-family:"IBM Plex Mono",monospace;
  font-size:.82rem;
  line-height:1.35;
  font-weight:600;
  letter-spacing:.01em;
}}
.luna-report-generated {{
  color:var(--muted);
  font-family:"IBM Plex Mono",monospace;
  font-size:.6rem;
  line-height:1.35;
  text-align:right;
}}
.luna-print-controls {{
  position:static;
  z-index:1;
  display:flex;
  align-items:end;
  gap:.75rem;
  justify-content:flex-end;
  padding:.75rem clamp(1rem,4vw,3.2rem);
  background:rgba(255,255,255,.97);
  border-bottom:1px solid var(--black);
}}
.luna-print-field {{
  display:flex;
  flex-direction:column;
  gap:.2rem;
}}
.luna-print-field label {{
  font-family:"IBM Plex Mono",monospace;
  font-size:.6rem;
  text-transform:uppercase;
}}
.luna-print-field select {{
  min-height:2.5rem;
  border:1px solid var(--black);
  background:var(--white);
  padding:.4rem .55rem;
}}
.luna-print-check {{
  margin-left:auto;
  font-size:.85rem;
}}
.luna-print-controls button {{
  min-height:2.5rem;
  border:1px solid var(--black);
  background:var(--black);
  color:var(--white);
  padding:.55rem .8rem;
  font-family:"IBM Plex Mono",monospace;
  text-transform:uppercase;
  cursor:pointer;
}}
@media (max-width:720px) {{
  .luna-monthly-meta,
  .luna-hero-theme,
  .luna-do-dont,
  .luna-romance-grid,
  .luna-next-move,
  .luna-evidence-grid,
  .luna-date-grid,
  .luna-story-date-grid,
  .luna-story-act {{
    grid-template-columns:1fr;
    flex-direction:column;
  }}
  .luna-monthly-hero h1 {{
    font-size:clamp(2.35rem,11vw,3.75rem);
  }}
  .luna-hero-theme {{
    gap:.25rem;
  }}
  .luna-do-dont div + div {{
    border-left:none;
    border-top:1px solid var(--black);
    padding-left:0;
  }}
  .luna-story-act {{
    gap:.8rem;
  }}
  .luna-evidence-anchor {{
    grid-template-columns:1fr;
    gap:.25rem;
  }}
  .luna-story-date {{
    display:grid;
    grid-template-columns:auto 1fr;
    gap:.7rem;
    align-items:baseline;
  }}
  .luna-life-row {{
    grid-template-columns:1fr;
    gap:.35rem;
  }}
  .luna-report-details {{
    align-items:flex-start;
    flex-direction:column;
    gap:.25rem;
  }}
  .luna-report-generated {{ text-align:left; }}
  .luna-report-details > div:nth-child(-n+2) {{ border-bottom:1px solid var(--line); }}
  .luna-print-controls {{
    align-items:stretch;
    flex-wrap:wrap;
  }}
  .luna-print-controls button {{
    width:100%;
  }}
}}
#luna-print-portal {{
  display:none;
}}
@media print {{
  body.luna-print-active > *:not(#luna-print-portal):not(style):not(script) {{
    display:none !important;
  }}
  #luna-print-portal {{
    display:block !important;
    position:static !important;
    width:100% !important;
    max-width:none !important;
    margin:0 !important;
    padding:0 !important;
  }}
  #luna-print-portal .luna-monthly-report {{
    display:block !important;
    position:static !important;
    width:100% !important;
    max-width:none !important;
    height:auto !important;
    max-height:none !important;
    overflow:visible !important;
    margin:0 !important;
  }}
  html, body {{
    margin:0 !important;
    padding:0 !important;
    background:#fff !important;
  }}
  .luna-monthly-report {{
    position:static !important;
    width:100%;
    max-width:none;
    margin:0;
  }}
  .luna-print-controls {{ display:none !important; }}
  .luna-report-details {{
    display:grid !important;
    grid-template-columns:repeat(4,1fr) !important;
    background:#fff !important;
    border-top:1px solid #050505 !important;
    border-bottom:1px solid #050505 !important;
    break-inside:avoid;
    page-break-inside:avoid;
  }}
  .luna-report-details > div {{
    padding:3mm 2.5mm !important;
    border-right:1px solid #050505 !important;
    border-bottom:none !important;
  }}
  .luna-report-details > div:last-child {{ border-right:none !important; }}
  .luna-report-details span {{ color:#333 !important; font-size:7pt !important; }}
  .luna-report-details strong {{ color:#050505 !important; font-size:9pt !important; }}
  .luna-monthly-hero {{
    padding:7mm 0 6mm;
    color:#050505 !important;
    background:#fff !important;
    border-top:3mm solid #050505;
    border-bottom:1px solid #050505;
    break-inside:avoid;
    page-break-inside:avoid;
  }}
  .luna-monthly-meta {{
    color:#050505 !important;
    border-bottom-color:#050505 !important;
  }}
  .luna-monthly-hero h1 {{
    color:#050505 !important;
    font-size:34pt;
  }}
  .luna-hero-theme {{
    color:#050505 !important;
  }}
  .luna-monthly-section {{
    padding:6mm 0;
  }}
  .luna-opening-story {{
    display:flex !important;
    flex-direction:column !important;
    padding-top:4mm !important;
    padding-bottom:4mm !important;
  }}
  .luna-opening-story > .luna-eyebrow {{ order:1; }}
  .luna-opening-story > h2 {{
    order:2;
    font-size:25pt;
    margin-bottom:2.5mm !important;
  }}
  .luna-opening-story > .luna-do-dont {{
    order:3;
    margin:1mm 0 3mm !important;
    break-inside:avoid;
    page-break-inside:avoid;
  }}
  .luna-opening-story > .luna-story-prose {{ order:4; }}
  .luna-story-prose p {{
    font-size:9.7pt;
    line-height:1.42;
    margin:.25rem 0 .55rem;
  }}
  .luna-report-footer {{
    padding:3mm 0 0;
  }}
  .luna-story-act,
  .luna-story-date-card,
  .luna-romance-grid article,
  .luna-life-row,
  .luna-date-card,
  .luna-evidence-grid div {{
    break-inside:avoid;
    page-break-inside:avoid;
  }}
  .luna-monthly-report[data-print-orientation="portrait"] .luna-story-act,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-story-date-grid,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-romance-grid,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-evidence-grid,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-date-grid,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-life-row,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-next-move {{
    grid-template-columns:1fr;
  }}
  .luna-monthly-report[data-print-orientation="portrait"] .luna-life-row {{
    padding:2.5mm 0;
  }}
  .luna-monthly-report[data-print-orientation="portrait"] .luna-next-move h2 {{
    font-size:25pt;
  }}
  .luna-monthly-report[data-print-orientation="portrait"] .luna-story-section,
  .luna-monthly-report[data-print-orientation="portrait"] .luna-story-dates-section {{
    break-before:auto;
    page-break-before:auto;
  }}
  .luna-monthly-report[data-print-orientation="portrait"] .luna-do-dont {{
    break-inside:avoid;
    page-break-inside:avoid;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-monthly-hero h1 {{
    font-size:30pt;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-monthly-section {{
    padding:4mm 0;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-story-act {{
    grid-template-columns:30mm 1fr;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-life-list {{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    border-left:1px solid #050505;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-life-row {{
    display:block;
    padding:4mm;
    border-right:1px solid #050505;
    border-bottom:1px solid #050505;
  }}
  .luna-monthly-report[data-print-orientation="landscape"] .luna-story-date-grid,
  .luna-monthly-report[data-print-orientation="landscape"] .luna-romance-grid,
  .luna-monthly-report[data-print-orientation="landscape"] .luna-evidence-grid,
  .luna-monthly-report[data-print-orientation="landscape"] .luna-date-grid {{
    grid-template-columns:repeat(2,1fr);
  }}
  .luna-evidence-stack {{
    break-before:page;
    page-break-before:always;
  }}
  .luna-evidence-stack details > *:not(summary) {{
    display:block !important;
  }}
  .luna-evidence-stack details summary span {{
    display:none !important;
  }}
  .luna-evidence-stack details summary {{
    break-after:avoid;
    page-break-after:avoid;
  }}
}}
</style>

<div
  class="luna-monthly-report"
  id="{instance_id}-report"
  data-luna-report
  data-print-paper="{_safe(default_paper)}"
  data-print-orientation="{_safe(default_orientation)}"
  data-print-file-title="{_safe(print_file_title)}"
>
  <section class="luna-monthly-hero">
    <div class="luna-monthly-meta">
      <span>Monthly / {_safe(narrative.sign)}</span>
      <span>{_safe(narrative.label)} · {_safe(result.get("timezone_name", "local time"))}</span>
    </div>
    <h1>{_safe(narrative.hook_headline)}</h1>
    <div class="luna-hero-theme">
      <span>Monthly theme</span>
      <strong>{_safe(narrative.headline)}</strong>
    </div>
  </section>

  {report_details}

  {controls}

  {body}

  <footer class="luna-report-footer">
    {_safe(FOOTER_DISCLAIMER)}
    {f'<br>Order reference: {_safe(order_reference)}' if order_reference else ''}
  </footer>
</div>

<script>
(() => {{
  const root = document.getElementById("{instance_id}");
  if (!root) return;

  const report = root.querySelector("[data-luna-report]");
  const paper = root.querySelector("[data-luna-paper]");
  const orientation = root.querySelector("[data-luna-orientation]");
  const printButton = root.querySelector("[data-luna-print]");
  const pageStyle = root.querySelector("style[data-luna-page-size]");
  let prePrintDocumentTitle = null;
  let prePrintParentTitle = null;

  function selectedPaper() {{
    return paper ? paper.value : "{default_paper}";
  }}

  function selectedOrientation() {{
    return orientation ? orientation.value : "{default_orientation}";
  }}

  function applyPrintSettings() {{
    const paperValue = selectedPaper();
    const orientationValue = selectedOrientation();
    report.dataset.printPaper = paperValue;
    report.dataset.printOrientation = orientationValue;
    pageStyle.textContent =
      "@page {{ size: " + paperValue + " " + orientationValue + "; margin: 12mm; }}";
  }}

  function removeAnyPrintPortal() {{
    document.querySelectorAll("[data-luna-print-portal]").forEach((node) => node.remove());
    document.body.classList.remove("luna-print-active");
  }}

  function applyOuterPrintTitle(printTitle) {{
    if (prePrintDocumentTitle === null) {{
      prePrintDocumentTitle = document.title;
    }}
    document.title = printTitle;

    try {{
      if (window.parent && window.parent !== window) {{
        if (prePrintParentTitle === null) {{
          prePrintParentTitle = window.parent.document.title;
        }}
        window.parent.document.title = printTitle;
      }}
    }} catch (error) {{
      // Parent title access can be blocked by browser sandboxing.
    }}
  }}

  function restoreOuterPrintTitle() {{
    if (prePrintDocumentTitle !== null) {{
      document.title = prePrintDocumentTitle;
      prePrintDocumentTitle = null;
    }}
    try {{
      if (prePrintParentTitle !== null && window.parent && window.parent !== window) {{
        window.parent.document.title = prePrintParentTitle;
      }}
    }} catch (error) {{
      // Ignore a sandboxed parent-title restore.
    }}
    prePrintParentTitle = null;
  }}

  function createPrintPortal() {{
    // Remove any portal left by a previous report. This is what makes
    // sequential Aries -> Pisces printing deterministic in one Streamlit session.
    removeAnyPrintPortal();
    applyPrintSettings();

    const portal = document.createElement("div");
    portal.id = "luna-print-portal";
    portal.setAttribute("data-luna-print-portal", "{instance_id}");

    const clone = report.cloneNode(true);
    clone.id = "{instance_id}-report-print";
    clone.dataset.printPaper = selectedPaper();
    clone.dataset.printOrientation = selectedOrientation();
    clone.querySelectorAll(".luna-print-controls").forEach((node) => node.remove());
    clone.querySelectorAll("details").forEach((detail) => {{
      detail.open = true;
      detail.setAttribute("open", "");
    }});

    portal.appendChild(clone);
    document.body.appendChild(portal);
    document.body.classList.add("luna-print-active");
    return portal;
  }}

  function cleanupAfterPrint() {{
    // Delay title restore slightly because Chromium can derive the Save-as-PDF
    // filename late in the print-dialog lifecycle.
    window.setTimeout(() => {{
      restoreOuterPrintTitle();
      removeAnyPrintPortal();
    }}, 1200);
  }}

  function printCurrentReportOnly() {{
    if (!report) return;
    const printTitle = report.dataset.printFileTitle || "Luna_Convergence_Monthly";
    createPrintPortal();
    applyOuterPrintTitle(printTitle);

    // IMPORTANT: call window.print() directly inside the click event. The v3.5
    // hidden-iframe implementation waited for fonts/layout first; some browsers
    // then treated print() as no longer user-initiated, so the button appeared dead.
    window.print();
  }}

  if (paper) paper.addEventListener("change", applyPrintSettings);
  if (orientation) orientation.addEventListener("change", applyPrintSettings);

  window.addEventListener("afterprint", cleanupAfterPrint);

  if (printButton) {{
    printButton.addEventListener("click", (event) => {{
      event.preventDefault();
      printCurrentReportOnly();
    }});
  }}

  applyPrintSettings();
}})();
</script>
</div>
    """


def render_monthly_experience(
    narrative: MonthlyNarrative,
    result: dict,
    *,
    show_print: bool = True,
    preview: bool = False,
    order_reference: str = "",
    default_paper: str = "A4",
    default_orientation: str = "portrait",
) -> None:
    import streamlit as st

    st.html(
        build_monthly_experience_html(
            narrative,
            result,
            show_print=show_print,
            preview=preview,
            order_reference=order_reference,
            default_paper=default_paper,
            default_orientation=default_orientation,
        ),
        unsafe_allow_javascript=True,
    )
