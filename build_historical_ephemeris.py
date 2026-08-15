from __future__ import annotations

"""Build Luna's structured 1950-2050 Swiss Ephemeris archive.

Usage:
    python build_historical_ephemeris.py
    python build_historical_ephemeris.py --start 1950 --end 2050 --output data/custom.sqlite3
"""

from argparse import ArgumentParser
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
import math
import sqlite3

import swisseph as swe

from historical_ephemeris import ARCHIVE_VERSION, DEFAULT_DB_PATH


SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
PLANETS = (
    ("Sun", swe.SUN),
    ("Moon", swe.MOON),
    ("Mercury", swe.MERCURY),
    ("Venus", swe.VENUS),
    ("Mars", swe.MARS),
    ("Jupiter", swe.JUPITER),
    ("Saturn", swe.SATURN),
    ("Uranus", swe.URANUS),
    ("Neptune", swe.NEPTUNE),
    ("Pluto", swe.PLUTO),
    ("True Node", swe.TRUE_NODE),
)
# The Moon is retained in daily positions/ingresses but omitted from the precomputed
# 100-year major-aspect table. Fast lunar aspects are calculated on demand by Luna.
ASPECT_BODIES = tuple(name for name, _ in PLANETS if name != "Moon")
DIRECTED_ASPECT_TARGETS = {
    0.0: ("conjunction", 0.0),
    60.0: ("sextile", 60.0),
    90.0: ("square", 90.0),
    120.0: ("trine", 120.0),
    180.0: ("opposition", 180.0),
    240.0: ("trine", 120.0),
    270.0: ("square", 90.0),
    300.0: ("sextile", 60.0),
}


def calc(jd: float, pid: int):
    try:
        return swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
    except swe.Error:
        return swe.calc_ut(jd, pid, swe.FLG_MOSEPH | swe.FLG_SPEED)[0]


def sign_for(longitude: float) -> tuple[str, float]:
    value = longitude % 360.0
    idx = int(value // 30.0) % 12
    return SIGNS[idx], value % 30.0


def iso_from_jd(jd: float) -> str:
    y, m, d, hour = swe.revjul(jd, swe.GREG_CAL)
    h = int(hour)
    minute_float = (hour - h) * 60.0
    minute = int(minute_float)
    second = int(round((minute_float - minute) * 60.0))
    if second >= 60:
        second = 59
    return datetime(int(y), int(m), int(d), h, minute, second, tzinfo=timezone.utc).isoformat()


def equivalent_near(raw: float, target_reference: float) -> float:
    return raw + 360.0 * round((target_reference - raw) / 360.0)


def refine_aspect(jd0: float, jd1: float, pid1: int, pid2: int, target_unwrapped: float) -> float:
    def value_and_speed(jd: float) -> tuple[float, float]:
        v1 = calc(jd, pid1)
        v2 = calc(jd, pid2)
        raw = (v2[0] - v1[0]) % 360.0
        value = equivalent_near(raw, target_unwrapped) - target_unwrapped
        return value, (v2[3] - v1[3])
    f0, _ = value_and_speed(jd0)
    f1, _ = value_and_speed(jd1)
    denom = f1 - f0
    fraction = 0.5 if abs(denom) < 1e-10 else max(0.0, min(1.0, -f0 / denom))
    jd = jd0 + (jd1 - jd0) * fraction
    # Two Newton corrections use Swiss Ephemeris speed and normally converge to
    # much better than minute-level precision inside a one-day bracket.
    for _ in range(2):
        f, speed = value_and_speed(jd)
        if abs(speed) < 1e-8:
            break
        correction = f / speed
        if abs(correction) > 0.75:
            break
        jd = max(jd0, min(jd1, jd - correction))
    return jd


def refine_station(jd0: float, jd1: float, pid: int) -> float:
    s0 = calc(jd0, pid)[3]
    s1 = calc(jd1, pid)[3]
    denom = s1 - s0
    fraction = 0.5 if abs(denom) < 1e-12 else max(0.0, min(1.0, -s0 / denom))
    return jd0 + (jd1 - jd0) * fraction


def refine_ingress(jd0: float, jd1: float, pid: int, boundary_unwrapped: float) -> float:
    def value_and_speed(jd: float) -> tuple[float, float]:
        values = calc(jd, pid)
        raw = values[0] % 360.0
        return equivalent_near(raw, boundary_unwrapped) - boundary_unwrapped, values[3]
    f0, _ = value_and_speed(jd0)
    f1, _ = value_and_speed(jd1)
    denom = f1 - f0
    fraction = 0.5 if abs(denom) < 1e-10 else max(0.0, min(1.0, -f0 / denom))
    jd = jd0 + (jd1 - jd0) * fraction
    for _ in range(2):
        f, speed = value_and_speed(jd)
        if abs(speed) < 1e-8:
            break
        correction = f / speed
        if abs(correction) > 0.75:
            break
        jd = max(jd0, min(jd1, jd - correction))
    return jd


def schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode=OFF;
        PRAGMA synchronous=OFF;
        PRAGMA temp_store=MEMORY;
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE positions (
            day_key INTEGER NOT NULL,
            body_id INTEGER NOT NULL,
            longitude REAL NOT NULL,
            speed_longitude REAL NOT NULL,
            PRIMARY KEY (day_key, body_id)
        );
        CREATE TABLE events (
            exact_utc TEXT NOT NULL,
            event_type TEXT NOT NULL,
            body1 TEXT NOT NULL,
            body2 TEXT,
            aspect TEXT,
            angle REAL,
            body1_sign TEXT,
            body1_degree REAL,
            body2_sign TEXT,
            body2_degree REAL,
            direction TEXT,
            note TEXT
        );
        CREATE INDEX idx_events_type_time ON events(event_type, exact_utc);
        CREATE INDEX idx_events_pair_aspect_time ON events(body1, body2, aspect, exact_utc);
        CREATE INDEX idx_events_body_time ON events(body1, exact_utc);
        """
    )


def build(start_year: int, end_year: int, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    connection = sqlite3.connect(str(output))
    schema(connection)
    meta = {
        "archive_version": ARCHIVE_VERSION,
        "storage": "compact: YYYYMMDD integer + body id + longitude + speed; sign/degree/Rx derived at read time",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "start_year": str(start_year),
        "end_year": str(end_year),
        "frame": "geocentric",
        "zodiac": "tropical",
        "node": "True Node",
        "snapshot_utc": "00:00",
        "position_source": "Swiss Ephemeris via pyswisseph; Moshier fallback if required",
        "aspect_sampling": "derived on demand from daily UTC snapshots; roots refined with Swiss Ephemeris speed",
        "aspect_bodies": ", ".join(ASPECT_BODIES),
        "moon_aspects": "not precomputed; calculate on demand",
    }
    connection.executemany("INSERT INTO metadata(key,value) VALUES (?,?)", meta.items())

    planet_by_name = dict(PLANETS)
    start_jd = swe.julday(start_year, 1, 1, 0.0)
    end_jd = swe.julday(end_year + 1, 1, 1, 0.0)

    # 1) Daily 00:00 UTC positions.
    rows = []
    jd = start_jd
    while jd < end_jd - 1e-8:
        y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
        day_key = int(f"{int(y):04d}{int(m):02d}{int(d):02d}")
        for body_id, (name, pid) in enumerate(PLANETS):
            values = calc(jd, pid)
            rows.append((day_key, body_id, values[0] % 360.0, values[3]))
        if len(rows) >= 10000:
            connection.executemany(
                "INSERT INTO positions VALUES (?,?,?,?)", rows
            )
            rows.clear()
        jd += 1.0
    if rows:
        connection.executemany("INSERT INTO positions VALUES (?,?,?,?)", rows)
    connection.commit()

    # Historical events are derived on demand from the complete daily-position
    # archive and refined against Swiss Ephemeris. This avoids a large static event
    # index while supporting any requested pair, including the Moon.
    connection.execute("DELETE FROM events")
    connection.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES (?,?)", ("event_mode", "derived on demand from daily positions"))
    connection.commit()
    connection.execute("ANALYZE")
    connection.commit()
    connection.close()
    return output


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--start", type=int, default=1950)
    parser.add_argument("--end", type=int, default=2050)
    parser.add_argument("--output", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    result = build(args.start, args.end, args.output)
    print(result)


if __name__ == "__main__":
    main()
