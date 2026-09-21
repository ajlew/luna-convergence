from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path
import re
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

if TYPE_CHECKING:
    from natal_snapshot import NatalSnapshot


SOCIAL_SIZE = (1080, 1920)
# Render above social resolution so the matching PDF remains crisp. The canvas
# keeps the same 9:16 composition as Instagram Reels and Stories.
MASTER_SIZE = (2400, 4267)
PDF_SIZE = (5.625 * inch, 10 * inch)
WHITE = "#FFFFFF"
BLACK = "#050505"
MUTED = "#5D5D58"
GOLD = "#C59A32"

ASSET_DIR = Path(__file__).resolve().parent / "assets"

SUN_WORD = {
    "Aries": "Courage",
    "Taurus": "Devotion",
    "Gemini": "Curiosity",
    "Cancer": "Belonging",
    "Leo": "Radiance",
    "Virgo": "Purpose",
    "Libra": "Balance",
    "Scorpio": "Truth",
    "Sagittarius": "Wonder",
    "Capricorn": "Resolve",
    "Aquarius": "Freedom",
    "Pisces": "Imagination",
}

MOON_ENDING = {
    "Aries": "brave beginning waiting to move",
    "Taurus": "quiet strength waiting to take root",
    "Gemini": "bright idea waiting to be spoken",
    "Cancer": "tender place waiting to feel at home",
    "Leo": "warm light waiting to be seen",
    "Virgo": "useful gift waiting to take shape",
    "Libra": "harmony waiting to be chosen",
    "Scorpio": "deeper truth waiting to surface",
    "Sagittarius": "wider horizon waiting to open",
    "Capricorn": "steady promise waiting to become real",
    "Aquarius": "wild freedom waiting to break open",
    "Pisces": "private dream waiting to find form",
}

@dataclass(frozen=True)
class BirthdayCard:
    recipient_name: str
    birth_date: date
    date_label: str
    sun_sign: str
    moon_label: str
    poem: str
    birth_time_known: bool


def suggested_poem(sun_sign: str, moon_sign: str | None) -> str:
    opening = SUN_WORD.get(sun_sign, "The sky")
    ending = MOON_ENDING.get(moon_sign or "", "inner light waiting to unfold")
    return f"{opening} only reveals the {ending}."


def build_birthday_card(
    *,
    recipient_name: str,
    birth_date: date,
    snapshot: "NatalSnapshot",
    poem: str = "",
) -> BirthdayCard:
    name = " ".join(str(recipient_name or "").split()).strip()
    if not name:
        raise ValueError("recipient_name is required")

    by_planet = {item.planet: item for item in snapshot.positions}
    sun_sign = by_planet["Sun"].sign
    moon_sign = by_planet["Moon"].sign
    sun_uncertain = tuple(getattr(snapshot, "sun_uncertain", ()))
    if not snapshot.birth_time_known and len(sun_uncertain) > 1:
        sun_label = " / ".join(sun_uncertain)
        poem_sun = ""
    else:
        sun_label = sun_sign
        poem_sun = sun_sign
    if not snapshot.birth_time_known and len(snapshot.moon_uncertain) > 1:
        moon_label = " / ".join(snapshot.moon_uncertain)
        poem_moon = None
    else:
        moon_label = moon_sign
        poem_moon = moon_sign

    date_label = birth_date.strftime("%d %B").lstrip("0").upper()
    clean_poem = " ".join(str(poem or "").split()).strip()

    return BirthdayCard(
        recipient_name=name,
        birth_date=birth_date,
        date_label=date_label,
        sun_sign=sun_label,
        moon_label=moon_label,
        poem=clean_poem or suggested_poem(poem_sun, poem_moon),
        birth_time_known=snapshot.birth_time_known,
    )


def _font_candidates(role: str) -> list[Path]:
    local = ASSET_DIR / "fonts"
    choices = {
        "display": [
            local / "BodoniModa-SemiBold.ttf",
            local / "BodoniModa-VariableFont_opsz,wght.ttf",
            Path("/usr/share/fonts/opentype/urw-base35/NimbusRoman-Bold.otf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
        ],
        "sans": [
            local / "JosefinSans-Regular.ttf",
            local / "JosefinSans-VariableFont_wght.ttf",
            Path("/usr/share/fonts/opentype/urw-base35/NimbusSans-Regular.otf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ],
        "mono": [
            local / "IBMPlexMono-Regular.ttf",
            Path("/usr/share/fonts/opentype/urw-base35/NimbusMonoPS-Regular.otf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
        ],
    }
    return choices[role]


def _font(role: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _font_candidates(role):
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _fit_font(draw: ImageDraw.ImageDraw, text: str, role: str, start: int, max_width: int, minimum: int) -> ImageFont.ImageFont:
    size = start
    while size > minimum:
        font = _font(role, size)
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return font
        size -= 4
    return _font(role, minimum)


def _draw_tracked_center(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.ImageFont,
    *,
    tracking: int,
    fill: str = BLACK,
    width: int = MASTER_SIZE[0],
) -> None:
    glyph_widths = [draw.textlength(char, font=font) for char in text]
    total = sum(glyph_widths) + tracking * max(0, len(text) - 1)
    x = (width - total) / 2
    for char, glyph_width in zip(text, glyph_widths):
        draw.text((x, y), char, font=font, fill=fill)
        x += glyph_width + tracking


def _wrapped_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _poem_layout(draw: ImageDraw.ImageDraw, text: str, max_width: int) -> tuple[ImageFont.ImageFont, list[str], int]:
    for size in range(136, 39, -2):
        font = _font("display", size)
        lines = _wrapped_lines(draw, text, font, max_width)
        line_height = int(size * 1.34)
        if len(lines) <= 12 and len(lines) * line_height <= 740:
            return font, lines, line_height
    font = _font("display", 22)
    return font, _wrapped_lines(draw, text, font, max_width), 30


def render_birthday_card_master(card: BirthdayCard) -> Image.Image:
    width, height = MASTER_SIZE
    image = Image.new("RGB", MASTER_SIZE, WHITE)
    draw = ImageDraw.Draw(image)

    mono = _font("mono", 80)
    draw.text((190, 260), card.date_label, font=mono, fill=BLACK)
    draw.text((190, 375), "A BIRTHDAY SKY", font=_font("mono", 46), fill=MUTED)

    # The recipient is the visual event: this complete title field occupies the
    # upper third of the tall card, as in the approved Luna mockup.
    _draw_tracked_center(draw, "HAPPY BIRTHDAY", 700, _font("sans", 92), tracking=25)
    display_name = card.recipient_name.upper()
    name_font = _fit_font(draw, display_name, "display", 330, 2020, 140)
    draw.text((width / 2, 1010), display_name, font=name_font, fill=BLACK, anchor="mm")

    draw.line((190, 1370, width - 190, 1370), fill=BLACK, width=3)
    label_font = _font("mono", 50)
    left_icon_x, right_icon_x, icon_y = 260, 1260, 1590
    icon_r = 40
    # Keep celestial symbols with their calculated positions. A decorative Sun
    # in the top corner made the whole composition visually top-heavy.
    draw.ellipse(
        (left_icon_x - icon_r, icon_y - icon_r, left_icon_x + icon_r, icon_y + icon_r),
        outline=GOLD,
        width=8,
    )
    draw.ellipse(
        (left_icon_x - 7, icon_y - 7, left_icon_x + 7, icon_y + 7),
        fill=GOLD,
    )
    draw.ellipse(
        (right_icon_x - icon_r, icon_y - icon_r, right_icon_x + icon_r, icon_y + icon_r),
        fill=BLACK,
    )
    draw.ellipse(
        (right_icon_x - 5, icon_y - icon_r - 2, right_icon_x + icon_r + 9, icon_y + icon_r + 2),
        fill=WHITE,
    )

    left_x, right_x = 340, 1340
    draw.text((left_x, 1445), "SUN", font=label_font, fill=MUTED)
    sun_font = _fit_font(draw, f"IN {card.sun_sign.upper()}", "sans", 96, 930, 52)
    draw.text((left_x, 1535), f"IN {card.sun_sign.upper()}", font=sun_font, fill=BLACK)
    draw.text((right_x, 1445), "MOON", font=label_font, fill=MUTED)
    moon_font = _fit_font(draw, f"IN {card.moon_label.upper()}", "sans", 96, 930, 52)
    draw.text((right_x, 1535), f"IN {card.moon_label.upper()}", font=moon_font, fill=BLACK)

    poem_font, poem_lines, line_height = _poem_layout(draw, card.poem, 1740)
    poem_top = 2290
    for index, line in enumerate(poem_lines):
        draw.text((width / 2, poem_top + index * line_height), line, font=poem_font, fill=BLACK, anchor="ma")

    # A restrained Luna cube, drawn as vector shapes so the export remains crisp.
    cx, cy, cube = 260, 3920, 82
    draw.polygon([(cx, cy - cube), (cx + cube, cy - cube // 2), (cx, cy), (cx - cube, cy - cube // 2)], fill="#202020")
    draw.polygon([(cx - cube, cy - cube // 2), (cx, cy), (cx, cy + cube), (cx - cube, cy + cube // 2)], fill="#050505")
    draw.polygon([(cx, cy), (cx + cube, cy - cube // 2), (cx + cube, cy + cube // 2), (cx, cy + cube)], fill="#0D0D0D")
    brand_font = _font("sans", 37)
    draw.text((420, 3884), "L U N A   C O N V E R G E N C E", font=brand_font, fill=BLACK)
    draw.text((420, 3956), "THE UNIVERSE SHIFTS. YOU'VE GOT THIS.", font=_font("mono", 30), fill=MUTED)

    return image


def render_birthday_card_png(card: BirthdayCard) -> bytes:
    master = render_birthday_card_master(card)
    social = master.resize(SOCIAL_SIZE, Image.Resampling.LANCZOS)
    buffer = BytesIO()
    social.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def render_birthday_card_pdf(card: BirthdayCard) -> bytes:
    master = render_birthday_card_master(card)
    image_buffer = BytesIO()
    master.save(image_buffer, format="PNG", optimize=True)
    image_buffer.seek(0)

    output = BytesIO()
    page_width, page_height = PDF_SIZE
    pdf = canvas.Canvas(output, pagesize=PDF_SIZE)
    pdf.setTitle(f"Luna Birthday Card for {card.recipient_name}")
    pdf.setAuthor("Luna Convergence")
    pdf.drawImage(ImageReader(image_buffer), 0, 0, width=page_width, height=page_height, preserveAspectRatio=True)
    pdf.showPage()
    pdf.save()
    return output.getvalue()


def birthday_card_filename(card: BirthdayCard, extension: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", card.recipient_name.lower()).strip("-") or "birthday"
    return f"luna-birthday-card-{slug}.{extension.lstrip('.')}"
