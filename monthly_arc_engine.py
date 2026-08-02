from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Mapping, Sequence

from date_display import human_date, human_date_range
from scenario_engine import SIGN_RULERS, ScenarioResult, rank_scenarios


TRIGGER_WEIGHTS = {
    "eclipse": 1.60,
    "lunation": 1.40,
    "station": 1.30,
    "aspect": 1.00,
    "ingress": 0.90,
}

HOUSE_SHORT = {
    1: "identity and direction",
    2: "income and personal money",
    3: "messages, contracts and movement",
    4: "home and private life",
    5: "romance and creativity",
    6: "work and wellbeing",
    7: "relationships and agreements",
    8: "shared money and obligations",
    9: "travel, publishing and opportunity",
    10: "career and visibility",
    11: "friends, audiences and future plans",
    12: "rest, closure and private matters",
}


@dataclass(frozen=True)
class ArcBeat:
    role: str
    start_date: str
    end_date: str
    title: str
    summary: str
    response: str
    score: float
    houses: tuple[int, ...]
    planets: tuple[str, ...]
    scenarios: tuple[str, ...]
    evidence: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "title": self.title,
            "summary": self.summary,
            "response": self.response,
            "score": round(self.score, 2),
            "houses": list(self.houses),
            "planets": list(self.planets),
            "scenarios": list(self.scenarios),
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class MonthlyArc:
    sign: str
    label: str
    headline: str
    central_storyline: str
    theme_axis: str
    primary_house: int
    secondary_house: int
    opening: tuple[str, ...]
    complication: tuple[str, ...]
    pivot: tuple[str, ...]
    climax: tuple[str, ...]
    resolution: tuple[str, ...]
    relationship_test: tuple[str, ...]
    do_line: str
    dont_line: str
    beats: tuple[ArcBeat, ...]
    ranked_scenarios: tuple[ScenarioResult, ...]
    inherited_events: tuple[dict, ...]
    equation: str

    def to_dict(self) -> dict:
        return {
            "sign": self.sign,
            "label": self.label,
            "headline": self.headline,
            "central_storyline": self.central_storyline,
            "theme_axis": self.theme_axis,
            "primary_house": self.primary_house,
            "secondary_house": self.secondary_house,
            "opening": list(self.opening),
            "complication": list(self.complication),
            "pivot": list(self.pivot),
            "climax": list(self.climax),
            "resolution": list(self.resolution),
            "relationship_test": list(self.relationship_test),
            "do_line": self.do_line,
            "dont_line": self.dont_line,
            "beats": [item.to_dict() for item in self.beats],
            "ranked_scenarios": [item.to_dict() for item in self.ranked_scenarios],
            "inherited_events": list(self.inherited_events),
            "equation": self.equation,
        }


def _value(event: object, key: str, default: object = None) -> object:
    if isinstance(event, Mapping):
        return event.get(key, default)
    return getattr(event, key, default)


def _date_value(event: object) -> date:
    value = _value(event, "event_date")
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _event_dict(event: object) -> dict:
    return {
        "event_date": _date_value(event).isoformat(),
        "kind": str(_value(event, "kind", "")),
        "title": str(_value(event, "title", "Transition")),
        "detail": str(_value(event, "detail", "")),
        "importance": float(_value(event, "importance", 0.0) or 0.0),
        "planets": list(_value(event, "planets", ()) or ()),
        "houses": [int(item) for item in (_value(event, "houses", ()) or ())],
        "polarity": str(_value(event, "polarity", "neutral")),
    }


def _event_weight(event: object, sign: str) -> float:
    kind = str(_value(event, "kind", ""))
    importance = float(_value(event, "importance", 0.0) or 0.0)
    planets = set(_value(event, "planets", ()) or ())
    polarity = str(_value(event, "polarity", "neutral"))

    if planets == {"Moon"} and kind not in {"lunation", "eclipse"}:
        return 0.0

    weight = TRIGGER_WEIGHTS.get(kind, 0.72) * max(0.35, importance / 6.5)
    rulers = set(SIGN_RULERS.get(sign, ()))
    if planets & rulers:
        weight *= 1.25
    if kind == "aspect" and planets <= {"Uranus", "Neptune", "Pluto"}:
        # Slow-planet contacts define climate, but should not outrank a timed
        # lunation, station or sign-ruler climax by volume alone.
        weight *= 0.72
    if polarity == "pressure":
        weight *= 1.08
    elif polarity in {"opportunity", "release", "culmination"}:
        weight *= 1.05
    return weight


def _meaningful(events: Iterable[object]) -> list[object]:
    selected = []
    for event in events:
        kind = str(_value(event, "kind", ""))
        importance = float(_value(event, "importance", 0.0) or 0.0)
        planets = set(_value(event, "planets", ()) or ())
        if planets == {"Moon"} and kind not in {"lunation", "eclipse"}:
            continue
        if importance < 5.0 and kind not in {"lunation", "eclipse", "station"}:
            continue
        selected.append(event)
    return sorted(selected, key=_date_value)


def _clusters(events: Sequence[object], sign: str, window_days: int = 2) -> list[dict]:
    meaningful = _meaningful(events)
    candidates: list[dict] = []
    for anchor in meaningful:
        anchor_date = _date_value(anchor)
        members = [
            event
            for event in meaningful
            if abs((_date_value(event) - anchor_date).days) <= window_days
        ]
        if not members:
            continue
        dates = [_date_value(item) for item in members]
        houses = [int(house) for item in members for house in (_value(item, "houses", ()) or ())]
        planets = [str(planet) for item in members for planet in (_value(item, "planets", ()) or ())]
        score = sum(_event_weight(item, sign) for item in members)
        score += len({str(_value(item, "kind", "")) for item in members}) * 0.35
        score += len(set(houses)) * 0.12
        score += len(set(planets)) * 0.08
        candidates.append(
            {
                "start": min(dates),
                "end": max(dates),
                "score": score,
                "events": members,
                "houses": tuple(house for house, _ in Counter(houses).most_common()),
                "planets": tuple(planet for planet, _ in Counter(planets).most_common()),
            }
        )

    # Deduplicate identical windows and preserve the strongest representation.
    unique: dict[tuple[date, date, tuple[str, ...]], dict] = {}
    for item in candidates:
        fingerprint = (
            item["start"],
            item["end"],
            tuple(sorted(str(_value(event, "title", "")) for event in item["events"])),
        )
        previous = unique.get(fingerprint)
        if previous is None or item["score"] > previous["score"]:
            unique[fingerprint] = item
    return sorted(unique.values(), key=lambda item: (item["start"], -item["score"]))


def _cluster_overlap_days(first: dict | None, second: dict | None) -> int:
    if not first or not second:
        return 0
    start = max(first["start"], second["start"])
    end = min(first["end"], second["end"])
    return max(0, (end - start).days + 1)


def _cluster_span_days(cluster: dict | None) -> int:
    if not cluster:
        return 0
    return max(1, (cluster["end"] - cluster["start"]).days + 1)


def _substantially_overlaps(cluster: dict | None, used_clusters: Sequence[dict | None], ratio: float = 0.55) -> bool:
    if not cluster:
        return False
    span = _cluster_span_days(cluster)
    return any(
        _cluster_overlap_days(cluster, other) / span >= ratio
        for other in used_clusters
        if other
    )


def _best_cluster(
    clusters: Sequence[dict],
    start: date,
    end: date,
    *,
    polarities: set[str] | None = None,
    kinds: set[str] | None = None,
    exclude: set[tuple[date, date]] | None = None,
) -> dict | None:
    exclude = exclude or set()
    candidates = []
    for cluster in clusters:
        if cluster["end"] < start or cluster["start"] > end:
            continue
        if (cluster["start"], cluster["end"]) in exclude:
            continue
        events = cluster["events"]
        if polarities and not any(str(_value(item, "polarity", "")) in polarities for item in events):
            continue
        if kinds and not any(str(_value(item, "kind", "")) in kinds for item in events):
            continue
        candidates.append(cluster)
    return max(candidates, key=lambda item: item["score"], default=None)


def _event_label(event: object) -> str:
    d = _date_value(event)
    return f"{human_date(d)}: {str(_value(event, 'title', 'Transition'))}"


def _date_range_label(start: date, end: date) -> str:
    return human_date_range(start, end)


def _top_scenarios(
    events: Sequence[object],
    sign: str,
    main_focus: str,
    maximum: int = 3,
) -> tuple[ScenarioResult, ...]:
    return rank_scenarios(events, sign, main_focus, maximum=maximum)


def _scenario_keys(results: Sequence[ScenarioResult]) -> set[str]:
    return {item.key for item in results}


def _cluster_scenarios(cluster: dict | None, sign: str, main_focus: str) -> tuple[ScenarioResult, ...]:
    if not cluster:
        return ()
    return _top_scenarios(cluster["events"], sign, main_focus, maximum=3)


def _dominant_house(cluster: dict | None, fallback: int) -> int:
    if cluster and cluster.get("houses"):
        return int(cluster["houses"][0])
    return fallback


def _event_cluster(event: object, events: Sequence[object], sign: str, window_days: int = 1) -> dict:
    anchor_date = _date_value(event)
    members = [
        item
        for item in _meaningful(events)
        if abs((_date_value(item) - anchor_date).days) <= window_days
    ]
    houses = [int(house) for item in members for house in (_value(item, "houses", ()) or ())]
    planets = [str(planet) for item in members for planet in (_value(item, "planets", ()) or ())]
    return {
        "start": min((_date_value(item) for item in members), default=anchor_date),
        "end": max((_date_value(item) for item in members), default=anchor_date),
        "score": sum(_event_weight(item, sign) for item in members),
        "events": members or [event],
        "houses": tuple(house for house, _ in Counter(houses).most_common()),
        "planets": tuple(planet for planet, _ in Counter(planets).most_common()),
    }


def _select_complication(
    clusters: Sequence[dict],
    start: date,
    end: date,
    inherited: dict | None,
    sign: str,
    main_focus: str,
) -> dict | None:
    inherited_houses = set(inherited.get("houses", ())) if inherited else set()
    candidates: list[tuple[float, dict]] = []
    for cluster in clusters:
        midpoint = cluster["start"] + (cluster["end"] - cluster["start"]) / 2
        if midpoint < start or midpoint > end:
            continue
        events = cluster["events"]
        if not any(str(_value(item, "polarity", "")) in {"pressure", "review", "new cycle"} for item in events):
            continue
        score = float(cluster["score"])
        if any(str(_value(item, "kind", "")) in {"lunation", "eclipse"} for item in events):
            score += 2.4
        cluster_houses = set(cluster.get("houses", ()))
        if cluster_houses & inherited_houses:
            score += 1.4
        scenario_keys = _scenario_keys(_cluster_scenarios(cluster, sign, main_focus))
        if scenario_keys & {"funding_application", "paperwork_verification", "external_money", "financial_shock"}:
            score += 2.2
        candidates.append((score, cluster))
    return max(candidates, key=lambda item: item[0], default=(0.0, None))[1]


def _select_relationship_test(
    events: Sequence[object],
    start: date,
    end: date,
    sign: str,
    main_focus: str,
    used_clusters: Sequence[dict | None] = (),
) -> dict | None:
    relationship_houses = {5, 7, 8, 11}
    relationship_planets = {"Venus", "Mars", "Jupiter", "Saturn", "Neptune", "Pluto", "Uranus"}
    selected_events = [
        event for event in _meaningful(events)
        if start <= _date_value(event) <= end
        and (
            "Venus" in set(_value(event, "planets", ()) or ())
            or (
                set(_value(event, "houses", ()) or ()) & relationship_houses
                and set(_value(event, "planets", ()) or ()) & relationship_planets
            )
        )
    ]
    anchors = [
        event for event in selected_events
        if "Venus" in set(_value(event, "planets", ()) or ())
    ] or selected_events

    candidates: list[tuple[float, dict]] = []
    for anchor in anchors:
        anchor_date = _date_value(anchor)
        members = [
            event for event in selected_events
            if abs((_date_value(event) - anchor_date).days) <= 3
        ]
        if not members:
            continue
        dates = [_date_value(item) for item in members]
        houses = [int(house) for item in members for house in (_value(item, "houses", ()) or ())]
        planets = [str(planet) for item in members for planet in (_value(item, "planets", ()) or ())]
        cluster = {
            "start": min(dates),
            "end": max(dates),
            "score": sum(_event_weight(item, sign) for item in members),
            "events": members,
            "houses": tuple(house for house, _ in Counter(houses).most_common()),
            "planets": tuple(planet for planet, _ in Counter(planets).most_common()),
        }
        if _substantially_overlaps(cluster, used_clusters, ratio=0.45):
            continue
        planet_set = set(planets)
        polarities = {str(_value(item, "polarity", "neutral")) for item in members}
        score = float(cluster["score"])
        if "Venus" in planet_set:
            score += 1.5
        if "Jupiter" in planet_set:
            score += 2.0
        if "Saturn" in planet_set:
            score += 2.2
        if "Neptune" in planet_set or "Pluto" in planet_set:
            score += 0.6
        if set(houses) & relationship_houses:
            score += 1.0
        if polarities & {"opportunity", "new cycle"} and polarities & {"pressure", "review"}:
            score += 3.2
        scenario_keys = _scenario_keys(_cluster_scenarios(cluster, sign, main_focus))
        if "relationship_opening" in scenario_keys:
            score += 1.4
        candidates.append((score, cluster))

    chosen = max(candidates, key=lambda item: item[0], default=(0.0, None))
    return chosen[1] if chosen[0] >= 6.0 else None


def _relationship_test_copy(cluster: dict | None) -> tuple[str, ...]:
    if not cluster:
        return ()
    events = cluster.get("events", ())
    planets = {str(planet) for item in events for planet in (_value(item, "planets", ()) or ())}
    window = _date_range_label(cluster["start"], cluster["end"])
    if {"Venus", "Jupiter", "Saturn"} <= planets:
        return (
            f"Around {window}, attention, warmth or approval can rise quickly. Watch what follows: steady presence or passing interest?",
            "Enjoy the interest. Then compare warmth with effort. Consistency reveals what deserves more time.",
        )
    if "Venus" in planets and "Saturn" in planets:
        return (
            f"Around {window}, attraction or approval grows. Watch how timing, distance or availability changes the effort behind it.",
            "Notice what they continue to choose after the mood shifts. Actions make the answer clearer.",
        )
    if "Venus" in planets and ("Neptune" in planets or "Pluto" in planets):
        return (
            f"Around {window}, attraction may feel intense, flattering or unusually persuasive. Keep desire in the story and standards in the room.",
            "Enjoy the chemistry, then ask what creates clarity, safety and mutuality.",
        )
    return (
        f"Around {window}, behaviour gives attention its meaning. Watch who follows through when the next step becomes real.",
        "Choose the connection, audience or alliance that returns equal energy.",
    )


def _select_climax(
    clusters: Sequence[dict],
    start: date,
    end: date,
    sign: str,
) -> dict | None:
    rulers = set(SIGN_RULERS.get(sign, ()))
    candidates: list[tuple[float, dict]] = []
    for cluster in clusters:
        if cluster["end"] < start or cluster["start"] > end:
            continue
        events = cluster["events"]
        score = float(cluster["score"])
        if any(
            "Sun" in set(_value(item, "planets", ()) or ())
            and set(_value(item, "planets", ()) or ()) & rulers
            and str(_value(item, "kind", "")) == "aspect"
            for item in events
        ):
            score += 5.0
        if any(str(_value(item, "kind", "")) in {"lunation", "eclipse"} for item in events):
            score += 2.5
        if any(str(_value(item, "polarity", "")) in {"opportunity", "culmination", "release"} for item in events):
            score += 1.0
        score += max(0.0, (cluster["end"] - start).days * 0.08)
        candidates.append((score, cluster))
    return max(candidates, key=lambda item: item[0], default=(0.0, None))[1]


def _beat(
    role: str,
    cluster: dict | None,
    sign: str,
    main_focus: str,
    summary: str,
    response: str,
    fallback_date: date,
) -> ArcBeat:
    if cluster:
        scenarios = _cluster_scenarios(cluster, sign, main_focus)
        events = list(cluster["events"])
        if role == "pivot":
            strongest = next(
                (item for item in events if str(_value(item, "polarity", "")) == "release"),
                max(events, key=lambda item: _event_weight(item, sign)),
            )
        elif role == "climax":
            rulers = set(SIGN_RULERS.get(sign, ()))
            strongest = next(
                (
                    item
                    for item in events
                    if "Sun" in set(_value(item, "planets", ()) or ())
                    and set(_value(item, "planets", ()) or ()) & rulers
                ),
                next(
                    (item for item in events if str(_value(item, "kind", "")) in {"lunation", "eclipse"}),
                    max(events, key=lambda item: _event_weight(item, sign)),
                ),
            )
        elif role in {"resolution", "inherited state"}:
            strongest = next(
                (item for item in events if str(_value(item, "kind", "")) in {"lunation", "eclipse"}),
                max(events, key=lambda item: _event_weight(item, sign)),
            )
        elif role == "complication":
            strongest = next(
                (item for item in events if str(_value(item, "kind", "")) in {"lunation", "eclipse"}),
                next(
                    (item for item in events if str(_value(item, "polarity", "")) in {"pressure", "review"}),
                    max(events, key=lambda item: _event_weight(item, sign)),
                ),
            )
        elif role == "relationship test":
            strongest = next(
                (item for item in events if "Venus" in set(_value(item, "planets", ()) or ())),
                max(events, key=lambda item: _event_weight(item, sign)),
            )
        else:
            strongest = max(events, key=lambda item: _event_weight(item, sign))
        title = str(_value(strongest, "title", role.title()))
        evidence = tuple(_event_label(item) for item in sorted(cluster["events"], key=_date_value))
        return ArcBeat(
            role=role,
            start_date=cluster["start"].isoformat(),
            end_date=cluster["end"].isoformat(),
            title=title,
            summary=summary,
            response=response,
            score=float(cluster["score"]),
            houses=tuple(int(item) for item in cluster.get("houses", ())),
            planets=tuple(str(item) for item in cluster.get("planets", ())),
            scenarios=tuple(item.label for item in scenarios),
            evidence=evidence,
        )
    return ArcBeat(
        role=role,
        start_date=fallback_date.isoformat(),
        end_date=fallback_date.isoformat(),
        title=role.title(),
        summary=summary,
        response=response,
        score=0.0,
        houses=(),
        planets=(),
        scenarios=(),
        evidence=(),
    )


def _headline_and_axis(
    month: str,
    opening_scenarios: Sequence[ScenarioResult],
    climax_scenarios: Sequence[ScenarioResult],
) -> tuple[str, str, str]:
    opening = _scenario_keys(opening_scenarios)
    climax = _scenario_keys(climax_scenarios)

    financial = bool(opening & {"financial_shock", "external_money", "funding_application", "paperwork_verification"})
    expansion = bool(climax & {"travel", "publishing_media", "visa_legal_study", "career_interview", "contracts_agreements"})
    romance = bool(opening & {"relationship_opening"})
    property_close = bool(climax & {"property_home"})

    if financial and expansion:
        return (
            f"{month} checks the bank balance before it upgrades the itinerary",
            "The month starts with the price. It ends with the possibility.",
            "Money & obligations x Travel, publishing & opportunity",
        )
    if romance and property_close:
        return (
            "The spark arrives before the address is settled",
            "Attraction opens the story. Real life decides where it can live.",
            "Romance & connection x Home & private life",
        )
    if romance and expansion:
        return (
            "The invitation gets interesting when it leaves the group chat",
            "A connection widens the future, then asks for a real plan.",
            "Romance & relationships x Expansion & opportunity",
        )
    if expansion:
        return (
            "The future opens after the facts catch up",
            "The month moves from preparation into a larger visible opportunity.",
            "Preparation & proof x Expansion & visibility",
        )
    if financial:
        return (
            "The numbers speak before the wish list does",
            "The month exposes the true cost, then shows what can be rebuilt.",
            "Money & security x Decisions & structure",
        )
    return (
        "The first clue becomes a decision by month-end",
        "The month reveals the issue, tests it and leaves a clearer choice.",
        "Opening signal x Practical consequence",
    )


def _july_style_story(
    month: str,
    inherited_scenarios: Sequence[ScenarioResult],
    complication_scenarios: Sequence[ScenarioResult],
    pivot: dict | None,
    climax_scenarios: Sequence[ScenarioResult],
    inherited_date: str,
    complication_date: str,
    pivot_date: str,
    climax_date: str,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], str, str]:
    inherited_keys = _scenario_keys(inherited_scenarios)
    complication_keys = _scenario_keys(complication_scenarios)
    climax_keys = _scenario_keys(climax_scenarios)

    financial_open = bool(inherited_keys & {"financial_shock", "external_money"})
    paperwork_mid = bool(complication_keys & {"funding_application", "paperwork_verification", "external_money"})
    expansion_close = bool(climax_keys & {"travel", "publishing_media", "visa_legal_study", "career_interview", "contracts_agreements"})
    mercury_release = bool(
        pivot
        and any(
            "Mercury" in (_value(item, "planets", ()) or ())
            and str(_value(item, "polarity", "")) == "release"
            for item in pivot["events"]
        )
    )

    if financial_open and paperwork_mid and expansion_close:
        opening = (
            f"{month} begins inside a financial consequence that formed just before the month opened. "
            f"Around {inherited_date}, a bill, salary discussion, promised payment or shared expense may "
            "cost more - or arrive later - than expected. The issue is not necessarily that the money "
            "does not exist. The amount, timing or conditions may still be unclear.",
        )
        complication = (
            f"Near {complication_date}, another attempt to organise the situation can bring a mortgage, "
            "loan, grant, insurance matter, investment, business plan or shared-money decision into view. "
            "The process may require more forms, proof and conservative estimates than anticipated.",
            "This is where the opportunity meets Saturn's standard: accurate, verifiable and sustainable. "
            "A delay is not automatically a refusal, but vague numbers and incomplete documents will not carry the story forward.",
        )
        pivot_text = (
            f"Around {pivot_date}, communication begins to clear. Messages resume, stalled applications can move "
            "and agreements become easier to evaluate. A partner, colleague or useful contact may help connect the missing step."
            if mercury_release
            else f"Around {pivot_date}, the month changes direction as information, timing or support becomes easier to use."
        )
        climax = (
            f"By {climax_date}, the story widens dramatically. Travel, publishing, study, legal matters, international "
            "opportunities, an interview or an important agreement can move from possibility into a visible result.",
            "What felt delayed at the beginning of the month may not resolve in exactly the original form. "
            "The larger gain is movement: a future that was blocked begins to answer back.",
        )
        resolution = (
            "The month does not erase the early financial lesson. It uses that lesson to improve the terms of the opportunity that follows.",
        )
        return (
            opening,
            complication,
            (pivot_text,),
            climax,
            resolution,
            (),
            "Check the paperwork. Fairy dust still needs the correct account number.",
            "Call a delay a rejection. Mercury was only reorganising the filing cabinet.",
        )

    return (), (), (), (), (), (), "", ""


def _expansion_public_private_story(
    month: str,
    inherited: dict | None,
    inciting: dict | None,
    complication: dict | None,
    relationship_test: dict | None,
    climax: dict | None,
    resolution: dict | None,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], str, str] | None:
    def planets(cluster: dict | None) -> set[str]:
        return {
            str(planet)
            for item in (cluster or {}).get("events", ())
            for planet in (_value(item, "planets", ()) or ())
        }

    def houses(cluster: dict | None) -> set[int]:
        return {int(value) for value in (cluster or {}).get("houses", ())}

    inherited_houses = houses(inherited)
    inciting_houses = houses(inciting)
    complication_houses = houses(complication)
    climax_houses = houses(climax) | houses(resolution)
    complication_planets = planets(complication)
    relationship_planets = planets(relationship_test)

    signature = (
        bool(inherited_houses & {3, 9})
        and bool(inciting_houses & {9, 11})
        and bool(complication_houses & {8, 9})
        and bool({"Mercury", "Jupiter"} & complication_planets)
        and {10, 4} <= climax_houses
    )
    if not signature:
        return None

    inherited_window = _date_range_label(inherited["start"], inherited["end"]) if inherited else f"late in the previous month"
    inciting_window = _date_range_label(inciting["start"], inciting["end"]) if inciting else f"early {month}"
    complication_window = _date_range_label(complication["start"], complication["end"]) if complication else f"mid-{month}"
    relationship_window = _date_range_label(relationship_test["start"], relationship_test["end"]) if relationship_test else f"later in {month}"
    climax_window = _date_range_label(climax["start"], climax["end"]) if climax else f"late {month}"

    opening = (
        f"The breakthrough from around {inherited_window} enters {month} with momentum. A trip, course, application, publication, international contact or larger plan may already be opening a wider path.",
        f"Around {inciting_window}, support from a friend, audience, organisation or useful contact gives the idea shape. Possibility moves from imagination into conversation.",
    )
    complication_text = (
        f"Around {complication_window}, the important details come into focus. Timing, money, distance, trust, paperwork or another person's involvement may shape the choice.",
        "Keep the excitement, then ask the simple question that creates clarity. Understanding what comes with the opportunity makes the next step easier to choose.",
    )
    pivot_text: tuple[str, ...] = ()
    relationship_text = _relationship_test_copy(relationship_test)
    climax_text = (
        f"Around {climax_window}, the project, application, trip or relationship moves toward a visible result. Career, recognition or an official decision brings the story into view.",
        "Now place the result inside real life. Home, family, location and emotional ease reveal what truly belongs.",
    )
    resolution_text = (
        "The month closes with a clearer position: favour the future that shows care, supports priorities and fits the life already taking shape.",
    )

    if {"Venus", "Jupiter", "Saturn"} <= relationship_planets:
        relationship_text = (
            f"Around {relationship_window}, attention, warmth or approval rises. Watch what follows: steady presence or a passing moment?",
            "Enjoy the spark, then compare words with effort. Clear, consistent action shows what deserves more of the heart.",
        )

    return (
        opening,
        complication_text,
        pivot_text,
        climax_text,
        resolution_text,
        relationship_text,
        "Explore the possibility, name what matters and favour what supports the life already taking shape.",
        "Rush the spark into a promise. Give the story room to reveal its direction.",
    )


def _generic_story(
    month: str,
    inherited: dict | None,
    inciting: dict | None,
    complication: dict | None,
    pivot: dict | None,
    climax: dict | None,
    resolution: dict | None,
    relationship_test: dict | None,
    sign: str,
    main_focus: str,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], str, str]:
    def scenarios(cluster: dict | None) -> tuple[ScenarioResult, ...]:
        return _cluster_scenarios(cluster, sign, main_focus)

    inherited_results = scenarios(inherited)
    inciting_results = scenarios(inciting)
    complication_results = scenarios(complication)
    pivot_results = scenarios(pivot)
    climax_results = scenarios(climax)
    resolution_results = scenarios(resolution)
    relationship_results = scenarios(relationship_test)

    def examples(results: Sequence[ScenarioResult], maximum: int = 3) -> str:
        values: list[str] = []
        for item in results:
            for example in item.examples:
                if example not in values:
                    values.append(example)
                if len(values) >= maximum:
                    return ", ".join(values)
        return ", ".join(values) or "a person, choice or opportunity"

    opening = (
        f"{month} opens through {examples(inherited_results or inciting_results)}. "
        "Use the first development to identify the possibility worth shaping.",
    )
    complication_text = (
        f"In the middle of the month, {examples(complication_results)} comes into focus. "
        "Ask what this new detail changes, then choose the response deliberately.",
    )
    pivot_text = (
        f"Around {_date_range_label(pivot['start'], pivot['end']) if pivot else 'the middle of the month'}, direction changes. "
        f"Use clearer information, better timing or stronger cooperation to move {examples(pivot_results)} forward.",
    )
    climax_text = (
        f"Late in the month, the strongest energy gathers around {examples(climax_results)}. "
        "Turn the idea into a visible answer instead of extending the uncertainty.",
    )
    resolution_text = (
        f"As the month closes, the result connects with {examples(resolution_results, maximum=2)}. "
        "Choose what supports the life taking shape and use the rest as useful information.",
    )
    relationship_text = _relationship_test_copy(relationship_test)
    return (
        opening,
        complication_text,
        pivot_text,
        climax_text,
        resolution_text,
        relationship_text,
        "Read the sequence, then write the next move. The first scene does not decide the whole plot.",
        "Write the ending before the actions support it.",
    )


def _narrative_scenario_ranking(
    inherited: Sequence[ScenarioResult],
    complication: Sequence[ScenarioResult],
    climax: Sequence[ScenarioResult],
    global_results: Sequence[ScenarioResult],
    maximum: int = 8,
) -> tuple[ScenarioResult, ...]:
    process_keys = {
        "funding_application",
        "paperwork_verification",
        "contracts_agreements",
        "external_money",
    }
    expansion_keys = {
        "publishing_media",
        "travel",
        "visa_legal_study",
        "career_interview",
        "property_home",
        "relationship_opening",
    }
    ordered: list[ScenarioResult] = []

    def add(items: Sequence[ScenarioResult], limit: int | None = None) -> None:
        count = 0
        for item in items:
            if any(existing.key == item.key for existing in ordered):
                continue
            ordered.append(item)
            count += 1
            if limit is not None and count >= limit:
                break

    inherited_order = {
        "financial_shock": 0,
        "external_money": 1,
        "paperwork_verification": 2,
        "funding_application": 3,
    }
    inherited_priority = sorted(
        [item for item in inherited if item.key in inherited_order],
        key=lambda item: (inherited_order[item.key], -item.score),
    )
    add(inherited_priority or inherited, 2)
    add([item for item in complication if item.key in process_keys], 2)
    add([item for item in climax if item.key in expansion_keys], 3)
    add(complication, 1)
    add(climax, 1)
    add(global_results)
    return tuple(ordered[:maximum])


def build_monthly_arc(
    sign: str,
    start: date,
    end: date,
    label: str,
    events: Sequence[object],
    inherited_events: Sequence[object],
    retrograde_cycles: Sequence[object] = (),
    main_focus: str = "General overview",
) -> MonthlyArc:
    monthly_events = _meaningful(events)
    carryover = [
        event
        for event in _meaningful(inherited_events)
        if _date_value(event) >= start - timedelta(days=7)
        and (
            str(_value(event, "kind", "")) in {"lunation", "eclipse", "station"}
            or float(_value(event, "importance", 0.0) or 0.0) >= 6.4
        )
    ]

    monthly_clusters = _clusters(monthly_events, sign)
    inherited_clusters = _clusters(carryover, sign, window_days=3)

    carryover_triggers = [
        event
        for event in carryover
        if str(_value(event, "kind", "")) in {"lunation", "eclipse", "station"}
    ]
    if carryover_triggers:
        latest_date = max(_date_value(item) for item in carryover_triggers)
        latest = [item for item in carryover_triggers if _date_value(item) == latest_date]
        anchor = max(latest, key=lambda item: _event_weight(item, sign))
        inherited = _event_cluster(anchor, carryover, sign, window_days=2)
    else:
        inherited = max(inherited_clusters, key=lambda item: item["score"], default=None)
    used: set[tuple[date, date]] = set()
    if inherited:
        used.add((inherited["start"], inherited["end"]))

    early_limit = min(end, start + timedelta(days=9))
    early_candidates = [
        cluster for cluster in monthly_clusters
        if cluster["start"] <= early_limit
        and cluster["end"] <= early_limit + timedelta(days=1)
    ]
    inciting = max(early_candidates, key=lambda item: item["score"], default=None)
    if inciting:
        used.add((inciting["start"], inciting["end"]))

    complication = _select_complication(
        monthly_clusters,
        start + timedelta(days=8),
        min(end, start + timedelta(days=17)),
        inherited,
        sign,
        main_focus,
    )
    if complication:
        used.add((complication["start"], complication["end"]))

    relationship_test = _select_relationship_test(
        monthly_events,
        start + timedelta(days=12),
        min(end, start + timedelta(days=23)),
        sign,
        main_focus,
        used_clusters=(inciting, complication),
    )

    direct_events = [
        event
        for event in monthly_events
        if str(_value(event, "kind", "")) == "station"
        and str(_value(event, "polarity", "")) == "release"
    ]
    if direct_events:
        chosen_direct = max(direct_events, key=lambda item: _event_weight(item, sign))
        pivot = _event_cluster(chosen_direct, monthly_events, sign, window_days=1)
    else:
        pivot = _best_cluster(
            monthly_clusters,
            start + timedelta(days=14),
            min(end, start + timedelta(days=26)),
            polarities={"release", "opportunity"},
            kinds={"station", "aspect", "lunation", "ingress"},
            exclude=used,
        )
    if pivot and _substantially_overlaps(pivot, (complication, relationship_test), ratio=0.55):
        has_release_station = any(
            str(_value(item, "kind", "")) == "station"
            and str(_value(item, "polarity", "")) == "release"
            for item in pivot.get("events", ())
        )
        if not has_release_station:
            pivot = None
    if pivot:
        used.add((pivot["start"], pivot["end"]))

    climax = _select_climax(
        monthly_clusters,
        max(start, end - timedelta(days=9)),
        end,
        sign,
    )
    if climax:
        used.add((climax["start"], climax["end"]))

    final_triggers = [
        event
        for event in monthly_events
        if _date_value(event) >= max(start, end - timedelta(days=7))
        and str(_value(event, "kind", "")) in {"lunation", "eclipse"}
    ]
    if final_triggers:
        resolution = _event_cluster(max(final_triggers, key=_date_value), monthly_events, sign, window_days=0)
    else:
        resolution = climax

    inherited_scenarios = _top_scenarios(carryover + monthly_events[:3], sign, main_focus, maximum=4)
    complication_scenarios = _cluster_scenarios(complication, sign, main_focus)
    climax_scenarios = _cluster_scenarios(climax, sign, main_focus)
    global_scenarios = rank_scenarios(carryover + monthly_events, sign, main_focus, maximum=12)
    all_scenarios = _narrative_scenario_ranking(
        inherited_scenarios,
        complication_scenarios,
        climax_scenarios,
        global_scenarios,
        maximum=8,
    )

    month = label.split()[0]
    headline, central, axis = _headline_and_axis(month, inherited_scenarios, climax_scenarios)

    inherited_date = _date_range_label(inherited["start"], inherited["end"]) if inherited else f"early {month}"
    complication_date = _date_range_label(complication["start"], complication["end"]) if complication else f"mid-{month}"
    pivot_date = _date_range_label(pivot["start"], pivot["end"]) if pivot else f"late {month}"
    climax_date = _date_range_label(climax["start"], climax["end"]) if climax else f"the final week of {month}"

    story = _july_style_story(
        month,
        inherited_scenarios,
        complication_scenarios,
        pivot,
        climax_scenarios,
        inherited_date,
        complication_date,
        pivot_date,
        climax_date,
    )
    specialised_story = _expansion_public_private_story(
        month,
        inherited,
        inciting,
        complication,
        relationship_test,
        climax,
        resolution,
    )
    if specialised_story is not None:
        story = specialised_story
        headline = "A possibility becomes real through the choices that give it shape"
        central = (
            "A wider possibility opens. Attention shifts toward what supports joy, "
            "earns trust and belongs in the life already taking shape."
        )
        axis = "Possibility & attention x Clarity, care & a chosen life"
    elif not story[0]:
        story = _generic_story(
            month,
            inherited,
            inciting,
            complication,
            pivot,
            climax,
            resolution,
            relationship_test,
            sign,
            main_focus,
        )

    opening, complication_text, pivot_text, climax_text, resolution_text, relationship_text, do_line, dont_line = story

    if not relationship_text:
        relationship_text = _relationship_test_copy(relationship_test)

    primary_house = _dominant_house(inherited or complication or inciting, 1)
    secondary_house = _dominant_house(climax or resolution, primary_house)

    beat_list = [
        _beat(
            "inherited state",
            inherited,
            sign,
            main_focus,
            opening[0],
            "Name what matters before reacting.",
            start,
        ),
        _beat(
            "inciting event",
            inciting,
            sign,
            main_focus,
            (
                "A new opening enters the month and begins to shift the available future."
                if inciting
                else "The month reveals the first active choice."
            ),
            "Use the first response to open the conversation—not to write the ending.",
            start + timedelta(days=3),
        ),
        _beat(
            "complication",
            complication,
            sign,
            main_focus,
            complication_text[0],
            "Ask the simple question that brings the important details into focus.",
            start + timedelta(days=13),
        ),
    ]
    if pivot and pivot_text:
        beat_list.append(
            _beat(
                "pivot",
                pivot,
                sign,
                main_focus,
                pivot_text[0],
                "Use the new information to revise the choice and move forward.",
                start + timedelta(days=22),
            )
        )
    if relationship_test and relationship_text:
        beat_list.append(
            _beat(
                "relationship test",
                relationship_test,
                sign,
                main_focus,
                relationship_text[0],
                "Watch what they do next. Consistent effort tells the truth.",
                start + timedelta(days=18),
            )
        )
    beat_list.extend([
        _beat(
            "climax",
            climax,
            sign,
            main_focus,
            climax_text[0],
            "Move toward what feels promising and genuinely supported.",
            end - timedelta(days=2),
        ),
        _beat(
            "resolution",
            resolution,
            sign,
            main_focus,
            resolution_text[0],
            "Choose what still feels right after the excitement settles.",
            end,
        ),
    ])
    beats = tuple(sorted(beat_list, key=lambda item: (item.start_date, item.role)))


    return MonthlyArc(
        sign=sign,
        label=label,
        headline=headline,
        central_storyline=central,
        theme_axis=axis,
        primary_house=primary_house,
        secondary_house=secondary_house,
        opening=opening,
        complication=complication_text,
        pivot=pivot_text,
        climax=climax_text,
        resolution=resolution_text,
        relationship_test=relationship_text,
        do_line=do_line,
        dont_line=dont_line,
        beats=beats,
        ranked_scenarios=all_scenarios,
        inherited_events=tuple(_event_dict(item) for item in carryover),
        equation=(
            "Inherited state + trigger hierarchy + house/planet/ruler convergence + "
            "ranked scenario families + tension curve + relationship test + temporal roles = monthly arc"
        ),
    )
