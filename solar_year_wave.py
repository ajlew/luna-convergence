from __future__ import annotations

from datetime import datetime, timezone, timedelta
from html import escape
from zoneinfo import ZoneInfo
import math

import swisseph as swe

SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

TROPIC_DEG = 23.436


def _jd_from_datetime(value: datetime) -> float:
    utc = value.astimezone(timezone.utc)
    hour = utc.hour + utc.minute / 60.0 + utc.second / 3600.0 + utc.microsecond / 3_600_000_000.0
    return swe.julday(utc.year, utc.month, utc.day, hour)


def _datetime_from_jd(jd: float) -> datetime:
    year, month, day, hour = swe.revjul(jd, swe.GREG_CAL)
    whole_hour = int(hour)
    minute_float = (hour - whole_hour) * 60.0
    minute = int(minute_float)
    second = int(round((minute_float - minute) * 60.0))
    if second >= 60:
        second = 59
    return datetime(year, month, day, whole_hour, minute, second, tzinfo=timezone.utc)


def _sun_ecliptic(jd: float) -> tuple[float, float]:
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    try:
        xx, _ = swe.calc_ut(jd, swe.SUN, flags)
    except Exception:
        xx, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_MOSEPH | swe.FLG_SPEED)
    return float(xx[0] % 360.0), float(xx[3])


def _sun_declination(jd: float) -> float:
    flags = swe.FLG_SWIEPH | swe.FLG_EQUATORIAL
    try:
        xx, _ = swe.calc_ut(jd, swe.SUN, flags)
    except Exception:
        xx, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_MOSEPH | swe.FLG_EQUATORIAL)
    return float(xx[1])


def solar_gates(year: int, timezone_name: str = "UTC") -> tuple[tuple[str, datetime, float], ...]:
    """Return the four tropical solar gates for a year.

    Gate times are calculated from exact solar longitude crossings with Swiss Ephemeris,
    then converted to the requested IANA timezone for display.
    """
    start_jd = swe.julday(year, 1, 1, 0.0)
    tz = ZoneInfo(timezone_name)
    gates = []
    for label, longitude in (
        ("MAR EQUINOX", 0.0),
        ("JUN SOLSTICE", 90.0),
        ("SEP EQUINOX", 180.0),
        ("DEC SOLSTICE", 270.0),
    ):
        try:
            jd = swe.solcross_ut(longitude, start_jd, swe.FLG_SWIEPH)
        except Exception:
            jd = swe.solcross_ut(longitude, start_jd, swe.FLG_MOSEPH)
        dt_local = _datetime_from_jd(jd).astimezone(tz)
        gates.append((label, dt_local, longitude))
    return tuple(gates)


def sun_state(now: datetime) -> dict[str, object]:
    jd = _jd_from_datetime(now)
    longitude, _ = _sun_ecliptic(jd)
    declination = _sun_declination(jd)
    sign_index = int(longitude // 30.0) % 12
    return {
        "longitude": longitude,
        "declination": declination,
        "sign": SIGNS[sign_index],
        "degree": longitude % 30.0,
    }


def solar_year_wave_svg(now: datetime, timezone_name: str | None = None) -> str:
    """A quiet solar-year strip showing the Sun between the two tropics.

    The curve is the Sun's geocentric equatorial declination sampled through the
    current calendar year.  Equinoxes/solstices are exact solar-longitude
    crossings, while the current marker uses the actual Sun position at render time.
    """
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    timezone_name = timezone_name or getattr(now.tzinfo, "key", None) or "UTC"
    try:
        tz = ZoneInfo(timezone_name)
    except Exception:
        tz = timezone.utc
        timezone_name = "UTC"
    local_now = now.astimezone(tz)
    year = local_now.year

    width = 760.0
    height = 158.0
    left = 142.0
    right = 14.0
    top = 18.0
    bottom = 33.0
    plot_w = width - left - right
    plot_h = height - top - bottom
    max_decl = 26.0

    year_start_local = datetime(year, 1, 1, tzinfo=tz)
    next_year_local = datetime(year + 1, 1, 1, tzinfo=tz)
    year_seconds = (next_year_local - year_start_local).total_seconds()

    def x_for_datetime(dt: datetime) -> float:
        fraction = (dt.astimezone(tz) - year_start_local).total_seconds() / year_seconds
        return left + max(0.0, min(1.0, fraction)) * plot_w

    def y_for_declination(decl: float) -> float:
        fraction = (max_decl - decl) / (2.0 * max_decl)
        return top + fraction * plot_h

    # Sample at local noon every 3 days so the curve is smooth without being heavy.
    points = []
    cursor = year_start_local
    while cursor < next_year_local:
        sample = cursor.replace(hour=12)
        decl = _sun_declination(_jd_from_datetime(sample))
        points.append((x_for_datetime(sample), y_for_declination(decl)))
        cursor += timedelta(days=3)
    last_sample = next_year_local - timedelta(minutes=1)
    points.append((x_for_datetime(last_sample), y_for_declination(_sun_declination(_jd_from_datetime(last_sample)))))
    path_points = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)

    current = sun_state(local_now)
    current_x = x_for_datetime(local_now)
    current_y = y_for_declination(float(current["declination"]))
    anchor = "end" if current_x > width * 0.75 else "start"
    text_x = current_x - 8 if anchor == "end" else current_x + 8
    north_south = "N" if float(current["declination"]) >= 0 else "S"
    sun_label = (
        f"SUN · {float(current['degree']):.1f}° {current['sign'].upper()} · "
        f"{abs(float(current['declination'])):.1f}°{north_south}"
    )

    pieces = [
        f'<div class="solar-year-wave-wrap">',
        f'<svg class="solar-year-wave" viewBox="0 0 {int(width)} {int(height)}" role="img" '
        f'aria-label="Solar year: equator, Tropic of Cancer, Tropic of Capricorn, equinoxes, solstices and current Sun position">',
    ]

    # Latitude reference lines.
    for label, decl in (
        ("TROPIC OF CANCER · +23.4°", TROPIC_DEG),
        ("EQUATOR · 0°", 0.0),
        ("TROPIC OF CAPRICORN · −23.4°", -TROPIC_DEG),
    ):
        y = y_for_declination(decl)
        stroke = "#111" if decl == 0 else "#cfcfca"
        pieces.append(f'<line x1="{left:.1f}" y1="{y:.1f}" x2="{width-right:.1f}" y2="{y:.1f}" stroke="{stroke}" stroke-width="1"/>')
        pieces.append(
            f'<text x="6" y="{y + 3.5:.1f}" font-family="IBM Plex Mono, Courier New, monospace" '
            f'font-size="13" fill="#6e6e69">{escape(label)}</text>'
        )

    # Exact quarter gates.
    for label, gate_dt, _longitude in solar_gates(year, timezone_name):
        gx = x_for_datetime(gate_dt)
        pieces.append(f'<line x1="{gx:.1f}" y1="{top:.1f}" x2="{gx:.1f}" y2="{height-bottom+3:.1f}" stroke="#dddcd7" stroke-width="1"/>')
        pieces.append(
            f'<text x="{gx:.1f}" y="{height-14:.1f}" text-anchor="middle" '
            f'font-family="IBM Plex Mono, Courier New, monospace" font-size="11.5" fill="#555">{escape(label)}</text>'
        )

    pieces.append(f'<polyline points="{path_points}" fill="none" stroke="#111" stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round"/>')
    pieces.append(f'<line x1="{current_x:.1f}" y1="{top:.1f}" x2="{current_x:.1f}" y2="{height-bottom+3:.1f}" stroke="#111" stroke-width="1" stroke-dasharray="2 4" opacity="0.7"/>')
    pieces.append(f'<circle cx="{current_x:.1f}" cy="{current_y:.1f}" r="4.5" fill="#111"/>')
    pieces.append(
        f'<text x="{text_x:.1f}" y="{max(top+11, current_y-9):.1f}" text-anchor="{anchor}" '
        f'font-family="IBM Plex Mono, Courier New, monospace" font-size="12.5" font-weight="600" fill="#111">{escape(sun_label)}</text>'
    )
    pieces.append('</svg>')
    pieces.append('</div>')
    return "".join(pieces)
