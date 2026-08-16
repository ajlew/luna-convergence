from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta

from astrology_engine import ASPECTS, PLANET_WEIGHTS, Aspect, detect_aspects, positions_for_date


FAST_PLANETS = {"Sun", "Moon", "Mercury", "Venus", "Mars"}
STRUCTURAL_PLANETS = {"Jupiter", "Saturn"}

PLANET_THEMES = {
    "Sun": "visibility",
    "Moon": "instinct",
    "Mercury": "the message",
    "Venus": "value and desire",
    "Mars": "action",
    "Jupiter": "expansion",
    "Saturn": "the limit",
    "Uranus": "disruption",
    "Neptune": "imagination",
    "Pluto": "power",
    "True Node": "direction",
}

ASPECT_VERBS = {
    "conjunction": "conjunct",
    "sextile": "sextile",
    "square": "square",
    "trine": "trine",
    "opposition": "opposite",
}

ASPECT_HEADLINES = {
    "conjunction": (
        "TWO SIGNALS. ONE MICROPHONE.",
        "THE VOLUME JUST CHANGED.",
        "WHAT MERGES GAINS FORCE.",
    ),
    "sextile": (
        "A SMALL OPENING CAN CHANGE THE DAY.",
        "THE WINDOW IS OPEN.",
        "OPPORTUNITY JUST KNOCKED ONCE.",
    ),
    "square": (
        "FRICTION FOUND THE WEAK POINT.",
        "PRESSURE DOES NOT NEGOTIATE.",
        "THE CRACK IS THE MESSAGE.",
    ),
    "trine": (
        "THE DOOR IS OPEN. WALK.",
        "EASY DOES NOT MEAN AUTOMATIC.",
        "THE CURRENT IS WITH YOU.",
    ),
    "opposition": (
        "THE OTHER SIDE HAS LEVERAGE.",
        "THE TRADE-OFF IS NOW VISIBLE.",
        "TWO TRUTHS ENTER. ONE CHOICE LEAVES.",
    ),
}

# These are deliberate Luna treatments for recognisable human tensions. They
# are still anchored to a calculated aspect; no copy is selected without the
# matching evidence.
SPECIAL_COPY = {
    (frozenset({"Mars", "Neptune"}), "square"): (
        "CONFIDENCE IS NOT EVIDENCE.",
        "Reaction can arrive dressed as intuition.",
        "Move only after the facts survive daylight.",
        "Pause. Verify. Then act.",
    ),
    (frozenset({"Mercury", "Jupiter"}), "conjunction"): (
        "SAY THE BIGGER THING.",
        "The message wants more room than usual.",
        "Make it clear enough to travel without you.",
        "Send it. Pitch it. Make yourself visible.",
    ),
    (frozenset({"Moon", "Saturn"}), "square"): (
        "THE MOOD IS NOT THE VERDICT.",
        "A temporary heaviness is trying to sound permanent.",
        "Give the feeling a boundary, not the keys.",
        "Do the necessary thing. Reassess later.",
    ),
    (frozenset({"Mercury", "Neptune"}), "square"): (
        "A BEAUTIFUL STORY CAN STILL BE WRONG.",
        "The explanation may feel cleaner than the evidence.",
        "Charm is not a substitute for a missing fact.",
        "Check the detail nobody wants checked.",
    ),
    (frozenset({"Mars", "Saturn"}), "square"): (
        "FORCE MEETS THE WALL.",
        "More pressure will not repair bad timing.",
        "Technique now beats aggression.",
        "Change the method before adding effort.",
    ),
    (frozenset({"Jupiter", "Saturn"}), "conjunction"): (
        "GROWTH NEEDS A FRAME.",
        "The opportunity is real. So is the load it creates.",
        "Expansion without structure becomes expensive theatre.",
        "Build the container before increasing the volume.",
    ),
    (frozenset({"Venus", "Mars"}), "opposition"): (
        "ATTRACTION WANTS A DECISION.",
        "Wanting and pursuing are pulling in opposite directions.",
        "Ambiguity is exciting until somebody sends the invoice.",
        "Name what you want. Then watch what you do.",
    ),
}


@dataclass(frozen=True)
class WeeklyDay:
    reading_date: date
    headline: str
    evidence: str
    line_one: str
    line_two: str
    action: str
    planets: tuple[str, str]
    aspect_name: str
    orb: float
    phase: str

    @property
    def weekday(self) -> str:
        return self.reading_date.strftime("%A")

    @property
    def date_label(self) -> str:
        return self.reading_date.strftime("%d %B %Y").lstrip("0")

    def video_copy(self) -> str:
        return (
            f"{self.weekday.upper()} · {self.date_label.upper()}\n\n"
            f"{self.headline}\n\n"
            f"{self.evidence.upper()}\n\n"
            f"{self.line_one}\n\n"
            f"{self.line_two}\n\n"
            "YOUR MOVE\n"
            f"{self.action}\n\n"
            "LUNA CONVERGENCE"
        )


def monday_for(value: date) -> date:
    """Return the Monday that contains *value*."""
    return value - timedelta(days=value.weekday())


def default_week_start(today: date) -> date:
    """Use the live week, except on Sunday when Luna opens the next week."""
    if today.weekday() == 6:
        return today + timedelta(days=1)
    return monday_for(today)


def week_label(monday: date) -> str:
    sunday = monday + timedelta(days=6)
    if monday.year == sunday.year:
        if monday.month == sunday.month:
            return f"{monday.day}–{sunday.day} {monday.strftime('%B %Y')}"
        return f"{monday.day} {monday.strftime('%B')}–{sunday.day} {sunday.strftime('%B %Y')}"
    return f"{monday.day} {monday.strftime('%B %Y')}–{sunday.day} {sunday.strftime('%B %Y')}"


def _aspect_on(
    reading_date: date,
    timezone_name: str,
    planet1: str,
    planet2: str,
    aspect_name: str,
) -> Aspect | None:
    target = frozenset({planet1, planet2})
    for aspect in detect_aspects(
        positions_for_date(reading_date, timezone_name),
        include_moon=True,
    ):
        if frozenset({aspect.planet1, aspect.planet2}) == target and aspect.name == aspect_name:
            return aspect
    return None


def _phase(reading_date: date, timezone_name: str, aspect: Aspect) -> str:
    previous = _aspect_on(
        reading_date - timedelta(days=1),
        timezone_name,
        aspect.planet1,
        aspect.planet2,
        aspect.name,
    )
    following = _aspect_on(
        reading_date + timedelta(days=1),
        timezone_name,
        aspect.planet1,
        aspect.planet2,
        aspect.name,
    )
    if aspect.orb <= 0.2:
        return "exact"
    if following and following.orb < aspect.orb:
        return "applying"
    if previous and previous.orb < aspect.orb:
        return "separating"
    return "active"


def _candidate_score(
    aspect: Aspect,
    pair_counts: Counter[frozenset[str]],
    planet_counts: Counter[str],
    previous_pair: frozenset[str] | None,
) -> float:
    pair = frozenset({aspect.planet1, aspect.planet2})
    allowed_orb = ASPECTS[aspect.name][1]
    exactness = 1.0 - min(aspect.orb / allowed_orb, 1.0)
    fast_bonus = 1.35 if "Moon" in pair else 0.75 if pair & FAST_PLANETS else 0.0
    structural_bonus = 0.35 * (
        PLANET_WEIGHTS[aspect.planet1] + PLANET_WEIGHTS[aspect.planet2]
    )
    repetition_penalty = pair_counts[pair] * 4.0
    repetition_penalty += sum(planet_counts[item] for item in pair) * 0.18
    if pair == previous_pair:
        repetition_penalty += 6.0
    return (
        aspect.strength * 1.45
        + exactness * 2.2
        + fast_bonus
        + structural_bonus
        - repetition_penalty
    )


def _select_aspect(
    reading_date: date,
    timezone_name: str,
    pair_counts: Counter[frozenset[str]],
    planet_counts: Counter[str],
    previous_pair: frozenset[str] | None,
) -> Aspect:
    aspects = detect_aspects(
        positions_for_date(reading_date, timezone_name),
        include_moon=True,
    )
    relevant = [
        item
        for item in aspects
        if (
            {item.planet1, item.planet2} & FAST_PLANETS
            or (
                {item.planet1, item.planet2} & STRUCTURAL_PLANETS
                and item.orb <= 0.35
            )
        )
    ]
    pool = relevant or aspects
    if not pool:
        raise RuntimeError(f"No planetary aspect available for {reading_date.isoformat()}.")
    return max(
        pool,
        key=lambda item: _candidate_score(
            item,
            pair_counts,
            planet_counts,
            previous_pair,
        ),
    )


def _generic_copy(aspect: Aspect, reading_date: date) -> tuple[str, str, str, str]:
    first = PLANET_THEMES[aspect.planet1]
    second = PLANET_THEMES[aspect.planet2]
    headlines = ASPECT_HEADLINES[aspect.name]
    headline = headlines[reading_date.toordinal() % len(headlines)]

    if aspect.name == "conjunction":
        return (
            headline,
            f"{first.capitalize()} and {second} are sharing one microphone.",
            "The signal grows louder. So does the distortion.",
            "Choose what deserves amplification.",
        )
    if aspect.name == "square":
        return (
            headline,
            f"{first.capitalize()} wants movement. {second.capitalize()} changes the terms.",
            "Pressure exposes the weak joint. Forcing it makes the crack expensive.",
            "Fix the structure before forcing the result.",
        )
    if aspect.name == "opposition":
        return (
            headline,
            f"{first.capitalize()} and {second} are pulling from opposite ends.",
            "Pretending there is no trade-off gives the other side control.",
            "Name the trade-off. Then choose consciously.",
        )
    if aspect.name == "trine":
        return (
            headline,
            f"{first.capitalize()} and {second} are moving in the same direction.",
            "The opening is real, but unused advantage still expires.",
            "Use the easy opening before it becomes background noise.",
        )
    return (
        headline,
        f"{first.capitalize()} has found a usable opening through {second}.",
        "It stays potential until somebody acts.",
        "Make one clean move while the window is open.",
    )


def _day_from_aspect(
    reading_date: date,
    timezone_name: str,
    aspect: Aspect,
    used_headlines: set[str],
) -> WeeklyDay:
    phase = _phase(reading_date, timezone_name, aspect)
    selected_copy = SPECIAL_COPY.get(
        (frozenset({aspect.planet1, aspect.planet2}), aspect.name)
    ) or _generic_copy(aspect, reading_date)
    copy = list(selected_copy)
    if copy[0] in used_headlines:
        copy[0] = next(
            (
                headline
                for headline in ASPECT_HEADLINES[aspect.name]
                if headline not in used_headlines
            ),
            f"{aspect.planet1.upper()} MEETS {aspect.planet2.upper()}.",
        )
    verb = ASPECT_VERBS[aspect.name]
    evidence = (
        f"{aspect.planet1} {verb} {aspect.planet2} · "
        f"{phase} · {aspect.orb:.1f}° orb"
    )
    return WeeklyDay(
        reading_date=reading_date,
        headline=copy[0],
        evidence=evidence,
        line_one=copy[1],
        line_two=copy[2],
        action=copy[3],
        planets=(aspect.planet1, aspect.planet2),
        aspect_name=aspect.name,
        orb=aspect.orb,
        phase=phase,
    )


def build_weekly_view(monday: date, timezone_name: str) -> tuple[WeeklyDay, ...]:
    """Build seven copy-ready shared-sky cards, always Monday through Sunday."""
    if monday.weekday() != 0:
        raise ValueError("Weekly View must begin on a Monday.")

    pair_counts: Counter[frozenset[str]] = Counter()
    planet_counts: Counter[str] = Counter()
    previous_pair: frozenset[str] | None = None
    used_headlines: set[str] = set()
    result: list[WeeklyDay] = []

    for offset in range(7):
        reading_date = monday + timedelta(days=offset)
        aspect = _select_aspect(
            reading_date,
            timezone_name,
            pair_counts,
            planet_counts,
            previous_pair,
        )
        pair = frozenset({aspect.planet1, aspect.planet2})
        day = _day_from_aspect(
            reading_date,
            timezone_name,
            aspect,
            used_headlines,
        )
        result.append(day)
        used_headlines.add(day.headline)
        pair_counts[pair] += 1
        planet_counts.update(pair)
        previous_pair = pair

    return tuple(result)


def all_video_copy(days: tuple[WeeklyDay, ...]) -> str:
    return "\n\n------------------------------\n\n".join(
        item.video_copy() for item in days
    )
