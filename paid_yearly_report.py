from __future__ import annotations

"""Paid Yearly customer renderer.

Customer-facing language deliberately avoids internal model vocabulary.
The report keeps the same Natal Player foundation as Paid Monthly, then presents
the year as human stories, timing and choices.

Public API is unchanged:
    render_paid_yearly_report(...)
"""

from datetime import date, timedelta
from html import escape
from typing import Any, Callable, ContextManager

import streamlit as st

from paid_yearly_editorial import PaidYearlyEditorial
from year_ahead import YearPacket


PAID_YEARLY_REPORT_VERSION = "1.3-final-web-polish"


def _packet_dict(packet: YearPacket | dict[str, Any]) -> dict[str, Any]:
    return dict(packet) if isinstance(packet, dict) else packet.to_dict()


def _parse_date(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _date_label(value: object) -> str:
    text = str(value or "").strip()
    try:
        return date.fromisoformat(text[:10]).strftime("%d %B %Y").lstrip("0")
    except Exception:
        return text


def _next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _position_label(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    sign = str(value.get("sign") or "").strip()
    degree = value.get("degree")
    longitude = value.get("longitude")
    pieces = []
    if degree is not None and sign:
        pieces.append(f"{float(degree):.2f}° {sign}")
    elif sign:
        pieces.append(sign)
    if longitude is not None:
        pieces.append(f"{float(longitude):.2f}° ecliptic")
    return " · ".join(pieces)


def _story_paragraphs(paragraphs: tuple[str, ...] | list[str]) -> str:
    return "".join(
        f"<p>{escape(str(paragraph))}</p>"
        for paragraph in paragraphs
        if str(paragraph or "").strip()
    )


def _pass_rows(story: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in list(story.get("passes") or [])
        if isinstance(row, dict)
    ]


def _human_phase(value: object) -> str:
    phase = str(value or "QUIET").upper()
    return {
        "OPPORTUNITY": "OPENING",
        "PRESSURE": "DECISION",
        "STRUCTURAL": "STRUCTURE",
        "MIXED": "CHANGE",
        "DECISION": "DECISION",
        "POWER_SHIFT": "POWER SHIFT",
        "OPENING": "OPENING",
        "STRUCTURE": "STRUCTURE",
        "CHANGE": "CHANGE",
        "RETURN": "RETURN",
        "ENDING": "ENDING",
        "QUIET": "QUIETER GROUND",
        "QUIETER_GROUND": "QUIETER GROUND",
    }.get(phase, phase.replace("_", " "))


def _human_story_label(game: dict[str, Any] | None) -> str:
    if not game:
        return "Quieter ground"

    area = str(game.get("human_life_area") or "").lower()
    mappings = (
        (("relationship", "client", "competitor", "agreement"), "Relationships & terms"),
        (("shared money", "debt", "tax", "obligation"), "Money & obligations"),
        (("identity", "energy", "personal direction"), "Identity & direction"),
        (("career", "reputation", "authority", "public direction"), "Career & direction"),
        (("work routine", "health", "service", "daily obligation"), "Work & wellbeing"),
        (("home", "family", "root", "private life"), "Home & family"),
        (("communication", "learning", "sibling"), "Communication"),
        (("travel", "study", "publishing", "law", "belief", "international"), "Horizons & movement"),
        (("romance", "creativity", "pleasure", "children", "entrepreneur"), "Love & creativity"),
        (("friend", "network", "audience", "alliance", "long-term goal"), "Friends & future"),
        (("rest", "closure", "retreat", "hidden"), "Rest & closure"),
    )
    for needles, label in mappings:
        if any(needle in area for needle in needles):
            return label

    title = " ".join(str(game.get("title") or "").split())
    if title and len(title) <= 34:
        return title.title()

    first = " ".join(
        str(game.get("human_life_area") or "Your direction")
        .split(",")[0]
        .split()
    )
    return first.title() if first else "Your direction"


def _human_pass_label(
    row: dict[str, Any],
    index: int,
    total: int,
) -> str:
    if total <= 1:
        return "Exact contact"
    if bool(row.get("retrograde")):
        return "Returns"
    if index == 0:
        return "First contact"
    if index == total - 1:
        return "Final contact"
    return "Next contact"


def _pass_stage_copy(
    label: str,
    game: dict[str, Any] | None = None,
) -> str:
    game = dict(game or {})
    life_area = (
        _human_story_label(game)
        .lower()
        .replace(" & ", " and ")
        .strip()
    )
    story_phrase = f"your {life_area} story" if life_area else "this story"
    move = " ".join(str(game.get("move") or "").split()).rstrip(".")
    risk = " ".join(str(game.get("risk") or "").split()).rstrip(".")

    if label == "First contact":
        base = (
            f"This is where {story_phrase} stops being background and becomes a live choice. "
            "Notice what is now too concrete to leave vague."
        )
    elif label == "Returns":
        base = (
            f"The same {life_area or 'underlying'} question comes back for review. "
            "Treat the return as evidence about what did or did not hold after the first contact."
        )
    elif label == "Final contact":
        base = (
            f"This is the final exact contact in {story_phrase}. "
            "Decide what has proved sustainable and make that the new baseline."
        )
    elif label == "Exact contact":
        base = (
            f"This is the clearest exact contact in {story_phrase}. "
            "Judge the situation by what is actually happening rather than by anticipation."
        )
    else:
        base = (
            f"{story_phrase.capitalize()} becomes exact again. "
            "Use the repetition to see what has changed since the previous contact."
        )

    if move:
        return f"{base} Your move here: {move}."
    if risk:
        return f"{base} Watch for {risk.lower()}."
    return base


def _trigger_domain(game: dict[str, Any] | None) -> str:
    area = str((game or {}).get("human_life_area") or "").lower()
    if any(word in area for word in ("identity", "personal direction", "energy")):
        return "identity"
    if any(word in area for word in ("relationship", "agreement", "client", "competitor")):
        return "relationship"
    if any(word in area for word in ("career", "reputation", "authority", "public direction")):
        return "career"
    if any(word in area for word in ("shared money", "money", "debt", "tax", "obligation")):
        return "money"
    if any(word in area for word in ("home", "family", "private life", "root")):
        return "home"
    if any(word in area for word in ("work routine", "wellbeing", "health", "daily obligation", "service")):
        return "work"
    return "general"



def _trigger_stage(
    row: dict[str, Any],
    primary: dict[str, Any],
) -> str:
    trigger_date = _parse_date(row.get("date"))
    pass_dates = sorted(
        hit_date
        for hit_date in (
            _parse_date(hit.get("date"))
            for hit in _pass_rows(primary)
            if isinstance(hit, dict)
        )
        if hit_date is not None
    )
    if trigger_date is None or not pass_dates:
        return ""
    if trigger_date < pass_dates[0]:
        return "before"
    if trigger_date > pass_dates[-1]:
        return "after"
    if trigger_date in pass_dates:
        return "exact"
    return "between"


def _trigger_stage_note(stage: str) -> str:
    return {
        "before": (
            "Treat this as an early clue about what the coming exact contact is asking you to notice."
        ),
        "between": (
            "Use this moment to test what changed after the last exact contact before the story becomes exact again."
        ),
        "after": (
            "Notice whether your response now reflects what the exact contact has already made clear."
        ),
        "exact": (
            "This lands with an exact contact, so the supporting trigger and the main story peak together."
        ),
    }.get(stage, "")


def _human_trigger_label(
    row: dict[str, Any],
    game: dict[str, Any] | None = None,
    *,
    stage: str = "",
) -> str:
    planet = str(
        row.get("planet")
        or row.get("trigger_planet")
        or ""
    ).strip()
    domain = _trigger_domain(game)

    copy = {
        ("identity", "Sun"): (
            "The Sun makes your position more visible. "
            "What you stand for, refuse or take responsibility for is harder for others to miss."
        ),
        ("identity", "Mercury"): (
            "Mercury turns the identity question into a conversation, decision or message. "
            "Say what the boundary actually is rather than hoping it is understood."
        ),
        ("identity", "Venus"): (
            "Venus highlights presentation, self-worth and how easily other people respond to you. "
            "Notice which responses support the person you are trying to become."
        ),
        ("identity", "Mars"): (
            "Mars pushes the boundary into action. "
            "Use the extra force to defend a clear limit, not to turn firmness into conflict."
        ),

        ("relationship", "Sun"): (
            "The Sun makes the relationship terms more visible. "
            "What was background is harder to ignore, so notice what now needs a clear position."
        ),
        ("relationship", "Mercury"): (
            "Mercury puts the terms into words. "
            "Use the moment for the conversation, message or detail that removes an avoidable assumption."
        ),
        ("relationship", "Venus"): (
            "Venus foregrounds reciprocity, affection, fairness and value. "
            "Notice whether the agreement still feels balanced enough to keep."
        ),
        ("relationship", "Mars"): (
            "Mars adds pressure to the agreement. "
            "Act directly, but do not let urgency negotiate the terms for you."
        ),

        ("career", "Sun"): (
            "The Sun increases professional visibility. "
            "A role, result or ambition is easier to see, so be clear about the position you want to occupy."
        ),
        ("career", "Mercury"): (
            "Mercury brings a professional conversation, contract, pitch or decision into focus. "
            "Clarify scope and responsibility before the opportunity grows."
        ),
        ("career", "Venus"): (
            "Venus highlights professional support, reputation, money or alliances. "
            "Notice who values the work enough to back it in practical terms."
        ),
        ("career", "Mars"): (
            "Mars increases urgency, competition or delivery pressure. "
            "Move when the workload and ownership are clear enough to support the push."
        ),

        ("money", "Sun"): (
            "The Sun makes the obligation more visible. "
            "Put the cost, ownership and responsibility where everyone can see them."
        ),
        ("money", "Mercury"): (
            "Mercury brings the numbers, terms or paperwork into focus. "
            "Use the moment to verify what is owed, owned or promised."
        ),
        ("money", "Venus"): (
            "Venus brings value and exchange into focus. "
            "Check whether the price, benefit and responsibility still feel proportionate."
        ),
        ("money", "Mars"): (
            "Mars increases pressure around cost or obligation. "
            "Act on the clearest liability first rather than spreading effort across every concern."
        ),

        ("home", "Sun"): (
            "The Sun makes the private foundation more visible. "
            "Notice what home or family life needs in order to carry the rest of the year."
        ),
        ("home", "Mercury"): (
            "Mercury brings a practical home or family conversation into focus. "
            "Name the responsibility instead of letting it remain assumed."
        ),
        ("home", "Venus"): (
            "Venus highlights comfort, harmony and shared value at home. "
            "Notice what genuinely improves the private foundation and what only smooths over tension."
        ),
        ("home", "Mars"): (
            "Mars adds urgency to a home or family issue. "
            "Use the energy to solve the practical problem without turning it into a wider fight."
        ),

        ("work", "Sun"): (
            "The Sun makes the workload and routine more visible. "
            "Notice which repeated demand now needs a clearer structure."
        ),
        ("work", "Mercury"): (
            "Mercury brings scheduling, instructions or a practical detail into focus. "
            "Clarify the process before adding more work to it."
        ),
        ("work", "Venus"): (
            "Venus highlights what makes the routine easier to sustain. "
            "Notice where cooperation or a better arrangement reduces unnecessary friction."
        ),
        ("work", "Mars"): (
            "Mars raises the pace. "
            "Use the extra drive on the highest-value task instead of proving you can absorb every demand."
        ),
    }

    fallback = {
        "Sun": (
            "The Sun makes this story more visible. "
            "What was background is harder to ignore, so notice what now needs a clear position."
        ),
        "Mercury": (
            "Mercury turns the story into a conversation, decision or detail that needs naming. "
            "Clarify what matters rather than assume understanding."
        ),
        "Venus": (
            "Venus brings value, reciprocity and preference into the foreground. "
            "Notice what feels balanced enough to keep."
        ),
        "Mars": (
            "Mars adds urgency, initiative or friction. "
            "Act deliberately; speed is useful only when it serves the larger story."
        ),
    }

    base = copy.get((domain, planet), fallback.get(
        planet,
        "A faster-moving contact brings this story back into focus."
    ))
    stage_note = _trigger_stage_note(stage)
    return f"{base} {stage_note}".strip()


def _key_trigger_label(
    row: dict[str, Any],
    game: dict[str, Any] | None = None,
) -> str:
    planet = str(
        row.get("planet")
        or row.get("trigger_planet")
        or "Trigger"
    ).strip()
    domain = _trigger_domain(game)

    short = {
        ("identity", "Sun"): "visibility and personal position come into focus",
        ("identity", "Mercury"): "a boundary, message or decision needs words",
        ("identity", "Venus"): "presentation and self-worth come into focus",
        ("identity", "Mars"): "a personal boundary needs action",
        ("relationship", "Sun"): "the relationship terms become harder to ignore",
        ("relationship", "Mercury"): "the terms need a conversation or clarification",
        ("relationship", "Venus"): "reciprocity and fairness come into focus",
        ("relationship", "Mars"): "friction or urgency tests the agreement",
        ("career", "Sun"): "professional visibility rises",
        ("career", "Mercury"): "a professional decision, pitch or detail needs clarity",
        ("career", "Venus"): "support, reputation and value come into focus",
        ("career", "Mars"): "pressure to act or deliver increases",
        ("money", "Mercury"): "numbers, paperwork or terms need checking",
        ("money", "Venus"): "value and exchange come into focus",
        ("money", "Mars"): "cost or obligation needs action",
        ("home", "Mercury"): "a home or family responsibility needs naming",
        ("home", "Venus"): "comfort and shared value come into focus",
        ("home", "Mars"): "a practical home issue needs action",
        ("work", "Mercury"): "scheduling or process needs clarification",
        ("work", "Venus"): "cooperation can make the routine easier to sustain",
        ("work", "Mars"): "the pace increases; prioritise deliberately",
    }.get((domain, planet))

    if short:
        return f"{planet} · {short}"
    return f"{planet} · supporting trigger"


def _strongest_date(story: dict[str, Any], fallback: object) -> str:
    passes = _pass_rows(story)
    if not passes:
        return _date_label(fallback)
    peak = min(
        passes,
        key=lambda row: (
            float(row.get("orb", 99.0) or 99.0),
            str(row.get("date") or ""),
            str(row.get("time") or ""),
        ),
    )
    return _date_label(peak.get("date"))


def _render_year_at_a_glance(packet: dict[str, Any]) -> None:
    stats = dict(packet.get("year_statistics") or {})
    st.markdown("## The year at a glance")
    st.markdown(
        '<div class="timing-summary-grid">'
        f'<div><span>Major stories</span><strong>{int(stats.get("major_games", 0) or 0)}</strong></div>'
        f'<div><span>Turning points</span><strong>{int(stats.get("turning_points", 0) or 0)}</strong></div>'
        f'<div><span>Rule changes</span><strong>{int(stats.get("rule_changes", 0) or 0)}</strong></div>'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_year_map(packet: dict[str, Any]) -> None:
    rows = [
        row
        for row in list(packet.get("year_strip") or [])
        if isinstance(row, dict)
    ]
    games = [
        row
        for row in list(packet.get("games") or [])
        if isinstance(row, dict)
    ]
    period = dict(packet.get("period") or {})
    start = _parse_date(period.get("start"))
    end = _parse_date(period.get("end"))
    if not rows or start is None or end is None:
        return

    total_days = max(1, (end - start).days)
    month_labels = [escape(str(row.get("month") or "")) for row in rows]

    css = f"""
    <style>
    .luna-year-map-scroll{{overflow-x:auto;margin:8px 0 18px}}
    .luna-year-map{{min-width:790px;border:1px solid rgba(127,127,127,.24);border-radius:14px;padding:14px}}
    .luna-year-months,.luna-year-lane,.luna-year-rhythm{{display:grid;grid-template-columns:150px minmax(0,1fr);gap:12px;align-items:center}}
    .luna-year-months{{margin-bottom:8px}}
    .luna-year-month-grid,.luna-year-rhythm-grid{{display:grid;grid-template-columns:repeat({len(rows)},minmax(0,1fr));gap:2px}}
    .luna-year-month-grid div{{font-size:10px;letter-spacing:.06em;text-align:center;opacity:.68}}
    .luna-year-label{{font-size:12px;font-weight:700;line-height:1.15}}
    .luna-year-lane{{margin:13px 0}}
    .luna-year-track{{height:44px;position:relative;border-radius:8px;background:rgba(127,127,127,.08);overflow:visible}}
    .luna-year-bar{{position:absolute;top:18px;height:8px;background:currentColor;border-radius:999px;opacity:.72;min-width:5px}}
    .luna-year-marker{{position:absolute;top:11px;width:12px;height:12px;border-radius:50%;background:currentColor;transform:translateX(-50%);z-index:2}}
    .luna-year-marker span{{position:absolute;top:-16px;left:50%;transform:translateX(-50%);white-space:nowrap;font-size:9px;font-weight:700;padding:0 2px}}
    .luna-year-trigger{{position:absolute;top:16px;height:12px;width:2px;background:currentColor;opacity:.42;transform:translateX(-50%)}}
    .luna-year-rhythm{{margin-top:14px;padding-top:12px;border-top:1px solid rgba(127,127,127,.2)}}
    .luna-year-rhythm-cell{{text-align:center;min-width:0}}
    .luna-year-rhythm-bar{{display:block;width:62%;margin:0 auto 4px;background:currentColor;border-radius:4px 4px 1px 1px;min-height:5px}}
    .luna-year-rhythm-cell small{{display:block;font-size:8px;line-height:1.05;letter-spacing:.02em}}
    @media(max-width:720px){{
      .luna-year-map{{min-width:730px}}
      .luna-year-months,.luna-year-lane,.luna-year-rhythm{{grid-template-columns:120px minmax(0,1fr)}}
    }}
    </style>
    """

    month_html = "".join(f"<div>{label}</div>" for label in month_labels)
    lane_html: list[str] = []

    for game in games:
        game_start = _parse_date(game.get("start_date")) or start
        game_end = _parse_date(game.get("end_date")) or end
        clipped_start = max(start, game_start)
        clipped_end = min(end, game_end)

        left = max(
            0.0,
            min(
                100.0,
                ((clipped_start - start).days / total_days) * 100.0,
            ),
        )
        right = max(
            left,
            min(
                100.0,
                ((clipped_end - start).days / total_days) * 100.0,
            ),
        )
        width = max(1.0, right - left)

        primary = dict(game.get("primary_transit") or {})
        passes = _pass_rows(primary)

        markers: list[str] = []
        for index, hit in enumerate(passes):
            hit_date = _parse_date(hit.get("date"))
            if hit_date is None or hit_date < start or hit_date > end:
                continue
            pos = ((hit_date - start).days / total_days) * 100.0
            label = _human_pass_label(hit, index, len(passes))
            markers.append(
                f'<div class="luna-year-marker" style="left:{pos:.2f}%" '
                f'title="{escape(label, quote=True)} · {escape(_date_label(hit_date), quote=True)}">'
                f'<span>{escape(label)}</span></div>'
            )

        triggers: list[str] = []
        for trigger in list(primary.get("triggers") or []):
            if not isinstance(trigger, dict):
                continue
            trigger_date = _parse_date(trigger.get("date"))
            if (
                trigger_date is None
                or trigger_date < start
                or trigger_date > end
            ):
                continue
            pos = ((trigger_date - start).days / total_days) * 100.0
            title = _human_trigger_label(trigger)
            triggers.append(
                f'<div class="luna-year-trigger" style="left:{pos:.2f}%" '
                f'title="{escape(title, quote=True)} · {escape(_date_label(trigger_date), quote=True)}"></div>'
            )

        edge_notes = []
        if str(game.get("start_state") or "") == "already_active":
            edge_notes.append("already active")
        if str(game.get("end_state") or "") == "continues_beyond_year":
            edge_notes.append("continues beyond")
        edge_note = (
            '<small style="display:block;font-weight:400;opacity:.62;margin-top:3px">'
            + escape(" · ".join(edge_notes))
            + '</small>'
            if edge_notes
            else ""
        )

        lane_html.append(
            '<div class="luna-year-lane">'
            f'<div class="luna-year-label">{escape(_human_story_label(game))}{edge_note}</div>'
            '<div class="luna-year-track">'
            f'<div class="luna-year-bar" style="left:{left:.2f}%;width:{width:.2f}%"></div>'
            + "".join(triggers)
            + "".join(markers)
            + "</div></div>"
        )

    rhythm_cells: list[str] = []
    for row in rows:
        intensity = max(
            0.0,
            min(1.0, float(row.get("intensity") or 0.0)),
        )
        height = 5 + int(round(30 * intensity))
        rhythm_cells.append(
            '<div class="luna-year-rhythm-cell">'
            f'<i class="luna-year-rhythm-bar" '
            f'style="height:{height}px;opacity:{0.25 + 0.75 * intensity:.2f}"></i>'
            f'<small>{escape(_human_phase(row.get("phase")))}</small>'
            "</div>"
        )

    st.markdown("## How your year unfolds")
    st.caption(
        "Each line is one major story. Dots mark exact contacts; smaller ticks mark supporting triggers. "
        "Year rhythm shows how concentrated the selected personal activity is each month."
    )
    st.markdown(
        css
        + '<div class="luna-year-map-scroll"><div class="luna-year-map">'
        + '<div class="luna-year-months"><div></div><div class="luna-year-month-grid">'
        + month_html
        + "</div></div>"
        + "".join(lane_html)
        + '<div class="luna-year-rhythm"><div class="luna-year-label">Year rhythm</div>'
        + '<div class="luna-year-rhythm-grid">'
        + "".join(rhythm_cells)
        + "</div></div></div></div>",
        unsafe_allow_html=True,
    )


def _month_stage_label(
    row: dict[str, Any],
    *,
    same_story_as_previous: bool = False,
) -> str:
    phase = _human_phase(row.get("phase"))

    if phase == "RETURN":
        return "REVISIT"
    if phase == "ENDING":
        return "CLOSE THE LOOP"
    if phase == "POWER SHIFT":
        return "LEVERAGE SHIFTS"
    if phase == "STRUCTURE":
        return "SEE WHAT HOLDS" if same_story_as_previous else "BUILD THE STRUCTURE"
    if phase == "DECISION":
        return "TEST THE CHOICE" if same_story_as_previous else "MAKE THE CHOICE"
    if phase == "OPENING":
        return "BUILD ON IT" if same_story_as_previous else "THE OPENING"
    if phase == "CHANGE":
        return "ADJUST"
    if phase == "QUIETER GROUND":
        return "CONSOLIDATE"
    return phase


def _monthly_focus(row: dict[str, Any]) -> str:
    base = " ".join(str(row.get("focus") or "").split())
    phase = _human_phase(row.get("phase"))

    lead = {
        "OPENING": "Use the opening deliberately.",
        "DECISION": "Make the choice explicit.",
        "STRUCTURE": "Build around what has proved workable.",
        "POWER SHIFT": "Notice where the leverage has changed.",
        "CHANGE": "Stay flexible while the pattern changes.",
        "RETURN": "Revisit what was not fully settled.",
        "ENDING": "Close the loop deliberately.",
        "QUIETER GROUND": "Use the quieter stretch to consolidate.",
    }.get(phase, "")

    if not base:
        return lead
    if not lead:
        return base
    return f"{lead} {base}"


def _strongest_round_label(row: dict[str, Any]) -> str:
    raw = str(row.get("strongest_date") or "").strip()
    if not raw:
        return ""

    kind = str(row.get("strongest_kind") or "")
    kind_label = {
        "return": "Returns",
        "exact_contact": "Exact contact",
        "trigger": "Trigger",
    }.get(kind, "Turning point")

    return f"{_date_label(raw)} · {kind_label}"


def _month_by_month_rows(
    packet: dict[str, Any],
    editorial: PaidYearlyEditorial | None = None,
) -> list[dict[str, str]]:
    rounds = [
        row
        for row in list(packet.get("monthly_rounds") or [])
        if isinstance(row, dict)
    ]
    games = {
        int(game.get("number") or 0): game
        for game in list(packet.get("games") or [])
        if isinstance(game, dict)
    }

    if not rounds:
        return []

    output: list[dict[str, str]] = []
    previous_game_number: int | None = None

    for row in rounds:
        number = int(row.get("dominant_game_number") or 0)
        game = games.get(number)
        same_story_as_previous = bool(
            previous_game_number
            and number
            and number == previous_game_number
        )

        month_voice = (
            editorial.month_for(int(row.get("number") or 0))
            if editorial is not None
            else None
        )
        output.append(
            {
                "month": str(row.get("label") or ""),
                "phase": _month_stage_label(
                    row,
                    same_story_as_previous=same_story_as_previous,
                ),
                "story": _human_story_label(game),
                "focus": (
                    str(month_voice.focus).strip()
                    if month_voice is not None and str(month_voice.focus or "").strip()
                    else _monthly_focus(row)
                ),
                "strongest": _strongest_round_label(row),
            }
        )
        previous_game_number = number

    return output


def _render_month_by_month(
    packet: dict[str, Any],
    editorial: PaidYearlyEditorial | None = None,
) -> None:
    rows = _month_by_month_rows(packet, editorial)
    if not rows:
        return

    st.markdown("## Your year, one month at a time")
    st.caption(
        "Twelve stages of the same evolving year. When a story continues across several months, the label shows what changes next."
    )

    cards: list[str] = []
    for row in rows:
        strongest = (
            f'<div class="natal-evidence">{escape(row["strongest"])}</div>'
            if row.get("strongest")
            else ""
        )
        cards.append(
            '<div class="natal-signature-reading paid-key-date">'
            f'<div class="natal-evidence">{escape(row["month"])} · {escape(row["phase"])}</div>'
            f'<h3>{escape(row["story"])}</h3>'
            f'<p>{escape(row["focus"])}</p>'
            + strongest
            + "</div>"
        )

    st.markdown(
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px">'
        + "".join(cards)
        + "</div>",
        unsafe_allow_html=True,
    )


def _render_game_evidence(game: dict[str, Any]) -> None:
    stories = [dict(game.get("primary_transit") or {})] + [
        row
        for row in list(game.get("supporting_transits") or [])
        if isinstance(row, dict)
    ]

    for story in stories:
        technical = str(story.get("technical_label") or "")
        if not technical:
            continue

        st.markdown(f"**{technical}**")

        natal_position = _position_label(story.get("natal_position"))
        if natal_position:
            st.markdown(
                f"- Natal {story.get('natal_target') or 'target'} · "
                f"{natal_position}"
            )

        if story.get("natal_house") is not None:
            st.markdown(
                f"- House {int(story.get('natal_house'))}"
            )

        st.markdown(
            f"- Active window · "
            f"{_date_label(story.get('start'))} – "
            f"{_date_label(story.get('end'))}"
        )

        for index, hit in enumerate(_pass_rows(story)):
            when = _date_label(hit.get("date"))
            if hit.get("time"):
                when += f" · {hit.get('time')}"

            position = _position_label(
                hit.get("transit_position")
            )
            motion = (
                "retrograde"
                if bool(hit.get("retrograde"))
                else "direct"
            )

            details = [
                f"Pass {int(hit.get('pass_number') or index + 1)}",
                str(hit.get("pass_label") or ""),
                when,
                motion,
                f"{float(hit.get('orb') or 0.0):.2f}° orb",
            ]
            if position:
                details.append(position)

            st.markdown(
                "- " + " · ".join(
                    bit for bit in details if bit
                )
            )


def _render_story(
    game: dict[str, Any],
    editorial: PaidYearlyEditorial,
) -> None:
    number = int(game.get("number") or 0)
    issue = editorial.issue_for(number)
    primary = dict(game.get("primary_transit") or {})

    supporting = [
        row
        for row in list(game.get("supporting_transits") or [])
        if isinstance(row, dict)
    ][:2]

    st.markdown(
        '<div class="section-spacer"></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="eyebrow">Story {number:02d} · '
        f'{escape(str(game.get("human_life_area") or ""))}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"## {escape(str(game.get('title') or 'A major story of the year'))}"
    )

    st.markdown("### What is changing")
    if issue is not None and issue.paragraphs:
        st.markdown(
            '<div class="natal-signature-reading paid-monthly-longform paid-monthly-article">'
            + _story_paragraphs(issue.paragraphs[:1])
            + "</div>",
            unsafe_allow_html=True,
        )
        if len(issue.paragraphs) > 1:
            st.markdown("### What this may look like")
            st.markdown(
                '<div class="natal-signature-reading paid-monthly-longform paid-monthly-article">'
                + _story_paragraphs(issue.paragraphs[1:])
                + "</div>",
                unsafe_allow_html=True,
            )
    else:
        summary = str(primary.get("summary") or "")
        if summary:
            st.markdown(
                '<div class="natal-signature-reading paid-monthly-article">'
                f"<p>{escape(summary)}</p>"
                "</div>",
                unsafe_allow_html=True,
            )

    risk_parts = [
        str(game.get("risk") or "").strip(),
        str(game.get("dont") or "").strip(),
    ]
    risk = " ".join(bit for bit in risk_parts if bit)
    if risk:
        st.markdown("### What can trip you up")
        st.markdown(escape(risk))

    move = str(
        game.get("move")
        or primary.get("move")
        or ""
    ).strip()
    advantage = str(
        game.get("advantage")
        or ""
    ).strip()

    if move or advantage:
        st.markdown("### Your move")
        st.markdown(
            '<div class="timing-move">'
            + (
                f"<p>{escape(move)}</p>"
                if move
                else ""
            )
            + (
                f'<p><strong>Why it helps:</strong> '
                f'{escape(advantage)}</p>'
                if advantage
                else ""
            )
            + "</div>",
            unsafe_allow_html=True,
        )

    start_state = str(game.get("start_state") or "")
    end_state = str(game.get("end_state") or "")
    start_label = (
        "Already active"
        if start_state == "already_active"
        else "Begins"
    )
    end_label = (
        "Continues beyond your year"
        if end_state == "continues_beyond_year"
        else "Eases"
    )

    st.markdown("### Timing")
    st.markdown(
        '<div class="timing-phase-grid">'
        f'<div><span>{escape(start_label)}</span><strong>{escape(_date_label(game.get("start_date")))}</strong></div>'
        f'<div><span>Strongest</span><strong>{escape(_strongest_date(primary, game.get("start_date")))}</strong></div>'
        f'<div><span>{escape(end_label)}</span><strong>{escape(_date_label(game.get("end_date")))}</strong></div>'
        "</div>",
        unsafe_allow_html=True,
    )

    passes = _pass_rows(primary)
    if passes:
        st.markdown("### How this story develops")

        for index, row in enumerate(passes):
            label = _human_pass_label(
                row,
                index,
                len(passes),
            )
            when = _date_label(row.get("date"))
            motion = (
                "retrograde"
                if bool(row.get("retrograde"))
                else "direct"
            )

            st.markdown(
                '<div class="natal-signature-reading paid-key-date">'
                f'<div class="natal-evidence">'
                f'{escape(label.upper())} · '
                f'{escape(when)} · '
                f'{escape(motion.upper())}'
                f"</div>"
                f"<p>{escape(_pass_stage_copy(label, game))}</p>"
                "</div>",
                unsafe_allow_html=True,
            )

    triggers = [
        row
        for row in list(primary.get("triggers") or [])
        if isinstance(row, dict)
    ]
    if triggers:
        st.markdown("### Moments that bring it into focus")
        for row in triggers[:4]:
            when = _date_label(row.get("date"))
            stage = _trigger_stage(row, primary)
            st.markdown(
                '<div class="natal-signature-reading paid-key-date">'
                f'<div class="natal-evidence">{escape(when)}</div>'
                f"<p>{escape(_human_trigger_label(row, game, stage=stage))}</p>"
                "</div>",
                unsafe_allow_html=True,
            )

    if supporting:
        st.markdown("### Also influencing this story")
        for story in supporting:
            summary = str(
                story.get("summary")
                or ""
            ).strip()
            if summary:
                st.markdown(
                    '<div class="natal-signature-reading">'
                    f"<p>{escape(summary)}</p>"
                    "</div>",
                    unsafe_allow_html=True,
                )

    with st.expander(
        "Why Luna sees this · calculations",
        expanded=False,
    ):
        _render_game_evidence(game)


def _key_moments(packet: dict[str, Any]) -> None:
    rows: list[tuple[str, str, str]] = []

    for game in [
        row
        for row in list(packet.get("games") or [])
        if isinstance(row, dict)
    ]:
        primary = dict(game.get("primary_transit") or {})
        passes = _pass_rows(primary)

        for index, hit in enumerate(passes):
            raw_date = str(hit.get("date") or "")[:10]
            if not raw_date:
                continue

            rows.append(
                (
                    raw_date,
                    _date_label(raw_date),
                    f"{str(game.get('title') or _human_story_label(game))} · "
                    f"{_human_pass_label(hit, index, len(passes))}",
                )
            )

        for trigger in [
            row
            for row in list(primary.get("triggers") or [])
            if isinstance(row, dict)
        ]:
            raw_date = str(
                trigger.get("date")
                or ""
            )[:10]
            if not raw_date:
                continue

            rows.append(
                (
                    raw_date,
                    _date_label(raw_date),
                    _key_trigger_label(trigger, game),
                )
            )

    if not rows:
        return

    st.markdown("## Key moments")
    st.caption(
        "A short reference list of exact contacts and the faster moments that bring a major story into focus."
    )

    seen = set()
    for sort_key, date_text, label in sorted(
        rows,
        key=lambda row: (row[0], row[2]),
    )[:15]:
        key = (sort_key, label)
        if key in seen:
            continue
        seen.add(key)

        st.markdown(
            '<div class="natal-signature-reading paid-key-date">'
            f'<div class="natal-evidence">{escape(date_text)}</div>'
            f"<p>{escape(label)}</p>"
            "</div>",
            unsafe_allow_html=True,
        )


def _render_evidence_body(
    packet: dict[str, Any],
) -> None:
    for game in [
        row
        for row in list(packet.get("games") or [])
        if isinstance(row, dict)
    ]:
        st.markdown(
            f"**Story {int(game.get('number') or 0):02d} · "
            f"{str(game.get('title') or '')}**"
        )
        _render_game_evidence(game)



_CORE_THREAD_YEAR_LANGUAGE = {
    "Sun": "conscious direction and identity",
    "Moon": "instinctive needs and emotional response",
    "Mercury": "thinking, information and communication",
    "Venus": "values, reciprocity and relationship choices",
    "Mars": "action, assertion and how you use force",
    "Jupiter": "growth, confidence and expansion",
    "Saturn": "structure, limits and responsibility",
    "Uranus": "change, freedom and disruption",
    "Neptune": "imagination, ideals and uncertainty",
    "Pluto": "power, intensity and deep change",
    "Ascendant": "identity, presentation and personal direction",
    "Midheaven": "career, reputation and public direction",
}


def _core_thread_year_bridge(
    snapshot: Any,
    packet: dict[str, Any],
) -> str:
    """Explain why the strongest natal pattern is relevant without inventing activation."""
    aspects = list(getattr(snapshot, "aspects", ()) or ())
    if not aspects:
        return ""

    strongest = aspects[0]
    natal_planets = [
        str(getattr(strongest, "planet1", "") or ""),
        str(getattr(strongest, "planet2", "") or ""),
    ]
    natal_planets = [planet for planet in natal_planets if planet]
    if not natal_planets:
        return ""

    games = [
        row
        for row in list(packet.get("games") or [])
        if isinstance(row, dict)
    ]
    counts = {planet: 0 for planet in natal_planets}

    for game in games:
        stories = [dict(game.get("primary_transit") or {})] + [
            dict(row)
            for row in list(game.get("supporting_transits") or [])
            if isinstance(row, dict)
        ]
        story_text = " ".join(
            " ".join(
                [
                    str(story.get("transiting_planet") or ""),
                    str(story.get("natal_target") or ""),
                    str(story.get("technical_label") or ""),
                ]
            )
            for story in stories
        )
        for planet in natal_planets:
            if re.search(rf"\b{re.escape(planet)}\b", story_text, flags=re.IGNORECASE):
                counts[planet] += 1

    planet, count = max(counts.items(), key=lambda item: item[1])
    if count <= 0:
        return ""

    p1, p2 = natal_planets[0], natal_planets[-1]
    aspect_name = str(getattr(strongest, "name", "") or "").lower()
    theme = _CORE_THREAD_YEAR_LANGUAGE.get(planet, planet.lower())
    total = max(1, len(games))

    return (
        f"{planet} appears in {count} of your {total} major annual "
        f"{'story' if total == 1 else 'stories'}. That does not mean those transits recreate "
        f"your natal {p1} {aspect_name} {p2}. It means one side of that lifelong pattern — "
        f"{theme} — is especially prominent in the timing selected for this year."
    )


def render_paid_yearly_report(
    *,
    snapshot: Any,
    packet: YearPacket | dict[str, Any],
    editorial: PaidYearlyEditorial,
    label: str,
    natal_precision: str = "",
    order_reference: str = "",
    render_natal_core: Callable[..., None],
    evidence_panel: Callable[[str], ContextManager[Any]] | None = None,
    trust_statement: str = "",
    trust_disclosure: str = "",
) -> None:
    """Render Paid Yearly using human story language rather than engine language."""
    value = _packet_dict(packet)

    st.markdown(
        '<section class="natal-shell paid-yearly-editorial-shell">',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="editorial-title">'
        f'{escape(editorial.headline or "Your Year Ahead")}'
        f"</div>",
        unsafe_allow_html=True,
    )

    intro = str(editorial.deck or "").strip()
    intro_text = str(label or "")
    if intro:
        intro_text += (
            " · " if intro_text else ""
        ) + intro

    st.markdown(
        f'<div class="natal-intro">{escape(intro_text)}</div>',
        unsafe_allow_html=True,
    )

    # Reuse the canonical Natal Player presentation, but replace the generic
    # Paid-Yearly "Read the pattern" fallback with the explanatory Core Thread.
    render_natal_core(
        snapshot,
        precision_note=str(natal_precision or ""),
        show_evidence=False,
        use_live_voice=False,
        use_live_signature_moves=False,
        show_core_thread=True,
        core_thread_year_bridge=_core_thread_year_bridge(snapshot, value),
    )

    st.markdown(
        '<div class="section-spacer"></div>',
        unsafe_allow_html=True,
    )

    _render_year_at_a_glance(value)

    st.markdown("## Read the year")
    if editorial.voice_complete and editorial.read_year:
        st.markdown(
            '<div class="natal-signature-reading paid-monthly-longform paid-monthly-article">'
            + _story_paragraphs(editorial.read_year)
            + "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.error(
            "Luna could not complete the paid annual reading cleanly. "
            "Please regenerate it."
        )

    _render_year_map(value)
    _render_month_by_month(value, editorial)

    st.markdown("## The major stories of your year")
    st.caption(
        "These are the strongest personal stories shaping the year. "
        "Meaning comes first; exact timing and technical proof stay underneath."
    )

    for game in [
        row
        for row in list(value.get("games") or [])
        if isinstance(row, dict)
    ]:
        _render_story(game, editorial)

    if editorial.closing:
        st.markdown(
            '<div class="section-spacer"></div>',
            unsafe_allow_html=True,
        )
        st.markdown("## What the year leaves you with")
        st.markdown(
            '<div class="natal-signature-reading paid-monthly-longform paid-monthly-article">'
            + _story_paragraphs(editorial.closing)
            + "</div>",
            unsafe_allow_html=True,
        )

    _key_moments(value)

    if evidence_panel is not None:
        with evidence_panel(
            "Why Luna sees this · chart evidence"
        ):
            _render_evidence_body(value)
            if trust_statement:
                st.markdown(f"**{trust_statement}**")
            if trust_disclosure:
                st.caption(trust_disclosure)
    else:
        with st.expander(
            "Why Luna sees this · chart evidence",
            expanded=False,
        ):
            _render_evidence_body(value)
            if trust_statement:
                st.markdown(f"**{trust_statement}**")
            if trust_disclosure:
                st.caption(trust_disclosure)

    if order_reference:
        st.caption(
            f"Order reference · {order_reference}"
        )

    st.markdown(
        "</section>",
        unsafe_allow_html=True,
    )
