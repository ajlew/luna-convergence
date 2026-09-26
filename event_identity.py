"""Canonical identity for Luna calculated sky events.

Identity describes the underlying calculated event, never its ranking,
classification, protection status, interpretation, or presentation.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Iterable


_ASPECT_ALIASES = {
    "conjunct": "conjunction",
    "conjunction": "conjunction",
    "opposite": "opposition",
    "opposition": "opposition",
    "square": "square",
    "trine": "trine",
    "sextile": "sextile",
}


def _slug(value: str) -> str:
    value = str(value or "").strip().casefold()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _normalise_aspect(
    aspect_name: str,
    technical_label: str,
) -> str:
    supplied = str(aspect_name or "").strip().casefold()

    if supplied in _ASPECT_ALIASES:
        return _ASPECT_ALIASES[supplied]

    source = str(technical_label or "").casefold()

    for word, canonical in _ASPECT_ALIASES.items():
        if re.search(rf"\b{re.escape(word)}\b", source):
            return canonical

    return ""


def canonical_event_identity(
    event_date: date | str,
    event_kind: str,
    technical_label: str,
    planets: Iterable[str] = (),
    aspect_name: str = "",
) -> str:
    """Return the stable identity of one calculated sky event."""

    day = (
        event_date.isoformat()
        if isinstance(event_date, date)
        else str(event_date or "").strip()
    )
    kind = str(event_kind or "").strip().casefold()
    bodies = tuple(
        str(body).strip().casefold()
        for body in (planets or ())
        if str(body).strip()
    )

    if kind == "aspect" and len(bodies) >= 2:
        aspect = _normalise_aspect(aspect_name, technical_label)

        if aspect:
            pair = sorted(bodies[:2])
            return f"{day}|aspect|{pair[0]}|{pair[1]}|{aspect}"

    return f"{day}|{kind}|{_slug(technical_label)}"


def event_identity(event: object) -> str:
    """Return canonical identity directly from an astrology Event-like object."""

    return canonical_event_identity(
        getattr(event, "event_date"),
        getattr(event, "kind"),
        getattr(event, "title"),
        getattr(event, "planets", ()),
        getattr(event, "aspect_name", ""),
    )
