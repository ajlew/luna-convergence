from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from difflib import SequenceMatcher
from functools import lru_cache
from html import escape
import re
from typing import Iterable

from astrology_engine import (
    ASPECTS,
    HOUSE_NAMES,
    convergence_points,
    detect_aspects,
    period_events,
    positions_for_date,
)


SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
MARKDOWN_MARKERS = re.compile(r"(?:\*\*|__|`|#+\s*)")
NON_WORD = re.compile(r"[^a-z0-9]+")

HOUSE_LABELS = {
    1: "Identity",
    2: "Money",
    3: "Communication",
    4: "Home",
    5: "Romance & creativity",
    6: "Work & wellbeing",
    7: "Relationships",
    8: "Trust & shared money",
    9: "Travel & learning",
    10: "Career",
    11: "Friends & future",
    12: "Rest & inner life",
}

HOUSE_INLINE = {
    1: "identity and personal direction",
    2: "money and self-worth",
    3: "communication and everyday decisions",
    4: "home and family",
    5: "romance and creativity",
    6: "work and wellbeing",
    7: "relationships and agreements",
    8: "trust and shared obligations",
    9: "travel and learning",
    10: "career and reputation",
    11: "friends and future plans",
    12: "rest and private reflection",
}

HOUSE_STORY = {
    1: "A personal decision may ask you to lead instead of waiting for approval.",
    2: "A price, purchase or money conversation may make you reconsider what is genuinely worth your energy.",
    3: "A message, invitation or overlooked detail may change the direction of a conversation.",
    4: "Something at home or within the family may need a calmer response than expected.",
    5: "A romantic or creative spark may become harder to dismiss.",
    6: "A routine problem may reveal the small adjustment that makes the whole day easier.",
    7: "Another person's honesty may show you where a relationship or agreement really stands.",
    8: "A shared cost, promise or trust issue may need to be named directly.",
    9: "An invitation to learn, travel or think bigger may suddenly feel more realistic.",
    10: "A work opportunity or visible responsibility may put you in a stronger position.",
    11: "A friend, audience or useful contact may open a future possibility.",
    12: "A quiet realisation may help you close a draining chapter.",
}

HOUSE_EXAMPLES = {
    1: "This may show up as a choice about your image, direction, energy or the role you are ready to claim.",
    2: "It may involve pricing, a purchase, a payment, a possession or a decision about what deserves further investment.",
    3: "It could arrive through a text, email, short trip, sales conversation, document or piece of information.",
    4: "It may concern family news, a domestic decision, property, privacy or the emotional tone at home.",
    5: "It could involve dating, attraction, children, pleasure, creative work or a project that feels personally yours.",
    6: "It may concern workload, health, scheduling, service, a colleague or a system that keeps repeating the same problem.",
    7: "It could involve a partner, client, collaborator, competitor or an agreement whose expectations need to be clearer.",
    8: "It may concern debt, tax, shared money, intimacy, trust, insurance or an obligation that has remained partly hidden.",
    9: "It could involve study, publishing, legal matters, travel, another culture or an opportunity beyond your usual world.",
    10: "It may involve a manager, public result, application, promotion, deadline or decision about professional direction.",
    11: "It could come through a friend, group, community, audience, online network or long-term plan.",
    12: "It may emerge through rest, a private conversation, unfinished grief, a dream or the need to step back before deciding.",
}

PLANET_READER_EFFECT = {
    "Sun": "The Sun makes this issue more visible and difficult to ignore.",
    "Moon": "The Moon makes feelings and reactions more immediate.",
    "Mercury": "Mercury puts extra weight on messages, choices and timing.",
    "Venus": "Venus brings attraction, value and relationship preferences to the surface.",
    "Mars": "Mars raises urgency, desire and the need to act.",
    "Jupiter": "Jupiter widens the opportunity and makes the larger possibility easier to see.",
    "Saturn": "Saturn asks for proof, patience and a boundary that can last.",
    "Uranus": "Uranus introduces surprise, freedom or an unconventional option.",
    "Neptune": "Neptune heightens intuition and imagination but can blur what is certain.",
    "Pluto": "Pluto intensifies power, truth and whatever has been hidden.",
    "True Node": "The lunar node points toward an unfamiliar but potentially developmental direction.",
}

SLOW_CLIMATE_VERBS = {
    "Jupiter": "expanding",
    "Saturn": "restructuring",
    "Uranus": "changing",
    "Neptune": "softening old boundaries around",
    "Pluto": "transforming",
    "True Node": "drawing attention toward",
}

PLANET_PRIORITY = {
    "Moon": 0,
    "Mercury": 1,
    "Venus": 2,
    "Mars": 3,
    "Sun": 4,
    "Jupiter": 5,
    "Saturn": 6,
    "Uranus": 7,
    "Neptune": 8,
    "Pluto": 9,
    "True Node": 10,
}


@dataclass(frozen=True)
class EvidenceSnapshot:
    active_planets: tuple[str, ...]
    aspect_label: str
    aspect_type: str
    orb: float | None
    phase: str
    activated_houses: tuple[int, ...]
    house_meanings: tuple[str, ...]
    strongest_influence: str
    active_window: str
    strength_score: int
    confidence_label: str
    convergence_label: str
    convergence_score: float | None
    convergence_window: str


@dataclass(frozen=True)
class DailyNarrative:
    sign: str
    reading_date: date
    headline: str
    today_story: tuple[str, ...]
    convergence_axis: str
    why_today_points: tuple[str, str, str]
    long_term_current: str
    emotional_weather: str
    hidden_opportunity: str
    watch_out: str
    action_today: str
    reflection_questions: tuple[str, ...]
    work_note: str
    money_note: str
    relationship_story: str
    daily_theme: str
    wider_context: str
    technical_aspects: tuple[str, ...]
    house_conclusion: str
    house_matrix: str
    sky_rows: tuple[tuple[str, str, int, str], ...]
    sun_house: int
    moon_house: int
    evidence: EvidenceSnapshot


def clean_customer_text(value: str) -> str:
    return re.sub(r"\s+", " ", MARKDOWN_MARKERS.sub("", value or "")).strip()


def split_sentences(value: str) -> list[str]:
    cleaned = clean_customer_text(value)
    if not cleaned:
        return []
    return [part.strip() for part in SENTENCE_SPLIT.split(cleaned) if part.strip()]


def _normalise(value: str) -> str:
    return NON_WORD.sub(" ", clean_customer_text(value).lower()).strip()


def _sentence_similarity(first: str, second: str) -> float:
    left = _normalise(first)
    right = _normalise(second)
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    left_words = set(left.split())
    right_words = set(right.split())
    union = left_words | right_words
    jaccard = len(left_words & right_words) / len(union) if union else 0.0
    sequence = SequenceMatcher(None, left, right).ratio()
    return max(jaccard, sequence)


def reading_comparison_text(reading) -> str:
    values = [
        reading.headline,
        *reading.forecast_paragraphs,
        reading.love_note,
        reading.work_note,
        reading.money_note,
        reading.opportunity,
        reading.caution,
    ]
    return " ".join(clean_customer_text(value) for value in values if value)


def _repetition_count(sentence: str, previous_texts: Iterable[str]) -> int:
    count = 0
    for previous in previous_texts:
        if any(
            _sentence_similarity(sentence, item) >= 0.74
            for item in split_sentences(previous)
        ):
            count += 1
    return count


def _aspect_match(d: date, timezone_name: str, planet1: str, planet2: str, name: str):
    positions = positions_for_date(d, timezone_name)
    target = frozenset({planet1, planet2})
    for aspect in detect_aspects(positions, include_moon=True):
        if frozenset({aspect.planet1, aspect.planet2}) == target and aspect.name == name:
            return aspect
    return None


def _aspect_phase(reading_date: date, timezone_name: str, anchor) -> str:
    if not anchor:
        return "No single aspect dominates"
    previous = _aspect_match(
        reading_date - timedelta(days=1), timezone_name,
        anchor.planet1, anchor.planet2, anchor.name,
    )
    following = _aspect_match(
        reading_date + timedelta(days=1), timezone_name,
        anchor.planet1, anchor.planet2, anchor.name,
    )
    previous_orb = previous.orb if previous else 99.0
    following_orb = following.orb if following else 99.0
    if anchor.orb <= previous_orb and anchor.orb <= following_orb:
        return "Closest to exact today"
    if following_orb < anchor.orb:
        return "Applying — still building"
    if previous_orb < anchor.orb:
        return "Separating — meaning is settling"
    return "Active within orb"


def _aspect_window(reading_date: date, timezone_name: str, anchor) -> str:
    if not anchor:
        return "Today"
    start = reading_date
    end = reading_date
    max_scan = 4 if "Moon" in anchor.planets else 14
    for offset in range(1, max_scan + 1):
        candidate = reading_date - timedelta(days=offset)
        if _aspect_match(candidate, timezone_name, anchor.planet1, anchor.planet2, anchor.name):
            start = candidate
        else:
            break
    for offset in range(1, max_scan + 1):
        candidate = reading_date + timedelta(days=offset)
        if _aspect_match(candidate, timezone_name, anchor.planet1, anchor.planet2, anchor.name):
            end = candidate
        else:
            break
    if start == end:
        return "Next 24 hours"
    if start.month == end.month:
        return f"{start.strftime('%B %d')}–{end.strftime('%d')}"
    return f"{start.strftime('%B %d')}–{end.strftime('%B %d')}"


def _strength_score(anchor, phase: str) -> int:
    if not anchor:
        return 25
    allowed_orb = ASPECTS.get(anchor.name, (0.0, 7.0))[1]
    closeness = max(0.0, 1.0 - anchor.orb / allowed_orb)
    score = 24 + 50 * closeness
    planets = anchor.planets
    if "Moon" in planets:
        score += 12
    if planets & {"Venus", "Mars"}:
        score += 7
    if "Mercury" in planets:
        score += 4
    if anchor.name in {"square", "opposition", "conjunction"}:
        score += 4
    if phase.startswith("Closest"):
        score += 8
    return max(1, min(100, round(score)))


def _confidence_label(score: int) -> str:
    if score >= 78:
        return "High"
    if score >= 52:
        return "Medium"
    return "Low"


@lru_cache(maxsize=256)
def _year_clusters(sign: str, year: int, timezone_name: str):
    events = period_events(date(year, 1, 1), date(year, 12, 31), sign, timezone_name)
    return tuple(convergence_points(events, maximum=9))


def _active_cluster(sign: str, reading_date: date, timezone_name: str):
    return next(
        (
            cluster
            for cluster in _year_clusters(sign, reading_date.year, timezone_name)
            if cluster.start_date - timedelta(days=14)
            <= reading_date
            <= cluster.end_date + timedelta(days=14)
        ),
        None,
    )


def _convergence_evidence(sign: str, reading_date: date, timezone_name: str):
    active = _active_cluster(sign, reading_date, timezone_name)
    if not active:
        return "Daily trigger", None, "Daily trigger carries more weight"
    if active.score >= 75:
        concentration = "High concentration"
    elif active.score >= 50:
        concentration = "Moderate concentration"
    else:
        concentration = "Background concentration"
    window = f"{active.start_date.strftime('%B %d')}–{active.end_date.strftime('%B %d')}"
    return concentration, round(active.score, 1), window


def _evidence_snapshot(reading, sign: str, reading_date: date, timezone_name: str) -> EvidenceSnapshot:
    anchor = reading.anchor_aspect
    phase = _aspect_phase(reading_date, timezone_name, anchor)
    convergence_label, convergence_score, convergence_window = _convergence_evidence(
        sign, reading_date, timezone_name
    )
    if anchor:
        planets = tuple(sorted(anchor.planets, key=lambda p: PLANET_PRIORITY.get(p, 99)))
        houses = tuple(dict.fromkeys((anchor.house1, anchor.house2)))
        meanings = tuple(HOUSE_NAMES[number] for number in houses)
        strongest = (
            f"{anchor.label} links house {anchor.house1} with house {anchor.house2}."
        )
        label = anchor.label
        aspect_type = anchor.name.capitalize()
        orb = anchor.orb
    else:
        planets = ("Moon", "Sun")
        houses = tuple(dict.fromkeys((reading.moon_house, reading.sun_house)))
        meanings = tuple(HOUSE_NAMES[number] for number in houses)
        strongest = "The moving Moon changes the daily emphasis inside the Sun's longer story."
        label = "Moon–Sun house pattern"
        aspect_type = "House emphasis"
        orb = None
    score = _strength_score(anchor, phase)
    return EvidenceSnapshot(
        active_planets=planets,
        aspect_label=label,
        aspect_type=aspect_type,
        orb=orb,
        phase=phase,
        activated_houses=houses,
        house_meanings=meanings,
        strongest_influence=strongest,
        active_window=_aspect_window(reading_date, timezone_name, anchor),
        strength_score=score,
        confidence_label=_confidence_label(score),
        convergence_label=convergence_label,
        convergence_score=convergence_score,
        convergence_window=convergence_window,
    )


def _trigger_house(reading) -> int:
    anchor = reading.anchor_aspect
    if not anchor:
        return reading.moon_house
    ordered = sorted(
        ((anchor.planet1, anchor.house1), (anchor.planet2, anchor.house2)),
        key=lambda item: PLANET_PRIORITY.get(item[0], 99),
    )
    return ordered[0][1]


def _other_house(reading, trigger_house: int) -> int:
    anchor = reading.anchor_aspect
    if not anchor:
        return reading.sun_house
    return anchor.house2 if anchor.house1 == trigger_house else anchor.house1


def _convergence_axis(reading) -> str:
    anchor = reading.anchor_aspect
    if not anchor:
        houses = (reading.moon_house, reading.sun_house)
    else:
        houses = (anchor.house1, anchor.house2)
    labels = []
    for house in houses:
        label = HOUSE_LABELS[house]
        if label not in labels:
            labels.append(label)
    return " × ".join(labels)


def _phase_sentence(phase: str) -> str:
    if phase.startswith("Closest"):
        return "The influence is at its clearest point today."
    if phase.startswith("Applying"):
        return "The influence is still building, so the next exchange may carry increasing weight."
    if phase.startswith("Separating"):
        return "The peak is passing, but the meaning of what happened is becoming easier to recognise."
    return "The pattern is active today and gives this issue more weight than usual."


def _story_paragraphs(reading, evidence: EvidenceSnapshot, previous_texts: list[str]) -> tuple[str, ...]:
    trigger = _trigger_house(reading)
    other = _other_house(reading, trigger)
    tone = reading.anchor_aspect.name if reading.anchor_aspect else "blend"

    consequence = HOUSE_STORY[trigger]
    if tone in {"trine", "sextile"}:
        bridge = (
            f"An easier current connects {HOUSE_INLINE[trigger]} with "
            f"{HOUSE_INLINE[other]}, making progress in one area useful to the other."
        )
    elif tone in {"square", "opposition"}:
        bridge = (
            f"The tension connects {HOUSE_INLINE[trigger]} with "
            f"{HOUSE_INLINE[other]}. One honest response can prevent a small issue from becoming a larger one."
        )
    else:
        bridge = (
            f"The day brings {HOUSE_INLINE[trigger]} and "
            f"{HOUSE_INLINE[other]} into the same decision."
        )
    first = f"{consequence} {bridge}"

    second = HOUSE_EXAMPLES[trigger]
    relationship = clean_customer_text(reading.love_note)
    third = relationship

    action = clean_customer_text(reading.best_move)
    fourth = f"The useful move is specific: {action[0].lower() + action[1:] if action else 'pause long enough to make the next step deliberate.'}"

    paragraphs = [first, second, third, fourth]
    result: list[str] = []
    for paragraph in paragraphs:
        if paragraph and _repetition_count(paragraph, previous_texts) < 3:
            result.append(paragraph)
    if len(result) < 3:
        result = paragraphs[:3]
    return tuple(result[:4])


def _why_today_points(reading, evidence: EvidenceSnapshot) -> tuple[str, str, str]:
    planets = list(evidence.active_planets)
    first = PLANET_READER_EFFECT.get(planets[0], "One planet sharpens the immediate story.")
    second_planet = planets[1] if len(planets) > 1 else "Sun"
    second = PLANET_READER_EFFECT.get(second_planet, "A second influence connects the story to a practical life area.")
    third = _phase_sentence(evidence.phase)
    return first, second, third


def _emotional_weather(reading) -> str:
    anchor = reading.anchor_aspect
    if not anchor:
        return {
            1: "Direct and self-aware",
            2: "Security-conscious",
            3: "Curious and mentally busy",
            4: "Private and sensitive",
            5: "Warm and expressive",
            6: "Practical but easily tired",
            7: "Relationship-aware",
            8: "Intense and perceptive",
            9: "Restless and hopeful",
            10: "Ambitious and visible",
            11: "Social and future-focused",
            12: "Quiet and reflective",
        }[reading.moon_house]
    planets = anchor.planets
    hard = anchor.name in {"square", "opposition"}
    if "Saturn" in planets:
        return "Sensitive but steady" if not hard else "Reserved and easily discouraged"
    if "Mars" in planets:
        return "Energetic and direct" if not hard else "Charged and impatient"
    if "Mercury" in planets:
        return "Curious and communicative" if not hard else "Restless and reactive"
    if "Venus" in planets:
        return "Warm and receptive" if not hard else "Tender but conflicted"
    if "Neptune" in planets:
        return "Intuitive and imaginative" if not hard else "Dreamy but uncertain"
    if "Pluto" in planets:
        return "Deep and perceptive" if not hard else "Intense and protective"
    if "Jupiter" in planets:
        return "Hopeful and open" if not hard else "Optimistic but overstretched"
    if "Uranus" in planets:
        return "Fresh and spontaneous" if not hard else "Restless and unpredictable"
    return "Alert and emotionally responsive"


def _long_term_current(reading, sign: str, reading_date: date, timezone_name: str) -> str:
    active = _active_cluster(sign, reading_date, timezone_name)
    slow_planets = ["Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "True Node"]
    selected = None
    if active:
        for planet in slow_planets:
            if planet in active.planets:
                selected = planet
                break
    if selected is None:
        selected = "Jupiter"
    house = reading.houses[selected]
    verb = SLOW_CLIMATE_VERBS[selected]
    return f"{selected} is {verb} {HOUSE_LABELS[house].lower()}. This is the climate: it lasts longer than today's trigger."


def _headline(reading, previous_texts: Iterable[str], evidence: EvidenceSnapshot) -> str:
    headline = clean_customer_text(reading.headline)
    if _repetition_count(headline, previous_texts) < 2:
        return headline
    if evidence.phase.startswith("Closest"):
        return f"{headline}—today is the turning point"
    if evidence.phase.startswith("Applying"):
        return f"{headline}—the story is still building"
    if evidence.phase.startswith("Separating"):
        return f"{headline}—notice what remains"
    return f"{headline}—look at what changes today"


def build_daily_narrative(
    reading,
    *,
    sign: str,
    reading_date: date,
    timezone_name: str,
    house_voice: dict,
    previous_texts: list[str] | None = None,
) -> DailyNarrative:
    del house_voice  # Kept in the signature for stable app integration.
    previous = previous_texts or []
    evidence = _evidence_snapshot(reading, sign, reading_date, timezone_name)
    story = _story_paragraphs(reading, evidence, previous)
    sky_rows = tuple(
        (
            planet,
            position.label(),
            reading.houses[planet],
            HOUSE_NAMES[reading.houses[planet]],
        )
        for planet, position in reading.positions.items()
    )
    return DailyNarrative(
        sign=sign,
        reading_date=reading_date,
        headline=_headline(reading, previous, evidence),
        today_story=story,
        convergence_axis=_convergence_axis(reading),
        why_today_points=_why_today_points(reading, evidence),
        long_term_current=_long_term_current(reading, sign, reading_date, timezone_name),
        emotional_weather=_emotional_weather(reading),
        hidden_opportunity=clean_customer_text(reading.opportunity),
        watch_out=clean_customer_text(reading.caution),
        action_today=clean_customer_text(reading.best_move),
        reflection_questions=tuple(clean_customer_text(item) for item in reading.reflection_questions),
        work_note=clean_customer_text(reading.work_note),
        money_note=clean_customer_text(reading.money_note),
        relationship_story=clean_customer_text(reading.love_note),
        daily_theme=reading.daily_theme,
        wider_context=reading.wider_context,
        technical_aspects=reading.aspects,
        house_conclusion=reading.conclusion,
        house_matrix=reading.house_matrix,
        sky_rows=sky_rows,
        sun_house=reading.sun_house,
        moon_house=reading.moon_house,
        evidence=evidence,
    )


def _paragraph_html(paragraphs: Iterable[str]) -> str:
    return "".join(f"<p>{escape(item)}</p>" for item in paragraphs if item)


def _render_css() -> None:
    import streamlit as st

    st.markdown(
        """
<style>
.explainable-section { max-width:900px; margin:2.15rem auto; }
.explainable-copy p {
    font-family:"Josefin Sans",sans-serif;
    font-size:clamp(1.12rem,1.65vw,1.34rem);
    line-height:1.68;
    font-weight:350;
}
.convergence-axis {
    border-top:1px solid #050505;
    border-bottom:1px solid #050505;
    padding:1.15rem 0;
    margin:1rem 0 2rem;
    font-family:"Bodoni MT","Bodoni 72","Bodoni Moda",Didot,Georgia,serif;
    font-size:clamp(1.8rem,3vw,3rem);
    line-height:1.05;
}
.why-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); border-top:1px solid #050505; border-left:1px solid #050505; }
.why-item { border-right:1px solid #050505; border-bottom:1px solid #050505; padding:1.1rem; min-height:8rem; }
.why-number { font-family:"IBM Plex Mono","Courier New",monospace; font-size:.67rem; text-transform:uppercase; }
.signal-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1rem; margin:2rem 0; }
.signal-card { border:1px solid #050505; padding:1.2rem; min-height:10rem; }
.signal-card p { margin-bottom:0; }
.sky-snapshot { width:100%; border-collapse:collapse; margin-top:1rem; }
.sky-snapshot td { border-bottom:1px solid #d8d8d3; padding:.85rem .5rem; vertical-align:top; }
.sky-snapshot td:first-child { width:13rem; font-family:"IBM Plex Mono","Courier New",monospace; font-size:.68rem; text-transform:uppercase; }
.snapshot-value { font-family:"Bodoni MT","Bodoni 72","Bodoni Moda",Didot,Georgia,serif; font-size:1.25rem; }
.weather-climate { display:grid; grid-template-columns:1fr 1fr; border:1px solid #050505; margin:2rem 0; }
.weather-climate > div { padding:1.1rem; }
.weather-climate > div:first-child { border-right:1px solid #050505; }
.confidence-note { font-family:"IBM Plex Mono","Courier New",monospace; font-size:.68rem; line-height:1.5; color:#696963; }
.technical-table { width:100%; border-collapse:collapse; }
.technical-table th,.technical-table td { border-bottom:1px solid #d8d8d3; padding:.7rem .55rem; text-align:left; vertical-align:top; }
.technical-table th { font-family:"IBM Plex Mono","Courier New",monospace; font-size:.68rem; text-transform:uppercase; }
@media (max-width:700px) {
    .why-grid,.signal-grid,.weather-climate { grid-template-columns:1fr; }
    .weather-climate > div:first-child { border-right:none; border-bottom:1px solid #050505; }
    .sky-snapshot td:first-child { width:8.5rem; }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_daily_narrative_v3(narrative: DailyNarrative) -> None:
    import streamlit as st

    _render_css()
    st.markdown(
        f"""
<div class="reading-card">
  <div class="daily-kicker">Free daily reading / {escape(narrative.sign)}</div>
  <div class="daily-headline">{escape(narrative.headline)}</div>
  <div class="daily-date">{narrative.reading_date.strftime('%A, %B %d, %Y')}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="explainable-section"><div class="eyebrow">Today\'s story</div></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="explainable-section explainable-copy">{_paragraph_html(narrative.today_story)}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("## Today’s convergence")
    st.markdown(
        f'<div class="convergence-axis">{escape(narrative.convergence_axis)}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("## Why this matters today")
    why_html = "".join(
        f'<div class="why-item"><div class="why-number">Evidence {index}</div><p>{escape(point)}</p></div>'
        for index, point in enumerate(narrative.why_today_points, 1)
    )
    st.markdown(f'<div class="why-grid">{why_html}</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
<div class="weather-climate">
  <div><div class="eyebrow">Weather / today</div><h3>{escape(narrative.emotional_weather)}</h3><p>The faster pattern describes the next day or two.</p></div>
  <div><div class="eyebrow">Climate / longer current</div><h3>{escape(narrative.long_term_current)}</h3></div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="signal-grid">', unsafe_allow_html=True)
    opportunity, watch, action = st.columns(3, gap="large")
    with opportunity:
        st.markdown(
            f'<div class="signal-card"><div class="eyebrow">Hidden opportunity</div><p>{escape(narrative.hidden_opportunity)}</p></div>',
            unsafe_allow_html=True,
        )
    with watch:
        st.markdown(
            f'<div class="signal-card"><div class="eyebrow">Watch out</div><p>{escape(narrative.watch_out)}</p></div>',
            unsafe_allow_html=True,
        )
    with action:
        st.markdown(
            f'<div class="signal-card"><div class="eyebrow">Action today</div><p>{escape(narrative.action_today)}</p></div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    evidence = narrative.evidence
    st.markdown("## Sky Snapshot")
    snapshot_rows = [
        ("Primary theme", narrative.convergence_axis),
        ("Emotional weather", narrative.emotional_weather),
        ("Strongest influence", evidence.aspect_label),
        ("Long-term current", narrative.long_term_current),
        ("Convergence strength", f"{evidence.confidence_label} ({evidence.strength_score}/100)"),
        ("Window", evidence.active_window),
    ]
    rows = "".join(
        f'<tr><td>{escape(label)}</td><td class="snapshot-value">{escape(value)}</td></tr>'
        for label, value in snapshot_rows
    )
    st.markdown(f'<table class="sky-snapshot"><tbody>{rows}</tbody></table>', unsafe_allow_html=True)
    st.markdown(
        '<div class="confidence-note">The strength score measures how clearly one astrological pattern dominates today. It is not the probability that a predicted event will occur.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("## Questions for today")
    question_html = "".join(
        f'<div class="question-item">{escape(question)}</div>'
        for question in narrative.reflection_questions
    )
    st.markdown(f'<div class="question-list">{question_html}</div>', unsafe_allow_html=True)

    with st.expander("Practical areas — relationships, work and money"):
        st.markdown("### Relationships")
        st.markdown(narrative.relationship_story)
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown("### Work")
            st.markdown(narrative.work_note)
        with right:
            st.markdown("### Money")
            st.markdown(narrative.money_note)

    with st.expander("See the calculations behind this reading"):
        orb_value = "Not applicable" if evidence.orb is None else f"{evidence.orb:.2f}°"
        st.markdown(f"**Aspect:** {evidence.aspect_label}")
        st.markdown(f"**Type:** {evidence.aspect_type}")
        st.markdown(f"**Orb:** {orb_value}")
        st.markdown(f"**Timing:** {evidence.phase}")
        st.markdown(f"**Active planets:** {', '.join(evidence.active_planets)}")
        st.markdown(f"**Active window:** {evidence.active_window}")
        st.markdown("### Activated houses")
        for number, meaning in zip(evidence.activated_houses, evidence.house_meanings):
            st.markdown(f"- **House {number}:** {meaning}")
        st.markdown("### Calculated daily theme")
        st.markdown(narrative.daily_theme)
        st.markdown("### Wider convergence context")
        st.markdown(narrative.wider_context)
        st.markdown("### Dominant aspects")
        for item in narrative.technical_aspects:
            st.markdown(item)
        st.markdown("### House-based conclusion")
        st.markdown(narrative.house_conclusion)

    with st.expander("Advanced Sky Snapshot — planetary positions"):
        rows = "".join(
            "<tr>"
            f"<td>{escape(planet)}</td>"
            f"<td>{escape(position)}</td>"
            f"<td>{house}</td>"
            f"<td>{escape(meaning)}</td>"
            "</tr>"
            for planet, position, house, meaning in narrative.sky_rows
        )
        st.markdown(
            '<table class="technical-table"><thead><tr><th>Body</th><th>Position</th><th>House</th><th>Life area</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>',
            unsafe_allow_html=True,
        )

    with st.expander("The 12-house reference matrix"):
        st.markdown(narrative.house_matrix)

    st.markdown(
        """
<div class="callout">
<strong>Explainable Astrology:</strong> the story appears first. The compact evidence below shows what changed today, what supports it and what belongs to the longer background. The detailed calculations remain available without interrupting the reading.
</div>
        """,
        unsafe_allow_html=True,
    )
