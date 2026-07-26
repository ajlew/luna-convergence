from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from collections import Counter
from urllib.parse import quote

from astrology_engine import (
    SIGNS,
    HOUSE_NAMES,
    Position,
    positions_for_date,
    house_map,
    detect_aspects,
    period_events,
    convergence_points,
)
from interpretation_library import HOUSE_STRATEGY, PLANET_MEANINGS
from synthesis import house_reference_matrix, house_aware_conclusion, convergence_interpretation


@dataclass(frozen=True)
class FreeDailyReading:
    sign: str
    reading_date: date
    sun_house: int
    moon_house: int
    daily_theme: str
    wider_context: str
    opportunity: str
    caution: str
    best_move: str
    conclusion: str
    house_matrix: str
    aspects: tuple[str, ...]
    positions: dict[str, Position]


def _active_convergence_context(sign: str, d: date, timezone_name: str) -> str:
    year_events = period_events(
        date(d.year, 1, 1),
        date(d.year, 12, 31),
        sign,
        timezone_name,
    )
    year_clusters = convergence_points(year_events, maximum=9)
    active = next(
        (
            cluster
            for cluster in year_clusters
            if cluster.start_date - timedelta(days=14)
            <= d
            <= cluster.end_date + timedelta(days=14)
        ),
        None,
    )
    if not active:
        return (
            "No major annual convergence is at its peak today. "
            "The daily house pattern is therefore the clearest guide."
        )

    material = convergence_interpretation(active)
    return (
        f"The wider background is **{material['title']}**. "
        f"{material['meaning']} {material['strategy']}"
    )


def _aspect_summary(
    positions: dict[str, Position],
    houses: dict[str, int],
    maximum: int = 3,
) -> tuple[str, ...]:
    aspects = detect_aspects(positions, include_moon=True, maximum=maximum)
    lines: list[str] = []
    for aspect in aspects:
        p1_theme = PLANET_MEANINGS[aspect.planet1]["core"]
        p2_theme = PLANET_MEANINGS[aspect.planet2]["core"]
        lines.append(
            f"**{aspect.planet1} {aspect.name} {aspect.planet2}** "
            f"(orb {aspect.orb:.2f}°) connects house {houses[aspect.planet1]} "
            f"with house {houses[aspect.planet2]}: {p1_theme} interact with {p2_theme}."
        )
    return tuple(lines)


def free_daily_reading(
    sign: str,
    d: date,
    timezone_name: str = "Australia/Sydney",
) -> FreeDailyReading:
    positions = positions_for_date(d, timezone_name)
    houses = house_map(positions, sign)
    sun_house = houses["Sun"]
    moon_house = houses["Moon"]

    daily_theme = (
        f"Build through house {sun_house}—{HOUSE_NAMES[sun_house]}—"
        f"while managing the faster reactions of house {moon_house}: "
        f"{HOUSE_NAMES[moon_house]}."
    )
    opportunity = HOUSE_STRATEGY[sun_house]["opportunity"]
    caution = HOUSE_STRATEGY[moon_house]["risk"]
    best_move = HOUSE_STRATEGY[sun_house]["action"]

    return FreeDailyReading(
        sign=sign,
        reading_date=d,
        sun_house=sun_house,
        moon_house=moon_house,
        daily_theme=daily_theme,
        wider_context=_active_convergence_context(sign, d, timezone_name),
        opportunity=opportunity,
        caution=caution,
        best_move=best_move,
        conclusion=house_aware_conclusion(sign, sun_house, moon_house),
        house_matrix=house_reference_matrix(sign, {sun_house, moon_house}),
        aspects=_aspect_summary(positions, houses),
        positions=positions,
    )


def prepared_order_email(
    email_address: str,
    product: str,
    customer_name: str,
    customer_email: str,
    sign: str,
    requested_period: str,
    timezone_name: str,
) -> str:
    subject = quote(f"{product} order details — {sign}")
    body = quote(
        "\n".join(
            [
                f"Product: {product}",
                f"Customer name: {customer_name}",
                f"Customer email: {customer_email}",
                f"Zodiac sign: {sign}",
                f"Requested month/year: {requested_period}",
                f"Timezone: {timezone_name}",
                "",
                "Payment reference or receipt:",
                "",
                "Additional note:",
            ]
        )
    )
    return f"mailto:{email_address}?subject={subject}&body={body}"
