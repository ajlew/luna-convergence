from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import BytesIO

from PIL import Image, ImageDraw

from birthday_card import (
    SOCIAL_SIZE,
    MASTER_SIZE,
    THEMES,
    _font,
    _fit_font,
    _wrapped_lines,
    _draw_tracked_center,
    _paste_celestial_asset,
    _draw_solar_disc,
    _draw_lunar_disc,
    _background_for,
)


@dataclass(frozen=True)
class SkyCard:
    card_date: date
    weekday: str
    event: str
    technical: str
    luna_copy: str
    timing: str = ""
    timezone: str = ""
    timezone_label: str = ""
    phase: str = ""
    protected: bool = False
    theme: str = "painted_blue"

    @property
    def date_label(self) -> str:
        return self.card_date.strftime("%d %B").lstrip("0").upper()


def build_sky_card(
    card_data: dict,
    luna_copy: str,
    *,
    theme: str = "painted_blue",
) -> SkyCard:
    """Combine calculated Sky Card evidence with Luna-written copy.

    This function does not calculate or invent astronomical events.
    """
    if not card_data.get("has_event"):
        raise ValueError("A Sky Card requires a selected calculated event.")

    event = str(card_data.get("event") or "").strip()
    copy = " ".join(str(luna_copy or "").split()).strip()

    if not event:
        raise ValueError("Sky Card event is required.")
    if not copy:
        raise ValueError("Luna copy is required.")

    return SkyCard(
        card_date=date.fromisoformat(card_data["date"]),
        weekday=str(card_data.get("weekday") or "").strip(),
        event=event,
        technical=str(card_data.get("technical") or "").strip(),
        luna_copy=copy,
        timing=str(card_data.get("timing") or "").strip(),
        timezone=str(card_data.get("timezone") or "").strip(),
        timezone_label=str(card_data.get("timezone_label") or "").strip(),
        phase=str(card_data.get("phase") or "").strip(),
        protected=bool(card_data.get("protected")),
        theme=theme if theme in THEMES else "painted_blue",
    )


def _background_for_sky_card(card: SkyCard):
    # Birthday renderer currently only needs an object carrying .theme.
    return _background_for(card)


def _draw_sky_stars(image: Image.Image, card: SkyCard) -> None:
    """Sparse deterministic stars keyed to the astronomical date/event."""
    import hashlib
    import random

    width, height = image.size
    seed_material = f"{card.card_date.isoformat()}|{card.event}".encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")
    rng = random.Random(seed)
    draw = ImageDraw.Draw(image, "RGBA")

    protected_regions = (
        (120, 180, 2280, 620),
        (150, 760, 2250, 1420),
        (180, 1900, 2220, 3100),
        (120, 3750, 1900, 4100),
    )

    def blocked(px: int, py: int) -> bool:
        return any(
            left <= px <= right and top <= py <= bottom
            for left, top, right, bottom in protected_regions
        )

    for _ in range(105):
        x = rng.randint(70, width - 70)
        y = rng.randint(80, height - 80)
        if blocked(x, y):
            continue
        radius = rng.choice((2, 2, 2, 3, 3, 4, 6))
        alpha = rng.randint(90, 190)
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=(237, 241, 247, alpha),
        )


def _copy_layout(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
):
    for size in range(86, 39, -2):
        font = _font("mono", size)
        lines = _wrapped_lines(draw, text, font, max_width)
        line_height = int(size * 1.5)
        if len(lines) <= 9 and len(lines) * line_height <= 900:
            return font, lines, line_height

    font = _font("mono", 38)
    return font, _wrapped_lines(draw, text, font, max_width), 57


def render_sky_card_master(card: SkyCard) -> Image.Image:
    width, height = MASTER_SIZE
    image, theme = _background_for_sky_card(card)

    if bool(theme["stars"]):
        _draw_sky_stars(image, card)

    draw = ImageDraw.Draw(image)
    text_colour = str(theme["text"])
    muted_colour = str(theme["muted"])
    accent_colour = str(theme["accent"])

    # Day/date
    draw.text(
        (190, 240),
        f"{card.weekday.upper()} · {card.date_label}",
        font=_font("mono", 62),
        fill=muted_colour,
    )

    _draw_tracked_center(
        draw,
        "TODAY'S SKY",
        500,
        _font("sans", 64),
        tracking=18,
        fill=muted_colour,
    )

    # Main calculated event
    event_text = card.event.upper()
    event_font = _fit_font(draw, event_text, "display", 220, 2020, 96)
    draw.text(
        (width / 2, 880),
        event_text,
        font=event_font,
        fill=text_colour,
        anchor="mm",
    )

    draw.line((850, 1130, 1550, 1130), fill=accent_colour, width=3)

    # Celestial visual anchors. These are decorative only; the event itself
    # remains determined upstream by the calculation system.
    left_x, right_x, icon_y = 760, 1640, 1430

    if not _paste_celestial_asset(
        image, "sun-photographic.png", left_x, icon_y, 300
    ):
        _draw_solar_disc(image, left_x, icon_y, 105)

    if not _paste_celestial_asset(
        image, "moon-photographic.png", right_x, icon_y, 270
    ):
        _draw_lunar_disc(image, right_x, icon_y, 105)

    draw = ImageDraw.Draw(image)

    # Luna interpretation
    copy_font, copy_lines, line_height = _copy_layout(
        draw, card.luna_copy, 1740
    )
    copy_top = 1900

    for index, line in enumerate(copy_lines):
        draw.text(
            (width / 2, copy_top + index * line_height),
            line,
            font=copy_font,
            fill=text_colour,
            anchor="ma",
        )

    # Calculation evidence
    evidence = card.technical or card.event
    if card.timing:
        evidence = f"{evidence} · {card.timing}"

    timezone_display = card.timezone_label or card.timezone
    if timezone_display:
        evidence = f"{evidence} · {timezone_display}"

    evidence_font = _font("mono", 34)
    evidence_lines = _wrapped_lines(draw, evidence.upper(), evidence_font, 1900)

    evidence_y = 3300
    for index, line in enumerate(evidence_lines[:3]):
        draw.text(
            (width / 2, evidence_y + index * 52),
            line,
            font=evidence_font,
            fill=muted_colour,
            anchor="ma",
        )

    if card.phase:
        draw.text(
            (width / 2, 3510),
            card.phase.upper(),
            font=_font("mono", 30),
            fill=accent_colour,
            anchor="ma",
        )

    # Luna branding
    cx, cy, cube = 260, 3920, 82
    draw.polygon(
        [(cx, cy - cube), (cx + cube, cy - cube // 2),
         (cx, cy), (cx - cube, cy - cube // 2)],
        fill=text_colour,
    )
    draw.polygon(
        [(cx - cube, cy - cube // 2), (cx, cy),
         (cx, cy + cube), (cx - cube, cy + cube // 2)],
        fill=accent_colour,
    )
    draw.polygon(
        [(cx, cy), (cx + cube, cy - cube // 2),
         (cx + cube, cy + cube // 2), (cx, cy + cube)],
        fill=muted_colour,
    )

    draw.text(
        (420, 3884),
        "L U N A   C O N V E R G E N C E",
        font=_font("sans", 37),
        fill=text_colour,
    )
    draw.text(
        (420, 3956),
        "THE UNIVERSE SHIFTS. YOU'VE GOT THIS.",
        font=_font("mono", 30),
        fill=muted_colour,
    )

    return image


def render_sky_card_png(card: SkyCard) -> bytes:
    master = render_sky_card_master(card)
    social = master.resize(SOCIAL_SIZE, Image.Resampling.LANCZOS)
    buffer = BytesIO()
    social.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
