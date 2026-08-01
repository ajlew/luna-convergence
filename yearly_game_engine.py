from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Mapping, Sequence

from astrology_engine import period_events, retrograde_cycles
from date_display import human_date, human_date_range
from monthly_arc_engine import build_monthly_arc
from scenario_engine import SIGN_RULERS


YEARLY_GAME_VERSION = "Yearly Game Map v1.0"

TRIGGER_WEIGHT = {
    "eclipse": 1.65,
    "lunation": 1.35,
    "station": 1.30,
    "aspect": 1.00,
    "ingress": 0.95,
}

PLANET_ROLES = {
    "Sun": "visibility and direction",
    "Moon": "events, reaction and culmination",
    "Mercury": "information, documents and decisions",
    "Venus": "attraction, value and approval",
    "Mars": "action, urgency and conflict",
    "Jupiter": "expansion, opportunity and reach",
    "Saturn": "limits, proof and durability",
    "Uranus": "shocks, freedom and rule changes",
    "Neptune": "imagination, ambiguity and missing information",
    "Pluto": "power, leverage and irreversible change",
    "True Node": "developmental direction and eclipse emphasis",
}


@dataclass(frozen=True)
class GameDefinition:
    key: str
    title: str
    question: str
    players: frozenset[str]
    houses: frozenset[int]
    advantage: str
    risk: str
    do_line: str
    dont_line: str


GAME_DEFINITIONS: tuple[GameDefinition, ...] = (
    GameDefinition(
        "expansion_capacity",
        "Expansion versus capacity",
        "Can the opportunity grow without outrunning time, money or structure?",
        frozenset({"Jupiter", "Saturn"}),
        frozenset({2, 6, 8, 9, 10, 11}),
        "Scale what has support, proof and repeatable structure.",
        "Treating access to opportunity as proof of capacity.",
        "Build the container before increasing the volume.",
        "Say yes to a future your calendar and budget cannot carry.",
    ),
    GameDefinition(
        "attraction_evidence",
        "Attraction versus evidence",
        "Does the connection continue after chemistry meets timing and responsibility?",
        frozenset({"Venus", "Neptune", "Jupiter", "Saturn"}),
        frozenset({5, 7, 8, 11}),
        "Enjoy attention while letting behaviour reveal motive and capacity.",
        "Promoting warmth, intensity or fantasy to commitment too early.",
        "Let the second move answer the question.",
        "Write a commitment speech for someone still checking their calendar.",
    ),
    GameDefinition(
        "information_ambiguity",
        "Information versus ambiguity",
        "Who has the facts, what remains hidden and what needs verification?",
        frozenset({"Mercury", "Neptune", "Pluto", "Saturn"}),
        frozenset({3, 8, 9, 10, 12}),
        "Ask direct questions, document terms and control the information flow.",
        "Allowing persuasion, silence or missing detail to make the decision.",
        "Get the facts in writing before the stakes rise.",
        "Confuse a convincing story with complete information.",
    ),
    GameDefinition(
        "independence_partnership",
        "Independence versus partnership",
        "How much freedom can the relationship or agreement contain?",
        frozenset({"Uranus", "Venus", "Mars", "Saturn"}),
        frozenset({1, 7, 11}),
        "Negotiate mutual terms without shrinking either person's agency.",
        "Using freedom to avoid definition or commitment to suppress autonomy.",
        "State the boundary before resentment states it for you.",
        "Call mixed signals independence.",
    ),
    GameDefinition(
        "value_obligation",
        "Personal value versus shared obligation",
        "Who pays, who owns, who owes and who carries the risk?",
        frozenset({"Venus", "Mars", "Jupiter", "Saturn", "Pluto"}),
        frozenset({2, 8}),
        "Make ownership, cost and responsibility visible before committing.",
        "Letting affection, urgency or optimism hide an unequal arrangement.",
        "Put the number and the owner next to every promise.",
        "Let chemistry cancel the fine print.",
    ),
    GameDefinition(
        "public_private",
        "Public ambition versus private security",
        "Can the visible result coexist with home, family and emotional wellbeing?",
        frozenset({"Sun", "Moon", "Mercury", "Saturn", "Uranus"}),
        frozenset({4, 10}),
        "Build success around a private life you still recognise.",
        "Winning publicly by exhausting the foundation that supports it.",
        "Choose the result that can live with you after the applause.",
        "Let ambition redecorate your private life without asking.",
    ),
    GameDefinition(
        "cooperation_control",
        "Cooperation versus control",
        "Is this a mutually useful alliance or a struggle over leverage?",
        frozenset({"Venus", "Jupiter", "Mars", "Pluto"}),
        frozenset({7, 8, 10, 11}),
        "Choose alliances where value, information and responsibility move both ways.",
        "Accepting access or intensity in exchange for reduced control.",
        "Keep the terms mutual and the exit visible.",
        "Mistake powerful chemistry for equal power.",
    ),
    GameDefinition(
        "optionality_commitment",
        "Optionality versus commitment",
        "Does keeping every option open prevent the strongest one from developing?",
        frozenset({"Uranus", "Jupiter", "Saturn"}),
        frozenset({1, 5, 7, 9, 11}),
        "Preserve flexibility until the evidence supports a deliberate choice.",
        "Using endless possibility to avoid the cost of choosing.",
        "Keep options open until one starts proving itself.",
        "Collect possibilities like they are outcomes.",
    ),
)


@dataclass(frozen=True)
class AnnualPlayer:
    planet: str
    role: str
    score: float
    houses: tuple[int, ...]
    evidence_count: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AnnualGame:
    key: str
    title: str
    question: str
    score: float
    players: tuple[str, ...]
    houses: tuple[int, ...]
    evidence_months: tuple[str, ...]
    advantage: str
    risk: str
    do_line: str
    dont_line: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class MonthlyRound:
    month: str
    month_number: int
    role: str
    headline: str
    central_storyline: str
    dominant_game: str
    key_window: str
    relationship_test: str
    carryover: str
    scenario_keys: tuple[str, ...]
    score: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AnnualAct:
    name: str
    role: str
    start_date: str
    end_date: str
    dominant_game: str
    summary: str
    months: tuple[str, ...]
    trigger: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class YearlyGameMap:
    sign: str
    year: int
    headline: str
    central_storyline: str
    narrator_paragraphs: tuple[str, ...]
    players: tuple[AnnualPlayer, ...]
    games: tuple[AnnualGame, ...]
    acts: tuple[AnnualAct, ...]
    rounds: tuple[MonthlyRound, ...]
    relationship_arc: tuple[str, ...]
    career_arc: tuple[str, ...]
    money_arc: tuple[str, ...]
    home_arc: tuple[str, ...]
    do_line: str
    dont_line: str
    equation: str
    version: str = YEARLY_GAME_VERSION

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "players": [item.to_dict() for item in self.players],
            "games": [item.to_dict() for item in self.games],
            "acts": [item.to_dict() for item in self.acts],
            "rounds": [item.to_dict() for item in self.rounds],
        }


def _value(event: object, key: str, default: object = None) -> object:
    if isinstance(event, Mapping):
        return event.get(key, default)
    return getattr(event, key, default)


def _event_date(event: object) -> date:
    value = _value(event, "event_date")
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _event_weight(event: object, sign: str) -> float:
    kind = str(_value(event, "kind", ""))
    importance = float(_value(event, "importance", 0.0) or 0.0)
    planets = set(_value(event, "planets", ()) or ())
    if planets == {"Moon"} and kind not in {"lunation", "eclipse"}:
        return 0.0
    weight = TRIGGER_WEIGHT.get(kind, 0.75) * max(0.25, importance / 6.5)
    if planets & set(SIGN_RULERS.get(sign, ())):
        weight *= 1.28
    if kind == "aspect" and planets <= {"Uranus", "Neptune", "Pluto"}:
        weight *= 0.72
    return weight


def _player_scores(events: Sequence[object], sign: str) -> tuple[AnnualPlayer, ...]:
    scores: defaultdict[str, float] = defaultdict(float)
    houses: defaultdict[str, Counter[int]] = defaultdict(Counter)
    counts: Counter[str] = Counter()
    for event in events:
        event_weight = _event_weight(event, sign)
        if event_weight <= 0:
            continue
        for planet in (_value(event, "planets", ()) or ()):
            planet = str(planet)
            scores[planet] += event_weight
            counts[planet] += 1
            for house in (_value(event, "houses", ()) or ()):
                houses[planet][int(house)] += 1
    rulers = set(SIGN_RULERS.get(sign, ()))
    results = []
    for planet, score in scores.items():
        if planet in rulers:
            score *= 1.18
        results.append(
            AnnualPlayer(
                planet=planet,
                role=("Lead strategist: " if planet in rulers else "") + PLANET_ROLES.get(planet, "strategic influence"),
                score=round(score, 2),
                houses=tuple(house for house, _ in houses[planet].most_common(4)),
                evidence_count=counts[planet],
            )
        )
    return tuple(sorted(results, key=lambda item: item.score, reverse=True)[:7])


def _monthly_game_support(arc: dict, definition: GameDefinition) -> float:
    beat_houses = {
        int(house)
        for beat in arc.get("beats") or []
        for house in beat.get("houses") or []
    }
    beat_planets = {
        str(planet)
        for beat in arc.get("beats") or []
        for planet in beat.get("planets") or []
    }
    house_overlap = len(beat_houses & definition.houses)
    planet_overlap = len(beat_planets & definition.players)
    relationship_bonus = 1.2 if definition.key == "attraction_evidence" and arc.get("relationship_test") else 0.0
    return house_overlap * 0.45 + planet_overlap * 0.32 + relationship_bonus


def _game_scores(
    events: Sequence[object],
    sign: str,
    monthly_arcs: Sequence[dict],
) -> tuple[AnnualGame, ...]:
    monthly_names = [date(2000, index, 1).strftime("%B") for index in range(1, 13)]
    results: list[AnnualGame] = []
    for definition in GAME_DEFINITIONS:
        score = 0.0
        evidence_months: list[str] = []
        for event in events:
            event_houses = {int(value) for value in (_value(event, "houses", ()) or ())}
            event_planets = {str(value) for value in (_value(event, "planets", ()) or ())}
            house_overlap = len(event_houses & definition.houses)
            planet_overlap = len(event_planets & definition.players)
            if not house_overlap or not planet_overlap:
                continue
            contribution = _event_weight(event, sign) * (1 + 0.18 * house_overlap + 0.16 * planet_overlap)
            score += contribution
            month_name = _event_date(event).strftime("%B")
            if month_name not in evidence_months:
                evidence_months.append(month_name)
        for index, arc in enumerate(monthly_arcs):
            support = _monthly_game_support(arc, definition)
            score += support
            if support >= 1.7 and monthly_names[index] not in evidence_months:
                evidence_months.append(monthly_names[index])
        results.append(
            AnnualGame(
                key=definition.key,
                title=definition.title,
                question=definition.question,
                score=round(score, 2),
                players=tuple(sorted(definition.players)),
                houses=tuple(sorted(definition.houses)),
                evidence_months=tuple(evidence_months[:8]),
                advantage=definition.advantage,
                risk=definition.risk,
                do_line=definition.do_line,
                dont_line=definition.dont_line,
            )
        )
    return tuple(sorted(results, key=lambda item: item.score, reverse=True)[:3])


def _dominant_game_for_arc(arc: dict, games: Sequence[AnnualGame]) -> AnnualGame:
    definitions = {item.key: item for item in GAME_DEFINITIONS}
    ranked = []
    for game in games:
        ranked.append((_monthly_game_support(arc, definitions[game.key]), game))
    return max(ranked, key=lambda item: item[0], default=(0.0, games[0]))[1]


def _round_role(month_number: int, arc: dict) -> str:
    beats = {str(item.get("role")): item for item in arc.get("beats") or []}
    eclipse = any("Eclipse" in str(item.get("title", "")) for item in beats.values())
    relationship_score = float((beats.get("relationship test") or {}).get("score", 0.0) or 0.0)
    complication_score = float((beats.get("complication") or {}).get("score", 0.0) or 0.0)
    climax_score = float((beats.get("climax") or {}).get("score", 0.0) or 0.0)
    inciting_score = float((beats.get("inciting event") or {}).get("score", 0.0) or 0.0)
    pivot_title = str((beats.get("pivot") or {}).get("title", ""))

    if eclipse and max(complication_score, climax_score) >= 8.0:
        return "Rule change"
    if relationship_score >= 7.0:
        return "Commitment test"
    if complication_score >= 7.5 and complication_score > climax_score * 1.05:
        return "Complication"
    if climax_score >= 9.0:
        return "Climax"
    if "stations direct" in pivot_title.lower() or pivot_title.lower().endswith(" direct"):
        return "Pivot"
    if month_number == 1:
        return "Inherited position"
    if month_number >= 11:
        return "Consolidation"
    if inciting_score >= 5.5:
        return "Expansion"
    return "Strategic move"


def _key_window(arc: dict) -> str:
    beats = list(arc.get("beats") or [])
    if not beats:
        return ""
    strongest = max(beats, key=lambda item: float(item.get("score", 0.0) or 0.0))
    return human_date_range(strongest.get("start_date"), strongest.get("end_date"))


def _build_monthly_arcs(
    sign: str,
    year: int,
    timezone_name: str,
    main_focus: str,
) -> tuple[dict, ...]:
    arcs: list[dict] = []
    for month in range(1, 13):
        start = date(year, month, 1)
        end = date(year, 12, 31) if month == 12 else date(year, month + 1, 1) - timedelta(days=1)
        events = period_events(start, end, sign, timezone_name)
        inherited = period_events(start - timedelta(days=7), start - timedelta(days=1), sign, timezone_name)
        cycles = retrograde_cycles(start, end, sign, timezone_name)
        arc = build_monthly_arc(
            sign=sign,
            start=start,
            end=end,
            label=f"{start.strftime('%B')} {year}",
            events=events,
            inherited_events=inherited,
            retrograde_cycles=cycles,
            main_focus=main_focus,
        ).to_dict()
        arcs.append(arc)
    return tuple(arcs)


def _build_rounds(monthly_arcs: Sequence[dict], games: Sequence[AnnualGame]) -> tuple[MonthlyRound, ...]:
    rounds: list[MonthlyRound] = []
    for month_number, arc in enumerate(monthly_arcs, 1):
        game = _dominant_game_for_arc(arc, games)
        relationship = tuple(str(item) for item in (arc.get("relationship_test") or ()))
        opening = tuple(str(item) for item in (arc.get("opening") or ()))
        scenario_keys = tuple(str(item.get("key")) for item in (arc.get("ranked_scenarios") or [])[:4])
        beat_score = max((float(item.get("score", 0.0) or 0.0) for item in (arc.get("beats") or [])), default=0.0)
        rounds.append(
            MonthlyRound(
                month=date(2000, month_number, 1).strftime("%B"),
                month_number=month_number,
                role=_round_role(month_number, arc),
                headline=str(arc.get("headline", "The month changes the board")),
                central_storyline=str(arc.get("central_storyline", "A strategic move develops.")),
                dominant_game=game.title,
                key_window=_key_window(arc),
                relationship_test=relationship[0] if relationship else "",
                carryover=opening[0] if opening else "",
                scenario_keys=scenario_keys,
                score=round(beat_score, 2),
            )
        )
    return tuple(rounds)


def _rule_change_candidates(events: Sequence[object], sign: str, year: int) -> list[dict]:
    rulers = set(SIGN_RULERS.get(sign, ()))
    slow = {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}
    selected = []
    for event in events:
        kind = str(_value(event, "kind", ""))
        planets = set(_value(event, "planets", ()) or ())
        importance = float(_value(event, "importance", 0.0) or 0.0)
        if kind in {"eclipse", "station"}:
            pass
        elif kind == "ingress" and not (planets & (slow | rulers)):
            continue
        elif kind == "aspect" and not (planets & rulers and importance >= 6.5):
            continue
        else:
            continue
        selected.append({
            "date": _event_date(event),
            "title": str(_value(event, "title", "Rule change")),
            "score": _event_weight(event, sign),
        })
    selected.sort(key=lambda item: item["date"])
    clusters: list[dict] = []
    for item in selected:
        existing = next((cluster for cluster in clusters if abs((cluster["date"] - item["date"]).days) <= 14), None)
        if existing:
            existing["score"] += item["score"]
            existing["titles"].append(item["title"])
            if item["score"] > existing["lead_score"]:
                existing["date"] = item["date"]
                existing["lead_score"] = item["score"]
        else:
            clusters.append({"date": item["date"], "score": item["score"], "lead_score": item["score"], "titles": [item["title"]]})
    eligible = [cluster for cluster in clusters if date(year, 2, 1) <= cluster["date"] <= date(year, 11, 30)]
    chosen: list[dict] = []
    for cluster in sorted(eligible, key=lambda item: item["score"], reverse=True):
        if all(abs((cluster["date"] - prior["date"]).days) >= 45 for prior in chosen):
            chosen.append(cluster)
        if len(chosen) >= 3:
            break
    return sorted(chosen, key=lambda item: item["date"])


def _build_acts(
    sign: str,
    year: int,
    rounds: Sequence[MonthlyRound],
    games: Sequence[AnnualGame],
    rule_changes: Sequence[dict],
) -> tuple[AnnualAct, ...]:
    boundaries = [date(year, 1, 1)] + [item["date"] for item in rule_changes] + [date(year, 12, 31)]
    roles = ("Opening position", "Expansion", "Test", "Rule change", "Resolution")
    acts: list[AnnualAct] = []
    for index in range(len(boundaries) - 1):
        start = boundaries[index]
        end = boundaries[index + 1] - timedelta(days=1) if index < len(boundaries) - 2 else boundaries[index + 1]
        included = [item for item in rounds if start.month <= item.month_number <= end.month]
        if not included:
            continue
        game_counts = Counter(item.dominant_game for item in included)
        dominant_game = game_counts.most_common(1)[0][0]
        strongest = max(included, key=lambda item: item.score)
        trigger = "Year opens" if index == 0 else ", ".join(dict.fromkeys(rule_changes[index - 1]["titles"]))
        role = roles[min(index, len(roles) - 1)]
        summary = (
            f"{included[0].month} to {included[-1].month} develops {dominant_game.lower()}. "
            f"{strongest.month} carries the strongest move: {strongest.central_storyline}"
        )
        acts.append(
            AnnualAct(
                name=f"Act {index + 1}",
                role=role,
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                dominant_game=dominant_game,
                summary=summary,
                months=tuple(item.month for item in included),
                trigger=trigger,
            )
        )
    return tuple(acts)


def _arc_by_scenarios(rounds: Sequence[MonthlyRound], keys: set[str], label: str) -> tuple[str, ...]:
    matches = [item for item in rounds if set(item.scenario_keys) & keys]
    if not matches:
        return (f"{label} remains a supporting theme rather than the year's main game.",)
    opening = matches[0]
    peak = max(matches, key=lambda item: item.score)
    closing = matches[-1]
    return (
        f"{label} enters the year through {opening.month}: {opening.central_storyline}",
        f"The strongest test arrives in {peak.month}. {peak.relationship_test or peak.central_storyline}",
        f"By {closing.month}, the issue is judged by what has become repeatable, mutual and practical.",
    )


def _headline(game: AnnualGame) -> str:
    return {
        "expansion_capacity": "Opportunity is not the scarce resource. Capacity is.",
        "attraction_evidence": "Attention gets louder. Standards decide what stays.",
        "information_ambiguity": "The year rewards the person who asks the second question.",
        "independence_partnership": "Freedom wants better relationship terms.",
        "value_obligation": "Every promise eventually meets the spreadsheet.",
        "public_private": "The public win still has to live somewhere.",
        "cooperation_control": "The alliance works only while the leverage stays mutual.",
        "optionality_commitment": "The year opens doors. Choice creates the future.",
    }.get(game.key, "The rules change. Your leverage changes with them.")


def _narrator_paragraphs(
    sign: str,
    year: int,
    games: Sequence[AnnualGame],
    acts: Sequence[AnnualAct],
    rounds: Sequence[MonthlyRound],
) -> tuple[str, ...]:
    first = games[0]
    second = games[1] if len(games) > 1 else games[0]
    strongest_round = max(rounds, key=lambda item: item.score)
    relationship_rounds = [item for item in rounds if item.relationship_test]
    relationship_peak = max(relationship_rounds, key=lambda item: item.score, default=None)
    final_round = rounds[-1]
    change_act = acts[1] if len(acts) > 1 else acts[0]
    paragraphs = [
        f"{year} does not arrive as twelve separate forecasts. Luna reads it as one changing board. {first.title} controls the opening position, and the reader's advantage comes from this rule: {first.advantage}",
        f"The second game is {second.title.lower()}. It asks: {second.question} The answer changes as information, resources and other people's behaviour become visible.",
        f"The first major rule change begins around {human_date(change_act.start_date)}. {change_act.summary}",
        f"{strongest_round.month} carries the strongest concentration of the year. {strongest_round.central_storyline} This is not automatically the happiest month; it is the round with the greatest ability to change later options.",
    ]
    if relationship_peak:
        paragraphs.append(
            f"Relationships have their own test in {relationship_peak.month}. {relationship_peak.relationship_test} Luna is not asking whether the attention feels good. She is asking whether it can become consistent."
        )
    else:
        paragraphs.append(
            "Romance may be active or quiet, but validation still has a storyline. Luna watches who returns, who contributes and which connections make the future easier to build."
        )
    paragraphs.append(
        f"By {final_round.month}, the year's result is less about collecting options and more about position. {final_round.central_storyline} The strongest outcome is the one that improves both leverage and daily life."
    )
    return tuple(paragraphs)


def build_yearly_game_map(
    sign: str,
    year: int,
    timezone_name: str,
    nearest_city: str = "",
    main_focus: str = "General year ahead",
    annual_events: Sequence[object] = (),
) -> YearlyGameMap:
    events = tuple(annual_events) or tuple(period_events(date(year, 1, 1), date(year, 12, 31), sign, timezone_name))
    monthly_arcs = _build_monthly_arcs(sign, year, timezone_name, main_focus)
    games = _game_scores(events, sign, monthly_arcs)
    rounds = _build_rounds(monthly_arcs, games)
    rule_changes = _rule_change_candidates(events, sign, year)
    acts = _build_acts(sign, year, rounds, games, rule_changes)
    players = _player_scores(events, sign)
    top_game = games[0]
    first_change = acts[1].start_date if len(acts) > 1 else f"{year}-07-01"
    central = (
        f"The year's main game is {top_game.title.lower()}. The rules shift around "
        f"{human_date(first_change)}, and the twelve monthly rounds show where the reader gains or loses leverage."
    )
    return YearlyGameMap(
        sign=sign,
        year=year,
        headline=_headline(top_game),
        central_storyline=central,
        narrator_paragraphs=_narrator_paragraphs(sign, year, games, acts, rounds),
        players=players,
        games=games,
        acts=acts,
        rounds=rounds,
        relationship_arc=_arc_by_scenarios(rounds, {"relationship_opening"}, "The relationship game"),
        career_arc=_arc_by_scenarios(rounds, {"career_interview", "publishing_media", "contracts_agreements"}, "The career game"),
        money_arc=_arc_by_scenarios(rounds, {"financial_shock", "external_money", "funding_application", "paperwork_verification"}, "The money game"),
        home_arc=_arc_by_scenarios(rounds, {"property_home"}, "The home game"),
        do_line=top_game.do_line,
        dont_line=top_game.dont_line,
        equation=(
            "Inherited regime + planetary players + dominant games + rule changes + "
            "twelve monthly rounds + path dependence = yearly game"
        ),
    )
