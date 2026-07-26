from __future__ import annotations

from dataclasses import dataclass, asdict
from io import BytesIO
import re

from pypdf import PdfReader


@dataclass
class EphemerisProfile:
    filename: str
    year: int | None
    zodiac: str | None
    perspective: str | None
    page_count: int
    planets: list[str]
    confidence: str
    supported: bool
    warnings: list[str]
    excerpt: str


def inspect_ephemeris_pdf(data: bytes, filename: str) -> EphemerisProfile:
    reader = PdfReader(BytesIO(data))
    page_count = len(reader.pages)
    text_parts = []
    for page in reader.pages[:3]:
        try:
            text_parts.append(page.extract_text() or "")
        except Exception:
            pass
    text = "\n".join(text_parts)
    compact = " ".join(text.split())

    year_match = re.search(r"(?:year|YEAR)\s+(19\d{2}|20\d{2}|21\d{2})", compact)
    if not year_match:
        year_match = re.search(r"\b(19\d{2}|20\d{2}|21\d{2})\b", compact)
    year = int(year_match.group(1)) if year_match else None

    lower = compact.lower()
    perspective = None
    if "geocentric" in lower:
        perspective = "geocentric"
    elif "heliocentric" in lower:
        perspective = "heliocentric"

    zodiac = None
    if "tropical" in lower:
        zodiac = "tropical"
    elif "sidereal" in lower:
        zodiac = "sidereal"

    planets = []
    contains_match = re.search(r"contains\s+(.+?)(?:Programming|Code|Astrodienst)", compact, re.I)
    if contains_match:
        raw = contains_match.group(1)
        raw = raw.replace("Moon's Node", "Moon Node")
        planets = [part.strip() for part in re.split(r",| and ", raw) if part.strip()]

    warnings = []
    supported = True
    if year is None:
        supported = False
        warnings.append("The year could not be detected. Enter it manually.")
    if perspective != "geocentric":
        supported = False
        warnings.append("Ordinary Sun-sign forecasts require a geocentric ephemeris.")
    if zodiac != "tropical":
        supported = False
        warnings.append("This app is currently configured for the tropical zodiac.")
    if "astrodienst" not in lower and "swiss ephemeris" not in lower:
        warnings.append("The file does not clearly identify itself as an Astrodienst/Swiss Ephemeris table.")

    confidence = "high" if year and perspective and zodiac else "medium" if year else "low"

    return EphemerisProfile(
        filename=filename,
        year=year,
        zodiac=zodiac,
        perspective=perspective,
        page_count=page_count,
        planets=planets,
        confidence=confidence,
        supported=supported,
        warnings=warnings,
        excerpt=compact[:1200],
    )


def profile_to_dict(profile: EphemerisProfile) -> dict:
    return asdict(profile)


def source_note(profile: EphemerisProfile | None) -> str:
    if not profile:
        return ""
    return (
        f"**Uploaded ephemeris reference:** {profile.filename} — "
        f"{profile.year or 'unknown year'}, {profile.zodiac or 'unknown zodiac'}, "
        f"{profile.perspective or 'unknown perspective'}. "
        "The PDF identifies the reference year and coordinate system; planetary positions are "
        "then regenerated directly with Swiss Ephemeris rather than extracted from tiny table glyphs."
    )
