from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

from astrology_engine import (
    ASPECTS,
    HOUSE_NAMES,
    PLANET_WEIGHTS,
    SIGNS,
    Aspect,
    angular_distance,
    detect_aspects,
    position_for_local_minute,
    positions_for_date,
    whole_sign_house,
)
from luna_voice import finalize_customer_prose
from major_event_registry import day_signal_bundle, major_sky_events


FAST_PLANETS = {"Sun", "Moon", "Mercury", "Venus", "Mars"}
STRUCTURAL_PLANETS = {"Jupiter", "Saturn"}

PLANET_THEMES = {
    "Sun": "what people can see",
    "Moon": "your gut",
    "Mercury": "the message",
    "Venus": "what you want",
    "Mars": "the move",
    "Jupiter": "the bigger option",
    "Saturn": "the limit",
    "Uranus": "the sudden change",
    "Neptune": "the imagined version",
    "Pluto": "who holds power",
    "True Node": "where this is heading",
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

GENERIC_COPY_VARIANTS = {
    "conjunction": (
        (
            "Choose what gets louder. {First} and {second} are arriving together.",
            "The signal grows louder. So does the distortion.",
            "Choose what deserves amplification.",
        ),
        (
            "Put both facts in the same room. {First} and {second} now have to work together.",
            "What agrees becomes powerful. What conflicts becomes impossible to hide.",
            "Decide what you are willing to make louder.",
        ),
        (
            "Stop running both signals at full volume. Put {first} beside {second}.",
            "Choose the setting before the noise chooses it for you.",
            "Give the combined force one precise job.",
        ),
    ),
    "square": (
        (
            "{First} wants movement. {Second} changes the terms.",
            "Pressure exposes the weak joint. Forcing it makes the crack expensive.",
            "Fix the structure before forcing the result.",
        ),
        (
            "Find the weak assumption. Put {first} beside {second}; the contradiction is the evidence.",
            "Use the irritation as evidence, not permission to overreact.",
            "Remove the false assumption, then make the move.",
        ),
        (
            "{First} demands speed while {second} demands a different reality.",
            "The conflict is not the enemy. Blind repetition is.",
            "Change one variable. Do not repeat the collision.",
        ),
    ),
    "opposition": (
        (
            "{First} and {second} are pulling from opposite ends.",
            "Pretending there is no trade-off gives the other side control.",
            "Name the trade-off. Then choose consciously.",
        ),
        (
            "Name both sides. {First} points one way; {Second} points another.",
            "The stalemate survives only while nobody names the cost.",
            "State both prices. Choose the cost you can carry.",
        ),
        (
            "Choose the priority first. {First} can say yes while {Second} exposes the cost.",
            "Compromise without a clear priority becomes slow surrender.",
            "Choose the priority. Negotiate everything else.",
        ),
    ),
    "trine": (
        (
            "{First} and {second} are moving in the same direction.",
            "The opening is real, but unused advantage still expires.",
            "Use the easy opening before it becomes background noise.",
        ),
        (
            "{First} and {second} are cooperating without asking permission.",
            "Momentum is available. Passivity is the only obvious sabotage.",
            "Put the easiest useful move in motion now.",
        ),
        (
            "{First} is carrying {second} further than effort alone could manage.",
            "The current helps, but it will not choose the destination for you.",
            "Aim the advantage at something worth finishing.",
        ),
    ),
    "sextile": (
        (
            "{First} has found a usable opening through {second}.",
            "It stays potential until somebody acts.",
            "Make one clean move while the window is open.",
        ),
        (
            "{First} has a quiet agreement available through {second}.",
            "The opportunity is small enough to miss and useful enough to matter.",
            "Answer the opening before it has to ask twice.",
        ),
        (
            "{First} can borrow leverage from {second} today.",
            "This is an invitation, not an automatic result.",
            "Test the opportunity with one reversible action.",
        ),
    ),
}

# These are deliberate Luna treatments for recognisable human tensions. They
# are still anchored to a calculated aspect; no copy is selected without the
# matching evidence.
SPECIAL_COPY = {
    (frozenset({"Moon", "Saturn"}), "conjunction"): (
        "THE MOOD NEEDS STRUCTURE.",
        "Responsibility feels personal today. A limit, delay or duty may make the emotional weight feel larger than it is.",
        "Use discipline as containment, not punishment.",
        "Set one boundary. Complete one necessary task. Delay permanent emotional conclusions.",
    ),
    (frozenset({"Moon", "Uranus"}), "conjunction"): (
        "THE FEELING CHANGED FASTER THAN THE PLAN.",
        "An emotional reaction or sudden development can disrupt the expected rhythm.",
        "Freedom is useful. Impulse is not the same as direction.",
        "Pause before changing the plan. Keep the useful surprise.",
    ),
    (frozenset({"Moon", "Mercury"}), "square"): (
        "THE FEELING AND THE MESSAGE DISAGREE.",
        "What you feel and what was said are not producing the same conclusion.",
        "Irritation can identify the gap, but it cannot verify the interpretation.",
        "Check the message before sending the response.",
    ),
    (frozenset({"Sun", "Moon"}), "trine"): (
        "THE INNER AND OUTER ANSWERS AGREE.",
        "Your visible direction and emotional response are briefly supporting each other.",
        "Ease creates usable momentum, not a guaranteed result.",
        "Use the clear opening while action feels natural.",
    ),
    (frozenset({"Venus", "True Node"}), "trine"): (
        "VALUES AND DIRECTION ARE COOPERATING.",
        "What you value and the direction developing ahead are moving with less resistance.",
        "Support is available, but it still needs a chosen destination.",
        "Put one relationship or value-led decision in motion.",
    ),
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
    (frozenset({"Venus", "Jupiter"}), "sextile"): (
        "PLEASURE JUST FOUND MORE ROOM.",
        "Value and desire have found an opening through expansion.",
        "More is available, but excess is waiting beside it with a smile.",
        "Take the opportunity. Leave the appetite unsupervised at your own risk.",
    ),
    (frozenset({"Venus", "Saturn"}), "opposition"): (
        "VALUE IS BEING TESTED.",
        "Desire wants reassurance. The limit wants proof.",
        "What survives the test is worth keeping. What fails was expensive decoration.",
        "Stop auditioning. Ask for the evidence.",
    ),
    (frozenset({"Sun", "Moon"}), "square"): (
        "THE FACE AND THE FEELING DISAGREE.",
        "The visible plan and the private reaction are refusing to cooperate.",
        "Performing certainty will not settle an argument happening underneath it.",
        "Name the feeling. Keep it away from the steering wheel.",
    ),
    (frozenset({"Sun", "True Node"}), "opposition"): (
        "THE FUTURE IS ARGUING WITH YOUR IMAGE.",
        "Visibility is pulling toward one version of you. Direction points elsewhere.",
        "Applause becomes a detour when it rewards the wrong role.",
        "Choose the path that still matters when nobody is watching.",
    ),
    (frozenset({"Moon", "Mercury"}), "trine"): (
        "SAY WHAT YOU ACTUALLY FEEL.",
        "Instinct and language are briefly speaking the same dialect.",
        "The truth can travel cleanly now, before analysis starts dressing it for court.",
        "Say it plainly. Stop after the honest sentence.",
    ),
    (frozenset({"Moon", "Neptune"}), "square"): (
        "FEELING IS NOT PROOF.",
        "Instinct is absorbing imagination and calling the mixture certainty.",
        "The emotion may be real. Its explanation is still under investigation.",
        "Feel it fully. Verify it separately.",
    ),
    (frozenset({"Mercury", "True Node"}), "opposition"): (
        "TWO TRUTHS ENTER. ONE CHOICE LEAVES.",
        "A yes can still send you somewhere you do not want to go.",
        "Compromise without a clear priority becomes slow surrender.",
        "Price the direction, not just the offer.",
    ),
    (frozenset({"Sun", "Mercury"}), "conjunction"): (
        "TWO SIGNALS. ONE MICROPHONE.",
        "What you say and what everybody can now see are becoming the same story.",
        "The signal grows louder. So does the distortion.",
        "Choose what deserves amplification.",
    ),
    (frozenset({"Sun", "Uranus"}), "square"): (
        "PRESSURE DOES NOT NEGOTIATE.",
        "Put the public story beside what just changed. If they no longer match, that is the evidence.",
        "Use the irritation as evidence, not permission to overreact.",
        "Remove the false assumption, then make the move.",
    ),
    (frozenset({"Sun", "Moon"}), "opposition"): (
        "THE OTHER SIDE HAS LEVERAGE.",
        "The public answer wants one thing. Your private reaction wants another.",
        "The stalemate survives only while nobody names the cost.",
        "State both prices. Choose the cost you can carry.",
    ),
    (frozenset({"Moon", "Neptune"}), "conjunction"): (
        "THE VOLUME JUST CHANGED.",
        "Put your gut beside the imagined version. Do not run both at full volume.",
        "Choose the setting before the noise chooses it for you.",
        "Give the combined force one precise job.",
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
    major_event_label: str = ""
    event_tier: str = ""
    supporting_events: tuple[str, ...] = ()
    peak_minute: int | None = None
    exact_time_label: str = ""

    @property
    def weekday(self) -> str:
        return self.reading_date.strftime("%A")

    @property
    def date_label(self) -> str:
        return self.reading_date.strftime("%d %B %Y").lstrip("0")

    def video_copy(self) -> str:
        major = f"{self.major_event_label.upper()}\n\n" if self.major_event_label else ""
        supporting = (
            "ALSO ACTIVE · " + " · ".join(self.supporting_events).upper() + "\n\n"
            if self.supporting_events else ""
        )
        return (
            f"{self.weekday.upper()} · {self.date_label.upper()}\n\n"
            f"{major}"
            f"{self.headline}\n\n"
            f"{self.evidence.upper()}\n\n"
            f"{supporting}"
            f"{finalize_customer_prose(self.line_one, product='weekly')}\n\n"
            f"{finalize_customer_prose(self.line_two, product='weekly')}\n\n"
            "YOUR MOVE\n"
            f"{finalize_customer_prose(self.action, product='weekly')}\n\n"
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


@dataclass(frozen=True)
class DailyAspectTiming:
    minimum_orb: float
    peak_minute: int
    phase: str
    exact_time_label: str = ""


def _aspect_orb_at_minute(
    iso_date: str,
    timezone_name: str,
    minute_of_day: int,
    planet1: str,
    planet2: str,
    aspect_name: str,
) -> float:
    first = position_for_local_minute(
        iso_date, timezone_name, minute_of_day, planet1
    )
    second = position_for_local_minute(
        iso_date, timezone_name, minute_of_day, planet2
    )
    distance = angular_distance(first.longitude, second.longitude)
    return abs(distance - ASPECTS[aspect_name][0])


def _local_clock_label(reading_date: date, timezone_name: str, minute: int) -> str:
    local_dt = datetime(
        reading_date.year,
        reading_date.month,
        reading_date.day,
        minute // 60,
        minute % 60,
        tzinfo=ZoneInfo(timezone_name),
    )
    hour = local_dt.hour % 12 or 12
    meridiem = "am" if local_dt.hour < 12 else "pm"
    zone = local_dt.tzname() or timezone_name
    return f"{hour}:{local_dt.minute:02d} {meridiem} {zone}"


@lru_cache(maxsize=50000)
def _daily_aspect_timing(
    iso_date: str,
    timezone_name: str,
    planet1: str,
    planet2: str,
    aspect_name: str,
) -> DailyAspectTiming:
    """Find the closest local-day orb instead of treating noon as the day."""
    coarse_minutes = tuple(range(0, 1440, 30)) + (1439,)
    coarse = [
        (
            _aspect_orb_at_minute(
                iso_date,
                timezone_name,
                minute,
                planet1,
                planet2,
                aspect_name,
            ),
            minute,
        )
        for minute in coarse_minutes
    ]
    _, coarse_peak = min(coarse)
    refine_start = max(0, coarse_peak - 45)
    refine_end = min(1439, coarse_peak + 45)
    minimum_orb, peak_minute = min(
        (
            _aspect_orb_at_minute(
                iso_date,
                timezone_name,
                minute,
                planet1,
                planet2,
                aspect_name,
            ),
            minute,
        )
        for minute in range(refine_start, refine_end + 1)
    )

    start_orb = coarse[0][0]
    end_orb = coarse[-1][0]
    exact_today = minimum_orb <= 0.03
    if exact_today:
        phase = "exact today"
        exact_time_label = _local_clock_label(
            date.fromisoformat(iso_date), timezone_name, peak_minute
        )
    elif end_orb + 0.01 < start_orb:
        phase = "applying"
        exact_time_label = ""
    elif start_orb + 0.01 < end_orb:
        phase = "separating"
        exact_time_label = ""
    else:
        phase = "active"
        exact_time_label = ""

    return DailyAspectTiming(
        minimum_orb=minimum_orb,
        peak_minute=peak_minute,
        phase=phase,
        exact_time_label=exact_time_label,
    )


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


def _generic_copy(
    aspect: Aspect,
    reading_date: date,
    used_copy_signatures: set[tuple[str, str, str]],
) -> tuple[str, str, str, str]:
    first = PLANET_THEMES[aspect.planet1]
    second = PLANET_THEMES[aspect.planet2]
    headlines = ASPECT_HEADLINES[aspect.name]
    headline = headlines[reading_date.toordinal() % len(headlines)]
    templates = GENERIC_COPY_VARIANTS[aspect.name]
    seed = reading_date.toordinal() + sum(ord(char) for char in aspect.planet1 + aspect.planet2)
    start = seed % len(templates)
    ordered = templates[start:] + templates[:start]
    formatted = [
        tuple(
            value.format(
                first=first,
                First=first.capitalize(),
                second=second,
                Second=second.capitalize(),
            )
            for value in template
        )
        for template in ordered
    ]
    selected = next(
        (
            candidate
            for candidate in formatted
            if candidate not in used_copy_signatures
        ),
        formatted[0],
    )
    line_one, line_two, action = selected
    return headline, line_one, line_two, action


def _day_from_aspect(
    reading_date: date,
    timezone_name: str,
    aspect: Aspect,
    used_headlines: set[str],
    used_copy_signatures: set[tuple[str, str, str]],
) -> WeeklyDay:
    timing = _daily_aspect_timing(
        reading_date.isoformat(),
        timezone_name,
        aspect.planet1,
        aspect.planet2,
        aspect.name,
    )
    phase = timing.phase
    selected_copy = SPECIAL_COPY.get(
        (frozenset({aspect.planet1, aspect.planet2}), aspect.name)
    )
    if selected_copy and tuple(selected_copy[1:]) in used_copy_signatures:
        selected_copy = None
    selected_copy = selected_copy or _generic_copy(
        aspect,
        reading_date,
        used_copy_signatures,
    )
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
    if timing.exact_time_label:
        evidence = (
            f"{aspect.planet1} {verb} {aspect.planet2} · exact today · "
            f"approximately {timing.exact_time_label}"
        )
    else:
        evidence = (
            f"{aspect.planet1} {verb} {aspect.planet2} · "
            f"{phase} · {timing.minimum_orb:.2f}° orb at closest approach"
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
        orb=timing.minimum_orb,
        phase=phase,
        peak_minute=timing.peak_minute,
        exact_time_label=timing.exact_time_label,
    )


def _day_from_major_signal(reading_date: date, signal, supporting) -> WeeklyDay:
    planets = tuple(signal.planets[:2])
    if len(planets) == 0:
        planets = ("Sun", "Moon")
    elif len(planets) == 1:
        planets = (planets[0], planets[0])
    evidence = f"{signal.display_label} · major sky event"
    line_one = signal.line_one
    line_two = signal.line_two
    action = signal.action
    primary_pair = frozenset(str(item) for item in signal.planets)
    mars_saturn_support = any(
        frozenset(str(item) for item in item.planets)
        == frozenset({"Mars", "Saturn"})
        for item in supporting
    )
    if primary_pair == frozenset({"Jupiter", "Saturn"}) and mars_saturn_support:
        line_two = (
            "The opening can last, but the Mars–Saturn pressure warns that "
            "force and bad timing will waste it."
        )
        action = "Choose one expansion. Give it a boundary, budget and next step."
    return WeeklyDay(
        reading_date=reading_date,
        headline=signal.headline,
        evidence=evidence,
        line_one=line_one,
        line_two=line_two,
        action=action,
        planets=(str(planets[0]), str(planets[1])),
        aspect_name=signal.event_class,
        orb=0.0,
        phase="major event",
        major_event_label=signal.display_label,
        event_tier=signal.tier,
        supporting_events=tuple(item.display_label for item in supporting),
    )


def build_weekly_view(monday: date, timezone_name: str) -> tuple[WeeklyDay, ...]:
    """Build seven shared-sky cards with mandatory-event and opportunity protection."""
    if monday.weekday() != 0:
        raise ValueError("Weekly View must begin on a Monday.")

    sunday = monday + timedelta(days=6)
    # Weekly is shared sky.  The global registry also injects Luna's four
    # foundational solar anchors, so an equinox or solstice cannot be ranked
    # away by an ordinary daily aspect.
    registry = major_sky_events(monday, sunday, "Aries", timezone_name)
    signals_by_day = {
        day: tuple(item for item in registry if item.event_date == day)
        for day in (monday + timedelta(days=offset) for offset in range(7))
    }

    pair_counts: Counter[frozenset[str]] = Counter()
    planet_counts: Counter[str] = Counter()
    previous_pair: frozenset[str] | None = None
    used_headlines: set[str] = set()
    used_copy_signatures: set[tuple[str, str, str]] = set()
    result: list[WeeklyDay] = []

    for offset in range(7):
        reading_date = monday + timedelta(days=offset)
        primary_signal, supporting = day_signal_bundle(
            signals_by_day.get(reading_date, ()),
            "weekly",
        )

        # Mandatory events always win. A high-value opportunity also gets the
        # day when no mandatory event outranks it. Ordinary aspects fill quiet days.
        if primary_signal is not None and (
            primary_signal.must_surface_in("weekly")
            or primary_signal.opportunity
            or primary_signal.sky_score >= 80.0
        ):
            day = _day_from_major_signal(reading_date, primary_signal, supporting)
            pair = frozenset(day.planets)
        else:
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
                used_copy_signatures,
            )
            # Do not discard a meaningful event simply because an ordinary
            # aspect won the card. High-value opportunities are always retained;
            # lesser major events stay visible when they add information.
            if (
                primary_signal is not None
                and (primary_signal.opportunity or primary_signal.sky_score >= 72.0)
                and primary_signal.technical_label.lower() not in day.evidence.lower()
            ):
                day = WeeklyDay(
                    **{**day.__dict__, "supporting_events": (primary_signal.display_label,)}
                )

        result.append(day)
        used_headlines.add(day.headline)
        used_copy_signatures.add((day.line_one, day.line_two, day.action))
        pair_counts[pair] += 1
        planet_counts.update(pair)
        previous_pair = pair

    return tuple(result)


WEEKLY_HOUSE_MATERIAL = {
    1: {
        "focus": "your identity and boundaries",
        "card": "YOU",
        "headline": "MAKE THE NEW DIRECTION CARRY ITS WEIGHT.",
        "move": "CHOOSE ONE DIRECTION. BUILD ITS SUPPORT.",
    },
    2: {
        "focus": "money, pricing and self-worth",
        "card": "MONEY",
        "headline": "MAKE THE NUMBERS CARRY THE PLAN.",
        "move": "PRICE THE OPPORTUNITY BEFORE COMMITTING.",
    },
    3: {
        "focus": "messages, documents and decisions",
        "card": "MESSAGE",
        "headline": "MAKE THE MESSAGE SURVIVE QUESTIONS.",
        "move": "CHECK THE FACTS BEFORE SENDING.",
    },
    4: {
        "focus": "home, family and private responsibilities",
        "card": "HOME",
        "headline": "MAKE THE PLAN FIT AT HOME.",
        "move": "STABILISE HOME BEFORE EXPANDING.",
    },
    5: {
        "focus": "romance, creativity and personal enterprise",
        "card": "CREATIVE DIRECTION",
        "headline": "TURN THE SPARK INTO FOLLOW-THROUGH.",
        "move": "TEST THE SPARK IN REAL LIFE.",
    },
    6: {
        "focus": "workload, health and daily routines",
        "card": "WORKLOAD",
        "headline": "MAKE THE ORDINARY WEEK SUPPORT IT.",
        "move": "FIX THE METHOD BEFORE PUSHING.",
    },
    7: {
        "focus": "relationships, clients and agreements",
        "card": "RELATIONSHIPS",
        "headline": "MAKE THE TERMS MATCH THE PROMISE.",
        "move": "PUT THE SHARED TERMS IN WRITING.",
    },
    8: {
        "focus": "shared money, trust and obligations",
        "card": "SHARED MONEY",
        "headline": "MAKE EVERY OBLIGATION VISIBLE.",
        "move": "NAME THE COST AND OWNER.",
    },
    9: {
        "focus": "travel, study and wider plans",
        "card": "WIDER PLAN",
        "headline": "MAKE THE WIDER OPTION SURVIVE LOGISTICS.",
        "move": "CHECK THE COSTS AND DEADLINES.",
    },
    10: {
        "focus": "career, reputation and responsibility",
        "card": "CAREER",
        "headline": "MAKE AUTHORITY COME WITH TERMS.",
        "move": "DEFINE THE ROLE BEFORE ACCEPTING.",
    },
    11: {
        "focus": "friends, audiences and future plans",
        "card": "FUTURE PLANS",
        "headline": "MAKE SUPPORT PROVE ITSELF.",
        "move": "CHOOSE WHO CARRIES THE NEXT STEP.",
    },
    12: {
        "focus": "rest, closure and private matters",
        "card": "REST · CLOSURE",
        "headline": "CLOSE THE NOISE AROUND THE DECISION.",
        "move": "PROTECT SPACE FOR THE REAL ANSWER.",
    },
}


PAIR_WEEKLY_CONTEXT = {
    (frozenset({"Moon", "Saturn"}), "conjunction"): (
        "emotional weight and responsibility need structure rather than amplification"
    ),
    (frozenset({"Jupiter", "Saturn"}), "trine"): (
        "growth has unusual support when ambition accepts limits, sequence and durable structure"
    ),
    (frozenset({"Mars", "Saturn"}), "square"): (
        "effort meets a limit, so method and timing matter more than force"
    ),
    (frozenset({"Sun", "Moon"}), "trine"): (
        "visible direction and emotional response can cooperate without guaranteeing the result"
    ),
    (frozenset({"Moon", "Uranus"}), "conjunction"): (
        "emotional surprise can reveal a needed change without making every impulse a direction"
    ),
    (frozenset({"Moon", "Mercury"}), "square"): (
        "feelings and words can conflict, making verification more useful than immediate reaction"
    ),
    (frozenset({"Venus", "True Node"}), "trine"): (
        "values, relationships and longer-term direction can move with less resistance"
    ),
}


PAIR_SIGN_SENTENCES = {
    (frozenset({"Moon", "Saturn"}), "conjunction"): (
        "Moon conjunct Saturn brings emotional weight and responsibility into {areas}."
    ),
    (frozenset({"Jupiter", "Saturn"}), "trine"): (
        "Jupiter trine Saturn opens controlled, sustainable growth across {areas}."
    ),
    (frozenset({"Mars", "Saturn"}), "square"): (
        "Mars square Saturn tests whether effort, timing and limits can work across {areas}."
    ),
    (frozenset({"Sun", "Moon"}), "trine"): (
        "Sun trine Moon aligns visible direction with emotional response across {areas}."
    ),
    (frozenset({"Moon", "Uranus"}), "conjunction"): (
        "Moon conjunct Uranus brings emotional surprise and sudden change into {areas}."
    ),
    (frozenset({"Moon", "Mercury"}), "square"): (
        "Moon square Mercury tests the gap between feelings and words across {areas}."
    ),
    (frozenset({"Venus", "True Node"}), "trine"): (
        "Venus trine the True Node supports alignment between values, relationships and direction across {areas}."
    ),
}


def _day_aspect_kind(day: WeeklyDay) -> str:
    if day.aspect_name in ASPECTS:
        return day.aspect_name
    text = f"{day.evidence} {day.major_event_label}".lower()
    for name in ("conjunction", "conjunct", "opposition", "opposite", "square", "trine", "sextile"):
        if name in text:
            return {
                "conjunct": "conjunction",
                "opposite": "opposition",
            }.get(name, name)
    return str(day.aspect_name or "active")


def _day_technical_label(day: WeeklyDay) -> str:
    value = day.major_event_label or day.evidence.split(" · ", 1)[0]
    return " ".join(str(value or "").split()).strip()


def _day_story_score(day: WeeklyDay) -> float:
    tier_score = {
        "S": 10.0,
        "A+": 9.0,
        "A": 8.0,
        "A-": 7.0,
        "B+": 6.0,
        "B": 5.0,
    }.get(day.event_tier, 4.0)
    pair_weight = sum(PLANET_WEIGHTS.get(item, 1.0) for item in set(day.planets))
    aspect_bonus = 1.0 if _day_aspect_kind(day) in {"square", "opposition", "trine", "sextile"} else 0.0
    structural_pressure_bonus = (
        3.0
        if _day_aspect_kind(day) in {"square", "opposition"}
        and "Saturn" in day.planets
        else 0.0
    )
    exact_bonus = 1.5 if day.phase == "exact today" else 0.0
    closeness = max(0.0, 1.5 - min(float(day.orb), 3.0) / 2.0)
    return (
        tier_score
        + pair_weight
        + aspect_bonus
        + structural_pressure_bonus
        + exact_bonus
        + closeness
    )


def _select_weekly_story_days(days: tuple[WeeklyDay, ...]):
    opening = days[0]
    supportive = [
        item
        for item in days
        if _day_aspect_kind(item) in {"trine", "sextile"}
        or "opportunity" in str(item.aspect_name).lower()
    ]
    pressure = [
        item for item in days if _day_aspect_kind(item) in {"square", "opposition"}
    ]
    support = max(supportive, key=_day_story_score) if supportive else None
    friction = max(pressure, key=_day_story_score) if pressure else None
    return opening, support, friction


def _shared_story_sentence(day: WeeklyDay, prefix: str) -> str:
    aspect = _day_aspect_kind(day)
    pair = frozenset(day.planets)
    label = _day_technical_label(day)
    context = PAIR_WEEKLY_CONTEXT.get((pair, aspect))
    if not context:
        context = finalize_customer_prose(day.line_one, product="weekly").rstrip(".")
        context = context[:1].lower() + context[1:] if context else "the week's conditions become concrete"
    timing = (
        f", exact at approximately {day.exact_time_label},"
        if day.exact_time_label
        else ":"
    )
    return f"{prefix} {label}{timing} {context}."


def build_weekly_synthesis(days: tuple[WeeklyDay, ...]) -> dict:
    """Connect the opening, support and pressure into one calculated weekly arc."""
    if not days:
        raise ValueError("Weekly synthesis requires at least one day.")
    opening, support, pressure = _select_weekly_story_days(days)
    if support and pressure:
        headline = "BUILD THE OPENING TO LAST."
        rule = "Use structure to protect the opportunity. Do not answer pressure with more force."
    elif support:
        headline = "USE THE OPENING WHILE IT IS REAL."
        rule = "Convert support into one concrete option before it becomes background weather."
    elif pressure:
        headline = "PRESSURE NEEDS A BETTER METHOD."
        rule = "Treat friction as evidence. Change the method before adding effort."
    else:
        headline = opening.headline
        rule = finalize_customer_prose(opening.action, product="weekly")

    paragraphs = [_shared_story_sentence(opening, "The week opens with")]
    later = []
    if support is not None and support.reading_date != opening.reading_date:
        later.append(_shared_story_sentence(support, "The usable opening is"))
    if pressure is not None and pressure.reading_date not in {
        opening.reading_date,
        support.reading_date if support else None,
    }:
        later.append(_shared_story_sentence(pressure, "The pressure test is"))
    if later:
        paragraphs.append(" ".join(later))
    return {"headline": headline, "paragraphs": tuple(paragraphs), "rule": rule}


def _event_houses(day: WeeklyDay, sign: str, timezone_name: str) -> tuple[tuple[str, int], ...]:
    native_index = SIGNS.index(sign)
    minute = day.peak_minute if day.peak_minute is not None else 720
    result = []
    for planet in dict.fromkeys(day.planets):
        if planet not in PLANET_WEIGHTS:
            continue
        position = position_for_local_minute(
            day.reading_date.isoformat(), timezone_name, minute, planet
        )
        result.append(
            (planet, whole_sign_house(position.sign_index, native_index))
        )
    return tuple(result)


def _focus_join(houses: tuple[int, ...]) -> str:
    values = [WEEKLY_HOUSE_MATERIAL[item]["focus"] for item in dict.fromkeys(houses)]
    if not values:
        return "the decision already in front of you"
    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + f" and {values[-1]}"


def _sign_event_sentence(day: WeeklyDay, sign: str, timezone_name: str) -> str:
    aspect = _day_aspect_kind(day)
    pair = frozenset(day.planets)
    houses = tuple(house for _, house in _event_houses(day, sign, timezone_name))
    areas = _focus_join(houses)
    template = PAIR_SIGN_SENTENCES.get((pair, aspect))
    if template:
        return template.format(areas=areas)
    label = _day_technical_label(day)
    if aspect in {"trine", "sextile"}:
        return f"{label} creates usable support across {areas}."
    if aspect in {"square", "opposition"}:
        return f"{label} exposes a pressure point across {areas}."
    if aspect == "conjunction":
        return f"{label} concentrates two planetary signals in {areas}."
    return f"{label} makes {areas} harder to treat as background."


def build_weekly_sign_translation(
    sign: str,
    monday: date,
    timezone_name: str,
    days: tuple[WeeklyDay, ...] | None = None,
) -> dict:
    """Translate the selected weekly events through whole-sign houses."""
    if sign not in SIGNS:
        raise ValueError(f"Unknown sign: {sign}")
    week = tuple(days or build_weekly_view(monday, timezone_name))
    opening, support, pressure = _select_weekly_story_days(week)

    scores: Counter[int] = Counter()
    first_seen: dict[int, tuple[int, int]] = {}
    for day_index, day in enumerate(week):
        day_weight = _day_story_score(day)
        for planet_index, (planet, house) in enumerate(
            _event_houses(day, sign, timezone_name)
        ):
            scores[house] += day_weight * PLANET_WEIGHTS.get(planet, 1.0)
            first_seen.setdefault(house, (day_index, planet_index))

    central_house = max(
        scores,
        key=lambda house: (scores[house], -first_seen.get(house, (99, 99))[0]),
    ) if scores else 1

    selected_houses = [central_house]
    # After the central house, show the pressure field before the opportunity
    # field so the card tells readers what must carry the opening.
    for day in (pressure, support, opening):
        if day is None:
            continue
        for _, house in _event_houses(day, sign, timezone_name):
            if house not in selected_houses:
                selected_houses.append(house)
            if len(selected_houses) >= 3:
                break
        if len(selected_houses) >= 3:
            break
    for house, _ in sorted(scores.items(), key=lambda item: (-item[1], first_seen[item[0]])):
        if house not in selected_houses:
            selected_houses.append(house)
        if len(selected_houses) >= 3:
            break

    story_days = []
    for day in (opening, support, pressure):
        if day is not None and day.reading_date not in {
            item.reading_date for item in story_days
        }:
            story_days.append(day)
    paragraphs = tuple(
        _sign_event_sentence(day, sign, timezone_name) for day in story_days
    )
    if support and pressure:
        paragraphs += (
            "The opportunity is real. It still needs a structure capable of carrying it.",
        )

    material = WEEKLY_HOUSE_MATERIAL[central_house]
    chosen = tuple(selected_houses[:3])
    return {
        "sign": sign,
        "headline": material["headline"],
        "areas": [WEEKLY_HOUSE_MATERIAL[house]["focus"] for house in chosen],
        "raw_areas": [HOUSE_NAMES[house] for house in chosen],
        "houses": list(chosen),
        "paragraphs": paragraphs,
        "interpretation": " ".join(paragraphs),
        "move": material["move"].rstrip("."),
        "social_area": " · ".join(
            WEEKLY_HOUSE_MATERIAL[house]["card"] for house in chosen
        ),
    }


def weekly_social_card_copy(summary: dict, monday: date) -> str:
    """Return complete, pre-compressed card copy without cutting sentences."""
    sunday = monday + timedelta(days=6)
    date_line = f"{monday.strftime('%d %b').lstrip('0')}–{sunday.strftime('%d %b').lstrip('0')}".upper()
    move = str(summary.get("move") or "VERIFY BEFORE COMMITTING").strip().rstrip(".").upper()
    social_area = str(summary.get("social_area") or "YOUR NEXT MOVE").strip().upper()
    return (
        f"THE WEEK AHEAD · {date_line}\n\n"
        f"{str(summary.get('sign', '')).upper()}\n\n"
        "WHERE IT LANDS\n"
        f"{social_area}\n\n"
        "YOUR MOVE\n"
        f"{move}.\n\n"
        "LUNA CONVERGENCE"
    )


def all_video_copy(days: tuple[WeeklyDay, ...]) -> str:
    return "\n\n------------------------------\n\n".join(
        item.video_copy() for item in days
    )
