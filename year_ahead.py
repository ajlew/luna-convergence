from __future__ import annotations

"""Deterministic Year Ahead composer.

This module does not calculate a second sky and does not call an LLM. It takes
Luna's already-ranked personal transit arcs from ``timing_map.py``, combines
related/overlapping arcs into a small number of memorable Games, and emits one
chronological packet for the eventual single Year Ahead voice call.

Step 7:
    ranked transit arcs -> approximately 3-5 Luna Games

Step 8:
    Games + Natal Player + year statistics + year strip -> one chronological
    Year Packet
"""

from dataclasses import asdict, dataclass
from datetime import date
import hashlib
import json
from typing import Any, Iterable, Sequence

from natal_snapshot import NatalSnapshot
from timing_map import TARGET_DOMAINS, TimingMapReport, TransitStory, month_intensity
from yearly_game_engine import GAME_DEFINITIONS, GameDefinition


YEAR_AHEAD_PACKET_VERSION = "1.0"
MAX_YEAR_GAMES = 5
TARGET_YEAR_GAMES = 3
PEAK_CLUSTER_GAP_DAYS = 45


@dataclass(frozen=True)
class YearGame:
    number: int
    key: str
    title: str
    strategic_frame: str
    question: str
    start_date: date
    end_date: date
    human_life_area: str
    polarity: str
    score: float
    primary_transit: dict[str, Any]
    supporting_transits: tuple[dict[str, Any], ...]
    advantage: str
    risk: str
    move: str
    dont: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["start_date"] = self.start_date.isoformat()
        value["end_date"] = self.end_date.isoformat()
        return value


@dataclass(frozen=True)
class YearPacket:
    version: str
    start_date: date
    end_date: date
    timezone_name: str
    natal_fingerprint: dict[str, Any]
    year_statistics: dict[str, Any]
    year_strip: tuple[dict[str, Any], ...]
    games: tuple[YearGame, ...]
    packet_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "period": {
                "start": self.start_date.isoformat(),
                "end": self.end_date.isoformat(),
                "timezone": self.timezone_name,
            },
            "natal_fingerprint": self.natal_fingerprint,
            "year_statistics": self.year_statistics,
            "year_strip": list(self.year_strip),
            "games": [game.to_dict() for game in self.games],
            "packet_hash": self.packet_hash,
        }


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _position_row(position: Any) -> dict[str, Any]:
    if position is None:
        return {}
    return {
        "planet": str(getattr(position, "planet", "")),
        "sign": str(getattr(position, "sign", "")),
        "degree": round(float(getattr(position, "degree", 0.0) or 0.0), 3),
        "house": getattr(position, "house", None),
        "retrograde": bool(getattr(position, "retrograde", False)),
    }


def _natal_fingerprint(snapshot: NatalSnapshot) -> dict[str, Any]:
    by_planet = {
        str(getattr(item, "planet", "")): item
        for item in (snapshot.positions or ())
    }
    signatures = []
    for item in list(snapshot.signatures or ())[:5]:
        signatures.append(
            {
                "title": str(getattr(item, "title", "")),
                "strength": str(getattr(item, "strength", "")),
                "evidence": str(getattr(item, "evidence", "")),
            }
        )

    fingerprint: dict[str, Any] = {
        "birth_time_known": bool(snapshot.birth_time_known),
        "sun": _position_row(by_planet.get("Sun")),
        "moon": _position_row(by_planet.get("Moon")),
        "dominant_element": str(snapshot.dominant_element or ""),
        "dominant_modality": str(snapshot.dominant_modality or ""),
        "strongest_signatures": signatures,
        "concentration_theme": dict(snapshot.concentration_theme or {}),
    }
    if snapshot.birth_time_known:
        fingerprint["ascendant"] = _position_row(snapshot.ascendant)
        fingerprint["midheaven"] = _position_row(snapshot.midheaven)
    return fingerprint


def _story_anchor_date(story: TransitStory) -> date:
    """Choose the strongest calculated peak for chronological clustering."""
    hits = list(story.hits or ())
    if hits:
        return min(
            hits,
            key=lambda hit: (
                float(getattr(hit, "orb", 99.0) or 99.0),
                hit.exact_date,
                str(getattr(hit, "exact_time", "") or ""),
            ),
        ).exact_date
    return story.first_date


def _story_players(story: TransitStory) -> set[str]:
    players = {
        str(story.transit_planet),
        str(story.natal_target),
    }
    for trigger in story.supporting_triggers or ():
        players.add(str(trigger.trigger_planet))
    return {item for item in players if item}


def _story_houses(story: TransitStory) -> set[int]:
    if story.natal_house is None:
        return set()
    return {int(story.natal_house)}


def _definition_support(stories: Sequence[TransitStory], definition: GameDefinition) -> float:
    """Reuse yearly_game_engine's existing game definitions for personal arcs."""
    score = 0.0
    for story in stories:
        players = _story_players(story)
        houses = _story_houses(story)
        player_overlap = len(players & set(definition.players))
        house_overlap = len(houses & set(definition.houses))

        if player_overlap:
            score += float(story.score) * (0.50 + 0.22 * player_overlap)
        if house_overlap:
            score += float(story.score) * 0.22 * house_overlap

        # Exact repeated passes and supporting triggers are already calculation-
        # owned importance signals. They can strengthen a match but never create
        # a Game without an underlying selected transit arc.
        if player_overlap and getattr(story, "is_multi_pass", False):
            score += 0.18 * float(story.score)
        if player_overlap and (story.supporting_triggers or ()):
            score += 0.06 * float(story.score) * min(len(story.supporting_triggers), 3)
    return round(score, 4)


def _best_definition(stories: Sequence[TransitStory]) -> GameDefinition:
    ranked = [
        (_definition_support(stories, definition), index, definition)
        for index, definition in enumerate(GAME_DEFINITIONS)
    ]
    _score, _index, definition = max(ranked, key=lambda item: (item[0], -item[1]))
    return definition


def _clusters_from_anchors(
    stories: Sequence[TransitStory],
    *,
    gap_days: int = PEAK_CLUSTER_GAP_DAYS,
) -> list[list[TransitStory]]:
    """Build chronological clusters from exact transit peaks, not broad orbs.

    Slow-planet active windows can overlap for months. Using the exact/closest
    calculated peaks prevents one long orb window from collapsing the whole
    year into a single Game.
    """
    ordered = sorted(
        stories,
        key=lambda item: (_story_anchor_date(item), -float(item.score)),
    )
    if not ordered:
        return []

    clusters: list[list[TransitStory]] = [[ordered[0]]]
    last_anchor = _story_anchor_date(ordered[0])

    for story in ordered[1:]:
        anchor = _story_anchor_date(story)
        if (anchor - last_anchor).days <= gap_days:
            clusters[-1].append(story)
        else:
            clusters.append([story])
        last_anchor = anchor
    return clusters


def _cluster_strength(cluster: Sequence[TransitStory]) -> float:
    base = sum(float(story.score) for story in cluster)
    multi = sum(0.16 * float(story.score) for story in cluster if story.is_multi_pass)
    trigger = sum(
        0.04 * float(story.score) * min(len(story.supporting_triggers or ()), 3)
        for story in cluster
    )
    overlap = sum(
        0.04 * float(story.score) * min(int(getattr(story, "overlap_count", 0) or 0), 3)
        for story in cluster
    )
    return round(base + multi + trigger + overlap, 4)


def _merge_adjacent_clusters(clusters: list[list[TransitStory]]) -> list[list[TransitStory]]:
    """Reduce a busy year to at most five chronological Games."""
    clusters = [list(cluster) for cluster in clusters if cluster]
    while len(clusters) > MAX_YEAR_GAMES:
        candidates: list[tuple[int, float, int]] = []
        for index in range(len(clusters) - 1):
            left = clusters[index]
            right = clusters[index + 1]
            left_anchor = max(_story_anchor_date(item) for item in left)
            right_anchor = min(_story_anchor_date(item) for item in right)
            gap = max(0, (right_anchor - left_anchor).days)

            left_definition = _best_definition(left)
            right_definition = _best_definition(right)
            semantic_bonus = 25.0 if left_definition.key == right_definition.key else 0.0
            combined_strength = _cluster_strength(left) + _cluster_strength(right)

            # Smaller effective gap is merged first. If two choices have the
            # same gap, preserve the stronger combined story.
            effective_gap = gap - semantic_bonus
            candidates.append((effective_gap, -combined_strength, index))

        _gap, _strength, index = min(candidates)
        clusters[index] = clusters[index] + clusters[index + 1]
        del clusters[index + 1]
    return clusters


def _split_for_minimum_games(clusters: list[list[TransitStory]]) -> list[list[TransitStory]]:
    """Aim for three Games when the transit evidence can support them."""
    clusters = [list(cluster) for cluster in clusters if cluster]
    total_stories = sum(len(cluster) for cluster in clusters)
    target = min(TARGET_YEAR_GAMES, total_stories)

    while len(clusters) < target:
        splittable = [
            (len(cluster), _cluster_strength(cluster), index)
            for index, cluster in enumerate(clusters)
            if len(cluster) >= 2
        ]
        if not splittable:
            break

        _size, _strength, index = max(splittable)
        cluster = sorted(
            clusters[index],
            key=lambda story: (_story_anchor_date(story), -float(story.score)),
        )

        # Prefer a real chronological break. If none is pronounced, split near
        # the middle while keeping each technical transit arc intact.
        gaps = [
            (
                (_story_anchor_date(cluster[i + 1]) - _story_anchor_date(cluster[i])).days,
                i + 1,
            )
            for i in range(len(cluster) - 1)
        ]
        _gap, split_at = max(gaps, default=(0, len(cluster) // 2))
        if split_at <= 0 or split_at >= len(cluster):
            split_at = len(cluster) // 2

        clusters[index:index + 1] = [cluster[:split_at], cluster[split_at:]]
        clusters.sort(key=lambda group: min(_story_anchor_date(item) for item in group))
    return clusters


def _serialize_hit(hit: Any) -> dict[str, Any]:
    return {
        "pass_number": int(getattr(hit, "pass_number", 1) or 1),
        "pass_label": str(getattr(hit, "pass_label", "") or ""),
        "date": hit.exact_date.isoformat(),
        "time": str(getattr(hit, "exact_time", "") or ""),
        "retrograde": bool(getattr(hit, "retrograde", False)),
        "orb": round(float(getattr(hit, "orb", 0.0) or 0.0), 4),
    }


def _serialize_trigger(trigger: Any) -> dict[str, Any]:
    return {
        "planet": str(trigger.trigger_planet),
        "aspect": str(trigger.aspect),
        "natal_target": str(trigger.natal_target),
        "date": trigger.exact_date.isoformat(),
        "time": str(getattr(trigger, "exact_time", "") or ""),
        "retrograde": bool(getattr(trigger, "retrograde", False)),
        "orb": round(float(getattr(trigger, "orb", 0.0) or 0.0), 4),
        "activates_pass_number": getattr(trigger, "activates_pass_number", None),
        "technical_label": str(getattr(trigger, "technical_label", "") or ""),
        "activation_label": str(getattr(trigger, "activation_label", "") or ""),
    }


def _serialize_story(story: TransitStory) -> dict[str, Any]:
    return {
        "technical_label": f"{story.transit_planet} {story.aspect} natal {story.natal_target}",
        "transiting_planet": str(story.transit_planet),
        "aspect": str(story.aspect),
        "natal_target": str(story.natal_target),
        "natal_house": story.natal_house,
        "headline": str(story.headline),
        "polarity": str(story.polarity),
        "score": round(float(story.score), 4),
        "base_score": (
            round(float(story.base_score), 4)
            if story.base_score is not None
            else None
        ),
        "exactness_bonus": round(float(story.exactness_bonus or 0.0), 4),
        "overlap_count": int(story.overlap_count or 0),
        "start": story.first_date.isoformat(),
        "end": story.last_date.isoformat(),
        "passes": [_serialize_hit(hit) for hit in story.hits],
        "triggers": [_serialize_trigger(item) for item in story.supporting_triggers],
        "summary": str(story.summary),
        "move": str(story.move),
        "watch": str(story.watch),
    }


def _cluster_dates(cluster: Sequence[TransitStory]) -> tuple[date, date]:
    return (
        min(story.first_date for story in cluster),
        max(story.last_date for story in cluster),
    )


def _cluster_polarity(cluster: Sequence[TransitStory]) -> str:
    weighted: dict[str, float] = {}
    for story in cluster:
        weighted[story.polarity] = weighted.get(story.polarity, 0.0) + float(story.score)
    return max(weighted.items(), key=lambda item: item[1])[0] if weighted else "mixed"


def _cluster_life_area(cluster: Sequence[TransitStory]) -> str:
    weighted: dict[str, float] = {}
    for story in cluster:
        label = TARGET_DOMAINS.get(
            str(story.natal_target),
            str(story.natal_target).lower(),
        )
        weighted[label] = weighted.get(label, 0.0) + float(story.score)
    return max(weighted.items(), key=lambda item: item[1])[0] if weighted else "personal direction"


def _build_game(number: int, cluster: Sequence[TransitStory]) -> YearGame:
    ordered = sorted(
        cluster,
        key=lambda story: (-float(story.score), _story_anchor_date(story)),
    )
    primary = ordered[0]
    supporting = ordered[1:]
    definition = _best_definition(cluster)
    start, end = _cluster_dates(cluster)

    return YearGame(
        number=number,
        key=definition.key,
        # The main calculated transit headline remains the customer-facing Game
        # title. The existing yearly_game_engine definition supplies the
        # strategic frame underneath rather than replacing personal evidence.
        title=str(primary.headline),
        strategic_frame=str(definition.title),
        question=str(definition.question),
        start_date=start,
        end_date=end,
        human_life_area=_cluster_life_area(cluster),
        polarity=_cluster_polarity(cluster),
        score=round(_cluster_strength(cluster), 4),
        primary_transit=_serialize_story(primary),
        supporting_transits=tuple(_serialize_story(item) for item in supporting),
        advantage=str(definition.advantage),
        risk=str(definition.risk),
        move=str(definition.do_line),
        dont=str(definition.dont_line),
    )


def build_year_games(report: TimingMapReport) -> tuple[YearGame, ...]:
    """Cluster the selected transit arcs into approximately 3-5 Games."""
    stories = list(report.stories or ())
    if not stories:
        return ()

    clusters = _clusters_from_anchors(stories)
    clusters = _merge_adjacent_clusters(clusters)
    clusters = _split_for_minimum_games(clusters)
    clusters.sort(key=lambda group: min(story.first_date for story in group))

    games = tuple(
        _build_game(index, cluster)
        for index, cluster in enumerate(clusters, start=1)
    )
    return games[:MAX_YEAR_GAMES]


def _year_strip(report: TimingMapReport) -> tuple[dict[str, Any], ...]:
    return tuple(
        {"month": label, "intensity": float(value)}
        for label, value in month_intensity(report)
    )


def _statistics(report: TimingMapReport, games: Sequence[YearGame]) -> dict[str, Any]:
    return {
        "major_games": len(games),
        "selected_transit_arcs": len(report.stories or ()),
        "turning_points": int(report.turning_points),
        "rule_changes": int(report.rule_changes),
        "multi_pass_arcs": sum(1 for story in report.stories if story.is_multi_pass),
        "supporting_triggers": sum(
            len(story.supporting_triggers or ())
            for story in report.stories
        ),
    }


def build_year_packet(
    snapshot: NatalSnapshot,
    report: TimingMapReport,
) -> YearPacket:
    """Build the single deterministic chronology that the Year Ahead voice uses.

    No LLM is called here. The packet contains only calculated or deterministic
    material already owned by Luna's natal, timing-map and existing yearly-game
    layers.
    """
    games = build_year_games(report)
    fingerprint = _natal_fingerprint(snapshot)
    strip = _year_strip(report)
    statistics = _statistics(report, games)

    hash_source = {
        "version": YEAR_AHEAD_PACKET_VERSION,
        "period": {
            "start": report.start_date.isoformat(),
            "end": report.end_date.isoformat(),
            "timezone": report.timezone_name,
        },
        "natal_fingerprint": fingerprint,
        "year_statistics": statistics,
        "year_strip": list(strip),
        "games": [game.to_dict() for game in games],
    }

    return YearPacket(
        version=YEAR_AHEAD_PACKET_VERSION,
        start_date=report.start_date,
        end_date=report.end_date,
        timezone_name=report.timezone_name,
        natal_fingerprint=fingerprint,
        year_statistics=statistics,
        year_strip=strip,
        games=games,
        packet_hash=_stable_hash(hash_source),
    )
