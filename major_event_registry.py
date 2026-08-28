from __future__ import annotations

"""Global major-sky event registry for Luna Convergence.

This module sits upstream of Daily, Weekly, Monthly, Yearly and Personal Timing.
It does not replace the ephemeris/event engine. It classifies already-calculated
`astrology_engine.Event` objects so a major event cannot be ranked away by an
ordinary aspect or disappear during editorial translation.

Core rule:
    - mandatory sky events survive into the customer experience;
    - high-value opportunity events are retained as either primary or supporting
      signals;
    - the technical event name stays visible while Luna supplies the human meaning.
"""

from dataclasses import asdict, dataclass
from datetime import date
from functools import lru_cache
import re
from typing import Iterable

from astrology_engine import Event, angular_distance, period_events, positions_for_date


STRUCTURAL_PLANETS = {"Saturn", "Uranus", "Neptune", "Pluto"}
SLOW_PLANETS = {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}
INNER_PLANETS = {"Mercury", "Venus", "Mars"}
FLOW_ASPECTS = {"trine", "sextile"}
HARD_ASPECTS = {"square", "opposition"}

PRODUCTS = frozenset({"daily", "weekly", "monthly", "yearly", "timing"})
SHORT_PRODUCTS = frozenset({"daily", "weekly", "monthly"})


@dataclass(frozen=True)
class MajorEventSignal:
    event_date: date
    source_kind: str
    event_class: str
    tier: str
    sky_score: float
    technical_label: str
    display_label: str
    source_title: str
    planets: tuple[str, ...]
    houses: tuple[int, ...]
    polarity: str
    importance: float
    opportunity: bool
    visible_products: frozenset[str]
    must_surface_products: frozenset[str]
    headline: str
    line_one: str
    line_two: str
    action: str
    watch: str

    def visible_in(self, product: str) -> bool:
        return str(product or "").lower() in self.visible_products

    def must_surface_in(self, product: str) -> bool:
        return str(product or "").lower() in self.must_surface_products

    def to_dict(self) -> dict:
        value = asdict(self)
        value["event_date"] = self.event_date.isoformat()
        value["visible_products"] = sorted(self.visible_products)
        value["must_surface_products"] = sorted(self.must_surface_products)
        return value


@dataclass(frozen=True)
class PersonalEventActivation:
    """A shared-sky event that also makes a close contact to a natal point."""

    event_date: date
    display_label: str
    event_class: str
    tier: str
    sky_score: float
    personal_score: float
    transit_planet: str
    natal_target: str
    aspect: str
    orb: float
    focus: str
    interpretation: str
    action: str
    opportunity: bool

    @property
    def combined_score(self) -> float:
        return round(
            max(float(self.sky_score), float(self.personal_score))
            + min(float(self.sky_score), float(self.personal_score)) * 0.08,
            3,
        )

    def to_dict(self) -> dict:
        value = asdict(self)
        value["event_date"] = self.event_date.isoformat()
        value["combined_score"] = self.combined_score
        return value


def _verb_label(title: str) -> str:
    text = str(title or "")
    return (
        text.replace(" conjunction ", " conjunct ")
        .replace(" opposition ", " opposite ")
    )


def _event_pair(event: Event) -> frozenset[str]:
    return frozenset(str(item) for item in (event.planets or ()))


def _is_cazimi(event: Event) -> str | None:
    if event.kind != "aspect" or event.aspect_name != "conjunction":
        return None
    pair = _event_pair(event)
    if pair == frozenset({"Sun", "Mercury"}):
        return "Mercury"
    if pair == frozenset({"Sun", "Venus"}):
        return "Venus"
    return None


def _copy_for(
    *,
    event: Event,
    event_class: str,
    opportunity: bool,
) -> tuple[str, str, str, str, str]:
    title = str(event.title or "")
    lower = title.lower()
    pair = _event_pair(event)

    if event_class == "eclipse":
        if "lunar" in lower:
            return (
                "SOMETHING HAS REACHED THE END OF THE ARGUMENT.",
                "A lunar eclipse concentrates a Full Moon into a sharper turning point. What has been building is harder to keep half-decided.",
                "Feelings can peak before the practical answer is ready. Name what has become undeniable without making noise do the deciding for you.",
                "Decide what needs an ending, an answer or a different arrangement. Then let the volume settle before adding anything irreversible.",
                "Do not confuse emotional intensity with proof that the first reaction is the right move.",
            )
        return (
            "A NEW CHAPTER JUST ACQUIRED CONSEQUENCES.",
            "A solar eclipse intensifies a New Moon. An opening can begin quickly, but the consequences usually take longer to reveal themselves.",
            "Treat the beginning seriously. Give the new direction terms, time and room to prove itself.",
            "Start the part you can support. Leave the rest flexible until the next facts arrive.",
            "Do not call a dramatic beginning a finished result.",
        )

    if event_class == "cazimi":
        if "mercury" in lower:
            return (
                "THE MESSAGE REACHES THE CENTRE.",
                "Mercury meets the Sun at the heart of the cycle. A message, answer or decision can become unusually clear once the noise is stripped away.",
                "Use the clarity while it is clean. Ask the question, correct the document or say the thing plainly.",
                "Find the sentence that still works after the explanation is removed. Use it.",
                "Do not decorate the answer after you find it.",
            )
        return (
            "VALUE REACHES THE CENTRE.",
            "Venus meets the Sun at the heart of the cycle. Desire, money or relationship priorities become harder to outsource.",
            "Name what you value before attention, aesthetics or convenience name it for you.",
            "Choose what is worth more of your time, money or affection.",
            "Do not mistake being wanted for being well matched.",
        )

    if event_class == "station":
        retrograde = "retrograde" in lower
        planet = event.planets[0] if event.planets else "A planet"
        if retrograde:
            return (
                "THE MOTION CHANGED. REVIEW THE PLAN.",
                f"{planet} has stationed retrograde. The issue does not disappear; the direction of work changes from expansion to review.",
                "Recheck what has already been set in motion before you add another layer.",
                "Review the terms, timing and assumption that would be expensive to carry forward unchanged.",
                "Do not interpret a review cycle as automatic failure.",
            )
        return (
            "THE MOTION CHANGED. USE WHAT THE REVIEW TAUGHT YOU.",
            f"{planet} has stationed direct. A question that has been looping can begin moving outward again.",
            "Use the new motion carefully. The station is a pivot, not proof that every delay has vanished.",
            "Act on the revision that survived the retrograde period.",
            "Do not recreate the old problem simply because movement has returned.",
        )

    if event_class == "ingress":
        planet = event.planets[0] if event.planets else "A planet"
        if planet in {"Pluto", "Neptune", "Uranus"}:
            return (
                "THE BACKGROUND JUST CHANGED SIGNS.",
                f"{planet} has entered a new sign. This is not a one-day mood; it changes the longer chapter the faster events will trigger.",
                "Notice which old assumptions stop fitting before you rush to define the entire new era.",
                "Mark the shift. Change the structure gradually enough to learn what the new conditions require.",
                "Do not reduce a multi-year change to a single dramatic day.",
            )
        if planet == "Saturn":
            return (
                "THE STANDARD JUST MOVED.",
                "Saturn has entered a new sign. Responsibility, limits and durable structure begin asking a different question.",
                "Define what now needs a boundary, a timetable or a real owner.",
                "Put the new responsibility into terms before it becomes background burden.",
                "Do not carry a new chapter using rules built for the old one.",
            )
        if planet == "Jupiter":
            return (
                "THE FIELD JUST GOT BIGGER.",
                "Jupiter has entered a new sign. A year-long growth chapter begins to favour a different kind of opportunity.",
                "Watch what starts offering more room, reach, learning or choice.",
                "Take the first useful opening. Price the extra load before you scale it.",
                "More is useful only when your actual life can carry it.",
            )
        return (
            "THE TONE JUST CHANGED.",
            f"{planet} has entered a new sign. The immediate style of action changes even if the larger story does not.",
            "Use the shift as fresh information rather than a reason to restart everything.",
            "Change the method that no longer fits the new conditions.",
            "Do not mistake a change in tone for a total change in direction.",
        )

    if event_class == "structural_alignment":
        return (
            "THE BACKGROUND BECAME AN EVENT.",
            "Two slow-moving planets have reached an exact major aspect. The pressure belongs to a longer collective cycle, not just today's mood.",
            "Treat faster events around this date as triggers inside the larger structural change.",
            "Name what is becoming more possible, more expensive or impossible to keep unchanged.",
            "Do not let a short-term distraction hide the slower shift underneath it.",
        )

    if event_class == "lunation":
        if "full moon" in lower:
            return (
                "THE STORY REACHED VISIBILITY.",
                "A Full Moon brings something to culmination, exposure or emotional volume.",
                "Use what becomes visible. Do not let the peak manufacture certainty that the facts do not support.",
                "Name what is complete, what needs an answer and what can now be released.",
                "Do not make the irreversible move only because the feeling is loud.",
            )
        return (
            "START SMALL ENOUGH TO LEARN.",
            "A New Moon opens a fresh cycle. The beginning matters more as a seed than as a finished result.",
            "Choose one action that gives the new direction something real to grow from.",
            "Begin the piece you can support now.",
            "Do not demand proof from a cycle that has only just started.",
        )

    if event_class == "node_contact":
        return (
            "THE OLD ROUTE AND THE NEXT ROUTE JUST TOUCHED.",
            "A close contact to the lunar nodes puts direction, repetition and unfinished material into the same conversation.",
            "Notice what is returning because it still needs a decision rather than because it deserves another life.",
            "Keep the useful lesson. Stop carrying the obsolete route.",
            "Do not mistake familiarity for direction.",
        )

    if opportunity:
        if frozenset({"Venus", "Jupiter"}) <= pair:
            return (
                "PLEASURE FOUND MORE ROOM.",
                "An invitation, purchase or attractive possibility can look unusually good now. The opening is real enough to test.",
                "Use the ease without asking it to prove permanence before ordinary life returns.",
                "Take the useful opening. Keep the appetite from writing the contract.",
                "Do not turn a good signal into permission to overextend.",
            )
        if "Jupiter" in pair:
            return (
                "THE OPENING IS REAL ENOUGH TO TEST.",
                "A conversation, application, booking or proposal can travel further than usual. More room is available if you use it.",
                "Convert the favourable condition into one concrete option while the support is usable.",
                "Make the call, application, proposal or booking that increases future choice.",
                "Do not confuse a larger field with a requirement to choose everything in it.",
            )
        return (
            "THE WINDOW IS OPEN.",
            "Something tentative has enough support to test in real life.",
            "Use the advantage on something concrete before it becomes background weather.",
            "Make one useful move while the opening is available.",
            "Do not waste clean support on vague intention.",
        )

    return (
        "THE SKY HAS A CLEAR PRESSURE POINT.",
        "An exact aspect is concentrated enough to matter today.",
        "Use the event as evidence. Keep the response proportionate to the actual stakes.",
        "Name the practical consequence, then choose the smallest move that improves the position.",
        "Do not let the headline become larger than the event itself.",
    )


def _signal_from_event(event: Event, same_day: tuple[Event, ...]) -> MajorEventSignal | None:
    pair = _event_pair(event)
    cazimi_planet = _is_cazimi(event)
    opportunity = bool(
        event.polarity == "opportunity"
        or (event.kind == "ingress" and "Jupiter" in pair)
        or (event.kind == "aspect" and "Jupiter" in pair and event.aspect_name in FLOW_ASPECTS | {"conjunction"})
    )

    event_class = ""
    tier = ""
    sky_score = 0.0
    visible_products: frozenset[str] = frozenset()
    must_surface_products: frozenset[str] = frozenset()
    display_label = _verb_label(event.title)

    if event.kind == "eclipse":
        event_class = "eclipse"
        tier = "S"
        sky_score = 100.0 + float(event.importance)
        visible_products = PRODUCTS
        must_surface_products = PRODUCTS
        companion = next(
            (
                item for item in same_day
                if item.kind == "lunation" and _event_pair(item) == frozenset({"Sun", "Moon"})
            ),
            None,
        )
        if companion:
            display_label = f"{event.title} · {companion.title}"
    elif cazimi_planet:
        event_class = "cazimi"
        tier = "A"
        sky_score = 90.0 + float(event.importance)
        visible_products = PRODUCTS
        must_surface_products = SHORT_PRODUCTS
        display_label = f"{cazimi_planet} cazimi · {_verb_label(event.title)}"
    elif event.kind == "aspect" and pair <= SLOW_PLANETS:
        # Exact slow-planet aspects matter, but not every supportive sextile or
        # trine is an era-defining event. Hard/conjunct structural contacts are
        # mandatory; supportive outer configurations remain visible without
        # crowding eclipses, ingresses and stations out of the calendar.
        major_angle = event.aspect_name in {"conjunction", "square", "opposition"}
        structural_pair = len(pair & STRUCTURAL_PLANETS) >= 2
        great_conjunction = pair == frozenset({"Jupiter", "Saturn"}) and event.aspect_name == "conjunction"
        if great_conjunction or (structural_pair and major_angle):
            event_class = "structural_alignment"
            tier = "S"
            sky_score = 96.0 + float(event.importance)
            visible_products = PRODUCTS
            must_surface_products = PRODUCTS
        elif structural_pair:
            event_class = "structural_alignment"
            tier = "A+"
            sky_score = 88.0 + float(event.importance)
            visible_products = PRODUCTS
            must_surface_products = frozenset()
            # A supportive outer-planet alignment can open collective conditions,
            # but it is not automatically a personal opportunity. Personal
            # opportunity is earned only through natal activation downstream.
            opportunity = False
        elif "Jupiter" in pair and event.aspect_name in FLOW_ASPECTS | {"conjunction"}:
            event_class = "opportunity"
            tier = "A"
            sky_score = 84.0 + float(event.importance)
            visible_products = PRODUCTS
            must_surface_products = frozenset()
            opportunity = True
        else:
            event_class = "structural_alignment"
            tier = "A"
            sky_score = 84.0 + float(event.importance)
            visible_products = PRODUCTS
            must_surface_products = frozenset()
    elif event.kind == "ingress":
        planet = event.planets[0] if event.planets else ""
        event_class = "ingress"
        if planet in {"Pluto", "Neptune", "Uranus"}:
            tier, sky_score, visible_products, must_surface_products = "A+", 96.0 + event.importance, PRODUCTS, PRODUCTS
        elif planet == "Saturn":
            tier, sky_score, visible_products, must_surface_products = "A+", 92.0 + event.importance, PRODUCTS, PRODUCTS
        elif planet == "Jupiter":
            tier, sky_score, visible_products, must_surface_products = "A", 87.0 + event.importance, PRODUCTS, PRODUCTS
        elif planet in {"Venus", "Mars"}:
            tier, sky_score, visible_products, must_surface_products = "B+", 75.0 + event.importance, SHORT_PRODUCTS, frozenset()
        elif planet == "Mercury":
            tier, sky_score, visible_products, must_surface_products = "B", 70.0 + event.importance, SHORT_PRODUCTS, frozenset()
        else:
            return None
    elif event.kind == "station":
        planet = event.planets[0] if event.planets else ""
        event_class = "station"
        if planet in SLOW_PLANETS:
            tier, sky_score, visible_products, must_surface_products = "A", 89.0 + event.importance, PRODUCTS, PRODUCTS
        elif planet in {"Venus", "Mars"}:
            tier, sky_score, visible_products, must_surface_products = "A", 85.0 + event.importance, PRODUCTS, frozenset({"daily", "weekly", "monthly", "yearly"})
        elif planet == "Mercury":
            tier, sky_score, visible_products, must_surface_products = "B+", 80.0 + event.importance, SHORT_PRODUCTS, SHORT_PRODUCTS
        else:
            return None
    elif event.kind == "lunation":
        # An eclipse on the same date already carries the lunation identity.
        if any(item.kind == "eclipse" for item in same_day):
            return None
        event_class = "lunation"
        tier = "B+"
        sky_score = 78.0 + float(event.importance)
        visible_products = SHORT_PRODUCTS
        must_surface_products = SHORT_PRODUCTS
    elif event.kind == "aspect" and "True Node" in pair and (event.orb is None or event.orb <= 0.8):
        event_class = "node_contact"
        tier = "B"
        sky_score = 72.0 + float(event.importance)
        visible_products = frozenset({"daily", "weekly", "monthly"})
        must_surface_products = frozenset()
    elif event.kind == "aspect" and opportunity and ("Jupiter" in pair or float(event.importance) >= 6.0):
        event_class = "opportunity"
        tier = "A-" if pair & SLOW_PLANETS else "B+"
        # Jupiter is Luna's primary opportunity carrier. Give exact supportive
        # Jupiter contacts a small ranking bonus so they cannot be crowded out
        # by a cluster of equally clean but less expansion-oriented aspects.
        sky_score = (80.0 if "Jupiter" in pair else 76.0) + float(event.importance)
        visible_products = frozenset({"daily", "weekly", "monthly", "yearly"}) if float(event.importance) >= 8.0 else SHORT_PRODUCTS
        must_surface_products = frozenset()
    elif event.kind == "aspect" and float(event.importance) >= 6.45:
        event_class = "trigger"
        tier = "B"
        sky_score = 68.0 + float(event.importance)
        visible_products = frozenset({"daily", "weekly"})
        must_surface_products = frozenset()
    else:
        return None

    headline, line_one, line_two, action, watch = _copy_for(
        event=event,
        event_class=event_class,
        opportunity=opportunity,
    )
    return MajorEventSignal(
        event_date=event.event_date,
        source_kind=event.kind,
        event_class=event_class,
        tier=tier,
        sky_score=round(sky_score, 3),
        technical_label=_verb_label(event.title),
        display_label=display_label,
        source_title=event.title,
        planets=tuple(event.planets or ()),
        houses=tuple(event.houses or ()),
        polarity=event.polarity,
        importance=float(event.importance),
        opportunity=opportunity,
        visible_products=visible_products,
        must_surface_products=must_surface_products,
        headline=headline,
        line_one=line_one,
        line_two=line_two,
        action=action,
        watch=watch,
    )


def classify_major_events(events: Iterable[Event]) -> tuple[MajorEventSignal, ...]:
    values = tuple(events)
    by_day: dict[date, tuple[Event, ...]] = {}
    for event in values:
        by_day.setdefault(event.event_date, tuple())
        by_day[event.event_date] = by_day[event.event_date] + (event,)

    signals = []
    for event in values:
        signal = _signal_from_event(event, by_day.get(event.event_date, ()))
        if signal is not None:
            signals.append(signal)

    # Same source event should not appear twice. Highest sky score wins.
    unique: dict[tuple[date, str], MajorEventSignal] = {}
    for signal in signals:
        key = (signal.event_date, signal.source_title)
        if key not in unique or signal.sky_score > unique[key].sky_score:
            unique[key] = signal

    return tuple(
        sorted(
            unique.values(),
            key=lambda item: (item.event_date, -item.sky_score, item.display_label),
        )
    )


@lru_cache(maxsize=512)
def major_sky_events(
    start: date,
    end: date,
    native_sign: str = "Aries",
    timezone_name: str = "Australia/Sydney",
) -> tuple[MajorEventSignal, ...]:
    return classify_major_events(period_events(start, end, native_sign, timezone_name))


def visible_signals(signals: Iterable[MajorEventSignal], product: str) -> tuple[MajorEventSignal, ...]:
    clean = str(product or "").lower()
    return tuple(item for item in signals if item.visible_in(clean))


def period_priority_signals(
    signals: Iterable[MajorEventSignal],
    product: str,
    *,
    limit: int = 10,
    opportunity_slots: int = 2,
) -> tuple[MajorEventSignal, ...]:
    """Return a product-sized set without losing mandatory events or opportunities."""
    clean = str(product or "").lower()
    pool = [item for item in signals if item.visible_in(clean)]
    mandatory = sorted(
        (item for item in pool if item.must_surface_in(clean)),
        key=lambda item: (-item.sky_score, item.event_date),
    )
    opportunities = sorted(
        (item for item in pool if item.opportunity and item not in mandatory),
        key=lambda item: (-item.sky_score, item.event_date),
    )[:max(0, int(opportunity_slots))]
    rest = sorted(
        (item for item in pool if item not in mandatory and item not in opportunities),
        key=lambda item: (-item.sky_score, item.event_date),
    )

    selected: list[MajorEventSignal] = []
    for item in mandatory + opportunities + rest:
        if item not in selected:
            selected.append(item)
        if len(selected) >= max(int(limit), len(mandatory) + len(opportunities)):
            break
    return tuple(sorted(selected, key=lambda item: (item.event_date, -item.sky_score)))


def day_signal_bundle(
    signals: Iterable[MajorEventSignal],
    product: str,
    *,
    supporting_limit: int = 2,
) -> tuple[MajorEventSignal | None, tuple[MajorEventSignal, ...]]:
    """Choose one primary day signal and retain a meaningful opportunity as support."""
    clean = str(product or "").lower()
    pool = sorted(
        (item for item in signals if item.visible_in(clean)),
        key=lambda item: (-int(item.must_surface_in(clean)), -item.sky_score, -int(item.opportunity)),
    )
    if not pool:
        return None, ()

    primary = pool[0]
    supporting: list[MajorEventSignal] = []

    # Preserve the best opportunity even when a higher-pressure/mandatory event wins the day.
    best_opportunity = next((item for item in pool[1:] if item.opportunity), None)
    if best_opportunity is not None:
        supporting.append(best_opportunity)

    for item in pool[1:]:
        if item in supporting:
            continue
        if item.sky_score < 73.0:
            continue
        supporting.append(item)
        if len(supporting) >= supporting_limit:
            break

    return primary, tuple(supporting[:supporting_limit])


def signals_for_day(
    reading_date: date,
    *,
    native_sign: str = "Aries",
    timezone_name: str = "Australia/Sydney",
    product: str = "daily",
) -> tuple[MajorEventSignal | None, tuple[MajorEventSignal, ...]]:
    signals = major_sky_events(reading_date, reading_date, native_sign, timezone_name)
    return day_signal_bundle(signals, product)


def serialized_priority_signals(
    events: Iterable[Event],
    product: str,
    *,
    limit: int = 10,
    opportunity_slots: int = 2,
) -> list[dict]:
    return [
        item.to_dict()
        for item in period_priority_signals(
            classify_major_events(events),
            product,
            limit=limit,
            opportunity_slots=opportunity_slots,
        )
    ]



_TIER_RANK = {"S": 6, "A+": 5, "A": 4, "A-": 3, "B+": 2, "B": 1}

_PERSONAL_TARGET_WEIGHT = {
    "Ascendant": 1.25,
    "Midheaven": 1.25,
    "Sun": 1.20,
    "Moon": 1.20,
    "Mercury": 1.00,
    "Venus": 1.05,
    "Mars": 1.00,
    "Jupiter": 0.88,
    "Saturn": 0.92,
    "Uranus": 0.80,
    "Neptune": 0.80,
    "Pluto": 0.84,
    "True Node": 0.90,
}

_PERSONAL_FOCUS = {
    "Ascendant": "your body, identity, boundaries and how other people meet you",
    "Midheaven": "your job, title, authority and public direction",
    "Sun": "your identity, confidence and the role you are choosing to inhabit",
    "Moon": "home, family, habit and what your nervous system has to live with",
    "Mercury": "the message, decision, document or conversation that needs an answer",
    "Venus": "relationships, money, attraction and what you are willing to value",
    "Mars": "effort, conflict, desire and what you are prepared to act on",
    "Jupiter": "growth, confidence, learning and the size of the opportunity",
    "Saturn": "responsibility, limits and what must become durable",
    "Uranus": "freedom, disruption and the rule you no longer want to live inside",
    "Neptune": "hope, projection, imagination and what still needs evidence",
    "Pluto": "power, dependency, control and what can no longer stay superficial",
    "True Node": "direction, repetition and the route that keeps asking for a decision",
}

_ASPECT_TARGETS = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}

_ASPECT_PERSONAL_WEIGHT = {
    "conjunction": 1.00,
    "opposition": 0.98,
    "square": 0.95,
    "trine": 0.82,
    "sextile": 0.74,
}


def featured_signals(
    signals: Iterable[MajorEventSignal],
    product: str,
    *,
    limit: int = 8,
    opportunity_slots: int = 2,
) -> tuple[MajorEventSignal, ...]:
    """Choose headline cards while explicitly reserving room for opportunity."""
    selected = list(
        period_priority_signals(
            signals,
            product,
            limit=max(limit, 1),
            opportunity_slots=max(opportunity_slots, 0),
        )
    )
    if not selected:
        return ()

    def mandatory_key(item: MajorEventSignal):
        return (
            -int(item.must_surface_in(product)),
            -_TIER_RANK.get(item.tier, 0),
            -item.sky_score,
            item.event_date,
        )

    opportunities = sorted(
        (item for item in selected if item.opportunity),
        key=lambda item: (-item.sky_score, item.event_date),
    )[:max(0, opportunity_slots)]

    structural = sorted(
        (
            item for item in selected
            if item not in opportunities
            and (item.tier == "S" or item.must_surface_in(product))
        ),
        key=mandatory_key,
    )

    featured: list[MajorEventSignal] = []
    structural_slots = max(0, int(limit) - len(opportunities))
    for item in structural[:structural_slots]:
        if item not in featured:
            featured.append(item)

    for item in opportunities:
        if item not in featured and len(featured) < int(limit):
            featured.append(item)

    rest = sorted(
        (item for item in selected if item not in featured),
        key=lambda item: (
            -_TIER_RANK.get(item.tier, 0),
            -int(item.opportunity),
            -item.sky_score,
            item.event_date,
        ),
    )
    for item in rest:
        if len(featured) >= int(limit):
            break
        featured.append(item)

    return tuple(sorted(featured, key=lambda item: (item.event_date, -item.sky_score)))


def _personal_orb_limit(signal: MajorEventSignal, natal_target: str) -> float:
    if signal.event_class == "eclipse":
        return 4.0 if natal_target in {"Ascendant", "Midheaven", "Sun", "Moon"} else 3.0
    if signal.event_class == "lunation":
        return 3.0 if natal_target in {"Ascendant", "Midheaven", "Sun", "Moon"} else 2.2
    if signal.event_class in {"station", "ingress", "structural_alignment"}:
        return 2.5 if natal_target in {"Ascendant", "Midheaven", "Sun", "Moon"} else 2.0
    if signal.event_class == "cazimi":
        return 2.0
    if signal.opportunity:
        return 2.0
    return 1.5


def _snapshot_positions(snapshot) -> tuple:
    values = list(getattr(snapshot, "positions", ()) or ())
    for angle_name in ("ascendant", "midheaven"):
        value = getattr(snapshot, angle_name, None)
        if value is not None:
            values.append(value)
    unique = {}
    for item in values:
        planet = str(getattr(item, "planet", "") or "")
        if planet:
            unique[planet] = item
    return tuple(unique.values())


def _closest_personal_contact(
    transit_longitude: float,
    natal_longitude: float,
) -> tuple[str, float]:
    distance = angular_distance(float(transit_longitude), float(natal_longitude))
    name, target = min(
        _ASPECT_TARGETS.items(),
        key=lambda pair: abs(distance - pair[1]),
    )
    return name, abs(distance - target)


def personalize_major_signals(
    signals: Iterable[MajorEventSignal],
    snapshot,
    timezone_name: str,
    *,
    limit: int = 10,
) -> tuple[PersonalEventActivation, ...]:
    """Overlay shared major events on a natal chart with a separate personal score."""
    targets = _snapshot_positions(snapshot)
    if not targets:
        return ()

    values: list[PersonalEventActivation] = []
    day_positions = {}

    for signal in signals:
        if signal.event_date not in day_positions:
            day_positions[signal.event_date] = positions_for_date(signal.event_date, timezone_name)
        transits = day_positions[signal.event_date]

        transit_names = [
            planet for planet in signal.planets
            if planet in transits and not (signal.event_class == "eclipse" and planet == "True Node")
        ]
        if not transit_names:
            continue

        for target in targets:
            natal_target = str(getattr(target, "planet", "") or "")
            natal_longitude = float(getattr(target, "longitude", 0.0) or 0.0)
            allowed = _personal_orb_limit(signal, natal_target)

            best = None
            for transit_planet in transit_names:
                transit_longitude = float(transits[transit_planet].longitude)
                aspect, orb = _closest_personal_contact(transit_longitude, natal_longitude)
                if orb > allowed:
                    continue
                aspect_weight = _ASPECT_PERSONAL_WEIGHT.get(aspect, 0.7)
                target_weight = _PERSONAL_TARGET_WEIGHT.get(natal_target, 0.75)
                exactness = max(0.0, 1.0 - orb / max(allowed, 0.1))
                event_bonus = {
                    "eclipse": 12.0,
                    "structural_alignment": 10.0,
                    "station": 8.0,
                    "ingress": 7.0,
                    "cazimi": 6.0,
                    "lunation": 5.0,
                    "opportunity": 5.0,
                }.get(signal.event_class, 3.0)
                personal_score = min(
                    100.0,
                    38.0
                    + exactness * 34.0
                    + target_weight * 12.0
                    + aspect_weight * 8.0
                    + event_bonus,
                )
                candidate = (personal_score, -orb, transit_planet, aspect)
                if best is None or candidate > best[0]:
                    best = (candidate, personal_score, orb, transit_planet, aspect)

            if best is None:
                continue

            _, personal_score, orb, transit_planet, aspect = best
            if personal_score < 64.0 and signal.sky_score < 92.0:
                continue
            focus = _PERSONAL_FOCUS.get(
                natal_target,
                "the part of life already asking for a decision",
            )
            interpretation = (
                f"{signal.display_label} also makes a close {aspect} to your natal {natal_target}. "
                f"This is not only shared sky; it lands on {focus}."
            )
            action = signal.action
            values.append(
                PersonalEventActivation(
                    event_date=signal.event_date,
                    display_label=signal.display_label,
                    event_class=signal.event_class,
                    tier=signal.tier,
                    sky_score=signal.sky_score,
                    personal_score=round(personal_score, 3),
                    transit_planet=transit_planet,
                    natal_target=natal_target,
                    aspect=aspect,
                    orb=round(orb, 2),
                    focus=focus,
                    interpretation=interpretation,
                    action=action,
                    opportunity=signal.opportunity,
                )
            )

    values.sort(key=lambda item: (-item.combined_score, item.event_date, item.orb))
    selected: list[PersonalEventActivation] = []
    per_event = {}
    for item in values:
        key = (item.event_date, item.display_label)
        count = per_event.get(key, 0)
        if count >= 4:
            continue
        selected.append(item)
        per_event[key] = count + 1
        if len(selected) >= max(1, int(limit)):
            break

    return tuple(sorted(selected, key=lambda item: (item.event_date, -item.combined_score)))


def personalize_serialized_signals(
    values: Iterable[dict],
    snapshot,
    timezone_name: str,
    *,
    limit: int = 10,
) -> tuple[PersonalEventActivation, ...]:
    signals = []
    for value in values or ():
        signal = parse_serialized_signal(dict(value or {}))
        if signal is not None:
            signals.append(signal)
    return personalize_major_signals(signals, snapshot, timezone_name, limit=limit)


def event_presentation_group(signal: MajorEventSignal, product: str = "") -> str:
    """Customer hierarchy. Importance stays visible without making every event equal."""
    event_class = str(getattr(signal, "event_class", "") or "")
    if event_class == "eclipse":
        return "TURNING POINT"
    if event_class == "cazimi":
        return "CLARITY POINT"
    if event_class in {"station", "ingress", "structural_alignment"}:
        return "STRUCTURAL SHIFT"
    if bool(getattr(signal, "opportunity", False)):
        return "OPENING"
    if event_class == "lunation":
        return "LUNATION"
    return "SKY EVENT"


def split_priority_signals(
    signals: Iterable[MajorEventSignal],
    product: str,
    *,
    limit: int = 10,
    opportunity_slots: int = 2,
) -> tuple[tuple[MajorEventSignal, ...], tuple[MajorEventSignal, ...], tuple[MajorEventSignal, ...]]:
    """Return turning points, openings and supporting dates without dropping selected events."""
    selected = period_priority_signals(
        signals, product, limit=limit, opportunity_slots=opportunity_slots
    )
    turning = []
    openings = []
    other = []
    for signal in selected:
        group = event_presentation_group(signal, product)
        if group in {"TURNING POINT", "CLARITY POINT"}:
            turning.append(signal)
        elif group == "OPENING":
            openings.append(signal)
        else:
            other.append(signal)
    return tuple(turning), tuple(openings), tuple(other)


def group_personal_activations(
    values: Iterable[PersonalEventActivation],
) -> tuple[tuple[PersonalEventActivation, ...], ...]:
    """One shared event, many natal contacts. Never make one eclipse look like several events."""
    groups: dict[tuple[date, str], list[PersonalEventActivation]] = {}
    for item in values or ():
        groups.setdefault((item.event_date, item.display_label), []).append(item)
    ordered = []
    for key, items in groups.items():
        items.sort(key=lambda item: (-item.combined_score, item.orb, item.natal_target))
        ordered.append(tuple(items))
    ordered.sort(key=lambda group: (group[0].event_date, -max(item.combined_score for item in group)))
    return tuple(ordered)


def group_serialized_personal_activations(values: Iterable[dict]) -> tuple[tuple[dict, ...], ...]:
    """Serialized equivalent used by report objects and renderers."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for raw in values or ():
        item = dict(raw or {})
        key = (str(item.get("event_date") or ""), str(item.get("display_label") or ""))
        groups.setdefault(key, []).append(item)
    ordered = []
    for key, items in groups.items():
        items.sort(key=lambda item: (
            -float(item.get("combined_score", item.get("personal_score", 0.0)) or 0.0),
            float(item.get("orb", 99.0) or 99.0),
            str(item.get("natal_target") or ""),
        ))
        ordered.append(tuple(items))
    ordered.sort(key=lambda group: (str(group[0].get("event_date") or ""), -max(float(item.get("combined_score", item.get("personal_score", 0.0)) or 0.0) for item in group)))
    return tuple(ordered)


def parse_serialized_signal(value: dict) -> MajorEventSignal | None:
    try:
        event_date = date.fromisoformat(str(value.get("event_date") or ""))
        return MajorEventSignal(
            event_date=event_date,
            source_kind=str(value.get("source_kind") or ""),
            event_class=str(value.get("event_class") or ""),
            tier=str(value.get("tier") or ""),
            sky_score=float(value.get("sky_score") or 0.0),
            technical_label=str(value.get("technical_label") or ""),
            display_label=str(value.get("display_label") or ""),
            source_title=str(value.get("source_title") or ""),
            planets=tuple(value.get("planets") or ()),
            houses=tuple(int(item) for item in (value.get("houses") or ())),
            polarity=str(value.get("polarity") or ""),
            importance=float(value.get("importance") or 0.0),
            opportunity=bool(value.get("opportunity")),
            visible_products=frozenset(value.get("visible_products") or ()),
            must_surface_products=frozenset(value.get("must_surface_products") or ()),
            headline=str(value.get("headline") or ""),
            line_one=str(value.get("line_one") or ""),
            line_two=str(value.get("line_two") or ""),
            action=str(value.get("action") or ""),
            watch=str(value.get("watch") or ""),
        )
    except Exception:
        return None


def select_serialized_signals(
    values: Iterable[dict],
    product: str,
    *,
    limit: int = 8,
    opportunity_slots: int = 2,
) -> tuple[MajorEventSignal, ...]:
    signals = []
    for value in values or ():
        signal = parse_serialized_signal(dict(value or {}))
        if signal is not None:
            signals.append(signal)
    return period_priority_signals(
        signals,
        product,
        limit=limit,
        opportunity_slots=opportunity_slots,
    )
