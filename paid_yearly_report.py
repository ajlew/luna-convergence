from __future__ import annotations

"""Paid Yearly customer renderer.

This deliberately mirrors the successful Paid Monthly hierarchy instead of
rendering an annual dashboard.

Sequence:
1. editorial headline + deck
2. the SAME natal core renderer used by Paid Monthly
   (Your natal signature -> Read the pattern -> natal chart -> Your strengths)
3. Read the year - the main paid article
4. Your year map - compact navigation only
5. The major issues of your year - substantial Luna chapters + timing
6. Key dates - quick reference only
7. Why Luna sees this - collapsed calculation evidence

This module does not calculate astrology and does not call the LLM.
"""

from datetime import date
from html import escape
from typing import Any, Callable, ContextManager

import streamlit as st

from paid_yearly_editorial import PaidYearlyEditorial
from year_ahead import YearPacket


PAID_YEARLY_REPORT_VERSION = "1.0"


def _packet_dict(packet: YearPacket | dict[str, Any]) -> dict[str, Any]:
    return dict(packet) if isinstance(packet, dict) else packet.to_dict()


def _date_label(value: object) -> str:
    text = str(value or "").strip()
    try:
        return date.fromisoformat(text[:10]).strftime("%d %B %Y").lstrip("0")
    except Exception:
        return text


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


def _render_year_map(packet: dict[str, Any]) -> None:
    rows = [row for row in list(packet.get("year_strip") or []) if isinstance(row, dict)]
    if not rows:
        return

    st.markdown("## Your year map")
    st.caption(
        "Quick reference only — the interpretation is already in Read the year. "
        "Height shows concentration; the word underneath shows the dominant phase."
    )
    cells = []
    for row in rows:
        month = escape(str(row.get("month") or ""))
        phase = escape(str(row.get("phase") or "QUIET"))
        intensity = max(0.0, min(1.0, float(row.get("intensity") or 0.0)))
        height = 8 + int(round(44 * intensity))
        opacity = 0.22 + 0.78 * intensity
        cells.append(
            '<div class="timing-month" style="min-width:0;text-align:center">'
            f'<span>{month}</span>'
            f'<i style="height:{height}px;opacity:{opacity:.2f}"></i>'
            f'<strong style="display:block;font-size:9px;line-height:1.15;margin-top:4px">{phase}</strong>'
            '</div>'
        )
    st.markdown(
        '<div class="timing-strip" aria-label="Paid Year Ahead map">'
        + "".join(cells)
        + "</div>",
        unsafe_allow_html=True,
    )


def _pass_rows(story: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row for row in list(story.get("passes") or [])
        if isinstance(row, dict)
    ]


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
    value = _date_label(peak.get("date"))
    if peak.get("time"):
        value += f" · {peak.get('time')}"
    return value


def _render_issue(
    game: dict[str, Any],
    editorial: PaidYearlyEditorial,
) -> None:
    number = int(game.get("number") or 0)
    issue = editorial.issue_for(number)
    primary = dict(game.get("primary_transit") or {})
    supporting = [
        row for row in list(game.get("supporting_transits") or [])
        if isinstance(row, dict)
    ]

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="eyebrow">Major issue {number:02d} · '
        f'{escape(str(game.get("human_life_area") or ""))}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"## {escape(str(game.get('title') or 'A major issue of the year'))}")

    if issue is not None and issue.paragraphs:
        st.markdown(
            '<div class="natal-signature-reading paid-monthly-longform paid-monthly-article">'
            + _story_paragraphs(issue.paragraphs)
            + "</div>",
            unsafe_allow_html=True,
        )
    else:
        # Deterministic facts remain usable if voice did not provide this chapter.
        summary = str(primary.get("summary") or "")
        if summary:
            st.markdown(
                '<div class="natal-signature-reading paid-monthly-article">'
                f"<p>{escape(summary)}</p>"
                "</div>",
                unsafe_allow_html=True,
            )

    # Timing comes after the interpretation, matching the Paid Monthly principle:
    # meaning first, exact evidence second.
    st.markdown("### Timing")
    timing_html = (
        '<div class="timing-phase-grid">'
        f'<div><span>Begins</span><strong>{escape(_date_label(game.get("start_date")))}</strong></div>'
        f'<div><span>Strongest</span><strong>{escape(_strongest_date(primary, game.get("start_date")))}</strong></div>'
        f'<div><span>Eases</span><strong>{escape(_date_label(game.get("end_date")))}</strong></div>'
        "</div>"
    )
    st.markdown(timing_html, unsafe_allow_html=True)

    passes = _pass_rows(primary)
    if passes:
        st.markdown("### How the issue develops")
        for row in passes:
            pass_number = int(row.get("pass_number") or 1)
            pass_label = str(row.get("pass_label") or f"Pass {pass_number}")
            when = _date_label(row.get("date"))
            if row.get("time"):
                when += f" · {row.get('time')}"
            motion = "retrograde" if bool(row.get("retrograde")) else "direct"
            st.markdown(
                '<div class="natal-signature-reading paid-key-date">'
                f'<div class="natal-evidence">PASS {pass_number} · {escape(when)} · {escape(motion.upper())}</div>'
                f'<h3>{escape(pass_label)}</h3>'
                "</div>",
                unsafe_allow_html=True,
            )

    triggers = [
        row for row in list(primary.get("triggers") or [])
        if isinstance(row, dict)
    ]
    if triggers:
        st.markdown("### Trigger dates")
        for row in triggers:
            when = _date_label(row.get("date"))
            if row.get("time"):
                when += f" · {row.get('time')}"
            label = str(
                row.get("activation_label")
                or row.get("technical_label")
                or "Supporting trigger"
            )
            pass_no = row.get("activates_pass_number")
            suffix = f" · sharpens Pass {pass_no}" if pass_no else ""
            st.markdown(
                '<div class="natal-signature-reading paid-key-date">'
                f'<div class="natal-evidence">{escape(when)}</div>'
                f'<p>{escape(label + suffix)}</p>'
                "</div>",
                unsafe_allow_html=True,
            )

    # Supporting slow arcs stay inside the same major issue rather than becoming
    # another catalogue.
    if supporting:
        st.markdown("### Also working underneath")
        for story in supporting:
            label = str(story.get("technical_label") or "")
            summary = str(story.get("summary") or "")
            st.markdown(
                '<div class="natal-signature-reading">'
                f'<div class="natal-evidence">{escape(label)}</div>'
                f'<p>{escape(summary)}</p>'
                "</div>",
                unsafe_allow_html=True,
            )


def _key_dates(packet: dict[str, Any]) -> None:
    rows: list[tuple[str, str, str]] = []

    for game in [
        row for row in list(packet.get("games") or [])
        if isinstance(row, dict)
    ]:
        story = dict(game.get("primary_transit") or {})
        technical = str(story.get("technical_label") or game.get("title") or "")

        for hit in _pass_rows(story):
            raw_date = str(hit.get("date") or "")[:10]
            if not raw_date:
                continue
            number = int(hit.get("pass_number") or 1)
            label = str(hit.get("pass_label") or f"Pass {number}")
            rows.append(
                (
                    raw_date,
                    _date_label(raw_date),
                    f"{technical} · Pass {number} · {label}",
                )
            )

        for trigger in [
            row for row in list(story.get("triggers") or [])
            if isinstance(row, dict)
        ]:
            raw_date = str(trigger.get("date") or "")[:10]
            if not raw_date:
                continue
            label = str(
                trigger.get("activation_label")
                or trigger.get("technical_label")
                or "Supporting trigger"
            )
            rows.append((raw_date, _date_label(raw_date), label))

    if not rows:
        return

    st.markdown("## Key dates")
    st.caption(
        "Quick reference only — the interpretation is already above. "
        "This index keeps the primary exact contacts and their trigger dates."
    )

    seen = set()
    for sort_key, date_text, label in sorted(rows, key=lambda row: (row[0], row[2]))[:20]:
        key = (sort_key, label)
        if key in seen:
            continue
        seen.add(key)
        st.markdown(
            '<div class="natal-signature-reading paid-key-date">'
            f'<div class="natal-evidence">{escape(date_text)}</div>'
            f'<p>{escape(label)}</p>'
            "</div>",
            unsafe_allow_html=True,
        )


def _render_evidence_body(
    packet: dict[str, Any],
) -> None:
    for game in [
        row for row in list(packet.get("games") or [])
        if isinstance(row, dict)
    ]:
        st.markdown(
            f"**Major issue {int(game.get('number') or 0):02d} · "
            f"{str(game.get('title') or '')}**"
        )
        stories = [dict(game.get("primary_transit") or {})] + [
            row for row in list(game.get("supporting_transits") or [])
            if isinstance(row, dict)
        ]
        for story in stories:
            technical = str(story.get("technical_label") or "")
            st.markdown(f"- **{technical}**")
            natal_position = _position_label(story.get("natal_position"))
            if natal_position:
                st.markdown(
                    f"  - Natal {story.get('natal_target') or 'target'} · {natal_position}"
                )
            if story.get("natal_house") is not None:
                st.markdown(f"  - House {int(story.get('natal_house'))}")
            st.markdown(
                f"  - Active window · {_date_label(story.get('start'))} – {_date_label(story.get('end'))}"
            )
            for hit in _pass_rows(story):
                when = _date_label(hit.get("date"))
                if hit.get("time"):
                    when += f" · {hit.get('time')}"
                position = _position_label(hit.get("transit_position"))
                motion = "retrograde" if bool(hit.get("retrograde")) else "direct"
                details = [
                    f"Pass {int(hit.get('pass_number') or 1)}",
                    str(hit.get("pass_label") or ""),
                    when,
                    motion,
                    f"{float(hit.get('orb') or 0.0):.2f}° orb",
                ]
                if position:
                    details.append(position)
                st.markdown("  - " + " · ".join(bit for bit in details if bit))


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
    """Render Paid Yearly with the same natal foundation as Paid Monthly."""
    value = _packet_dict(packet)

    st.markdown('<section class="natal-shell paid-yearly-editorial-shell">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="editorial-title">{escape(editorial.headline or "Your Year Ahead")}</div>',
        unsafe_allow_html=True,
    )

    intro = str(editorial.deck or "").strip()
    intro_text = str(label or "")
    if intro:
        intro_text += (" · " if intro_text else "") + intro
    st.markdown(
        f'<div class="natal-intro">{escape(intro_text)}</div>',
        unsafe_allow_html=True,
    )

    # Critical: this is the SAME canonical natal renderer Paid Monthly already
    # uses. No duplicate Yearly natal design is created here.
    render_natal_core(
        snapshot,
        precision_note=str(natal_precision or ""),
        show_evidence=False,
        use_live_voice=False,
        use_live_signature_moves=False,
    )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("## Read the year")

    if editorial.voice_complete and editorial.read_year:
        st.markdown(
            '<div class="natal-signature-reading paid-monthly-longform paid-monthly-article">'
            + _story_paragraphs(editorial.read_year)
            + "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.error("Luna could not complete the paid annual reading cleanly. Please regenerate it.")

    _render_year_map(value)

    st.markdown("## The major issues of your year")
    st.caption(
        "These are the strongest selected personal transit arcs. Each chapter explains "
        "the human situation first; exact passes and technical evidence stay underneath."
    )
    for game in [
        row for row in list(value.get("games") or [])
        if isinstance(row, dict)
    ]:
        _render_issue(game, editorial)

    if editorial.closing:
        st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
        st.markdown("## What the year leaves you with")
        st.markdown(
            '<div class="natal-signature-reading paid-monthly-longform paid-monthly-article">'
            + _story_paragraphs(editorial.closing)
            + "</div>",
            unsafe_allow_html=True,
        )

    _key_dates(value)

    if evidence_panel is not None:
        with evidence_panel("Why Luna sees this · chart evidence"):
            _render_evidence_body(value)
            if trust_statement:
                st.markdown(f"**{trust_statement}**")
            if trust_disclosure:
                st.caption(trust_disclosure)
    else:
        with st.expander("Why Luna sees this · chart evidence", expanded=False):
            _render_evidence_body(value)
            if trust_statement:
                st.markdown(f"**{trust_statement}**")
            if trust_disclosure:
                st.caption(trust_disclosure)

    if order_reference:
        st.caption(f"Order reference · {order_reference}")
    st.markdown("</section>", unsafe_allow_html=True)
