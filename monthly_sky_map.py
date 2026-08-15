from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
import math
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from astrology_engine import SIGNS, angular_distance, detect_aspects, house_map, positions_for_date


PLANET_SHORT = {
    "Sun": "SUN",
    "Moon": "MOON",
    "Mercury": "MER",
    "Venus": "VEN",
    "Mars": "MAR",
    "Jupiter": "JUP",
    "Saturn": "SAT",
    "Uranus": "URA",
    "Neptune": "NEP",
    "Pluto": "PLU",
    "True Node": "NODE",
}


@dataclass(frozen=True)
class MonthlySkySnapshot:
    snapshot_date: date
    timezone_name: str
    sign: str
    positions: dict
    houses: dict[str, int]
    aspects: tuple


def snapshot_date_for_period(start: date, end: date, timezone_name: str) -> date:
    """Choose a truthful anchor date for a monthly sky snapshot.

    Current month -> today's date in the report timezone.
    Future month  -> first day of the period.
    Past month    -> last day of the period.
    """
    try:
        today = datetime.now(ZoneInfo(timezone_name)).date()
    except Exception:
        today = datetime.utcnow().date()
    if start <= today <= end:
        return today
    if today < start:
        return start
    return end


def build_monthly_sky_snapshot(result: dict) -> MonthlySkySnapshot:
    start = date.fromisoformat(str(result.get("start")))
    end = date.fromisoformat(str(result.get("end")))
    timezone_name = str(result.get("timezone_name") or "UTC")
    sign = str(result.get("sign") or "Aries")
    snapshot_date = snapshot_date_for_period(start, end, timezone_name)
    positions = positions_for_date(snapshot_date, timezone_name, local_hour=12)
    houses = house_map(positions, sign)
    aspects = tuple(detect_aspects(positions, include_moon=True, maximum=8))
    return MonthlySkySnapshot(
        snapshot_date=snapshot_date,
        timezone_name=timezone_name,
        sign=sign,
        positions=positions,
        houses=houses,
        aspects=aspects,
    )


def monthly_sky_map_svg(snapshot: MonthlySkySnapshot, size: int = 640) -> str:
    """Return a restrained Luna wheel for a free sign-based monthly snapshot.

    This is not a natal wheel. The selected Sun sign is treated as whole-sign
    House 1, so the chart shows where the current sky gathers for that sign
    without implying an Ascendant, MC, or exact personal houses.
    """
    center = size / 2.0
    outer = size * 0.375
    inner = size * 0.272
    planet_r = size * 0.307
    sign_label_r = size * 0.418
    house_label_r = size * 0.235

    def xy(longitude: float, radius: float) -> tuple[float, float]:
        angle = math.radians(180.0 - (longitude % 360.0))
        return center + radius * math.cos(angle), center + radius * math.sin(angle)

    native_index = SIGNS.index(snapshot.sign)
    pieces = [
        f'<svg viewBox="0 0 {size} {size}" role="img" aria-label="{snapshot.sign} monthly sky map" '
        'style="width:100%;max-width:700px;height:auto;display:block;margin:.4rem auto 1rem;">',
        f'<circle cx="{center:.1f}" cy="{center:.1f}" r="{outer:.1f}" fill="none" stroke="#111" stroke-width="1.4"/>',
        f'<circle cx="{center:.1f}" cy="{center:.1f}" r="{inner:.1f}" fill="none" stroke="#c5c5c0" stroke-width="1"/>',
    ]

    for index, sign in enumerate(SIGNS):
        longitude = index * 30.0
        house = ((index - native_index) % 12) + 1
        x1, y1 = xy(longitude, inner)
        x2, y2 = xy(longitude, outer)
        is_house_one = house == 1
        pieces.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#{"111" if is_house_one else "c5c5c0"}" stroke-width="{2 if is_house_one else 1}"/>'
        )
        lx, ly = xy(longitude + 15.0, sign_label_r)
        pieces.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" '
            'font-family="monospace" font-size="11" fill="#555">'
            f'{sign[:3].upper()}</text>'
        )
        hx, hy = xy(longitude + 15.0, house_label_r)
        pieces.append(
            f'<text x="{hx:.1f}" y="{hy:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'font-family="monospace" font-size="9" font-weight="{700 if is_house_one else 400}" '
            f'fill="#{"111" if is_house_one else "8b8b85"}">H{house}</text>'
        )

    # A light aspect web helps the monthly map retain the visual language of the
    # Natal Snapshot while keeping the dominant sign/house concentration primary.
    for aspect in snapshot.aspects[:6]:
        p1 = snapshot.positions.get(aspect.planet1)
        p2 = snapshot.positions.get(aspect.planet2)
        if not p1 or not p2:
            continue
        x1, y1 = xy(p1.longitude, inner * 0.88)
        x2, y2 = xy(p2.longitude, inner * 0.88)
        dash = ' stroke-dasharray="4 4"' if aspect.name in {"square", "opposition"} else ""
        opacity = max(0.14, min(0.42, 0.14 + float(aspect.strength) * 0.13))
        pieces.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#333" stroke-width="1" opacity="{opacity:.2f}"{dash}/>'
        )

    ordered = sorted(snapshot.positions.values(), key=lambda item: item.longitude)
    previous_longitudes: list[float] = []
    for item in ordered:
        nearby = sum(1 for value in previous_longitudes[-3:] if angular_distance(item.longitude, value) < 8.0)
        radius = planet_r - min(nearby, 2) * 22
        px, py = xy(item.longitude, radius)
        pieces.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.4" fill="#111"/>')
        retro = " R" if item.retrograde else ""
        pieces.append(
            f'<text x="{px:.1f}" y="{py - 9:.1f}" text-anchor="middle" '
            'font-family="monospace" font-size="9.5" font-weight="600" fill="#111">'
            f'{PLANET_SHORT.get(item.planet, item.planet[:4].upper())}{retro}</text>'
        )
        previous_longitudes.append(item.longitude)

    label = snapshot.snapshot_date.strftime("%d %b %Y").upper()
    pieces.append(
        f'<text x="{center:.1f}" y="{center - 12:.1f}" text-anchor="middle" '
        'font-family="Georgia,serif" font-size="21" fill="#111">LUNA</text>'
    )
    pieces.append(
        f'<text x="{center:.1f}" y="{center + 10:.1f}" text-anchor="middle" '
        'font-family="monospace" font-size="8.5" letter-spacing="1.15" fill="#666">'
        f'{snapshot.sign.upper()} SKY MAP</text>'
    )
    pieces.append(
        f'<text x="{center:.1f}" y="{center + 29:.1f}" text-anchor="middle" '
        'font-family="monospace" font-size="8" fill="#888">'
        f'{label}</text>'
    )
    pieces.append('</svg>')
    return ''.join(pieces)


def _font(size: int, *, serif: bool = False, bold: bool = False):
    """Return a dependable bundled/system font for raster sky maps."""
    candidates = []
    if serif:
        candidates.extend([
            "DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf",
            "LiberationSerif-Bold.ttf" if bold else "LiberationSerif-Regular.ttf",
        ])
    else:
        candidates.extend([
            "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
            "LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf",
        ])
    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def monthly_sky_map_png(snapshot: MonthlySkySnapshot, size: int = 1000) -> bytes:
    """Rasterise the free monthly sky map without relying on browser SVG support.

    Streamlit's sanitised HTML path can leave SVG data-URI images broken in some
    hosted browsers. Drawing the same chart directly with Pillow produces a normal
    PNG that is safe for an ``<img>`` data URI and requires no browser SVG parsing.
    """
    size = max(640, int(size))
    image = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(image)

    center = size / 2.0
    outer = size * 0.365
    inner = size * 0.265
    planet_r = size * 0.300
    sign_label_r = size * 0.420
    house_label_r = size * 0.228

    def xy(longitude: float, radius: float) -> tuple[float, float]:
        angle = math.radians(180.0 - (longitude % 360.0))
        return center + radius * math.cos(angle), center + radius * math.sin(angle)

    line = "#c5c5c0"
    dark = "#111111"
    muted = "#777770"
    light = "#a9a9a3"

    # Rings
    draw.ellipse((center-outer, center-outer, center+outer, center+outer), outline=dark, width=max(2, size//500))
    draw.ellipse((center-inner, center-inner, center+inner, center+inner), outline=line, width=max(1, size//700))

    sign_font = _font(max(14, size // 72))
    house_font = _font(max(12, size // 82), bold=False)
    house1_font = _font(max(12, size // 82), bold=True)
    planet_font = _font(max(13, size // 70), bold=True)
    title_font = _font(max(26, size // 34), serif=True)
    small_font = _font(max(11, size // 86))

    native_index = SIGNS.index(snapshot.sign)
    for index, sign in enumerate(SIGNS):
        longitude = index * 30.0
        house = ((index - native_index) % 12) + 1
        x1, y1 = xy(longitude, inner)
        x2, y2 = xy(longitude, outer)
        is_house_one = house == 1
        draw.line((x1, y1, x2, y2), fill=dark if is_house_one else line, width=max(2 if is_house_one else 1, size//650))

        lx, ly = xy(longitude + 15.0, sign_label_r)
        label = sign[:3].upper()
        box = draw.textbbox((0, 0), label, font=sign_font)
        draw.text((lx-(box[2]-box[0])/2, ly-(box[3]-box[1])/2), label, font=sign_font, fill="#555555")

        hx, hy = xy(longitude + 15.0, house_label_r)
        hlabel = f"H{house}"
        hf = house1_font if is_house_one else house_font
        box = draw.textbbox((0, 0), hlabel, font=hf)
        draw.text((hx-(box[2]-box[0])/2, hy-(box[3]-box[1])/2), hlabel, font=hf, fill=dark if is_house_one else muted)

    # Restrained aspect web
    for aspect in snapshot.aspects[:6]:
        p1 = snapshot.positions.get(aspect.planet1)
        p2 = snapshot.positions.get(aspect.planet2)
        if not p1 or not p2:
            continue
        x1, y1 = xy(p1.longitude, inner * 0.88)
        x2, y2 = xy(p2.longitude, inner * 0.88)
        # Pillow dashed lines are awkward; use a lighter solid line for hard aspects.
        hard = aspect.name in {"square", "opposition"}
        draw.line((x1, y1, x2, y2), fill="#aaaaaa" if hard else "#c0c0bc", width=max(1, size//850))

    # Planets; push close longitudes inward to keep labels readable.
    ordered = sorted(snapshot.positions.values(), key=lambda item: item.longitude)
    previous_longitudes: list[float] = []
    dot_r = max(4, size // 180)
    for item in ordered:
        nearby = sum(1 for value in previous_longitudes[-3:] if angular_distance(item.longitude, value) < 8.0)
        radius = planet_r - min(nearby, 2) * (size * 0.034)
        px, py = xy(item.longitude, radius)
        draw.ellipse((px-dot_r, py-dot_r, px+dot_r, py+dot_r), fill=dark)
        retro = " R" if item.retrograde else ""
        label = f"{PLANET_SHORT.get(item.planet, item.planet[:4].upper())}{retro}"
        box = draw.textbbox((0, 0), label, font=planet_font)
        tx = px - (box[2]-box[0]) / 2
        ty = py - dot_r - (box[3]-box[1]) - max(5, size//180)
        draw.text((tx, ty), label, font=planet_font, fill=dark)
        previous_longitudes.append(item.longitude)

    # Centre label
    title = "LUNA"
    box = draw.textbbox((0, 0), title, font=title_font)
    draw.text((center-(box[2]-box[0])/2, center-size*0.032), title, font=title_font, fill=dark)

    subtitle = f"{snapshot.sign.upper()} SKY MAP"
    box = draw.textbbox((0, 0), subtitle, font=small_font)
    draw.text((center-(box[2]-box[0])/2, center+size*0.012), subtitle, font=small_font, fill="#666666")

    date_label = snapshot.snapshot_date.strftime("%d %b %Y").upper()
    box = draw.textbbox((0, 0), date_label, font=small_font)
    draw.text((center-(box[2]-box[0])/2, center+size*0.040), date_label, font=small_font, fill="#888888")

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
