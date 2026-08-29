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

from dataclasses import asdict, dataclass, replace
from datetime import date
from functools import lru_cache
import re
from typing import Iterable

from astrology_engine import Event, SIGNS, angular_distance, period_events, positions_for_date, whole_sign_house
from solar_cycle import solar_anchor_dates


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



_STATION_COPY = {
    ("Jupiter", True): (
        "THE OPENING NEEDS A SECOND LOOK.",
        "Jupiter has stationed retrograde. Growth does not vanish; it asks you to separate useful expansion from excess.",
        "Revisit the person, price, plan or opportunity that looked larger at first glance. Keep what still increases future choice.",
        "Do not abandon the opening. Recheck whether bigger is actually better and which part deserves more time.",
        "Do not confuse slower growth with lost opportunity.",
    ),
    ("Jupiter", False): (
        "THE OPENING CAN MOVE AGAIN.",
        "Jupiter has stationed direct. An option that survived the second look can begin moving outward again.",
        "Reopen the route that still makes sense. Use the part that gained value when you reviewed it.",
        "Move on the opportunity that survived scrutiny. Leave the inflated version behind.",
        "Do not mistake renewed momentum for permission to expand everything.",
    ),
    ("Saturn", True): (
        "THE RULE NEEDS REVISION.",
        "Saturn has stationed retrograde. Responsibility remains, but the terms, limit or structure need another inspection.",
        "Check which duty still has purpose and which one survives only because nobody has renegotiated it.",
        "Review the boundary, deadline or obligation before you renew it by habit.",
        "Do not call endless endurance responsibility.",
    ),
    ("Saturn", False): (
        "THE STANDARD CAN HOLD NOW.",
        "Saturn has stationed direct. The review is ready to become a boundary, timetable or durable decision.",
        "Use what the delay clarified. Put the responsibility into terms that can actually last.",
        "Turn the lesson into a boundary, deadline or responsibility you can maintain.",
        "Do not rebuild the same burden with cleaner paperwork.",
    ),
    ("Uranus", True): (
        "FREEDOM NEEDS A BETTER DESIGN.",
        "Uranus has stationed retrograde. The need for change remains, but the first escape route may not be the best one.",
        "Notice where freedom has become more expensive than expected. Revise the arrangement before rebellion becomes the only exit.",
        "Test a freer structure before you destroy the one that still protects something useful.",
        "Do not mistake impatience for a complete plan.",
    ),
    ("Uranus", False): (
        "THE CHANGE CAN LEAVE THE DRAWING BOARD.",
        "Uranus has stationed direct. A change that survived review can start becoming practical rather than merely disruptive.",
        "Use the route that creates more room without recreating the old restriction somewhere else.",
        "Move on the experiment that proved useful. Keep the part of the old structure that still earns its place.",
        "Do not make novelty the measure of freedom.",
    ),
    ("Neptune", True): (
        "THE STORY NEEDS VERIFICATION.",
        "Neptune has stationed retrograde. Imagination remains useful, but the story now needs a closer factual audit.",
        "Recheck the promise, fear or ideal that has been carrying too much certainty.",
        "Separate what you know from what you hope, fear or infer. Keep only the version that can survive evidence.",
        "Do not turn uncertainty into proof.",
    ),
    ("Neptune", False): (
        "KEEP THE DREAM THAT SURVIVED THE FACTS.",
        "Neptune has stationed direct. What remained meaningful through the review can begin moving again without needing false certainty.",
        "Keep the vision that survived contact with reality. Drop the version that required you not to look too closely.",
        "Use imagination on what the facts can support.",
        "Do not restore an illusion just because the fog feels familiar.",
    ),
    ("Pluto", True): (
        "POWER MOVED. REVIEW THE TERMS.",
        "Pluto has stationed retrograde. The deeper power question turns inward: who can decide, withhold, leave or change the terms?",
        "Review the dependency or leverage that would be expensive to carry forward unchanged.",
        "Name where the balance of power has already moved. Stop negotiating with the old map.",
        "Do not tighten control simply because the old arrangement feels less secure.",
    ),
    ("Pluto", False): (
        "THE POWER SHIFT IS NO LONGER THEORETICAL.",
        "Pluto has stationed direct. A change in leverage that survived review can begin producing visible consequences.",
        "Act on the power structure that exists now, not the one you wish still existed.",
        "Change the term, boundary or dependency that no longer matches the real balance.",
        "Do not restore the old order just because it is familiar.",
    ),
    ("Mercury", True): (
        "THE MESSAGE NEEDS A SECOND PASS.",
        "Mercury has stationed retrograde. Communication, logistics and decisions need review before speed becomes useful again.",
        "Re-read the message, document, booking or assumption that looked settled.",
        "Correct the detail before you repeat the decision.",
        "Do not confuse repetition with confirmation.",
    ),
    ("Mercury", False): (
        "THE ANSWER CAN MOVE AGAIN.",
        "Mercury has stationed direct. A stalled message, decision or logistical problem can begin moving outward again.",
        "Use what the review exposed. Confirm the detail that still matters.",
        "Send the corrected version. Do not resend the old assumption.",
        "Do not rush simply because movement returned.",
    ),
    ("Venus", True): (
        "VALUE NEEDS A SECOND LOOK.",
        "Venus has stationed retrograde. Relationships, money and desire need review without assuming the attraction or value has disappeared.",
        "Recheck reciprocity, price and what you actually want once attention stops doing the deciding.",
        "Keep what still feels valuable after the glamour is removed.",
        "Do not confuse being wanted with being well matched.",
    ),
    ("Venus", False): (
        "VALUE CAN MOVE FORWARD AGAIN.",
        "Venus has stationed direct. A relationship, money or value question that survived review can begin moving again.",
        "Use what the pause clarified about reciprocity, cost and desire.",
        "Choose what still deserves your time, money or affection.",
        "Do not restore the old terms merely because the feeling returned.",
    ),
    ("Mars", True): (
        "FORCE NEEDS A DIFFERENT METHOD.",
        "Mars has stationed retrograde. Drive and conflict turn inward enough to expose where effort is being wasted.",
        "Recheck the objective before adding more force.",
        "Change the method before you recommit the energy.",
        "Do not use frustration as proof that the goal still deserves pursuit.",
    ),
    ("Mars", False): (
        "THE ENGINE CAN MOVE AGAIN.",
        "Mars has stationed direct. Effort that survived the review can begin moving outward with more precision.",
        "Use the method that wasted less force during the slowdown.",
        "Act on the objective that still deserves the energy.",
        "Do not restart the old fight simply because momentum returned.",
    ),
}


def _station_copy(planet: str, retrograde: bool) -> tuple[str, str, str, str, str]:
    return _STATION_COPY.get(
        (str(planet or ""), bool(retrograde)),
        (
            "THE MOTION CHANGED. REVIEW THE PLAN." if retrograde else "THE MOTION CHANGED. USE WHAT THE REVIEW TAUGHT YOU.",
            (
                f"{planet} has stationed retrograde. The issue remains active, but the next useful move is review."
                if retrograde
                else f"{planet} has stationed direct. A question that has been looping can begin moving outward again."
            ),
            "Recheck what the cycle actually taught you before you add another layer.",
            (
                "Revise the part that became expensive to carry unchanged."
                if retrograde
                else "Act on the revision that still makes sense after the review."
            ),
            "Do not treat a change of motion as a verdict by itself.",
        ),
    )


_SOLAR_ANCHOR_COPY = {
    "March Equinox": (
        "THE SOLAR YEAR OPENS.",
        "The March Equinox opens Luna's tropical solar year as the Sun enters Aries. This is the first fixed reference point of the annual solar cycle.",
        "The next quarter is about initiation: decide what deserves a beginning before momentum chooses for you.",
        "Name what starts now. Give the new direction one concrete first move.",
        "Do not drag last cycle's unfinished business forward by default.",
    ),
    "June Solstice": (
        "THE SOLAR YEAR REACHES ITS FIRST TURN.",
        "The June Solstice marks a foundational solar turning point as the Sun enters Cancer. What began after the March Equinox now has to be protected, sustained or given a real base.",
        "The next quarter tests whether growth has enough support underneath it to keep developing.",
        "Protect what is worth carrying. Strengthen the part that has to hold the next stage.",
        "Do not confuse expansion with support; growth still needs somewhere to land.",
    ),
    "September Equinox": (
        "THE SOLAR YEAR REBALANCES.",
        "The September Equinox marks a foundational solar turning point as the Sun enters Libra. What has developed since June now meets reciprocity, consequence and the terms created with other people.",
        "The next quarter asks what must be corrected, shared, negotiated or brought back into balance.",
        "Put the terms beside the promise. Keep what can carry reciprocity and correct what cannot.",
        "Do not keep an arrangement merely because it survived the previous quarter.",
    ),
    "December Solstice": (
        "THE SOLAR YEAR TURNS TOWARD STRUCTURE.",
        "The December Solstice marks a foundational solar turning point as the Sun enters Capricorn. The year now asks what is durable enough to structure, complete or carry into the next cycle.",
        "The next quarter favours consolidation, redesign and release before the March Equinox opens the solar year again.",
        "Keep what can survive the next cycle. Give it structure; release what cannot justify the load.",
        "Do not preserve something simply because time has already been spent on it.",
    ),
}


def _solar_anchor_signal(
    gate_day: date,
    gate_name: str,
    ingress_sign: str,
    strategic_question: str,
    native_sign: str,
) -> MajorEventSignal:
    headline, line_one, line_two, action, watch = _SOLAR_ANCHOR_COPY[gate_name]
    try:
        house = whole_sign_house(SIGNS.index(ingress_sign), SIGNS.index(native_sign))
        houses = (int(house),)
    except Exception:
        houses = ()
    display_label = f"{gate_name} · Sun enters {ingress_sign}"
    return MajorEventSignal(
        event_date=gate_day,
        source_kind="solar_anchor",
        event_class="solar_anchor",
        tier="FOUNDATION",
        sky_score=120.0,
        technical_label=f"Sun enters {ingress_sign}",
        display_label=display_label,
        source_title=display_label,
        planets=("Sun",),
        houses=houses,
        polarity="foundation",
        importance=10.0,
        opportunity=False,
        visible_products=PRODUCTS,
        must_surface_products=PRODUCTS,
        headline=headline,
        line_one=line_one,
        line_two=f"{line_two} {strategic_question}".strip(),
        action=action,
        watch=watch,
    )


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
        return _station_copy(planet, retrograde)

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
            "Two slow-moving planets have reached an exact major aspect. This belongs to the longer background of the year, not just today's mood.",
            "Watch what faster events expose around this date; they can make the slower change visible in ordinary life.",
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



def _sequence_repeated_signals(signals: Iterable[MajorEventSignal]) -> tuple[MajorEventSignal, ...]:
    """Give repeated exact passes a chronology instead of repeating identical copy."""
    values = list(signals)
    groups: dict[tuple[str, tuple[str, ...], str], list[MajorEventSignal]] = {}
    for signal in values:
        if signal.event_class not in {"opportunity", "structural_alignment"} and not signal.opportunity:
            continue
        key = (
            signal.event_class,
            tuple(sorted(signal.planets)),
            re.sub(r"\s+", " ", signal.display_label.lower()).strip(),
        )
        groups.setdefault(key, []).append(signal)

    replacements: dict[tuple[date, str], MajorEventSignal] = {}
    for group in groups.values():
        if len(group) < 2:
            continue
        ordered = sorted(group, key=lambda item: item.event_date)
        for index, signal in enumerate(ordered):
            if index == 0:
                continue
            if index == 1:
                line_one = (
                    "The same pattern has returned. This pass is less about discovering the option "
                    "and more about proving which version actually works."
                    if signal.opportunity
                    else
                    "The same structural pattern has returned. Compare what changed after the first pass before you call this repetition."
                )
                action = (
                    "Return to the option that survived the first pass. Put dates, terms or a commitment behind it."
                    if signal.opportunity
                    else
                    "Compare the first pass with this one. Change the term or structure that failed to improve."
                )
            else:
                line_one = (
                    "The pattern is exact again. What keeps working across several passes has earned more trust than the first burst of enthusiasm."
                    if signal.opportunity
                    else
                    "The structural pattern is exact again. Repetition is now evidence about what has and has not changed."
                )
                action = (
                    "Formalise the part that proved workable. Drop the version that only looked good at the beginning."
                    if signal.opportunity
                    else
                    "Act on the repeated evidence. Stop carrying the version that each pass keeps disproving."
                )
            replacements[(signal.event_date, signal.source_title)] = replace(
                signal,
                line_one=line_one,
                action=action,
            )

    return tuple(
        replacements.get((signal.event_date, signal.source_title), signal)
        for signal in values
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

    sequenced = _sequence_repeated_signals(unique.values())
    return tuple(
        sorted(
            sequenced,
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
    """Return the complete shared-sky registry, anchored first by the Sun.

    Equinoxes and solstices are Luna's foundational solar clock. They are
    injected here so Daily, Weekly, Monthly, Yearly and Personal Timing cannot
    rank them away even though the lower-level astrology event engine treats
    them as ordinary Sun ingresses.
    """
    signals = list(classify_major_events(period_events(start, end, native_sign, timezone_name)))
    for gate_day, gate_name, ingress_sign, question in solar_anchor_dates(start, end, timezone_name):
        signals.append(
            _solar_anchor_signal(gate_day, gate_name, ingress_sign, question, native_sign)
        )

    unique: dict[tuple[date, str], MajorEventSignal] = {}
    for signal in signals:
        key = (signal.event_date, signal.source_title)
        if key not in unique or signal.sky_score > unique[key].sky_score:
            unique[key] = signal
    return tuple(sorted(unique.values(), key=lambda item: (item.event_date, -item.sky_score, item.display_label)))


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



_TIER_RANK = {"FOUNDATION": 7, "S": 6, "A+": 5, "A": 4, "A-": 3, "B+": 2, "B": 1}

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
    "Ascendant": "how you show up, where you set boundaries and what version of you other people are meeting",
    "Midheaven": "the job, title or public responsibility attached to your name",
    "Sun": "the role, identity or direction that still deserves your energy",
    "Moon": "home, family, habit and the routine your nervous system has to live with",
    "Mercury": "the message, document, conversation or decision that needs a clear answer",
    "Venus": "the person, price or relationship value you are choosing",
    "Mars": "the workload, conflict or desire that makes you act",
    "Jupiter": "the larger option and whether your actual life has room for it",
    "Saturn": "the responsibility, deadline or limit that needs proper terms",
    "Uranus": "the rule or arrangement that no longer leaves enough room",
    "Neptune": "the promise, fear or story that still needs evidence",
    "Pluto": "the dependency, leverage or power arrangement that can no longer stay vague",
    "True Node": "the unfamiliar route that becomes possible when the old one stops fitting",
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
    if signal.event_class == "solar_anchor":
        return 3.0 if natal_target in {"Ascendant", "Midheaven", "Sun", "Moon"} else 2.2
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



_PERSONAL_TARGET_SHORT = {
    "Ascendant": "how you show up and set boundaries",
    "Midheaven": "work and public responsibility",
    "Sun": "identity and direction",
    "Moon": "home and emotional security",
    "Mercury": "the conversation or decision",
    "Venus": "what you value in love or money",
    "Mars": "effort, conflict and the move you are making",
    "Jupiter": "growth and the larger option",
    "Saturn": "responsibility and limits",
    "Uranus": "freedom and the rule that needs changing",
    "Neptune": "the story that still needs evidence",
    "Pluto": "power, dependency and leverage",
    "True Node": "the route you are growing toward",
}


def _personal_activation_interpretation(
    signal: MajorEventSignal,
    natal_target: str,
    aspect: str,
    focus: str,
) -> str:
    planet = signal.planets[0] if signal.planets else ""
    target_short = _PERSONAL_TARGET_SHORT.get(natal_target, focus)

    if signal.event_class == "solar_anchor":
        gate_name = signal.display_label.split(" · ", 1)[0]
        return (
            f"{gate_name} makes {target_short} part of the new solar quarter. "
            "Use the contact as a three-month reference point rather than a one-day prediction."
        )

    if signal.event_class == "eclipse":
        if natal_target == "Pluto":
            return (
                "An old power arrangement becomes harder to keep half-hidden. "
                "Notice who controls access, money, information or the terms of staying."
            )
        if natal_target == "Moon":
            return (
                "Home and emotional security are directly involved. "
                "Do not agree to a new beginning or ending that your private life cannot actually carry."
            )
        if natal_target == "Mercury":
            return (
                "The eclipse reaches the conversation, document or decision itself. "
                "Say what has become unavoidable, then leave room for new facts before making the irreversible move."
            )
        if natal_target == "Venus":
            return (
                "Love, money or value is part of the turning point. "
                "Watch whether attraction and reciprocity still point in the same direction once the consequences are visible."
            )
        return (
            f"The eclipse makes {target_short} part of the turning point. "
            "Name what has become impossible to keep half-decided."
        )

    if signal.event_class == "station":
        retrograde = "retrograde" in signal.display_label.lower()
        if planet == "Jupiter" and natal_target == "Venus":
            return (
                "An opening around relationships, money or value has paused for a second look. "
                "The question is not whether more is available, but which option still looks valuable once the excitement settles."
                if retrograde
                else
                "A relationship, money or value opening can move again after the second look. "
                "Use the option that gained value under review rather than the one that merely looked abundant."
            )
        if planet == "Uranus" and natal_target == "Pluto":
            return (
                "Freedom and power have become the same argument. "
                "Notice where control is already shifting before you make the break irreversible."
                if retrograde
                else
                "A power shift that spent months under review can now produce visible change. "
                "Move where greater freedom also improves the real balance of power."
            )
        if planet == "Pluto" and natal_target == "Pluto":
            return (
                "A long power cycle is turning inward. "
                "Review the dependency or control pattern that no longer matches where the leverage actually sits."
                if retrograde
                else
                "A long power cycle can begin moving outward again. "
                "Act from the balance of power that survived the review."
            )
        return (
            f"The station makes {target_short} unusually exact. "
            + (
                "Use the pause to revise the assumption before you recommit."
                if retrograde
                else
                "Use the resumed motion on the version that survived the review."
            )
        )

    if signal.event_class == "ingress":
        return (
            f"The sign change becomes personal through {target_short}. "
            "Watch what changes in ordinary life as the new cycle begins asking for different terms."
        )

    if signal.event_class == "cazimi":
        return (
            f"The clarity point reaches {target_short}. "
            "Use the cleaner signal to make the sentence, choice or value judgment more exact."
        )

    if signal.event_class == "structural_alignment":
        return (
            f"The longer collective shift becomes personal through {target_short}. "
            "Do not react to the headline; notice what is becoming more possible, more expensive or harder to keep unchanged in your own life."
        )

    if signal.opportunity:
        return (
            f"The opening becomes personal through {target_short}. "
            "Use the extra room on something that increases future choice rather than merely present activity."
        )

    return (
        f"{target_short[:1].upper() + target_short[1:]} is directly involved. "
        "Use the exact contact to make the practical consequence visible."
    )


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
            interpretation = _personal_activation_interpretation(
                signal,
                natal_target,
                aspect,
                focus,
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
    planets = set(getattr(signal, "planets", ()) or ())
    if event_class == "solar_anchor":
        return "SOLAR ANCHOR"
    if event_class == "eclipse":
        return "TURNING POINT"
    if event_class == "cazimi":
        return "CLARITY POINT"
    if bool(getattr(signal, "opportunity", False)):
        return "OPENING"
    if event_class == "station":
        return "PIVOT"
    if event_class == "ingress" and planets & INNER_PLANETS:
        return "TRIGGER"
    if event_class in {"ingress", "structural_alignment"}:
        return "STRUCTURAL SHIFT"
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
        if group in {"SOLAR ANCHOR", "TURNING POINT", "CLARITY POINT"}:
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
