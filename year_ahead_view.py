from __future__ import annotations

"""Streamlit renderer for the deterministic Year Ahead.

The report is rendered from Python-owned YearPacket data whether Luna Voice is
available or not. Voice adds one optional "Read the Year" section and never
controls whether the calculated report exists.
"""

from datetime import date
from html import escape
from typing import Any

import streamlit as st

from year_ahead import YearPacket
from year_ahead_voice import generate_year_ahead_voice


YEAR_AHEAD_VIEW_VERSION = "1.0"


def _date_label(value: object) -> str:
    if isinstance(value, date):
        return value.strftime("%d %b %Y").lstrip("0")
    text = str(value or "").strip()
    try:
        return date.fromisoformat(text[:10]).strftime("%d %b %Y").lstrip("0")
    except (TypeError, ValueError):
        return text


def _time_suffix(value: object) -> str:
    text = str(value or "").strip()
    return f" · {text}" if text else ""


def _position_label(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    sign = str(value.get("sign") or "").strip()
    degree = value.get("degree")
    longitude = value.get("longitude")
    parts: list[str] = []
    if degree is not None and sign:
        parts.append(f"{float(degree):.2f}° {sign}")
    elif sign:
        parts.append(sign)
    if longitude is not None:
        parts.append(f"{float(longitude):.2f}° ecliptic")
    return " · ".join(parts)


def _render_year_strip(packet: YearPacket) -> None:
    rows = [item for item in list(packet.year_strip or ()) if isinstance(item, dict)]
    if not rows:
        return

    st.markdown("## Year strip")
    st.caption("Intensity shows how concentrated the selected transit arcs are. The phase label tells you what kind of month it is.")
    cells = []
    for item in rows:
        month = escape(str(item.get("month") or ""))
        phase = escape(str(item.get("phase") or "QUIET"))
        intensity = max(0.0, min(1.0, float(item.get("intensity") or 0.0)))
        height = 6 + int(round(38 * intensity))
        opacity = 0.18 + 0.82 * intensity
        cells.append(
            f'<div class="timing-month" style="min-width:0;text-align:center">'
            f'<span>{month}</span>'
            f'<i style="height:{height}px;opacity:{opacity:.2f}"></i>'
            f'<strong style="display:block;font:500 9px Josefin Sans,sans-serif;'
            f'letter-spacing:.03em">{phase}</strong></div>'
        )
    st.markdown(
        '<div class="timing-strip" aria-label="Year Ahead timing strip">'
        + "".join(cells)
        + "</div>",
        unsafe_allow_html=True,
    )


def _paragraphs(value: object) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    return [
        " ".join(part.split())
        for part in text.split("\n\n")
        if str(part or "").strip()
    ]


def _voice_once(
    packet: YearPacket,
    *,
    voice_enabled: bool,
    base_url: str,
    model: str,
    api_key: str,
) -> tuple[str, str]:
    """Return cached prose/error for this exact deterministic packet.

    Streamlit reruns must not create extra provider calls. A failed call is also
    cached for the packet so deterministic output remains stable and usable.
    """
    cache_key = "year-ahead-single-voice-v1"
    cached = st.session_state.get(cache_key)
    if isinstance(cached, dict) and cached.get("packet_hash") == packet.packet_hash:
        return str(cached.get("prose") or ""), str(cached.get("error") or "")

    if not voice_enabled:
        error = "Luna Voice is not configured."
        st.session_state[cache_key] = {
            "packet_hash": packet.packet_hash,
            "prose": "",
            "error": error,
        }
        return "", error

    try:
        with st.spinner("Luna is turning the calculated year into one connected story. Keep this page open…"):
            prose = generate_year_ahead_voice(
                packet,
                base_url=base_url,
                model=model,
                api_key=api_key,
            )
        error = ""
    except Exception as exc:
        prose = ""
        error = " ".join(str(exc or "Voice unavailable").split())[:700]

    st.session_state[cache_key] = {
        "packet_hash": packet.packet_hash,
        "prose": prose,
        "error": error,
    }
    return prose, error


def _primary_peak(primary: dict[str, Any]) -> dict[str, Any] | None:
    passes = [item for item in list(primary.get("passes") or []) if isinstance(item, dict)]
    if not passes:
        return None
    return min(
        passes,
        key=lambda item: (
            float(item.get("orb", 99.0) or 99.0),
            str(item.get("date") or ""),
            str(item.get("time") or ""),
        ),
    )


def _render_passes(primary: dict[str, Any]) -> None:
    passes = [item for item in list(primary.get("passes") or []) if isinstance(item, dict)]
    if not passes:
        st.caption("No exact pass fell inside this 12-month window.")
        return

    for item in passes:
        number = int(item.get("pass_number") or 1)
        label = str(item.get("pass_label") or f"Pass {number}")
        motion = "retrograde" if bool(item.get("retrograde")) else "direct"
        when = _date_label(item.get("date")) + _time_suffix(item.get("time"))
        orb = float(item.get("orb") or 0.0)
        position = _position_label(item.get("transit_position"))
        position_text = f" · {escape(position)}" if position else ""
        st.markdown(
            f"- **Pass {number} — {escape(label)}:** {escape(when)} · "
            f"{escape(motion)}{position_text} · {orb:.2f}° orb"
        )


def _render_triggers(primary: dict[str, Any]) -> None:
    triggers = [item for item in list(primary.get("triggers") or []) if isinstance(item, dict)]
    if not triggers:
        return

    st.markdown("**Supporting triggers**")
    for item in triggers:
        label = str(item.get("activation_label") or item.get("technical_label") or "Trigger")
        when = _date_label(item.get("date")) + _time_suffix(item.get("time"))
        pass_number = item.get("activates_pass_number")
        pass_text = f" · activates Pass {pass_number}" if pass_number else ""
        position = _position_label(item.get("transit_position"))
        position_text = f" · {escape(position)}" if position else ""
        orb = float(item.get("orb") or 0.0)
        st.markdown(
            f"- {escape(label)} · **{escape(when)}**{escape(pass_text)}"
            f"{position_text} · {orb:.2f}° orb"
        )


def _render_game(game: Any) -> None:
    primary = dict(game.primary_transit or {})
    supporting = [
        dict(item) for item in list(game.supporting_transits or [])
        if isinstance(item, dict)
    ]
    peak = _primary_peak(primary)

    starts = _date_label(game.start_date)
    strongest = (
        _date_label(peak.get("date")) + _time_suffix(peak.get("time"))
        if peak else starts
    )
    eases = _date_label(game.end_date)

    st.markdown(
        f"""<article class="timing-story year-game-card">
<div class="timing-meta">GAME {int(game.number):02d} · {escape(str(game.polarity).upper())} · {escape(str(game.human_life_area))}</div>
<h2>{escape(str(game.title))}</h2>
<p><strong>{escape(str(game.strategic_frame))}</strong></p>
<div class="timing-plain-grid">
  <div><span>What is happening</span><p>{escape(str(primary.get("summary") or ""))}</p></div>
  <div><span>Your strategic edge</span><p>{escape(str(game.advantage))}</p></div>
</div>
<div class="timing-phase-grid">
  <div><span>Starts</span><strong>{escape(starts)}</strong></div>
  <div><span>Strongest</span><strong>{escape(strongest)}</strong></div>
  <div><span>Eases</span><strong>{escape(eases)}</strong></div>
</div>
<div class="timing-move"><div class="timing-move-label">Your move</div><p>{escape(str(game.move))}</p></div>
</article>""",
        unsafe_allow_html=True,
    )

    with st.expander("Why Luna sees this · calculations", expanded=False):
        st.markdown(
            f"**Primary transit:** {escape(str(primary.get('technical_label') or ''))}"
            + (
                f" · natal house {int(primary['natal_house'])}"
                if primary.get("natal_house") is not None
                else ""
            )
        )
        natal_position = _position_label(primary.get("natal_position"))
        if natal_position:
            st.markdown(
                f"**Natal {escape(str(primary.get('natal_target') or 'target'))}:** "
                f"{escape(natal_position)}"
            )
        st.markdown(
            f"**Active window:** {escape(_date_label(primary.get('start')))} → "
            f"{escape(_date_label(primary.get('end')))}"
        )
        _render_passes(primary)
        _render_triggers(primary)

        if supporting:
            st.markdown("**Supporting transits**")
            for item in supporting:
                label = str(item.get("technical_label") or "")
                natal_position = _position_label(item.get("natal_position"))
                natal_text = f" · natal {escape(natal_position)}" if natal_position else ""
                st.markdown(f"- **{escape(label)}**{natal_text}")
                for hit in list(item.get("passes") or []):
                    if not isinstance(hit, dict):
                        continue
                    pass_number = int(hit.get("pass_number") or 1)
                    pass_label = str(hit.get("pass_label") or f"Pass {pass_number}")
                    motion = "retrograde" if bool(hit.get("retrograde")) else "direct"
                    when = _date_label(hit.get("date")) + _time_suffix(hit.get("time"))
                    orb = float(hit.get("orb") or 0.0)
                    position = _position_label(hit.get("transit_position"))
                    position_text = f" · {escape(position)}" if position else ""
                    st.markdown(
                        f"  - Pass {pass_number} — {escape(pass_label)}: "
                        f"{escape(when)} · {escape(motion)}{position_text} · {orb:.2f}° orb"
                    )

        st.markdown(f"**Risk:** {escape(str(game.risk))}")
        st.markdown(f"**Do not:** {escape(str(game.dont))}")


def render_year_ahead(
    packet: YearPacket,
    *,
    voice_enabled: bool,
    base_url: str,
    model: str,
    api_key: str,
) -> None:
    """Render the calculated report first; voice is optional enrichment."""
    stats = dict(packet.year_statistics or {})

    st.markdown(
        f"""<div class="timing-summary-grid">
  <div><span>Major games</span><strong>{int(stats.get("major_games", 0) or 0)}</strong></div>
  <div><span>Turning points</span><strong>{int(stats.get("turning_points", 0) or 0)}</strong></div>
  <div><span>Rule changes</span><strong>{int(stats.get("rule_changes", 0) or 0)}</strong></div>
</div>""",
        unsafe_allow_html=True,
    )

    _render_year_strip(packet)

    prose, error = _voice_once(
        packet,
        voice_enabled=voice_enabled,
        base_url=base_url,
        model=model,
        api_key=api_key,
    )

    if prose:
        st.markdown("## Read the year")
        paragraph_html = "".join(
            f"<p>{escape(paragraph)}</p>"
            for paragraph in _paragraphs(prose)
        )
        st.markdown(
            f'<section class="weekly-synthesis luna-guided-story">{paragraph_html}</section>',
            unsafe_allow_html=True,
        )
    elif error:
        # Customer-facing deterministic report remains complete. Keep provider
        # details out of sight; owner diagnostics can be inspected separately.
        st.caption("Luna's narrative voice is unavailable right now. Your calculated Year Ahead remains below.")

    st.markdown("## Your major games")
    st.caption(
        "These are the strongest personal transit arcs in chronological order. "
        "Repeated direct/retrograde contacts stay together as one developing story."
    )

    if not packet.games:
        st.info("No major exact transit arcs passed the current threshold in this 12-month window.")
        return

    for game in packet.games:
        _render_game(game)
