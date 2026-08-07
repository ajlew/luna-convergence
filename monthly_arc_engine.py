from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Mapping, Sequence

from date_display import human_date, human_date_range
from scenario_engine import SIGN_RULERS, ScenarioResult, event_importance_score, rank_scenarios


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
    scenario_provenance: tuple[dict, ...]
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
            "scenario_provenance": list(self.scenario_provenance),
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
    supporting_house: int
    selection_rationale: str
    intensity_rating: str
    rulership_amplified: bool
    rulership_evidence: tuple[str, ...]
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
            "supporting_house": self.supporting_house,
            "selection_rationale": self.selection_rationale,
            "intensity_rating": self.intensity_rating,
            "rulership_amplified": self.rulership_amplified,
            "rulership_evidence": list(self.rulership_evidence),
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


def _event_weight(
    event: object,
    sign: str,
    house_weights: Mapping[int, float] | None = None,
) -> float:
    """Normalized 0-10 event importance for narrative selection."""
    return event_importance_score(event, sign, house_weights)


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


def _clusters(
    events: Sequence[object],
    sign: str,
    window_days: int = 2,
    house_weights: Mapping[int, float] | None = None,
) -> list[dict]:
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
        ranked_weights = sorted(
            (_event_weight(item, sign, house_weights) for item in members),
            reverse=True,
        )
        score = (
            (ranked_weights[0] if ranked_weights else 0.0)
            + (0.55 * ranked_weights[1] if len(ranked_weights) > 1 else 0.0)
            + (0.30 * ranked_weights[2] if len(ranked_weights) > 2 else 0.0)
        )
        score += len({str(_value(item, "kind", "")) for item in members}) * 0.30
        score += min(0.6, len(set(houses)) * 0.08)
        score += min(0.5, len(set(planets)) * 0.05)
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
    *,
    house_weights: Mapping[int, float] | None = None,
    required_houses: Iterable[int] | None = None,
) -> tuple[ScenarioResult, ...]:
    return rank_scenarios(
        events,
        sign,
        main_focus,
        maximum=maximum,
        house_weights=house_weights,
        required_houses=required_houses,
    )


def _scenario_keys(results: Sequence[ScenarioResult]) -> set[str]:
    return {item.key for item in results}


def _cluster_scenarios(
    cluster: dict | None,
    sign: str,
    main_focus: str,
    *,
    house_weights: Mapping[int, float] | None = None,
    required_house: int | None = None,
) -> tuple[ScenarioResult, ...]:
    if not cluster:
        return ()
    if required_house is None:
        fallback = int(max((house_weights or {1: 1.0}).items(), key=lambda item: item[1])[0])
        required_house = _cluster_dominant_house(cluster, sign, house_weights, fallback)
    return _top_scenarios(
        cluster["events"],
        sign,
        main_focus,
        maximum=3,
        house_weights=house_weights,
        required_houses={required_house},
    )


def _dominant_house(cluster: dict | None, fallback: int) -> int:
    if cluster and cluster.get("houses"):
        return int(cluster["houses"][0])
    return fallback


def _cluster_dominant_house(
    cluster: dict | None,
    sign: str,
    house_weights: Mapping[int, float] | None,
    fallback: int,
) -> int:
    if not cluster:
        return fallback
    houses = [int(value) for value in cluster.get("houses", ())]
    if not houses:
        return fallback

    # Event hierarchy inside a cluster: eclipse first; then an exact Sun contact
    # with the sign ruler; then an ordinary lunation. Nearby aspects modify the
    # anchor rather than voting it out by sheer volume.
    cluster_events = list(cluster.get("events", ()))
    eclipses = [event for event in cluster_events if str(_value(event, "kind", "")) == "eclipse"]
    rulers = set(SIGN_RULERS.get(sign, ()))
    ruler_sun_contacts = [
        event for event in cluster_events
        if str(_value(event, "kind", "")) == "aspect"
        and "Sun" in set(_value(event, "planets", ()) or ())
        and set(_value(event, "planets", ()) or ()) & rulers
        and "conjunction" in str(_value(event, "title", "")).lower()
    ]
    lunations = [event for event in cluster_events if str(_value(event, "kind", "")) == "lunation"]
    anchors = eclipses or ruler_sun_contacts or lunations
    if anchors:
        anchor = max(anchors, key=lambda event: _event_weight(event, sign, house_weights))
        anchor_houses = [int(value) for value in (_value(anchor, "houses", ()) or ())]
        if anchor_houses:
            return max(anchor_houses, key=lambda house: float((house_weights or {}).get(house, 0.0)))

    maximum_house_weight = max((float(v) for v in (house_weights or {}).values()), default=1.0) or 1.0
    scored: list[tuple[float, int]] = []
    for house in houses:
        event_support = sum(
            _event_weight(event, sign, house_weights)
            for event in cluster.get("events", ())
            if house in {int(value) for value in (_value(event, "houses", ()) or ())}
        )
        raw_bonus = 2.2 * (float((house_weights or {}).get(house, 0.0)) / maximum_house_weight)
        scored.append((event_support + raw_bonus, house))
    return max(scored, key=lambda item: (item[0], -item[1]))[1]


def _cluster_label(cluster: dict | None) -> str:
    if not cluster:
        return "no dominant cluster"
    return _date_range_label(cluster["start"], cluster["end"])


def _event_cluster(
    event: object,
    events: Sequence[object],
    sign: str,
    window_days: int = 1,
    house_weights: Mapping[int, float] | None = None,
) -> dict:
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
        "score": sum(
            weight * factor
            for weight, factor in zip(
                sorted((_event_weight(item, sign, house_weights) for item in members), reverse=True)[:3],
                (1.0, 0.55, 0.30),
            )
        ),
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
    house_weights: Mapping[int, float] | None = None,
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
        scenario_keys = _scenario_keys(
            _cluster_scenarios(cluster, sign, main_focus, house_weights=house_weights)
        )
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
    house_weights: Mapping[int, float] | None = None,
) -> dict | None:
    # Love remains in every report's dedicated Love section. It only becomes a
    # chronological monthly beat when the sky itself directly activates the
    # romance/partnership houses. This prevents a generic Venus aspect in H8/H11
    # from becoming a compulsory Act III relationship test.
    relationship_houses = {5, 7}
    relationship_planets = {"Venus", "Mars", "Jupiter", "Saturn", "Neptune", "Pluto", "Uranus"}

    # A relationship subplot must be materially important for the sign, not just
    # present somewhere in a multi-day cluster. This closes the Pisces-style leak
    # where a weak H5 event near a Venus aspect could create a compulsory romance
    # chapter even though the month is actually about H6 -> H1.
    weights = {int(key): float(value) for key, value in (house_weights or {}).items()}
    if weights:
        top_weight = max(weights.values(), default=0.0)
        qualified_relationship_houses = {
            house for house in relationship_houses
            if weights.get(house, 0.0) >= max(45.0, top_weight * 0.70)
        }
        if not qualified_relationship_houses:
            return None
    else:
        qualified_relationship_houses = set(relationship_houses)

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
    # A relationship beat needs direct house provenance on the anchor event,
    # not merely a nearby event in the same multi-day cluster. This is the key
    # guard against every sign receiving the same Venus-led Act III.
    direct_relationship_events = [
        event for event in selected_events
        if set(int(value) for value in (_value(event, "houses", ()) or ())) & qualified_relationship_houses
    ]
    if not direct_relationship_events:
        return None
    anchors = [
        event for event in direct_relationship_events
        if "Venus" in set(_value(event, "planets", ()) or ())
    ] or direct_relationship_events

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
        anchor_houses = set(int(value) for value in (_value(anchor, "houses", ()) or ()))
        candidate_relationship_houses = anchor_houses & qualified_relationship_houses
        if not candidate_relationship_houses:
            continue
        relationship_house = max(
            candidate_relationship_houses,
            key=lambda house: weights.get(house, 0.0) if weights else 1.0,
        )
        cluster = {
            "start": min(dates),
            "end": max(dates),
            "score": sum(_event_weight(item, sign) for item in members),
            "events": members,
            "houses": tuple(house for house, _ in Counter(houses).most_common()),
            "planets": tuple(planet for planet, _ in Counter(planets).most_common()),
            "relationship_house": relationship_house,
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
        if set(houses) & qualified_relationship_houses:
            score += 1.0
        if polarities & {"opportunity", "new cycle"} and polarities & {"pressure", "review"}:
            score += 3.2
        scenario_keys = _scenario_keys(
            _cluster_scenarios(cluster, sign, main_focus, house_weights=house_weights)
        )
        if "relationship_opening" in scenario_keys:
            score += 1.4
        candidates.append((score, cluster))

    chosen = max(candidates, key=lambda item: item[0], default=(0.0, None))
    return chosen[1] if chosen[0] >= 6.0 else None


def _relationship_test_copy(cluster: dict | None, sign: str = "") -> tuple[str, ...]:
    if not cluster:
        return ()
    events = cluster.get("events", ())
    planets = {str(planet) for item in events for planet in (_value(item, "planets", ()) or ())}
    houses = {int(value) for value in cluster.get("houses", ())}
    window = _date_range_label(cluster["start"], cluster["end"])
    direct_house = int(cluster.get("relationship_house") or (7 if 7 in houses else 5 if 5 in houses else 0))
    sign_order = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    variant = sign_order.index(sign) % 4 if sign in sign_order else 0

    if direct_house == 7:
        first_options = (
            f"Around {window}, a connection or agreement becomes more revealing once the next step has to be mutual.",
            f"Around {window}, another person's response matters more than the first wave of attention.",
            f"Around {window}, partnership energy moves from interest into terms, timing and reciprocity.",
            f"Around {window}, the useful question is no longer whether there is interest, but whether both sides can carry the plan.",
        )
    else:
        first_options = (
            f"Around {window}, chemistry, pleasure or creative attention gets a chance to prove it can develop.",
            f"Around {window}, the spark is easy to notice; the second move tells you whether it has direction.",
            f"Around {window}, attraction or creative excitement becomes more useful when somebody turns it into a plan.",
            f"Around {window}, attention rises quickly, but continuity is what gives the moment meaning.",
        )

    if {"Venus", "Jupiter", "Saturn"} <= planets:
        second_options = (
            "Enjoy the warmth, then watch what remains when timing and responsibility enter the room.",
            "Let optimism open the door; let consistency and realistic timing decide how far it stays open.",
            "A generous first response is encouraging. The stronger evidence is follow-through after the practical question arrives.",
            "Approval is useful, but durability is better evidence than intensity alone.",
        )
    elif "Venus" in planets and "Saturn" in planets:
        second_options = (
            "Interest may be real, but timing, distance, availability or responsibility reveals whether it can continue.",
            "Do not measure the connection by chemistry alone; measure what each person is prepared to carry.",
            "The practical limit is not a romance killer. It is the information that makes the next choice cleaner.",
            "Watch what remains after the mood changes. Effort is the evidence.",
        )
    elif "Venus" in planets and ("Neptune" in planets or "Pluto" in planets):
        second_options = (
            "Keep motive, terms and power balance visible while the chemistry is strong.",
            "Intensity can introduce the story; it should not be allowed to write the agreement by itself.",
            "Enjoy the pull, but verify what is actually being offered before giving it more meaning.",
            "The strongest attraction is still easier to trust when expectations can be spoken plainly.",
        )
    else:
        second_options = (
            "Let behaviour decide what earns more access.",
            "The second response carries more information than the first impression.",
            "Consistency is the part of the story worth keeping.",
            "Notice whether the connection still works when a real plan is required.",
        )
    return (first_options[variant], second_options[variant])


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
    *,
    house_weights: Mapping[int, float] | None = None,
    required_house: int | None = None,
) -> ArcBeat:
    if cluster:
        scenarios = _cluster_scenarios(
            cluster,
            sign,
            main_focus,
            house_weights=house_weights,
            required_house=required_house,
        )
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
            scenario_provenance=tuple(
                {
                    "key": item.key,
                    "scenario_houses": list(item.scenario_houses),
                    "matched_houses": list(item.matched_houses),
                }
                for item in scenarios
            ),
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
        scenario_provenance=(),
        evidence=(),
    )


def _headline_and_axis(
    month: str,
    opening_scenarios: Sequence[ScenarioResult],
    climax_scenarios: Sequence[ScenarioResult],
    *,
    primary_house: int | None = None,
    secondary_house: int | None = None,
) -> tuple[str, str, str]:
    opening = _scenario_keys(opening_scenarios)
    climax = _scenario_keys(climax_scenarios)
    pair = (primary_house, secondary_house)

    # High-value combinations get bespoke consequence-first language. These are
    # narrative families, not sign templates: the pair is chosen by the event
    # graph for the month.
    ordered_pair_copy = {
        (5, 12): (
            "The spark grows louder before the quieter truth decides what stays",
            "Romance, creativity or pleasure opens the month; rest, closure or private reality decides what deserves a future.",
            "Romance & creativity x Rest & private renewal",
        ),
        (4, 11): (
            "The private foundation changes when the right people widen the future",
            "Home or family sets the starting condition; friends, audiences or future plans show which version can grow.",
            "Home & family x Friends & future plans",
        ),
        (3, 4): (
            "The conversation changes the options; home decides where they land",
            "Messages, contracts or movement open the plot; home, family or location determines the workable result.",
            "Communication & decisions x Home & private life",
        ),
        (2, 9): (
            "The numbers clear the runway for a wider move",
            "Money and value set the terms; travel, study, publishing or an international opening shows what those terms can support.",
            "Money & value x Travel & wider horizons",
        ),
        (3, 10): (
            "The message becomes a career decision once the result is visible",
            "A contract, assignment or important conversation opens the month; career, reputation or a public result shows what the message can become.",
            "Communication & decisions x Career & visibility",
        ),
        (1, 8): (
            "The new direction gets real when trust and resources are named",
            "A personal opening gathers force, then shared money, ownership or responsibility reveals what can actually continue.",
            "Identity & direction x Trust & shared resources",
        ),
        (12, 1): (
            "The private ending clears space for a more visible beginning",
            "Closure, recovery or unfinished business changes the background; a personal decision then makes the next direction visible.",
            "Rest & private renewal x Identity & direction",
        ),
        (12, 7): (
            "The private chapter reaches its answer through another person",
            "Rest, closure or confidential work shapes the background; a partner, collaborator or agreement then requires a clear decision about what continues.",
            "Rest & private renewal x Relationships & agreements",
        ),
        (11, 6): (
            "The future plan survives only if the week can carry it",
            "Friends, audiences or a larger goal create momentum; workload, routine and wellbeing decide whether it can last.",
            "Friends & future plans x Work & wellbeing",
        ),
        (10, 5): (
            "The visible result matters more when desire and creativity return",
            "Career or reputation moves into view; romance, pleasure or creative response changes what the success is for.",
            "Career & visibility x Romance & creativity",
        ),
        (9, 4): (
            "The wider horizon opens; home decides what can stay",
            "A larger possibility gathers momentum, then home, family or location determines how it can fit real life.",
            "Travel & wider horizons x Home & private life",
        ),
        (8, 3): (
            "The shared stake becomes manageable once the facts are spoken",
            "Trust, debt or shared resources set the pressure; a message, document or direct conversation makes the next move usable.",
            "Shared resources & trust x Communication & decisions",
        ),
        (7, 2): (
            "The relationship or agreement gets serious when value is clear",
            "A partner, client or agreement opens the month; money, pricing or personal value decides what the arrangement can support.",
            "Relationships & agreements x Money & value",
        ),
        (6, 1): (
            "The workload changes shape when you decide what deserves your energy",
            "Work, routine or wellbeing reveals the practical condition; a personal decision then resets the direction.",
            "Work & wellbeing x Identity & direction",
        ),
    }
    if pair in ordered_pair_copy:
        return ordered_pair_copy[pair]
    if pair in {(5, 6), (6, 5)}:
        return (
            "The spark becomes real when the week can carry it",
            "A creative, romantic or entrepreneurial opening gains value when the daily rhythm can support it.",
            "Romance & creativity x Work & wellbeing",
        )
    if pair in {(1, 2), (1, 8)}:
        return (
            "The new direction gets real when the numbers do",
            "A personal opening gathers force, then money, value or shared obligations reveal what can actually continue.",
            "Identity & direction x Money & resources",
        )
    if pair in {(9, 10), (10, 9)}:
        return (
            "The wider horizon matters most when it produces a visible result",
            "Travel, study, publishing or an international opening becomes consequential when it changes the public direction.",
            "Travel & wider horizons x Career & visibility",
        )
    if pair in {(9, 4), (4, 9)}:
        return (
            "The wider horizon opens; home decides what can stay",
            "A larger possibility gathers momentum, then home, family or location determines how it can fit real life.",
            "Expansion & opportunity x Home & private life",
        )
    if pair in {(7, 8), (8, 7)}:
        return (
            "The connection gets serious when trust and resources are named",
            "A relationship or agreement develops, then shared money, ownership or responsibility reveals the workable terms.",
            "Relationships & agreements x Trust & shared resources",
        )

    financial = bool(opening & {"financial_shock", "earned_income", "external_money", "funding_application", "paperwork_verification"})
    expansion = bool(climax & {"travel", "publishing_media", "visa_legal_study", "career_interview", "contracts_agreements"})
    romance = bool(opening & {"relationship_opening", "romance_creativity", "partnership_commitment"})
    property_close = bool(climax & {"property_home"})

    if financial and expansion:
        return (
            f"{month} checks the numbers before it widens the plan",
            "The month starts with terms and proof, then shows which larger possibility can carry them.",
            "Money & obligations x Expansion & opportunity",
        )
    if romance and property_close:
        return (
            "The spark arrives before the address is settled",
            "Attraction opens the story. Real life decides where it can live.",
            "Romance & connection x Home & private life",
        )
    if romance and expansion:
        return (
            "The invitation becomes meaningful when it creates a real next step",
            "A connection widens the future, then timing, distance or direction asks for a practical plan.",
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

    primary_label = HOUSE_SHORT.get(primary_house or 1, "the opening")
    secondary_label = HOUSE_SHORT.get(secondary_house or primary_house or 1, "the practical result")
    return (
        f"{primary_label.capitalize()} changes shape when {secondary_label} becomes real",
        "The strongest event cluster opens the plot; a later cluster changes the terms and leaves a clearer decision.",
        f"{primary_label.title()} x {secondary_label.title()}",
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
        f"The breakthrough that appeared around {inherited_window} enters {month} with unfinished momentum. A trip, course, application, publication, international contact or larger plan may already be answering back.",
        f"Around {inciting_window}, a friend, audience, organisation or useful contact can help give the idea shape. The possibility starts to look less hypothetical and more discussable.",
    )
    complication_text = (
        f"Around {complication_window}, the opportunity becomes more exciting - and more consequential. Cost, distance, shared money, ownership, trust, paperwork or another person's influence may enter the picture.",
        "The complication does not automatically weaken the opening. It reveals the terms of the game. A message, agreement or approval can make the next step visible once those terms are named.",
    )
    pivot_text: tuple[str, ...] = ()
    relationship_text = _relationship_test_copy(relationship_test, sign)
    climax_text = (
        f"Around {climax_window}, the project, application, trip or relationship seeks a visible result. Career, reputation or an official decision moves the story into public view.",
        "Then home, family, location or emotional security asks where the result will live. The opportunity earns its place only when public ambition and private reality can support each other.",
    )
    resolution_text = (
        "The month ends with a clearer position: keep the future that can name its cost, show consistent effort and fit the life you actually want to live.",
    )

    if {"Venus", "Jupiter", "Saturn"} <= relationship_planets:
        relationship_text = (
            f"Around {relationship_window}, attention, warmth or approval rises before Saturn asks for proof. Are they here for you - or just for the fun of it?",
            "Let the second move answer. Interest becomes valuable when it survives timing, responsibility and the need for an actual plan.",
        )

    return (
        opening,
        complication_text,
        pivot_text,
        climax_text,
        resolution_text,
        relationship_text,
        "Let the larger plan name its cost, next step and place in your life.",
        "Mistake a thrilling opening for a finished agreement. Even magic needs logistics.",
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
    primary_plot: dict | None = None,
    secondary_plot: dict | None = None,
    *,
    primary_house: int,
    secondary_house: int,
    house_weights: Mapping[int, float] | None = None,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], str, str]:
    fallback_house = int(max((house_weights or {1: 1.0}).items(), key=lambda item: item[1])[0])

    def cluster_house(cluster: dict | None, fallback: int) -> int:
        return _cluster_dominant_house(cluster, sign, house_weights, fallback) if cluster else fallback

    def scenarios(cluster: dict | None, required_house: int | None = None) -> tuple[ScenarioResult, ...]:
        if not cluster:
            return ()
        target_house = required_house or cluster_house(cluster, fallback_house)
        return _cluster_scenarios(
            cluster,
            sign,
            main_focus,
            house_weights=house_weights,
            required_house=target_house,
        )

    inherited_results = scenarios(inherited)
    inciting_results = scenarios(inciting)
    complication_results = scenarios(complication, primary_house if complication is primary_plot else None)
    pivot_results = scenarios(pivot)
    climax_results = scenarios(climax, secondary_house if climax is secondary_plot else None)
    resolution_results = scenarios(resolution, secondary_house if resolution is secondary_plot else None)
    relationship_results = scenarios(relationship_test)
    primary_results = scenarios(primary_plot, primary_house)
    secondary_results = scenarios(secondary_plot, secondary_house)

    def examples(results: Sequence[ScenarioResult], maximum: int = 3) -> str:
        values: list[str] = []
        for item in results:
            for example in item.examples:
                if example not in values:
                    values.append(example)
                if len(values) >= maximum:
                    return ", ".join(values)
        return ", ".join(values) or "a person, choice or opportunity"

    opening_basis = primary_results or inciting_results or inherited_results
    climax_basis = secondary_results or climax_results or resolution_results

    primary_leads = {
        1: "A personal opening starts the month",
        2: "The month opens by putting a number on what matters",
        3: "A message, contract or assignment opens the plot",
        4: "Home, family or location sets the starting condition",
        5: "Romance, creativity or pleasure supplies the opening spark",
        6: "Work, routine or wellbeing reveals the practical condition first",
        7: "A partner, client or agreement opens the story",
        8: "Shared money, trust or obligation sets the first terms",
        9: "A wider-world possibility gives the month its opening momentum",
        10: "Career or public visibility moves to the front of the month",
        11: "Friends, audiences or a future goal create the first opening",
        12: "The month begins quietly, through closure, preparation or private work",
    }
    secondary_leads = {
        1: "By late month, the answer becomes personal",
        2: "By late month, value and cash flow decide what survives",
        3: "By late month, the decisive fact arrives through a message, document or conversation",
        4: "By late month, home, family or location decides how the opening fits real life",
        5: "By late month, desire, creativity or a child-related matter changes the stakes",
        6: "By late month, workload, staffing, routine or wellbeing tests the plan",
        7: "By late month, another person or agreement requires a clear answer",
        8: "By late month, shared money, ownership or responsibility exposes the real terms",
        9: "By late month, travel, study, publishing or an official wider-world matter changes the route",
        10: "By late month, career, reputation or a visible result makes the outcome public",
        11: "By late month, friends, networks or the future plan show which version can grow",
        12: "By late month, rest, closure or a private reality decides what should be released",
    }
    do_lines = {
        1: "Choose the version that gives you more agency after the excitement fades.",
        2: "Put the number beside the promise before you commit.",
        3: "Get the important words, dates and terms into writing.",
        4: "Make sure the larger plan can live inside the home and family reality.",
        5: "Enjoy the spark, then give it one concrete next step.",
        6: "Protect the routine that lets the opportunity keep working.",
        7: "Ask for mutual terms instead of guessing what the other person intends.",
        8: "Name ownership, cost and responsibility before trust does the work for you.",
        9: "Turn the wider possibility into an itinerary, application or decision.",
        10: "Make the result visible and let the response become evidence.",
        11: "Follow the introductions that support the future you actually want.",
        12: "Leave enough quiet to hear what the month is asking you to finish.",
    }
    dont_lines = {
        1: "Let other people's enthusiasm choose your direction for you.",
        2: "Confuse a hopeful number with money that is already available.",
        3: "Assume everyone heard the same thing you did.",
        4: "Build the future on a private arrangement nobody has agreed to.",
        5: "Call chemistry, applause or excitement a finished plan.",
        6: "Spend tomorrow's energy to make today's opening look bigger.",
        7: "Fill in the other person's half of the agreement yourself.",
        8: "Leave shared obligations vague because the mood is good.",
        9: "Treat inspiration as permission to skip the document, deadline or route.",
        10: "Mistake visibility for permanence before the terms are clear.",
        11: "Say yes to every invitation just because the room is opening.",
        12: "Force an ending to become a new beginning before it is complete.",
    }

    opening = (
        f"{primary_leads.get(primary_house, month + ' reveals its main opening')}: {examples(opening_basis)}. "
        "The early movement is useful because it shows where the month is gathering force, not because it guarantees the final outcome.",
    )

    complication_window = _date_range_label(complication['start'], complication['end']) if complication else f"mid-{month}"
    complication_text = (
        f"Around {complication_window}, the opening has to deal with {examples(complication_results)}. "
        "That detail changes the terms: what looked attractive now has to become workable.",
    )

    pivot_window = _date_range_label(pivot['start'], pivot['end']) if pivot else f"the middle of {month}"
    pivot_subject = examples(pivot_results)
    pivot_house_lines = {
        1: "a personal decision becomes easier to own once the missing fact arrives",
        2: "a price, payment or value question becomes easier to judge once the number is usable",
        3: "a message, document or conversation begins to clear the stalled part of the plan",
        4: "a home, family or location question becomes easier to place inside the larger decision",
        5: "a creative or romantic opening becomes easier to judge once there is a believable next move",
        6: "a workload, routine or wellbeing issue becomes easier to organise once the practical condition is visible",
        7: "a partner, client or agreement becomes easier to evaluate once both sides respond clearly",
        8: "a shared-money or responsibility question becomes easier to manage once ownership is named",
        9: "a travel, study, publishing or legal path becomes easier to use once the official step is clear",
        10: "a career or visibility decision becomes easier to make once the public response is measurable",
        11: "a network, audience or future plan becomes easier to trust once the useful people keep showing up",
        12: "a private or unfinished matter becomes easier to release once you know what no longer needs your energy",
    }
    if pivot_results:
        pivot_clause = pivot_subject
    else:
        pivot_clause = pivot_house_lines.get(primary_house, "the stalled part of the story begins to clear")
    pivot_text = (
        f"Around {pivot_window}, {pivot_clause}. The new information does not erase the earlier condition; it gives you a better way to respond to it.",
    )

    climax_window = _date_range_label((secondary_plot or climax or resolution)['start'], (secondary_plot or climax or resolution)['end']) if (secondary_plot or climax or resolution) else f"late {month}"
    climax_text = (
        f"{secondary_leads.get(secondary_house, 'By late month, the second plot takes control')}. Around {climax_window}, this can look like {examples(climax_basis)}. "
        "The point is not to predict one literal event; it is to show where the month's consequence becomes hardest to ignore.",
    )

    resolution_basis = resolution_results or secondary_results or climax_results
    resolution_text = (
        f"The closing decision is therefore about {HOUSE_SHORT.get(secondary_house, 'what the second plot requires')}. "
        f"Use {examples(resolution_basis, maximum=2)} as possible manifestations, then keep the version that remains coherent with the evidence already visible.",
    )
    relationship_text = _relationship_test_copy(relationship_test, sign)
    return (
        opening,
        complication_text,
        pivot_text,
        climax_text,
        resolution_text,
        relationship_text,
        do_lines.get(primary_house, "Follow the evidence from opening to outcome."),
        dont_lines.get(primary_house, "Treat the first scene as the whole story."),
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
    house_weights: Mapping[int, float] | None = None,
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

    monthly_clusters = _clusters(monthly_events, sign, house_weights=house_weights)
    inherited_clusters = _clusters(carryover, sign, window_days=3, house_weights=house_weights)

    carryover_triggers = [
        event
        for event in carryover
        if str(_value(event, "kind", "")) in {"lunation", "eclipse", "station"}
    ]
    if carryover_triggers:
        latest_date = max(_date_value(item) for item in carryover_triggers)
        latest = [item for item in carryover_triggers if _date_value(item) == latest_date]
        anchor = max(latest, key=lambda item: _event_weight(item, sign))
        inherited = _event_cluster(anchor, carryover, sign, window_days=2, house_weights=house_weights)
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
        house_weights,
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
        house_weights=house_weights,
    )

    direct_events = [
        event
        for event in monthly_events
        if str(_value(event, "kind", "")) == "station"
        and str(_value(event, "polarity", "")) == "release"
    ]
    if direct_events:
        chosen_direct = max(direct_events, key=lambda item: _event_weight(item, sign))
        pivot = _event_cluster(chosen_direct, monthly_events, sign, window_days=1, house_weights=house_weights)
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
        resolution = _event_cluster(max(final_triggers, key=_date_value), monthly_events, sign, window_days=0, house_weights=house_weights)
    else:
        resolution = climax

    inherited_scenarios = _cluster_scenarios(
        inherited, sign, main_focus, house_weights=house_weights
    ) or _top_scenarios(
        carryover + monthly_events[:3],
        sign,
        main_focus,
        maximum=4,
        house_weights=house_weights,
    )
    complication_scenarios = _cluster_scenarios(
        complication, sign, main_focus, house_weights=house_weights
    )
    climax_scenarios = _cluster_scenarios(
        climax, sign, main_focus, house_weights=house_weights
    )
    global_scenarios = rank_scenarios(carryover + monthly_events, sign, main_focus, maximum=12, house_weights=house_weights)
    all_scenarios = _narrative_scenario_ranking(
        inherited_scenarios,
        complication_scenarios,
        climax_scenarios,
        global_scenarios,
        maximum=8,
    )

    # Event-led story driver selection. The main plot comes from the strongest
    # pre-climax cluster; the late major cluster becomes the secondary plot /
    # resolution. Raw house weights remain a supporting signal rather than a
    # mandatory solar-house backbone.
    primary_candidates = [
        cluster for cluster in monthly_clusters
        if cluster["start"] <= max(start, end - timedelta(days=8))
    ] or list(monthly_clusters)
    complication_has_major_lunation = bool(
        complication
        and any(str(_value(item, "kind", "")) in {"eclipse", "lunation"} for item in complication.get("events", ()))
    )
    primary_plot = (
        complication
        if complication_has_major_lunation
        else max(primary_candidates, key=lambda item: item["score"], default=complication or inciting or inherited)
    )

    resolution_has_eclipse = bool(
        resolution
        and any(str(_value(item, "kind", "")) == "eclipse" for item in resolution.get("events", ()))
    )
    # A late eclipse is a genuine ending/reversal and must control the second
    # plot. A routine full moon may close the month without displacing a much
    # stronger late conjunction or station that carries the actual result.
    secondary_plot = resolution if resolution_has_eclipse else (climax or resolution)

    fallback_house = int(max((house_weights or {1: 1.0}).items(), key=lambda item: item[1])[0])
    primary_house = _cluster_dominant_house(primary_plot, sign, house_weights, fallback_house)
    secondary_house = _cluster_dominant_house(secondary_plot, sign, house_weights, primary_house)
    raw_ranked_houses = [
        int(house) for house, _weight in sorted((house_weights or {}).items(), key=lambda item: -item[1])
    ]
    supporting_house = next(
        (house for house in raw_ranked_houses if house not in {primary_house, secondary_house}),
        primary_house,
    )

    primary_plot_scenarios = _cluster_scenarios(
        primary_plot,
        sign,
        main_focus,
        house_weights=house_weights,
        required_house=primary_house,
    )
    secondary_plot_scenarios = _cluster_scenarios(
        secondary_plot,
        sign,
        main_focus,
        house_weights=house_weights,
        required_house=secondary_house,
    )
    month = label.split()[0]
    headline, central, axis = _headline_and_axis(
        month,
        primary_plot_scenarios or inherited_scenarios,
        secondary_plot_scenarios or climax_scenarios,
        primary_house=primary_house,
        secondary_house=secondary_house,
    )

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
    # v3 intentionally avoids a universal expansion/relationship template.
    # If the calibrated July pattern does not apply, assemble the story from
    # the actual event graph instead.
    if not story[0]:
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
            primary_plot,
            secondary_plot,
            primary_house=primary_house,
            secondary_house=secondary_house,
            house_weights=house_weights,
        )


    opening, complication_text, pivot_text, climax_text, resolution_text, relationship_text, do_line, dont_line = story

    if not relationship_text:
        relationship_text = _relationship_test_copy(relationship_test, sign)

    beat_list = [
        _beat(
            "inherited state",
            inherited,
            sign,
            main_focus,
            opening[0],
            "Identify the amount, timing or condition before reacting.",
            start,
            house_weights=house_weights,
            required_house=_cluster_dominant_house(inherited, sign, house_weights, primary_house) if inherited else primary_house,
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
            "Treat the first response as information, not the final result.",
            start + timedelta(days=3),
            house_weights=house_weights,
            required_house=_cluster_dominant_house(inciting, sign, house_weights, primary_house) if inciting else primary_house,
        ),
        _beat(
            "complication",
            complication,
            sign,
            main_focus,
            complication_text[0],
            "Make the cost, document, expectation or practical condition visible.",
            start + timedelta(days=13),
            house_weights=house_weights,
            required_house=primary_house if complication is primary_plot else (_cluster_dominant_house(complication, sign, house_weights, primary_house) if complication else primary_house),
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
                "Use the new information to revise the decision rather than repeat the delay.",
                start + timedelta(days=22),
                house_weights=house_weights,
                required_house=_cluster_dominant_house(pivot, sign, house_weights, primary_house) if pivot else primary_house,
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
                "Let the second move reveal whether the interest can become consistent.",
                start + timedelta(days=18),
                house_weights=house_weights,
                required_house=int(relationship_test.get("relationship_house") or 7) if relationship_test else 7,
            )
        )
    beat_list.extend([
        _beat(
            "climax",
            climax,
            sign,
            main_focus,
            climax_text[0],
            "Act on the strongest supported opportunity while the evidence is visible.",
            end - timedelta(days=2),
            house_weights=house_weights,
            required_house=secondary_house if climax is secondary_plot else (_cluster_dominant_house(climax, sign, house_weights, secondary_house) if climax else secondary_house),
        ),
        _beat(
            "resolution",
            resolution,
            sign,
            main_focus,
            resolution_text[0],
            "Keep the outcome that survives both excitement and practical reality.",
            end,
            house_weights=house_weights,
            required_house=secondary_house,
        ),
    ])
    beats = tuple(sorted(beat_list, key=lambda item: (item.start_date, item.role)))

    story_events = list((primary_plot or {}).get("events", ())) + list((secondary_plot or {}).get("events", ()))
    rulers = set(SIGN_RULERS.get(sign, ()))
    ruler_events = [
        event for event in story_events
        if set(str(value) for value in (_value(event, "planets", ()) or ())) & rulers
    ]
    rulership_evidence = tuple(
        _event_label(event) for event in sorted(ruler_events, key=_date_value)[:4]
    )
    peak_event_score = max(
        (_event_weight(event, sign, house_weights) for event in story_events),
        default=0.0,
    )
    ruler_peak = max(
        (_event_weight(event, sign, house_weights) for event in ruler_events),
        default=0.0,
    )
    rulership_amplified = bool(ruler_events and ruler_peak >= 7.2)
    if rulership_amplified and peak_event_score >= 8.5:
        intensity_rating = "High / inflection point"
    elif peak_event_score >= 8.5:
        intensity_rating = "High"
    elif peak_event_score >= 7.0:
        intensity_rating = "Elevated"
    else:
        intensity_rating = "Steady"

    return MonthlyArc(
        sign=sign,
        label=label,
        headline=headline,
        central_storyline=central,
        theme_axis=axis,
        primary_house=primary_house,
        secondary_house=secondary_house,
        supporting_house=supporting_house,
        selection_rationale=(
            f"Primary plot: {_cluster_label(primary_plot)} / house {primary_house}. "
            f"Secondary plot: {_cluster_label(secondary_plot)} / house {secondary_house}. "
            f"House {supporting_house} retained as strongest additional monthly evidence."
        ),
        intensity_rating=intensity_rating,
        rulership_amplified=rulership_amplified,
        rulership_evidence=rulership_evidence,
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
            "Normalized event importance + sign-ruler relevance + house evidence + "
            "event clustering + deterministic scenario ranking + temporal roles = monthly narrative graph"
        ),
    )
