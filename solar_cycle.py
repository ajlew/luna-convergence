from __future__ import annotations

from calendar import monthrange
from dataclasses import asdict, dataclass
from datetime import date, timedelta
import math
import re
from typing import Iterable, Mapping

from astrology_engine import SIGNS, positions_for_date, whole_sign_house
from date_display import human_date


@dataclass(frozen=True)
class CityLocation:
    name: str
    country: str
    latitude: float
    longitude: float
    timezone: str


@dataclass(frozen=True)
class SolarConvergence:
    calculation_date: str
    native_sign: str
    solar_longitude: float
    solar_sign: str
    solar_quarter: str
    solar_process: str
    practical_phase: str
    current_solar_gate: str
    next_solar_gate: str
    next_gate_date: str
    days_to_next_gate: int
    hemisphere: str
    local_season: str
    daylight_minutes: float
    daylight_change: float
    light_direction: str
    city: str
    country: str
    location_basis: str
    activated_house: int
    activated_house_name: str
    start_solar_sign: str
    end_solar_sign: str
    start_house: int
    end_house: int
    solar_transition: str
    main_focus: str
    headline: str
    meaning: tuple[str, ...]
    focus_meaning: str
    opportunity: str
    risk: str
    action: str
    solar_rule: str
    equation: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SolarYearChapter:
    name: str
    gate: str
    start_date: str
    end_date: str
    signs: tuple[str, str, str]
    houses: tuple[int, int, int]
    local_season: str
    process: str
    strategic_question: str
    focus_direction: str

    def to_dict(self) -> dict:
        return asdict(self)


HOUSE_NAMES = {
    1: "identity and personal direction",
    2: "money, value and security",
    3: "communication and everyday decisions",
    4: "home, family and private foundations",
    5: "romance, pleasure and creativity",
    6: "work, health and daily systems",
    7: "relationships, agreements and other people",
    8: "trust, intimacy and shared finances",
    9: "travel, learning, publishing and wider horizons",
    10: "career, authority and visible results",
    11: "friends, communities and future plans",
    12: "rest, closure and private reflection",
}

HOUSE_EQUATION = {
    1: "identity taking form",
    2: "value becoming measurable",
    3: "information becoming a decision",
    4: "a private foundation becoming secure",
    5: "desire becoming creative expression",
    6: "an idea becoming a sustainable routine",
    7: "a connection becoming an agreement",
    8: "intensity becoming accountable trust",
    9: "knowledge becoming a larger direction",
    10: "knowledge becoming a public result",
    11: "a possibility becoming a shared future",
    12: "experience becoming closure and insight",
}

SOLAR_QUARTERS = {
    "Aries": ("Emergence", "Initiate", "Beginning"),
    "Taurus": ("Emergence", "Stabilise", "Beginning"),
    "Gemini": ("Emergence", "Communicate", "Beginning"),
    "Cancer": ("Expression", "Protect", "Expansion"),
    "Leo": ("Expression", "Create", "Expansion"),
    "Virgo": ("Expression", "Refine", "Expansion"),
    "Libra": ("Rebalancing", "Relate", "Evaluation"),
    "Scorpio": ("Rebalancing", "Transform", "Evaluation"),
    "Sagittarius": ("Rebalancing", "Understand", "Evaluation"),
    "Capricorn": ("Gestation", "Structure", "Closure"),
    "Aquarius": ("Gestation", "Renew", "Closure"),
    "Pisces": ("Gestation", "Release", "Closure"),
}

QUARTER_SIGNS = {
    "Emergence": ("Aries", "Taurus", "Gemini"),
    "Expression": ("Cancer", "Leo", "Virgo"),
    "Rebalancing": ("Libra", "Scorpio", "Sagittarius"),
    "Gestation": ("Capricorn", "Aquarius", "Pisces"),
}

GATES = (
    ("March Equinox", 0, "Aries", "What must begin?"),
    ("June Solstice", 90, "Cancer", "What must be protected and sustained?"),
    ("September Equinox", 180, "Libra", "What must be corrected or reciprocated?"),
    ("December Solstice", 270, "Capricorn", "What must survive the next cycle?"),
)

SOLAR_CLOCK_PRINCIPLE = "The Sun is Luna's primary natural clock."
SOLAR_SEQUENCE = "Aries → Taurus → Gemini → Cancer → Leo → Virgo → Libra → Scorpio → Sagittarius → Capricorn → Aquarius → Pisces"
GATE_LABELS = {
    "March Equinox": "Aries Gate · March Equinox",
    "June Solstice": "Cancer Gate · June Solstice",
    "September Equinox": "Libra Gate · September Equinox",
    "December Solstice": "Capricorn Gate · December Solstice",
}


def solar_gate_label(gate_name: str) -> str:
    return GATE_LABELS.get(str(gate_name), str(gate_name))


def local_light_statement(*, city: str, direction: str, change: float) -> str:
    if direction == "Near a solar turning point":
        movement = "is near a solar turning point"
    elif abs(change) < 0.05:
        movement = "is almost steady"
    else:
        movement = f"is {direction.lower()} by approximately {abs(change):.1f} minutes per day"
    return (
        f"In {city}, daylight {movement}. "
        "That local light direction does not alter the Aries-to-Pisces solar sequence."
    )


SOLAR_CYCLE_COMPACT = "Aries Gate → 12-sign solar cycle → Aries Gate"
SOLAR_GATE_CONVERGENCE_WINDOW_DAYS = 5


def _event_value(event: object, key: str, default=None):
    if isinstance(event, dict):
        return event.get(key, default)
    return getattr(event, key, default)


def _event_date_value(event: object) -> date | None:
    raw = _event_value(event, "event_date", "")
    if isinstance(raw, date):
        return raw
    try:
        return date.fromisoformat(str(raw))
    except (TypeError, ValueError):
        return None


def _event_house_values(event: object) -> set[int]:
    values: set[int] = set()
    for item in (_event_value(event, "houses", ()) or ()):
        try:
            values.add(int(item))
        except (TypeError, ValueError):
            continue
    return values


def _event_importance_value(event: object) -> float:
    try:
        return float(_event_value(event, "importance", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def monthly_solar_gate_convergence(
    *,
    solar: Mapping[str, object] | dict,
    trajectory: Mapping[str, object] | dict,
    events: Iterable[object],
    period_start: date,
    period_end: date,
) -> dict:
    """Test whether a cardinal solar gate materially reinforces the monthly story.

    The solar gate never invents a plot. It becomes customer-visible only when:
    1) the gate falls inside the report period; and
    2) the Sun's post-gate life area matches a primary, bridge or result area in
       the independently calculated planetary trajectory; and
    3) nearby astronomical events provide concrete evidence in that same area.

    This keeps the Sun as Luna's reference clock while preserving the faster
    planetary weather as the authority on what is actually happening.
    """
    gate_raw = str(solar.get("next_gate_date") or "")
    try:
        gate_date = date.fromisoformat(gate_raw)
    except ValueError:
        return {"status": "NONE", "material": False, "reason": "No solar gate date was available inside the report."}
    if not (period_start <= gate_date <= period_end):
        return {"status": "NONE", "material": False, "reason": "No cardinal solar gate falls inside this report period."}

    try:
        gate_house = int(solar.get("end_house") or solar.get("activated_house") or 0)
    except (TypeError, ValueError):
        gate_house = 0
    primary = int(trajectory.get("primary_house") or 0) if trajectory.get("primary_house") not in (None, "") else 0
    secondary = int(trajectory.get("secondary_house") or 0) if trajectory.get("secondary_house") not in (None, "") else 0
    bridge = dict(trajectory.get("bridge") or {})
    bridge_house = int(bridge.get("house") or 0) if bridge.get("house") not in (None, "") else 0

    if gate_house and gate_house == secondary:
        matched_role = "result"
        role_weight = 3
    elif gate_house and gate_house == bridge_house:
        matched_role = "bridge"
        role_weight = 2
    elif gate_house and gate_house == primary:
        matched_role = "primary"
        role_weight = 1
    else:
        matched_role = "background"
        role_weight = 0

    nearby: list[tuple[float, date, str]] = []
    for event in events:
        event_date = _event_date_value(event)
        if event_date is None or abs((event_date - gate_date).days) > SOLAR_GATE_CONVERGENCE_WINDOW_DAYS:
            continue
        if gate_house and gate_house not in _event_house_values(event):
            continue
        importance = _event_importance_value(event)
        if importance < 5.0:
            continue
        title = str(_event_value(event, "title", "astronomical event") or "astronomical event")
        nearby.append((importance, event_date, title))

    nearby.sort(key=lambda item: (abs((item[1] - gate_date).days), -item[0], item[1]))
    evidence: list[str] = []
    seen: set[tuple[str, str]] = set()
    for _importance, event_date, title in nearby:
        key = (event_date.isoformat(), title.lower())
        if key in seen:
            continue
        seen.add(key)
        evidence.append(f"{title} on {human_date(event_date)}")
        if len(evidence) >= 4:
            break

    if role_weight >= 3 and len(evidence) >= 2:
        status = "STRONG"
    elif role_weight >= 2 and len(evidence) >= 1:
        status = "MATERIAL"
    elif role_weight >= 1 and len(evidence) >= 2:
        status = "MATERIAL"
    else:
        status = "BACKGROUND"

    material = status in {"MATERIAL", "STRONG"}
    gate_label = solar_gate_label(str(solar.get("next_solar_gate") or "Solar gate"))
    area = HOUSE_NAMES.get(gate_house, "the post-gate life area")
    end_sign = str(solar.get("end_solar_sign") or solar.get("solar_sign") or "the next sign")

    if matched_role == "result":
        alignment = f"the planetary trajectory is independently moving into the same result area: {area}"
    elif matched_role == "bridge":
        alignment = f"the planetary trajectory independently uses {area} as the bridge between its opening and later result"
    elif matched_role == "primary":
        alignment = f"the planetary trajectory is already concentrated in the same primary area: {area}"
    else:
        alignment = f"the solar emphasis moves into {area}, but the planetary trajectory does not independently make that area central"

    evidence_text = "; ".join(evidence)
    if material:
        customer_line = (
            f"The Solar Clock reinforces this turn. At the {gate_label} on {human_date(gate_date)}, "
            f"the Sun moves into {end_sign}, shifting the solar emphasis toward {area}; {alignment}."
        )
        if evidence_text:
            customer_line += f" Nearby Nature confirms the timing: {evidence_text}."
    else:
        customer_line = ""

    return {
        "status": status,
        "material": material,
        "gate_date": gate_date.isoformat(),
        "gate_label": gate_label,
        "gate_house": gate_house,
        "gate_area": area,
        "matched_role": matched_role,
        "evidence": evidence,
        "summary": customer_line if material else f"Solar gate remains background context: {alignment}.",
        "customer_line": customer_line,
        "reason": alignment,
        "window_days": SOLAR_GATE_CONVERGENCE_WINDOW_DAYS,
    }

SIGN_RULES = {
    "Aries": "Begin with a clear direction",
    "Taurus": "make the beginning stable",
    "Gemini": "give the beginning language and movement",
    "Cancer": "protect what has begun to grow",
    "Leo": "let the work be seen",
    "Virgo": "make the visible result dependable",
    "Libra": "test the result through fairness and reciprocity",
    "Scorpio": "remove what cannot survive deeper truth",
    "Sagittarius": "extract meaning and a wider direction",
    "Capricorn": "build the structure that must endure",
    "Aquarius": "redesign the structure for the future",
    "Pisces": "release what the next cycle no longer needs",
}

PHASE_ACTIONS = {
    "Emergence": {
        "opportunity": "Begin one credible step and give it enough structure to continue.",
        "risk": "Starting too many directions before any one of them becomes viable.",
        "action": "Choose the beginning that can still be supported next month.",
    },
    "Expression": {
        "opportunity": "Bring developed work into view and let real feedback refine it.",
        "risk": "Seeking visibility before the structure, capacity or boundaries are ready.",
        "action": "Show the strongest version, then correct what the response reveals.",
    },
    "Rebalancing": {
        "opportunity": "Use relationships, evidence and consequences to improve the result.",
        "risk": "Defending momentum after the facts show that terms or direction need correction.",
        "action": "Measure reciprocity, remove distortion and keep only what remains true.",
    },
    "Gestation": {
        "opportunity": "Consolidate what works, redesign the weak structure and clear the remainder.",
        "risk": "Mistaking quiet preparation for failure or holding a completed cycle open.",
        "action": "Protect the essential structure and release what cannot serve the next cycle.",
    },
}

HOUSE_SOLAR_GUIDANCE = {
    1: {
        "prepare": "clarify the personal direction you actually want",
        "arrive": "choose one self-directed move that makes the new identity tangible",
        "risk": "performing a new identity before it has a workable shape",
    },
    2: {
        "prepare": "name the value, price or resource requirement",
        "arrive": "put the number, budget or personal priority on firmer ground",
        "risk": "expanding the plan without knowing what it costs or what it is worth",
    },
    3: {
        "prepare": "get the facts, words and terms into usable form",
        "arrive": "turn the message, contract or decision into a clear next step",
        "risk": "moving on assumptions when the wording, timing or paperwork is still loose",
    },
    4: {
        "prepare": "stabilise the private foundation",
        "arrive": "make the home, family or location decision support the wider plan",
        "risk": "building outward while the private arrangement underneath it remains unsettled",
    },
    5: {
        "prepare": "give the creative, romantic or joyful opening room to develop",
        "arrive": "choose the version of the spark that has a believable next move",
        "risk": "mistaking excitement, applause or chemistry for a finished structure",
    },
    6: {
        "prepare": "strengthen the routine, workload and practical support system",
        "arrive": "make the week capable of carrying what you want to continue",
        "risk": "asking energy, health or operations to absorb more than the system can sustain",
    },
    7: {
        "prepare": "make your own position clear before negotiating with another person",
        "arrive": "put the relationship, client or agreement into mutual and explicit terms",
        "risk": "letting another person's expectations define the arrangement by default",
    },
    8: {
        "prepare": "name ownership, trust, cost and shared responsibility",
        "arrive": "make the shared-money or obligation structure explicit enough to manage",
        "risk": "assuming trust will compensate for unclear money, ownership or obligations",
    },
    9: {
        "prepare": "turn the wider possibility into an itinerary, application or decision",
        "arrive": "give travel, study, publishing, legal or international plans a usable route forward",
        "risk": "falling in love with the horizon before documents, timing or commitments are workable",
    },
    10: {
        "prepare": "develop the result until it is ready to be judged",
        "arrive": "make the career, role or public outcome visible on terms you can support",
        "risk": "seeking recognition before the responsibilities and consequences are understood",
    },
    11: {
        "prepare": "identify the people, audience or alliance that can genuinely help",
        "arrive": "give the future plan a network and a realistic next milestone",
        "risk": "confusing popularity or group momentum with durable support",
    },
    12: {
        "prepare": "protect enough quiet to finish, recover or understand what is ending",
        "arrive": "close the private chapter without forcing the next public move too early",
        "risk": "keeping a completed pattern alive because silence feels less certain than action",
    },
}


FOCUS_PHASES = {
    "Love and relationships": {
        "Emergence": "A relationship may be beginning or asking for new terms. Look for mutual curiosity and a workable first step.",
        "Expression": "Feelings, attraction or commitment need to become visible through consistent behaviour.",
        "Rebalancing": "The relationship is being tested through reciprocity, boundaries and the consequences of earlier choices.",
        "Gestation": "The connection needs consolidation, redesign or an honest release of a completed pattern.",
    },
    "Career and work": {
        "Emergence": "Work is entering a beginning phase: choose the direction and make the first result viable.",
        "Expression": "Developed work is ready for visibility, evaluation and professional refinement.",
        "Rebalancing": "Results, relationships and market response are testing whether the work creates real value.",
        "Gestation": "Consolidate the operating structure, redesign weak systems and clear work that no longer supports the next cycle.",
    },
    "Career or business": {
        "Emergence": "Work is entering a beginning phase: choose the direction and make the first result viable.",
        "Expression": "Developed work is ready for visibility, evaluation and professional refinement.",
        "Rebalancing": "Results, relationships and market response are testing whether the work creates real value.",
        "Gestation": "Consolidate the operating structure, redesign weak systems and clear work that no longer supports the next cycle.",
    },
    "Money and security": {
        "Emergence": "This is an acquisition and setup phase: establish the number, ownership and recurring cost.",
        "Expression": "Income or value can grow, but expansion must be matched by cash, capacity and clear obligations.",
        "Rebalancing": "Correct pricing, debt, shared costs or assumptions that no longer match the evidence.",
        "Gestation": "Conserve what matters, close leaks and redesign the financial structure for the next cycle.",
    },
    "Home and family": {
        "Emergence": "A new private arrangement or foundation needs a clear beginning and defined responsibilities.",
        "Expression": "The home or family structure is developing and needs protection, visibility and practical support.",
        "Rebalancing": "Expectations, care and responsibility require correction or more equal exchange.",
        "Gestation": "Consolidate the private foundation, redesign weak arrangements and clear a completed chapter.",
    },
    "Home or relocation": {
        "Emergence": "A new private arrangement or foundation needs a clear beginning and defined responsibilities.",
        "Expression": "The home or family structure is developing and needs protection, visibility and practical support.",
        "Rebalancing": "Expectations, care and responsibility require correction or more equal exchange.",
        "Gestation": "Consolidate the private foundation, redesign weak arrangements and clear a completed chapter.",
    },
    "Personal growth": {
        "Emergence": "A new identity is forming. Give it one repeatable behaviour rather than a dramatic declaration.",
        "Expression": "The developing identity needs visible expression and practical refinement.",
        "Rebalancing": "Relationships and consequences are testing which parts of the new identity are genuine.",
        "Gestation": "Integrate what has been learned and release the identity that belongs to the completed cycle.",
    },
    "Personal reinvention": {
        "Emergence": "A new identity is forming. Give it one repeatable behaviour rather than a dramatic declaration.",
        "Expression": "The developing identity needs visible expression and practical refinement.",
        "Rebalancing": "Relationships and consequences are testing which parts of the new identity are genuine.",
        "Gestation": "Integrate what has been learned and release the identity that belongs to the completed cycle.",
    },
    "General overview": {
        "Emergence": "The cycle favours beginning and making the first direction viable.",
        "Expression": "The cycle favours development, visibility and refinement.",
        "Rebalancing": "The cycle favours evaluation, reciprocity and correction.",
        "Gestation": "The cycle favours consolidation, redesign and closure.",
    },
    "General year ahead": {
        "Emergence": "The cycle favours beginning and making the first direction viable.",
        "Expression": "The cycle favours development, visibility and refinement.",
        "Rebalancing": "The cycle favours evaluation, reciprocity and correction.",
        "Gestation": "The cycle favours consolidation, redesign and closure.",
    },
}

CITY_LOCATIONS = {
    "Sydney": CityLocation("Sydney", "Australia", -33.8688, 151.2093, "Australia/Sydney"),
    "Melbourne": CityLocation("Melbourne", "Australia", -37.8136, 144.9631, "Australia/Melbourne"),
    "Brisbane": CityLocation("Brisbane", "Australia", -27.4698, 153.0251, "Australia/Brisbane"),
    "Perth": CityLocation("Perth", "Australia", -31.9523, 115.8613, "Australia/Perth"),
    "Adelaide": CityLocation("Adelaide", "Australia", -34.9285, 138.6007, "Australia/Adelaide"),
    "Canberra": CityLocation("Canberra", "Australia", -35.2809, 149.1300, "Australia/Sydney"),
    "Hobart": CityLocation("Hobart", "Australia", -42.8821, 147.3272, "Australia/Hobart"),
    "Darwin": CityLocation("Darwin", "Australia", -12.4634, 130.8456, "Australia/Darwin"),
    "Auckland": CityLocation("Auckland", "New Zealand", -36.8509, 174.7645, "Pacific/Auckland"),
    "Alotau": CityLocation("Alotau", "Papua New Guinea", -10.3167, 150.4667, "Pacific/Port_Moresby"),
    "Port Moresby": CityLocation("Port Moresby", "Papua New Guinea", -9.4438, 147.1803, "Pacific/Port_Moresby"),
    "Suva": CityLocation("Suva", "Fiji", -18.1248, 178.4501, "Pacific/Fiji"),
    "Manila": CityLocation("Manila", "Philippines", 14.5995, 120.9842, "Asia/Manila"),
    "Jakarta": CityLocation("Jakarta", "Indonesia", -6.2088, 106.8456, "Asia/Jakarta"),
    "Bangkok": CityLocation("Bangkok", "Thailand", 13.7563, 100.5018, "Asia/Bangkok"),
    "Kuala Lumpur": CityLocation("Kuala Lumpur", "Malaysia", 3.1390, 101.6869, "Asia/Kuala_Lumpur"),
    "Hong Kong": CityLocation("Hong Kong", "Hong Kong", 22.3193, 114.1694, "Asia/Hong_Kong"),
    "Taipei": CityLocation("Taipei", "Taiwan", 25.0330, 121.5654, "Asia/Taipei"),
    "Kathmandu": CityLocation("Kathmandu", "Nepal", 27.7172, 85.3240, "Asia/Kathmandu"),
    "Dhaka": CityLocation("Dhaka", "Bangladesh", 23.8103, 90.4125, "Asia/Dhaka"),
    "Karachi": CityLocation("Karachi", "Pakistan", 24.8607, 67.0011, "Asia/Karachi"),
    "Cairo": CityLocation("Cairo", "Egypt", 30.0444, 31.2357, "Africa/Cairo"),
    "Amman": CityLocation("Amman", "Jordan", 31.9539, 35.9106, "Asia/Amman"),
    "Baghdad": CityLocation("Baghdad", "Iraq", 33.3152, 44.3661, "Asia/Baghdad"),
    "Beirut": CityLocation("Beirut", "Lebanon", 33.8938, 35.5018, "Asia/Beirut"),
    "Wellington": CityLocation("Wellington", "New Zealand", -41.2866, 174.7756, "Pacific/Auckland"),
    "London": CityLocation("London", "United Kingdom", 51.5074, -0.1278, "Europe/London"),
    "Dublin": CityLocation("Dublin", "Ireland", 53.3498, -6.2603, "Europe/Dublin"),
    "Paris": CityLocation("Paris", "France", 48.8566, 2.3522, "Europe/Paris"),
    "Berlin": CityLocation("Berlin", "Germany", 52.5200, 13.4050, "Europe/Berlin"),
    "Rome": CityLocation("Rome", "Italy", 41.9028, 12.4964, "Europe/Rome"),
    "New York": CityLocation("New York", "United States", 40.7128, -74.0060, "America/New_York"),
    "Los Angeles": CityLocation("Los Angeles", "United States", 34.0522, -118.2437, "America/Los_Angeles"),
    "Chicago": CityLocation("Chicago", "United States", 41.8781, -87.6298, "America/Chicago"),
    "Toronto": CityLocation("Toronto", "Canada", 43.6532, -79.3832, "America/Toronto"),
    "Vancouver": CityLocation("Vancouver", "Canada", 49.2827, -123.1207, "America/Vancouver"),
    "Cape Town": CityLocation("Cape Town", "South Africa", -33.9249, 18.4241, "Africa/Johannesburg"),
    "Johannesburg": CityLocation("Johannesburg", "South Africa", -26.2041, 28.0473, "Africa/Johannesburg"),
    "Singapore": CityLocation("Singapore", "Singapore", 1.3521, 103.8198, "Asia/Singapore"),
    "Tokyo": CityLocation("Tokyo", "Japan", 35.6762, 139.6503, "Asia/Tokyo"),
    "Seoul": CityLocation("Seoul", "South Korea", 37.5665, 126.9780, "Asia/Seoul"),
    "New Delhi": CityLocation("New Delhi", "India", 28.6139, 77.2090, "Asia/Kolkata"),
    "Dubai": CityLocation("Dubai", "United Arab Emirates", 25.2048, 55.2708, "Asia/Dubai"),
    "Mexico City": CityLocation("Mexico City", "Mexico", 19.4326, -99.1332, "America/Mexico_City"),
    "Sao Paulo": CityLocation("Sao Paulo", "Brazil", -23.5505, -46.6333, "America/Sao_Paulo"),
    "Buenos Aires": CityLocation("Buenos Aires", "Argentina", -34.6037, -58.3816, "America/Argentina/Buenos_Aires"),
    "Greenwich": CityLocation("Greenwich", "United Kingdom", 51.4826, 0.0077, "UTC"),
}

CITY_ALIASES = {
    "nyc": "New York",
    "new york city": "New York",
    "la": "Los Angeles",
    "los angeles ca": "Los Angeles",
    "sydney nsw": "Sydney",
    "melbourne vic": "Melbourne",
    "brisbane qld": "Brisbane",
    "perth wa": "Perth",
    "auckland nz": "Auckland",
    "alotau png": "Alotau",
    "alotau papua new guinea": "Alotau",
    "port moresby png": "Port Moresby",
    "london uk": "London",
    "sao paulo": "Sao Paulo",
    "são paulo": "Sao Paulo",
}

TIMEZONE_DEFAULT_CITY = {
    "Australia/Sydney": "Sydney",
    "Australia/Melbourne": "Melbourne",
    "Australia/Brisbane": "Brisbane",
    "Australia/Perth": "Perth",
    "Australia/Adelaide": "Adelaide",
    "Australia/Hobart": "Hobart",
    "Australia/Darwin": "Darwin",
    "Pacific/Auckland": "Auckland",
    "Pacific/Port_Moresby": "Port Moresby",
    "Europe/London": "London",
    "Europe/Dublin": "Dublin",
    "Europe/Paris": "Paris",
    "Europe/Berlin": "Berlin",
    "Europe/Rome": "Rome",
    "America/New_York": "New York",
    "America/Los_Angeles": "Los Angeles",
    "America/Chicago": "Chicago",
    "America/Toronto": "Toronto",
    "America/Vancouver": "Vancouver",
    "Africa/Johannesburg": "Johannesburg",
    "Asia/Singapore": "Singapore",
    "Asia/Tokyo": "Tokyo",
    "Asia/Seoul": "Seoul",
    "Asia/Kolkata": "New Delhi",
    "Asia/Dubai": "Dubai",
    "America/Mexico_City": "Mexico City",
    "America/Sao_Paulo": "Sao Paulo",
    "America/Argentina/Buenos_Aires": "Buenos Aires",
    "UTC": "Greenwich",
}


def _normalise_city(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def representative_city_name(timezone_name: str) -> str:
    return TIMEZONE_DEFAULT_CITY.get(timezone_name, "Greenwich")


def city_input_help(timezone_name: str) -> str:
    default = representative_city_name(timezone_name)
    return (
        f"Enter the nearest major city, for example {default}, so Luna can observe local daylight accurately. "
        "No street address is required. Unsupported or blank cities use the timezone's representative city as an estimate."
    )


def resolve_location(
    nearest_city: str | None,
    timezone_name: str,
) -> tuple[CityLocation, str]:
    raw = (nearest_city or "").strip()
    if raw:
        normalised = _normalise_city(raw)
        alias = CITY_ALIASES.get(normalised)
        if alias:
            return CITY_LOCATIONS[alias], "customer city"
        for name, location in CITY_LOCATIONS.items():
            if _normalise_city(name) == normalised:
                return location, "customer city"

    fallback = representative_city_name(timezone_name)
    return CITY_LOCATIONS[fallback], "timezone estimate"


def _solar_declination(day_of_year: int) -> float:
    gamma = 2.0 * math.pi / 365.0 * (day_of_year - 1)
    return (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma)
        + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma)
        + 0.00148 * math.sin(3 * gamma)
    )


def daylight_minutes(d: date, latitude: float) -> float:
    declination = _solar_declination(d.timetuple().tm_yday)
    latitude_radians = math.radians(max(-89.8, min(89.8, latitude)))
    altitude = math.radians(-0.833)
    denominator = math.cos(latitude_radians) * math.cos(declination)
    if abs(denominator) < 1e-12:
        return 720.0
    cosine_hour_angle = (
        math.sin(altitude)
        - math.sin(latitude_radians) * math.sin(declination)
    ) / denominator
    if cosine_hour_angle <= -1:
        return 1440.0
    if cosine_hour_angle >= 1:
        return 0.0
    hour_angle = math.acos(cosine_hour_angle)
    return 8.0 * math.degrees(hour_angle)


def daylight_change_minutes(d: date, latitude: float) -> float:
    earlier = daylight_minutes(d - timedelta(days=3), latitude)
    later = daylight_minutes(d + timedelta(days=3), latitude)
    return (later - earlier) / 6.0


def _light_direction(change: float) -> str:
    if change > 0.25:
        return "Increasing"
    if change < -0.25:
        return "Decreasing"
    return "Near a solar turning point"


def _hemisphere(latitude: float) -> str:
    if latitude > 3:
        return "Northern"
    if latitude < -3:
        return "Southern"
    return "Equatorial"


def _local_season(quarter: str, hemisphere: str) -> str:
    """Backward-compatible field value. Luna no longer uses hemisphere season names.

    The physical observation is local daylight direction; the universal solar clock
    remains Aries through Pisces in both hemispheres.
    """
    return "Location-aware light cycle"


def _gate_date(year: int, gate_index: int, timezone_name: str) -> date:
    rough_dates = (
        date(year, 3, 20),
        date(year, 6, 21),
        date(year, 9, 22),
        date(year, 12, 21),
    )
    target_sign_index = (0, 3, 6, 9)[gate_index]
    rough = rough_dates[gate_index]
    for offset in range(-5, 7):
        candidate = rough + timedelta(days=offset)
        today_sign = positions_for_date(candidate, timezone_name)["Sun"].sign_index
        previous_sign = positions_for_date(
            candidate - timedelta(days=1),
            timezone_name,
        )["Sun"].sign_index
        if today_sign == target_sign_index and previous_sign != target_sign_index:
            return candidate
    return rough


def _gate_context(d: date, solar_longitude: float, timezone_name: str):
    quarter_index = int((solar_longitude % 360.0) // 90.0)
    current_gate = GATES[quarter_index]
    next_index = (quarter_index + 1) % 4
    next_year = d.year + (1 if quarter_index == 3 else 0)
    next_gate = GATES[next_index]
    next_date = _gate_date(next_year, next_index, timezone_name)
    return current_gate, next_gate, next_date


def _solar_house(solar_sign: str, native_sign: str) -> int:
    return whole_sign_house(SIGNS.index(solar_sign), SIGNS.index(native_sign))


def _focus_text(main_focus: str, quarter: str) -> str:
    material = FOCUS_PHASES.get(
        main_focus,
        FOCUS_PHASES["General overview"],
    )
    return material[quarter]


def _rule(start_sign: str, end_sign: str) -> str:
    first = SIGN_RULES[start_sign].rstrip(".")
    second = SIGN_RULES[end_sign].rstrip(".")
    if start_sign == end_sign:
        return first.capitalize() + "."
    return first.capitalize() + ", then " + second + "."


def _solar_headline(light_direction: str, end_house: int) -> str:
    light = {
        "Increasing": "Returning light",
        "Decreasing": "Diminishing light",
        "Near a solar turning point": "A solar turning point",
    }[light_direction]
    outcome = {
        1: "reshapes personal direction",
        2: "asks value to become measurable",
        3: "turns information into a decision",
        4: "strengthens the private foundation",
        5: "awakens creative and romantic expression",
        6: "asks growth to become sustainable",
        7: "tests the meaning of relationship",
        8: "requires accountable trust",
        9: "opens a wider horizon",
        10: "becomes visible direction",
        11: "tests the future through community",
        12: "reveals what is ready for closure",
    }[end_house]
    return f"{light} {outcome}"


def daily_solar_convergence(
    native_sign: str,
    d: date,
    timezone_name: str,
    nearest_city: str = "",
    main_focus: str = "General overview",
) -> SolarConvergence:
    location, basis = resolve_location(nearest_city, timezone_name)
    sun = positions_for_date(d, timezone_name)["Sun"]
    quarter, process, practical = SOLAR_QUARTERS[sun.sign]
    current_gate, next_gate, next_gate_date = _gate_context(
        d,
        sun.longitude,
        timezone_name,
    )
    change = daylight_change_minutes(d, location.latitude)
    direction = _light_direction(change)
    hemisphere = _hemisphere(location.latitude)
    house = _solar_house(sun.sign, native_sign)
    focus_text = _focus_text(main_focus, quarter)
    phase = PHASE_ACTIONS[quarter]
    meaning = (
        f"{SOLAR_CLOCK_PRINCIPLE} The current Sun is in {sun.sign}, moving through the universal Aries-to-Pisces solar-zodiacal cycle. "
        f"For {native_sign}, this activates house {house}: {HOUSE_NAMES[house]}.",
        local_light_statement(city=location.name, direction=direction, change=change),
        f"The next solar gate is the {solar_gate_label(next_gate[0])} on {human_date(next_gate_date)}, "
        f"{max(0, (next_gate_date - d).days)} days away.",
    )
    return SolarConvergence(
        calculation_date=d.isoformat(),
        native_sign=native_sign,
        solar_longitude=round(sun.longitude, 4),
        solar_sign=sun.sign,
        solar_quarter=quarter,
        solar_process=process,
        practical_phase=practical,
        current_solar_gate=current_gate[0],
        next_solar_gate=next_gate[0],
        next_gate_date=next_gate_date.isoformat(),
        days_to_next_gate=max(0, (next_gate_date - d).days),
        hemisphere=hemisphere,
        local_season=_local_season(quarter, hemisphere),
        daylight_minutes=round(daylight_minutes(d, location.latitude), 1),
        daylight_change=round(change, 2),
        light_direction=direction,
        city=location.name,
        country=location.country,
        location_basis=basis,
        activated_house=house,
        activated_house_name=HOUSE_NAMES[house],
        start_solar_sign=sun.sign,
        end_solar_sign=sun.sign,
        start_house=house,
        end_house=house,
        solar_transition=f"{sun.sign}: {process.lower()} through {HOUSE_NAMES[house]}",
        main_focus=main_focus,
        headline=_solar_headline(direction, house),
        meaning=meaning,
        focus_meaning=focus_text,
        opportunity=phase["opportunity"],
        risk=phase["risk"],
        action=phase["action"],
        solar_rule=_rule(sun.sign, sun.sign),
        equation=(
            f"{direction} light x house {house} ({HOUSE_NAMES[house]}) "
            f"= {HOUSE_EQUATION[house]}"
        ),
    )


def monthly_solar_convergence(
    native_sign: str,
    year: int,
    month: int,
    timezone_name: str,
    nearest_city: str = "",
    main_focus: str = "General overview",
) -> SolarConvergence:
    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    midpoint = start + (end - start) // 2

    base = daily_solar_convergence(
        native_sign,
        midpoint,
        timezone_name,
        nearest_city,
        main_focus,
    )
    start_sun = positions_for_date(start, timezone_name)["Sun"]
    end_sun = positions_for_date(end, timezone_name)["Sun"]
    start_house = _solar_house(start_sun.sign, native_sign)
    end_house = _solar_house(end_sun.sign, native_sign)

    location, basis = resolve_location(nearest_city, timezone_name)
    daylight_start = daylight_minutes(start, location.latitude)
    daylight_end = daylight_minutes(end, location.latitude)
    month_change = daylight_end - daylight_start
    direction = (
        "Increasing"
        if month_change > 5
        else "Decreasing"
        if month_change < -5
        else "Near a solar turning point"
    )

    gate_in_month = ""
    for gate_index, gate in enumerate(GATES):
        gate_day = _gate_date(year, gate_index, timezone_name)
        if start <= gate_day <= end:
            gate_in_month = (
                f"The month crosses the {solar_gate_label(gate[0])} on {gate_day.strftime('%B %d')}, "
                f"one of the four cardinal gates of Luna's solar clock."
            )
            break

    transition = (
        f"{start_sun.sign} to {end_sun.sign}: "
        f"{SOLAR_QUARTERS[start_sun.sign][1].lower()} becomes "
        f"{SOLAR_QUARTERS[end_sun.sign][1].lower()}."
        if start_sun.sign != end_sun.sign
        else f"{start_sun.sign}: {SOLAR_QUARTERS[start_sun.sign][1].lower()} remains the monthly solar process."
    )
    meaning = (
        f"{SOLAR_CLOCK_PRINCIPLE} During {start.strftime('%B')}, the current Sun moves from {start_sun.sign} into {end_sun.sign}. "
        f"For {native_sign}, the emphasis moves from house {start_house} - {HOUSE_NAMES[start_house]} - "
        f"into house {end_house} - {HOUSE_NAMES[end_house]}.",
        f"In {location.name}, daylight is {direction.lower()}, changing from approximately {daylight_start / 60:.1f} to {daylight_end / 60:.1f} hours across the month. "
        "That local light direction does not alter the Aries-to-Pisces solar sequence.",
        gate_in_month
        or (
            f"The next solar gate is the {solar_gate_label(base.next_solar_gate)} on "
            f"{human_date(base.next_gate_date)}, "
            f"{base.days_to_next_gate} days from the middle of the month."
        ),
    )
    quarter = SOLAR_QUARTERS[base.solar_sign][0]
    phase = PHASE_ACTIONS[quarter]
    equation_result = HOUSE_EQUATION[end_house]
    equation = (
        f"{direction} light x house {start_house} expansion x "
        f"house {end_house} visibility = {equation_result}"
        if start_house != end_house
        else (
            f"{direction} light x house {end_house} "
            f"({HOUSE_NAMES[end_house]}) = {equation_result}"
        )
    )

    return SolarConvergence(
        calculation_date=midpoint.isoformat(),
        native_sign=native_sign,
        solar_longitude=base.solar_longitude,
        solar_sign=base.solar_sign,
        solar_quarter=base.solar_quarter,
        solar_process=base.solar_process,
        practical_phase=base.practical_phase,
        current_solar_gate=base.current_solar_gate,
        next_solar_gate=base.next_solar_gate,
        next_gate_date=base.next_gate_date,
        days_to_next_gate=base.days_to_next_gate,
        hemisphere=base.hemisphere,
        local_season=base.local_season,
        daylight_minutes=base.daylight_minutes,
        daylight_change=round(month_change, 1),
        light_direction=direction,
        city=location.name,
        country=location.country,
        location_basis=basis,
        activated_house=end_house,
        activated_house_name=HOUSE_NAMES[end_house],
        start_solar_sign=start_sun.sign,
        end_solar_sign=end_sun.sign,
        start_house=start_house,
        end_house=end_house,
        solar_transition=transition,
        main_focus=main_focus,
        headline=_solar_headline(direction, end_house),
        meaning=meaning,
        focus_meaning=(
            _focus_text(main_focus, quarter)
            if main_focus not in {"General overview", "General year ahead"}
            else f"Background emphasis: {HOUSE_SOLAR_GUIDANCE[end_house]['arrive'].capitalize()}."
        ),
        opportunity=(
            f"Use house {start_house} to {HOUSE_SOLAR_GUIDANCE[start_house]['prepare']}. "
            f"As the emphasis moves into house {end_house}, {HOUSE_SOLAR_GUIDANCE[end_house]['arrive']}."
        ),
        risk=(
            f"Watch for {HOUSE_SOLAR_GUIDANCE[end_house]['risk']}. "
            f"The solar background is context for the event-led story, not a replacement for it."
        ),
        action=(
            f"During the {start_sun.sign} phase, {HOUSE_SOLAR_GUIDANCE[start_house]['prepare']}. "
            f"During the {end_sun.sign} phase, {HOUSE_SOLAR_GUIDANCE[end_house]['arrive']}."
        ),
        solar_rule=_rule(start_sun.sign, end_sun.sign),
        equation=equation,
    )


def yearly_solar_chapters(
    native_sign: str,
    year: int,
    timezone_name: str,
    nearest_city: str = "",
    main_focus: str = "General year ahead",
) -> tuple[SolarYearChapter, ...]:
    location, _basis = resolve_location(nearest_city, timezone_name)
    chapters = []
    for index, (gate_name, _longitude, gate_sign, question) in enumerate(GATES):
        start = _gate_date(year, index, timezone_name)
        if index < 3:
            end = _gate_date(year, index + 1, timezone_name) - timedelta(days=1)
        else:
            end = _gate_date(year + 1, 0, timezone_name) - timedelta(days=1)
        quarter = SOLAR_QUARTERS[gate_sign][0]
        signs = QUARTER_SIGNS[quarter]
        houses = tuple(_solar_house(sign, native_sign) for sign in signs)
        chapters.append(
            SolarYearChapter(
                name=quarter,
                gate=gate_name,
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                signs=signs,
                houses=houses,
                local_season=(
                    f"{_light_direction(daylight_change_minutes(start + (end - start) // 2, location.latitude))} from {location.name}"
                ),
                process=" -> ".join(SOLAR_QUARTERS[sign][1] for sign in signs),
                strategic_question=question,
                focus_direction=_focus_text(main_focus, quarter),
            )
        )
    return tuple(chapters)


def yearly_solar_markdown(chapters: Iterable[SolarYearChapter]) -> str:
    lines = [
        "# The Solar Clock - four cardinal gates",
        "",
        "The Sun is Luna's primary natural clock. The Aries Gate at the March Equinox is the head of the universal Aries-to-Pisces solar cycle; local geography changes the observed light, never the zodiacal order.",
        "",
    ]
    for chapter in chapters:
        start = date.fromisoformat(chapter.start_date)
        end = date.fromisoformat(chapter.end_date)
        lines.extend(
            [
                f"## {chapter.name} - {solar_gate_label(chapter.gate)}",
                f"**Window:** {start.strftime('%B %d')} to {end.strftime('%B %d')}",
                "",
                f"**Solar process:** {chapter.process}",
                "",
                f"**Activated houses:** {', '.join(str(item) for item in chapter.houses)}",
                "",
                f"**Local light:** {chapter.local_season}",
                "",
                f"**Strategic question:** {chapter.strategic_question}",
                "",
                chapter.focus_direction,
                "",
            ]
        )
    return "\n".join(lines)
