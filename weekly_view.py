from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta

from astrology_engine import ASPECTS, PLANET_WEIGHTS, Aspect, detect_aspects, positions_for_date
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
    phase = _phase(reading_date, timezone_name, aspect)
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


def _day_from_major_signal(reading_date: date, signal, supporting) -> WeeklyDay:
    planets = tuple(signal.planets[:2])
    if len(planets) == 0:
        planets = ("Sun", "Moon")
    elif len(planets) == 1:
        planets = (planets[0], planets[0])
    evidence = f"{signal.display_label} · major sky event"
    return WeeklyDay(
        reading_date=reading_date,
        headline=signal.headline,
        evidence=evidence,
        line_one=signal.line_one,
        line_two=signal.line_two,
        action=signal.action,
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


def all_video_copy(days: tuple[WeeklyDay, ...]) -> str:
    return "\n\n------------------------------\n\n".join(
        item.video_copy() for item in days
    )
