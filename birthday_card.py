from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
from io import BytesIO
import math
from pathlib import Path
import random
import re
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont, ImageOps
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
BACKGROUND = "#101827"
TEXT = "#F5F0E6"
MUTED = "#CBC8C1"
GOLD = "#A88A4A"
SUN_CORE = "#E7B94F"
SUN_EDGE = "#9D6F20"
MOON_LIGHT = "#D9DCE2"
MOON_MID = "#AEB4BE"
MOON_DARK = "#757D89"
ASPECT_ANGLES = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}

ASSET_DIR = Path(__file__).resolve().parent / "assets"
CELESTIAL_DIR = ASSET_DIR / "celestial"
BACKGROUND_DIR = ASSET_DIR / "backgrounds"
THEMES = {
    "painted_blue": {
        "asset": "painted-blue.png",
        "text": "#F7F0E4",
        "muted": "#DED5C8",
        "accent": "#E0B654",
        "overlay": (7, 18, 38, 74),
        "stars": True,
    },
    "ivory_paper": {
        "asset": "ivory-paper.png",
        "text": "#17140F",
        "muted": "#5D5143",
        "accent": "#8A5E28",
        "overlay": (255, 248, 232, 15),
        "stars": False,
    },
}

@dataclass(frozen=True)
class BirthdayCard:
    recipient_name: str
    birth_date: date
    date_label: str
    sun_sign: str
    moon_label: str
    sun_calculation: str | None
    moon_calculation: str | None
    poem: str
    birth_time_known: bool
    theme: str = "painted_blue"


def _aspect_phase(aspect, by_planet: dict[str, object]) -> str:
    """Describe whether a natal aspect is tightening or releasing at birth."""
    first = by_planet[aspect.planet1]
    second = by_planet[aspect.planet2]
    target = ASPECT_ANGLES[aspect.name]

    def separation(first_longitude: float, second_longitude: float) -> float:
        raw = abs(first_longitude - second_longitude) % 360.0
        return min(raw, 360.0 - raw)

    current_orb = abs(separation(first.longitude, second.longitude) - target)
    # Project one hour using the Swiss Ephemeris daily speeds retained on each
    # natal position. This mirrors Weekly Studio's applying/separating logic
    # without pretending a natal aspect has a day-wide "closest approach".
    future_first = (float(first.longitude) + float(first.speed) / 24.0) % 360.0
    future_second = (float(second.longitude) + float(second.speed) / 24.0) % 360.0
    future_orb = abs(separation(future_first, future_second) - target)
    if current_orb <= 0.03:
        return "exact"
    return "applying" if future_orb < current_orb else "separating"


def _luminary_calculation(snapshot: "NatalSnapshot", luminary: str) -> str | None:
    if not snapshot.birth_time_known:
        return None
    relevant = [
        item
        for item in snapshot.aspects
        if luminary in {item.planet1, item.planet2}
    ]
    if not relevant:
        return None
    aspect = sorted(
        relevant,
        key=lambda item: (-float(getattr(item, "strength", 0.0)), float(item.orb)),
    )[0]
    other = aspect.planet2 if aspect.planet1 == luminary else aspect.planet1
    by_planet = {item.planet: item for item in snapshot.positions}
    phase = _aspect_phase(aspect, by_planet)
    return f"{luminary} {aspect.name} {other} · {phase} · {aspect.orb:.2f}° orb at birth"

def build_birthday_card(
    *,
    recipient_name: str,
    birth_date: date,
    snapshot: "NatalSnapshot",
    poem: str,
    date_only_calculations: dict[str, str] | None = None,
    theme: str = "painted_blue",
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
    else:
        sun_label = sun_sign
    if not snapshot.birth_time_known and len(snapshot.moon_uncertain) > 1:
        moon_label = " / ".join(snapshot.moon_uncertain)
    else:
        moon_label = moon_sign

    date_label = birth_date.strftime("%d %B").lstrip("0").upper()
    clean_poem = " ".join(str(poem or "").split()).strip()
    if not clean_poem:
        raise ValueError("A validated or customer-supplied birthday poem is required.")

    if snapshot.birth_time_known:
        sun_calculation = _luminary_calculation(snapshot, "Sun")
        moon_calculation = _luminary_calculation(snapshot, "Moon")
    else:
        safe_calculations = date_only_calculations or {}
        sun_calculation = safe_calculations.get(
            "Sun", "Birth time unknown · exact Sun aspect unavailable"
        )
        moon_calculation = safe_calculations.get(
            "Moon", "Birth time unknown · exact Moon aspect unavailable"
        )

    return BirthdayCard(
        recipient_name=name,
        birth_date=birth_date,
        date_label=date_label,
        sun_sign=sun_label,
        moon_label=moon_label,
        sun_calculation=sun_calculation,
        moon_calculation=moon_calculation,
        poem=clean_poem,
        birth_time_known=snapshot.birth_time_known,
        theme=theme if theme in THEMES else "painted_blue",
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
    fill: str = TEXT,
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
    for size in range(92, 35, -2):
        font = _font("mono", size)
        lines = _wrapped_lines(draw, text, font, max_width)
        line_height = int(size * 1.48)
        if len(lines) <= 12 and len(lines) * line_height <= 740:
            return font, lines, line_height
    font = _font("mono", 22)
    return font, _wrapped_lines(draw, text, font, max_width), 34


def _draw_calculation(
    draw: ImageDraw.ImageDraw,
    text: str | None,
    x: int,
    y: int,
    max_width: int,
    fill: str = MUTED,
) -> None:
    if not text:
        return
    font = _font("sans", 32)
    for index, line in enumerate(_wrapped_lines(draw, text.upper(), font, max_width)[:2]):
        draw.text((x, y + index * 46), line, font=font, fill=fill)


def _draw_solar_disc(image: Image.Image, x: int, y: int, radius: int) -> None:
    """Draw a luminous solar sphere with a soft corona and mottled surface."""
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow = ImageDraw.Draw(layer)
    for extra, alpha in ((42, 12), (28, 22), (16, 38)):
        glow.ellipse(
            (x - radius - extra, y - radius - extra, x + radius + extra, y + radius + extra),
            fill=(231, 185, 79, alpha),
        )
    image.paste(Image.alpha_composite(image.convert("RGBA"), layer).convert("RGB"))
    draw = ImageDraw.Draw(image)
    for current in range(radius, 0, -1):
        ratio = current / radius
        red = int(231 + (255 - 231) * (1 - ratio))
        green = int(145 + (210 - 145) * (1 - ratio))
        blue = int(34 + (92 - 34) * (1 - ratio))
        draw.ellipse((x - current, y - current, x + current, y + current), fill=(red, green, blue))
    for angle, distance, spot_r in ((0.5, 0.47, 8), (2.5, 0.33, 6), (4.2, 0.52, 5), (5.4, 0.25, 4)):
        spot_x = x + int(math.cos(angle) * radius * distance)
        spot_y = y + int(math.sin(angle) * radius * distance)
        draw.ellipse((spot_x - spot_r, spot_y - spot_r, spot_x + spot_r, spot_y + spot_r), fill="#8B5319")
    draw.arc((x - radius + 18, y - radius + 28, x + radius - 12, y + radius - 34), 205, 340, fill="#FFD878", width=5)


def _draw_lunar_disc(image: Image.Image, x: int, y: int, radius: int) -> None:
    """Draw a shaded lunar sphere with visible maria and crater rims."""
    diameter = radius * 2 + 1
    sphere = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    pixels = sphere.load()
    for py in range(diameter):
        for px in range(diameter):
            nx = (px - radius) / radius
            ny = (py - radius) / radius
            distance_sq = nx * nx + ny * ny
            if distance_sq > 1.0:
                continue
            nz = math.sqrt(1.0 - distance_sq)
            light = max(0.0, nx * -0.38 + ny * -0.28 + nz * 0.88)
            shade = int(82 + light * 158)
            pixels[px, py] = (shade, shade + 2, min(255, shade + 8), 255)
    moon_draw = ImageDraw.Draw(sphere, "RGBA")
    craters = (
        (0.29, 0.30, 0.16),
        (0.66, 0.59, 0.19),
        (0.31, 0.70, 0.10),
        (0.71, 0.27, 0.08),
        (0.50, 0.48, 0.07),
    )
    for cx, cy, scale in craters:
        crater_r = max(4, int(radius * scale))
        crater_x = int(diameter * cx)
        crater_y = int(diameter * cy)
        moon_draw.ellipse(
            (crater_x - crater_r, crater_y - crater_r, crater_x + crater_r, crater_y + crater_r),
            fill=(72, 78, 90, 72),
            outline=(229, 232, 237, 105),
            width=max(2, radius // 28),
        )
    image.paste(sphere, (x - radius, y - radius), sphere)


def _paste_celestial_asset(
    image: Image.Image,
    filename: str,
    x: int,
    y: int,
    diameter: int,
) -> bool:
    """Composite a photographic celestial cutout, returning False for fallback."""
    path = CELESTIAL_DIR / filename
    if not path.is_file():
        return False
    try:
        asset = Image.open(path).convert("RGBA")
        alpha_box = asset.getchannel("A").getbbox()
        if alpha_box:
            asset = asset.crop(alpha_box)
        asset.thumbnail((diameter, diameter), Image.Resampling.LANCZOS)
        image.paste(asset, (x - asset.width // 2, y - asset.height // 2), asset)
        return True
    except OSError:
        return False


def _background_for(card: BirthdayCard) -> tuple[Image.Image, dict[str, object]]:
    theme = THEMES.get(card.theme, THEMES["painted_blue"])
    path = BACKGROUND_DIR / str(theme["asset"])
    if path.is_file():
        with Image.open(path) as source:
            image = ImageOps.fit(source.convert("RGB"), MASTER_SIZE, method=Image.Resampling.LANCZOS)
    else:
        image = Image.new("RGB", MASTER_SIZE, BACKGROUND)
    overlay = Image.new("RGBA", MASTER_SIZE, tuple(theme["overlay"]))
    image.paste(Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB"))
    return image, theme


def _draw_sparse_stars(image: Image.Image, card: BirthdayCard) -> None:
    """Add a deterministic sparse star field without competing with copy."""
    width, height = image.size
    seed_material = f"{card.recipient_name}|{card.birth_date.isoformat()}".encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big")
    rng = random.Random(seed)
    draw = ImageDraw.Draw(image, "RGBA")

    protected = (
        (130, 200, 1250, 500),
        (180, 620, 2220, 1240),
        (120, 1320, 2280, 2090),
        (210, 2150, 2190, 3170),
        (120, 3750, 1780, 4100),
    )

    def protected_point(px: int, py: int) -> bool:
        return any(left <= px <= right and top <= py <= bottom for left, top, right, bottom in protected)

    for _ in range(105):
        sx = rng.randint(70, width - 70)
        sy = rng.randint(80, height - 80)
        if protected_point(sx, sy):
            continue
        star_r = rng.choices((2, 3, 4, 6, 9), weights=(48, 29, 15, 6, 2))[0]
        if rng.random() < 0.16:
            colour = (225, 193, 140, rng.randint(95, 175))
        else:
            colour = (237, 241, 247, rng.randint(90, 205))
        draw.ellipse((sx - star_r, sy - star_r, sx + star_r, sy + star_r), fill=colour)
        if star_r >= 6:
            draw.line((sx - star_r * 2, sy, sx + star_r * 2, sy), fill=colour, width=2)
            draw.line((sx, sy - star_r * 2, sx, sy + star_r * 2), fill=colour, width=2)


def render_birthday_card_master(card: BirthdayCard) -> Image.Image:
    width, height = MASTER_SIZE
    image, theme = _background_for(card)
    if bool(theme["stars"]):
        _draw_sparse_stars(image, card)
    draw = ImageDraw.Draw(image)
    text_colour = str(theme["text"])
    muted_colour = str(theme["muted"])
    accent_colour = str(theme["accent"])

    mono = _font("mono", 80)
    draw.text((190, 260), card.date_label, font=mono, fill=text_colour)
    draw.text((190, 375), "A BIRTHDAY SKY", font=_font("mono", 46), fill=muted_colour)

    # The recipient is the visual event: this complete title field occupies the
    # upper third of the tall card, as in the approved Luna mockup.
    _draw_tracked_center(draw, "HAPPY BIRTHDAY", 700, _font("sans", 92), tracking=25, fill=text_colour)
    display_name = card.recipient_name.upper()
    name_font = _fit_font(draw, display_name, "display", 330, 2020, 140)
    draw.text((width / 2, 1010), display_name, font=name_font, fill=text_colour, anchor="mm")

    draw.line((930, 1370, 1470, 1370), fill=accent_colour, width=3)
    label_font = _font("mono", 50)
    left_icon_x, right_icon_x, icon_y = 650, 1750, 1540
    icon_r = 108
    # Keep recognisable celestial bodies beside their calculated positions.
    if not _paste_celestial_asset(image, "sun-photographic.png", left_icon_x, icon_y, 310):
        _draw_solar_disc(image, left_icon_x, icon_y, icon_r)
    if not _paste_celestial_asset(image, "moon-photographic.png", right_icon_x, icon_y, 270):
        _draw_lunar_disc(image, right_icon_x, icon_y, icon_r)
    draw = ImageDraw.Draw(image)

    left_x, right_x = 280, 1380
    draw.text((left_x, 1705), "SUN", font=label_font, fill=muted_colour)
    sun_font = _fit_font(draw, f"IN {card.sun_sign.upper()}", "sans", 96, 930, 52)
    draw.text((left_x, 1790), f"IN {card.sun_sign.upper()}", font=sun_font, fill=text_colour)
    draw.text((right_x, 1705), "MOON", font=label_font, fill=muted_colour)
    moon_font = _fit_font(draw, f"IN {card.moon_label.upper()}", "sans", 96, 930, 52)
    draw.text((right_x, 1790), f"IN {card.moon_label.upper()}", font=moon_font, fill=text_colour)
    _draw_calculation(draw, card.sun_calculation, left_x, 1915, 800, muted_colour)
    _draw_calculation(draw, card.moon_calculation, right_x, 1915, 800, muted_colour)

    poem_font, poem_lines, line_height = _poem_layout(draw, card.poem, 1740)
    poem_top = 2290
    for index, line in enumerate(poem_lines):
        draw.text((width / 2, poem_top + index * line_height), line, font=poem_font, fill=text_colour, anchor="ma")

    # A restrained Luna cube, drawn as vector shapes so the export remains crisp.
    cx, cy, cube = 260, 3920, 82
    draw.polygon([(cx, cy - cube), (cx + cube, cy - cube // 2), (cx, cy), (cx - cube, cy - cube // 2)], fill=text_colour)
    draw.polygon([(cx - cube, cy - cube // 2), (cx, cy), (cx, cy + cube), (cx - cube, cy + cube // 2)], fill=accent_colour)
    draw.polygon([(cx, cy), (cx + cube, cy - cube // 2), (cx + cube, cy + cube // 2), (cx, cy + cube)], fill=muted_colour)
    brand_font = _font("sans", 37)
    draw.text((420, 3884), "L U N A   C O N V E R G E N C E", font=brand_font, fill=text_colour)
    draw.text((420, 3956), "THE UNIVERSE SHIFTS. YOU'VE GOT THIS.", font=_font("mono", 30), fill=muted_colour)

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
