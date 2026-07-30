from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from urllib.parse import quote

from astrology_engine import (
    HOUSE_NAMES,
    Aspect,
    Position,
    convergence_points,
    detect_aspects,
    house_map,
    period_events,
    positions_for_date,
)
from interpretation_library import HOUSE_STRATEGY, PLANET_MEANINGS
from synthesis import (
    convergence_interpretation,
    house_aware_conclusion,
    house_reference_matrix,
)


HOUSE_VOICE = {
    1: {
        "headline": "Choose yourself without closing the door",
        "opening": (
            "Your attention is returning to your own direction, energy and sense of identity. "
            "A personal choice may feel more urgent because you can no longer ignore what no longer fits."
        ),
        "sensitivity": (
            "Your emotional weather is close to the surface, so another person's reaction may feel "
            "like a judgment of your whole identity rather than a response to one moment."
        ),
        "opportunity": "Act from a clearer sense of who you are becoming.",
        "caution": "Do not make every response from another person a verdict on your worth.",
        "best_move": "Make one choice that quietly matches the person you intend to become.",
        "questions": (
            "Which choice would feel honest even without anyone's approval?",
            "Am I responding to the present moment, or defending an older version of myself?",
        ),
    },
    2: {
        "headline": "Know what is truly worth your energy",
        "opening": (
            "Money, value, ownership and self-worth are asking for a calmer look. "
            "A practical decision becomes easier when you separate what is valuable from what is merely active or impressive."
        ),
        "sensitivity": (
            "Your emotional weather is tied to money, security and self-worth. "
            "A small concern about cost or value may feel more personal than it really is."
        ),
        "opportunity": "Strengthen what gives you genuine security and lasting value.",
        "caution": "Do not confuse attention, turnover, credit or possessions with financial strength.",
        "best_move": "Check the real income, cost and continuing obligation before you decide.",
        "questions": (
            "Does this choice create real security, or only more activity?",
            "What am I valuing because it matters, and what am I valuing because it looks impressive?",
        ),
    },
    3: {
        "headline": "Say less, mean more",
        "opening": (
            "A conversation, message or piece of information can change the shape of the day. "
            "The useful answer is likely to come through careful language rather than a louder argument."
        ),
        "sensitivity": (
            "Your mind may be moving faster than the facts. "
            "A message can feel urgent before its meaning, tone or consequences are completely clear."
        ),
        "opportunity": "Use clear language to create understanding and movement.",
        "caution": "Do not let noise, repetition or the need to be right replace useful information.",
        "best_move": "Ask one precise question, then listen to the complete answer.",
        "questions": (
            "What could I learn by speaking less and listening longer?",
            "Which fact still needs to be checked before I respond?",
        ),
    },
    4: {
        "headline": "Return to what steadies you",
        "opening": (
            "The condition of your private world matters more than it first appears. "
            "Home, family or an unresolved emotional foundation may be shaping an outside decision."
        ),
        "sensitivity": (
            "You may need more privacy, reassurance or familiarity than usual. "
            "Pressure outside the home can expose what has not yet been settled inside it."
        ),
        "opportunity": "Create a steadier base from which the next decision can be made.",
        "caution": "Do not carry unresolved private pressure into every public conversation.",
        "best_move": "Repair one part of the foundation before asking yourself to carry more.",
        "questions": (
            "What would make my private world feel genuinely steadier?",
            "Am I reacting to today's situation, or to an older family or emotional pattern?",
        ),
    },
    5: {
        "headline": "Let the heart become more honest",
        "opening": (
            "Creativity, pleasure, romance or self-expression wants room to breathe. "
            "What attracts you can reveal a real desire, but desire still needs form and follow-through."
        ),
        "sensitivity": (
            "You may feel especially responsive to attention, affection or creative recognition. "
            "Enjoyment is useful information, but it is not the same as a finished commitment."
        ),
        "opportunity": "Give a creative or heartfelt impulse enough structure to become real.",
        "caution": "Do not confuse intensity, admiration or inspiration with lasting compatibility.",
        "best_move": "Give one promising idea or connection a simple real-world test.",
        "questions": (
            "What do I want when I stop performing for a response?",
            "How could pleasure or inspiration become something sustainable?",
        ),
    },
    6: {
        "headline": "Make the day kinder to your body",
        "opening": (
            "Work, health, routine and the small systems supporting daily life need attention. "
            "The most meaningful improvement may be ordinary, repeatable and easy to overlook."
        ),
        "sensitivity": (
            "Your mood may be closely tied to fatigue, unfinished tasks or a routine that asks too much. "
            "Irritation can be a signal that the system—not your character—needs adjustment."
        ),
        "opportunity": "Make daily life more reliable, healthy and manageable.",
        "caution": "Do not turn every problem into more work or punish yourself with impossible standards.",
        "best_move": "Remove one recurring source of friction and give your body a realistic pace.",
        "questions": (
            "Which repeated task is draining more energy than it deserves?",
            "What would make today easier to repeat tomorrow?",
        ),
    },
    7: {
        "headline": "Let the relationship show you the truth",
        "opening": (
            "A partner, client, collaborator or opponent may reveal something you cannot see alone. "
            "The relationship becomes clearer when both people are allowed to have a real position."
        ),
        "sensitivity": (
            "Another person's mood or decision may carry unusual emotional weight. "
            "Agreement is not the only sign of connection; honest difference can also create clarity."
        ),
        "opportunity": "Strengthen a relationship through clearer expectations and mutual respect.",
        "caution": "Do not surrender your judgment or turn every difference into a contest.",
        "best_move": "Ask what each person is actually promising, needing and responsible for.",
        "questions": (
            "What is this relationship showing me that I could not see alone?",
            "Are the expectations mutual, or am I quietly carrying both sides?",
        ),
    },
    8: {
        "headline": "Bring the hidden cost into the light",
        "opening": (
            "Shared money, trust, obligation or emotional dependence may need more honesty. "
            "What is uncomfortable to name is often the exact thing that restores choice."
        ),
        "sensitivity": (
            "You may be more aware of what is owed, shared or emotionally entangled. "
            "Uncertainty can create a strong desire to control the outcome before all obligations are visible."
        ),
        "opportunity": "Make shared responsibilities, debts and expectations easier to understand.",
        "caution": "Do not let secrecy, fear or borrowing capacity disguise the real obligation.",
        "best_move": "Name the commitment, cost and ownership before agreeing to carry it.",
        "questions": (
            "What obligation needs to be made visible?",
            "Where am I calling something shared when the responsibility is not actually equal?",
        ),
    },
    9: {
        "headline": "Go further, but take the facts with you",
        "opening": (
            "A wider horizon is opening through learning, travel, publishing, legal matters "
            "or people beyond your usual circle. A proven idea may be ready to travel further."
        ),
        "sensitivity": (
            "You may feel restless for a larger answer, a new direction or a broader field. "
            "Excitement about what could be possible can make preparation look less important than it is."
        ),
        "opportunity": "Take a sound idea into a larger world.",
        "caution": "Do not let enthusiasm, certainty or grand claims outrun practical preparation.",
        "best_move": "Test the wider opportunity with someone who understands its real conditions.",
        "questions": (
            "Which idea is genuinely ready for a wider audience?",
            "What practical fact would make this expansion more trustworthy?",
        ),
    },
    10: {
        "headline": "Let the work speak before you do",
        "opening": (
            "Career, reputation or visible responsibility is asking for a clearer result. "
            "The day favours substance that can be seen rather than a performance of being busy."
        ),
        "sensitivity": (
            "You may feel unusually aware of how your work or choices are being judged. "
            "Public pressure can make recognition feel more urgent than the quality of the result."
        ),
        "opportunity": "Create a visible result that strengthens trust in your abilities.",
        "caution": "Do not let status anxiety or the need to be noticed replace the work itself.",
        "best_move": "Complete one result that another person can clearly see and evaluate.",
        "questions": (
            "What result would speak more clearly than another explanation?",
            "Am I improving the work, or managing how I appear while doing it?",
        ),
    },
    11: {
        "headline": "Choose the people who share the future",
        "opening": (
            "Friends, audiences, networks and long-term plans are becoming more important. "
            "The right connection may not be the largest one, but the one that genuinely supports the future you are building."
        ),
        "sensitivity": (
            "You may be more affected by belonging, exclusion or the response of a group. "
            "Popularity can feel like proof even when loyalty and shared purpose are missing."
        ),
        "opportunity": "Strengthen the relationships that support a meaningful long-term direction.",
        "caution": "Do not chase reach, approval or group identity at the expense of genuine connection.",
        "best_move": "Give your attention to the few people who consistently create trust and possibility.",
        "questions": (
            "Which relationship genuinely supports the future I want?",
            "Am I looking for belonging, approval or a real shared purpose?",
        ),
    },
    12: {
        "headline": "Make room for the answer to surface",
        "opening": (
            "Rest, privacy, closure and the quieter parts of your inner life need room. "
            "An answer may be forming beneath the level of immediate action."
        ),
        "sensitivity": (
            "You may feel more tired, private or affected by something difficult to name. "
            "The urge to withdraw is useful when it creates recovery, not when it becomes avoidance."
        ),
        "opportunity": "Recover perspective and complete what has been quietly draining you.",
        "caution": "Do not use silence, secrecy or exhaustion to postpone an issue that needs care.",
        "best_move": "Reduce unnecessary noise and finish one unresolved matter privately.",
        "questions": (
            "What becomes clearer when I stop demanding an immediate answer?",
            "Am I resting in order to recover, or withdrawing in order to avoid?",
        ),
    },
}


PLANET_DRIVE = {
    "Sun": "the need to move in a clear direction and be recognised",
    "Moon": "instinct, mood and the need to feel emotionally safe",
    "Mercury": "messages, facts and the way a decision is explained",
    "Venus": "attraction, relationship needs and judgments about value",
    "Mars": "urgency, desire and the impulse to act",
    "Jupiter": "optimism, growth and the desire to make life larger",
    "Saturn": "responsibility, limits and the need for a durable structure",
    "Uranus": "freedom, surprise and the wish to break an old pattern",
    "Neptune": "imagination, sensitivity and uncertainty about boundaries",
    "Pluto": "power, control and the pressure to uncover what is hidden",
    "True Node": "the pull toward an unfamiliar direction",
}


PLANET_QUESTION = {
    "Sun": "Am I following a clear direction, or protecting how I want to be seen?",
    "Moon": "What feeling needs to settle before I treat it as a fact?",
    "Mercury": "What information still needs to be checked or heard completely?",
    "Venus": "Am I choosing what is genuinely valuable, or merely pleasing in the moment?",
    "Mars": "Would less force and better timing improve the result?",
    "Jupiter": "Which part of this opportunity has already been proven?",
    "Saturn": "What responsibility or boundary needs a clearer shape?",
    "Uranus": "What change has a workable replacement rather than only an exciting escape?",
    "Neptune": "What is intuition here, and what may be wishful thinking?",
    "Pluto": "Am I protecting the truth, or protecting my control over the outcome?",
    "True Node": "What unfamiliar step feels developmental rather than merely novel?",
}


PAIR_HEADLINES = {
    frozenset({3, 9}): "Listen before you expand",
    frozenset({2, 8}): "Name the real cost",
    frozenset({1, 7}): "Stay yourself inside the relationship",
    frozenset({4, 10}): "Protect the private foundation",
    frozenset({5, 11}): "Let the right people see the real work",
    frozenset({6, 12}): "Rest before your body asks for it",
}


PAIR_BRIDGES = {
    frozenset({3, 9}): (
        "A conversation, message or outside opinion may reveal the part of a larger plan "
        "that enthusiasm has overlooked."
    ),
    frozenset({2, 9}): (
        "The question is not only how far an idea can travel, but whether its value, cost "
        "and continuing demands are clear."
    ),
    frozenset({7, 9}): (
        "A relationship or agreement may become the doorway to a larger world, but the terms "
        "need to support the promise."
    ),
    frozenset({2, 3}): (
        "A discussion about money, pricing or personal value needs unusually precise language."
    ),
    frozenset({3, 7}): (
        "The quality of a relationship may depend on what is said clearly—and what is finally heard."
    ),
    frozenset({4, 10}): (
        "A public decision is closely connected to the condition of your private foundation."
    ),
    frozenset({5, 11}): (
        "A creative or heartfelt idea becomes more real when it meets the right audience or community."
    ),
    frozenset({6, 12}): (
        "The balance between effort and recovery is carrying more meaning than another push for productivity."
    ),
    frozenset({1, 7}): (
        "Another person can offer a true mirror, provided you do not abandon your own position."
    ),
    frozenset({2, 8}): (
        "Personal security and shared obligation need to be distinguished before trust can deepen."
    ),
}


PAIR_PSYCHOLOGY = {
    frozenset({"Sun", "Pluto"}): (
        "The tension between direction and control can make it easy to defend a conclusion "
        "before the full truth has been heard."
    ),
    frozenset({"Sun", "Jupiter"}): (
        "Confidence is strong, but the day asks you to distinguish genuine possibility from "
        "the desire for everything to become larger at once."
    ),
    frozenset({"Mercury", "Pluto"}): (
        "Words can carry unusual influence today, making honest inquiry more useful than interrogation "
        "or strategic silence."
    ),
    frozenset({"Mercury", "Saturn"}): (
        "A serious conversation or practical limit may slow the answer down, but it can also make "
        "the eventual decision more dependable."
    ),
    frozenset({"Venus", "Mars"}): (
        "Attraction and irritation may be close together, so intensity should not be mistaken for "
        "compatibility or certainty."
    ),
    frozenset({"Jupiter", "Pluto"}): (
        "Growth raises questions of power, ownership and scale. The opening is real only when the "
        "structure does not depend on pressure or hidden control."
    ),
    frozenset({"Jupiter", "Saturn"}): (
        "Hope and restraint can work together. A larger future becomes believable when it has a sequence, "
        "a limit and a realistic responsibility."
    ),
    frozenset({"Mars", "Saturn"}): (
        "Pressure is meeting resistance. Better timing and technique will accomplish more than trying "
        "to overpower the limit."
    ),
    frozenset({"Jupiter", "Neptune"}): (
        "Vision is generous, but imagination needs one measurable fact to keep inspiration from becoming projection."
    ),
}


@dataclass(frozen=True)
class DailyAspect:
    planet1: str
    planet2: str
    name: str
    orb: float
    house1: int
    house2: int
    position1: str
    position2: str

    @property
    def planets(self) -> frozenset[str]:
        return frozenset({self.planet1, self.planet2})

    @property
    def houses(self) -> frozenset[int]:
        return frozenset({self.house1, self.house2})

    @property
    def label(self) -> str:
        return f"{self.planet1} {self.name} {self.planet2}"


@dataclass(frozen=True)
class FreeDailyReading:
    sign: str
    reading_date: date
    sun_house: int
    moon_house: int
    headline: str
    forecast_paragraphs: tuple[str, str]
    reflection_questions: tuple[str, str, str, str]
    daily_theme: str
    wider_context: str
    opportunity: str
    caution: str
    best_move: str
    conclusion: str
    house_matrix: str
    aspects: tuple[str, ...]
    anchor_aspect: DailyAspect | None
    love_note: str
    work_note: str
    money_note: str
    positions: dict[str, Position]
    houses: dict[str, int]


@lru_cache(maxsize=256)
def _year_convergence_clusters(sign: str, year: int, timezone_name: str):
    year_events = period_events(
        date(year, 1, 1),
        date(year, 12, 31),
        sign,
        timezone_name,
    )
    return tuple(convergence_points(year_events, maximum=9))


def _active_convergence_context(sign: str, d: date, timezone_name: str) -> str:
    clusters = _year_convergence_clusters(sign, d.year, timezone_name)

    current = next(
        (
            cluster
            for cluster in clusters
            if cluster.start_date <= d <= cluster.end_date
        ),
        None,
    )
    upcoming = next(
        (
            cluster
            for cluster in sorted(clusters, key=lambda item: item.start_date)
            if d < cluster.start_date <= d + timedelta(days=14)
        ),
        None,
    )
    recent = next(
        (
            cluster
            for cluster in sorted(
                clusters,
                key=lambda item: item.end_date,
                reverse=True,
            )
            if d - timedelta(days=14) <= cluster.end_date < d
        ),
        None,
    )

    cluster = current or upcoming or recent
    if not cluster:
        return (
            "No major annual convergence is currently active or approaching. "
            "The daily house pattern is therefore the clearest guide."
        )

    if current:
        timing = "The wider background currently active is"
    elif upcoming:
        timing = "The next wider background approaching is"
    else:
        timing = "The most recent wider background was"

    material = convergence_interpretation(cluster)
    return (
        f"{timing} **{material['title']}**. "
        f"{material['meaning']} {material['strategy']}"
    )


def _daily_aspect(
    aspect: Aspect,
    positions: dict[str, Position],
    houses: dict[str, int],
) -> DailyAspect:
    return DailyAspect(
        planet1=aspect.planet1,
        planet2=aspect.planet2,
        name=aspect.name,
        orb=aspect.orb,
        house1=houses[aspect.planet1],
        house2=houses[aspect.planet2],
        position1=positions[aspect.planet1].label(),
        position2=positions[aspect.planet2].label(),
    )


def _aspect_summary(
    positions: dict[str, Position],
    houses: dict[str, int],
    maximum: int = 3,
) -> tuple[str, ...]:
    aspects = detect_aspects(positions, include_moon=True, maximum=maximum)
    lines: list[str] = []
    for aspect in aspects:
        p1_theme = PLANET_MEANINGS[aspect.planet1]["core"]
        p2_theme = PLANET_MEANINGS[aspect.planet2]["core"]
        lines.append(
            f"**{aspect.planet1} {aspect.name} {aspect.planet2}** "
            f"(orb {aspect.orb:.2f}°) connects house {houses[aspect.planet1]} "
            f"with house {houses[aspect.planet2]}: {p1_theme} interact with {p2_theme}."
        )
    return tuple(lines)


def _headline(
    primary_house: int,
    anchor: DailyAspect | None,
) -> str:
    if anchor and anchor.name in {"square", "opposition"}:
        pair_headline = PAIR_HEADLINES.get(anchor.houses)
        if pair_headline:
            return pair_headline
        if "Pluto" in anchor.planets:
            return "Do not force the conclusion"
        if "Mercury" in anchor.planets:
            return "Check what was actually said"
        if "Venus" in anchor.planets:
            return "Choose what is valuable, not merely attractive"
        if "Mars" in anchor.planets:
            return "Use less force and better timing"
        if "Saturn" in anchor.planets:
            return "Let the limit improve the plan"

    if anchor and anchor.name in {"trine", "sextile"}:
        if "Jupiter" in anchor.planets:
            return "Let the opportunity prove itself"
        if "Venus" in anchor.planets:
            return "Follow what feels both warm and worthwhile"
        if "Mercury" in anchor.planets:
            return "The useful answer is ready to be heard"

    return HOUSE_VOICE[primary_house]["headline"]


def _bridge_sentence(anchor: DailyAspect | None) -> str:
    if not anchor:
        return ""
    specific = PAIR_BRIDGES.get(anchor.houses)
    if specific:
        return specific

    first = HOUSE_NAMES[anchor.house1]
    second = HOUSE_NAMES[anchor.house2]
    if anchor.name in {"square", "opposition"}:
        return (
            f"The day places **{first}** in tension with **{second}**. "
            "A decision in one area is likely to expose what the other area still needs."
        )
    if anchor.name in {"trine", "sextile"}:
        return (
            f"A supportive link between **{first}** and **{second}** makes it easier "
            "for progress in one area to open a door in the other."
        )
    return (
        f"The day concentrates **{first}** and **{second}** into one connected question."
    )


def _psychology_sentence(anchor: DailyAspect | None) -> str:
    if not anchor:
        return (
            "The value of the day lies in responding to what is actually happening "
            "rather than trying to produce certainty too quickly."
        )

    specific = PAIR_PSYCHOLOGY.get(anchor.planets)
    if specific:
        return specific

    drive1 = PLANET_DRIVE[anchor.planet1]
    drive2 = PLANET_DRIVE[anchor.planet2]
    if anchor.name in {"square", "opposition"}:
        return (
            f"{drive1.capitalize()} may pull against {drive2}. "
            "Neither side needs to win immediately; the tension is showing where a more honest adjustment is required."
        )
    if anchor.name in {"trine", "sextile"}:
        return (
            f"{drive1.capitalize()} can cooperate with {drive2}, creating an opening that feels natural "
            "but still benefits from one practical test."
        )
    return (
        f"{drive1.capitalize()} is merging with {drive2}. "
        "The feeling may be strong because the two concerns are difficult to separate today."
    )


def _closing_sentence(anchor: DailyAspect | None) -> str:
    if not anchor:
        return "Give the quieter truth enough time to become clear before you turn it into a decision."
    if "Pluto" in anchor.planets:
        return (
            "What is hidden becomes useful when you stop trying to control the conclusion "
            "and allow the less convenient truth to be heard."
        )
    if "Mercury" in anchor.planets:
        return "Read the message twice, ask for clarification and leave room for the answer to change your mind."
    if "Saturn" in anchor.planets:
        return "The delay or limit is not necessarily a refusal; it may be the structure that makes the choice sustainable."
    if "Jupiter" in anchor.planets:
        return "Let confidence open the door, then ask evidence to decide how far you walk through it."
    if "Neptune" in anchor.planets:
        return "Keep the inspiration, but give it one clear boundary and one fact that can be checked."
    if "Mars" in anchor.planets:
        return "A measured action will protect more of your energy than an immediate attempt to settle everything."
    if "Venus" in anchor.planets:
        return "Choose the response that preserves both warmth and self-respect rather than simply reducing tension."
    return "Give the facts and the quieter response equal weight before you decide what the day means."


def _forecast_paragraphs(
    primary_house: int,
    secondary_house: int,
    anchor: DailyAspect | None,
) -> tuple[str, str]:
    primary = HOUSE_VOICE[primary_house]
    secondary = HOUSE_VOICE[secondary_house]

    first = " ".join(
        part
        for part in (
            primary["opening"],
            _bridge_sentence(anchor),
            _psychology_sentence(anchor),
        )
        if part
    )

    second = " ".join(
        (
            secondary["sensitivity"],
            f"The main risk is this: {secondary['caution'].lower()}",
            _closing_sentence(anchor),
        )
    )
    return first, second


def _unique_questions(
    primary_house: int,
    secondary_house: int,
    anchor: DailyAspect | None,
) -> tuple[str, str, str, str]:
    questions: list[str] = []

    if anchor and anchor.houses == frozenset({3, 9}):
        questions.append("What could I learn by speaking less and listening longer?")

    questions.extend(HOUSE_VOICE[primary_house]["questions"])
    questions.append(HOUSE_VOICE[secondary_house]["questions"][0])

    if anchor:
        questions.append(PLANET_QUESTION[anchor.planet2])
        questions.append(PLANET_QUESTION[anchor.planet1])
        if anchor.name in {"square", "opposition"}:
            questions.append("What becomes clearer when I stop forcing an immediate conclusion?")
        elif anchor.name in {"trine", "sextile"}:
            questions.append("Which opening feels both encouraging and practical?")
        else:
            questions.append("Where are two concerns becoming impossible to separate?")

    result: list[str] = []
    seen: set[str] = set()
    for question in questions:
        if question not in seen:
            result.append(question)
            seen.add(question)
        if len(result) == 4:
            break

    while len(result) < 4:
        fallback = HOUSE_VOICE[secondary_house]["questions"][len(result) % 2]
        if fallback not in seen:
            result.append(fallback)
            seen.add(fallback)
        else:
            result.append("What would a calmer and more honest response look like?")
    return tuple(result)  # type: ignore[return-value]


def _area_note(
    area: str,
    primary_house: int,
    secondary_house: int,
    anchor: DailyAspect | None,
) -> str:
    active = [primary_house, secondary_house]
    if anchor:
        active.extend([anchor.house1, anchor.house2])

    targets = {
        "love": {5, 7, 8, 11},
        "work": {3, 6, 9, 10, 11},
        "money": {2, 5, 8, 10},
    }
    relevant = next((house for house in active if house in targets[area]), None)

    if area == "love":
        if relevant == 5:
            return "Let affection or attraction be enjoyable without asking it to prove the whole future today."
        if relevant == 7:
            return "A relationship becomes clearer through mutual expectations, not silent guessing."
        if relevant == 8:
            return "Trust deepens when emotional and practical obligations can be named without pressure."
        if relevant == 11:
            return "Friendship and shared purpose may matter more than dramatic reassurance."
        return "Love is not the loudest theme today; keep the conversation honest and allow the other person room to respond."

    if area == "work":
        if relevant == 3:
            return "A useful message, question or correction can improve the direction of the work."
        if relevant == 6:
            return "Fix one repeated source of friction instead of asking yourself to work harder around it."
        if relevant == 9:
            return "A proven idea may be ready for a wider audience, new market or larger field of study."
        if relevant == 10:
            return "Finish something visible; a clear result will carry more authority than another promise."
        if relevant == 11:
            return "The right collaborator or audience can strengthen a long-term plan."
        return "Keep the work simple enough to judge by its result rather than by the amount of activity around it."

    if relevant == 2:
        return "Check real income, cost and continuing obligation; movement is not the same as financial strength."
    if relevant == 5:
        return "Enjoy the idea, but keep speculation and emotional spending within a clear limit."
    if relevant == 8:
        return "Bring debts, shared costs or hidden obligations into the open before agreeing to more."
    if relevant == 10:
        return "A professional opportunity is valuable only when the compensation and responsibility are equally clear."
    return "Money is not the central theme today; avoid spending merely to relieve uncertainty or prove momentum."


FAST_PLANETS = {"Sun", "Moon", "Mercury", "Venus", "Mars"}
SLOW_PLANETS = {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "True Node"}
RELATIONSHIP_HOUSES = {5, 7, 8, 11}


DAILY_HEADLINES = {
    frozenset({"Moon", "Mercury"}): {
        "hard": "Read between the lines",
        "flow": "Say what you actually mean",
        "blend": "The conversation has a second meaning",
    },
    frozenset({"Moon", "Venus"}): {
        "hard": "Do not bargain with your own heart",
        "flow": "Let yourself receive the affection",
        "blend": "Your feelings know what feels valuable",
    },
    frozenset({"Moon", "Mars"}): {
        "hard": "Desire does not need a fight",
        "flow": "Say yes to the honest spark",
        "blend": "The feeling wants movement",
    },
    frozenset({"Moon", "Jupiter"}): {
        "hard": "Do not promise more than the moment can hold",
        "flow": "Let hope make the room larger",
        "blend": "The feeling wants a bigger life",
    },
    frozenset({"Moon", "Saturn"}): {
        "hard": "Do not mistake distance for rejection",
        "flow": "Let consistency seduce you",
        "blend": "The heart is asking for proof",
    },
    frozenset({"Moon", "Uranus"}): {
        "hard": "The surprise is the point",
        "flow": "Follow the unexpected spark",
        "blend": "Something in you wants freedom",
    },
    frozenset({"Moon", "Neptune"}): {
        "hard": "The mystery is doing half the seduction",
        "flow": "Trust the feeling, then check the story",
        "blend": "The dream is emotionally persuasive",
    },
    frozenset({"Moon", "Pluto"}): {
        "hard": "Do not hand your power to the feeling",
        "flow": "The deeper truth is ready",
        "blend": "The feeling goes further than expected",
    },
    frozenset({"Venus", "Mars"}): {
        "hard": "Chemistry wants a reaction",
        "flow": "Desire can move without a chase",
        "blend": "Attraction is changing the temperature",
    },
    frozenset({"Venus", "Saturn"}): {
        "hard": "The slow burn needs a real future",
        "flow": "Loyalty is becoming attractive",
        "blend": "Love is asking for substance",
    },
    frozenset({"Venus", "Uranus"}): {
        "hard": "The rebel is not the whole story",
        "flow": "Make room for the unconventional",
        "blend": "Attraction refuses the usual script",
    },
    frozenset({"Venus", "Neptune"}): {
        "hard": "Do not fall in love with the missing pieces",
        "flow": "Keep the romance and the clear eyes",
        "blend": "The fantasy is beautifully convincing",
    },
    frozenset({"Venus", "Pluto"}): {
        "hard": "Magnetism is not permission",
        "flow": "Let intimacy deepen without surrender",
        "blend": "The attraction has real gravity",
    },
    frozenset({"Mercury", "Saturn"}): {
        "hard": "The silence needs a better question",
        "flow": "A serious answer is worth waiting for",
        "blend": "The words need structure",
    },
    frozenset({"Mercury", "Pluto"}): {
        "hard": "Do not interrogate the truth",
        "flow": "The hidden answer can be named",
        "blend": "The conversation has power",
    },
    frozenset({"Sun", "Uranus"}): {
        "hard": "Freedom needs more than an escape",
        "flow": "The unexpected door is open",
        "blend": "A new version of you is arriving",
    },
    frozenset({"Sun", "Jupiter"}): {
        "hard": "Bigger is not automatically better",
        "flow": "The bigger life is calling",
        "blend": "Confidence is taking up more space",
    },
    frozenset({"Sun", "Pluto"}): {
        "hard": "Do not force the transformation",
        "flow": "Own the power you have earned",
        "blend": "A deeper identity is taking shape",
    },
}


def _aspect_key(aspect: Aspect) -> tuple[str, str, str]:
    p1, p2 = sorted((aspect.planet1, aspect.planet2))
    return p1, p2, aspect.name


def _daily_trigger_aspect(
    d: date,
    timezone_name: str,
    positions: dict[str, Position],
    houses: dict[str, int],
) -> DailyAspect | None:
    """Select a date-sensitive trigger rather than a slow generational aspect."""
    aspects = detect_aspects(positions, include_moon=True)
    if not aspects:
        return None

    previous = {
        _aspect_key(item): item.orb
        for item in detect_aspects(
            positions_for_date(d - timedelta(days=1), timezone_name),
            include_moon=True,
        )
    }
    following = {
        _aspect_key(item): item.orb
        for item in detect_aspects(
            positions_for_date(d + timedelta(days=1), timezone_name),
            include_moon=True,
        )
    }

    scored: list[tuple[float, Aspect]] = []
    for aspect in aspects:
        planets = {aspect.planet1, aspect.planet2}
        if planets <= SLOW_PLANETS:
            continue

        score = aspect.strength
        if "Moon" in planets:
            score += 3.4
        if "Venus" in planets:
            score += 1.5
        if "Mars" in planets:
            score += 1.4
        if "Mercury" in planets:
            score += 0.9
        if "Sun" in planets:
            score += 0.5
        if aspect.name in {"square", "opposition"}:
            score += 0.8

        key = _aspect_key(aspect)
        before_orb = previous.get(key, 99.0)
        after_orb = following.get(key, 99.0)
        if aspect.orb <= before_orb and aspect.orb <= after_orb and aspect.orb <= 3.0:
            score += 2.8
        if after_orb < aspect.orb:
            score += 0.7
        elif before_orb < aspect.orb:
            score -= 0.6

        score -= max(0.0, aspect.orb - 3.0) * 0.25
        scored.append((score, aspect))

    if not scored:
        return _daily_aspect(aspects[0], positions, houses)

    scored.sort(key=lambda item: (-item[0], item[1].orb))
    return _daily_aspect(scored[0][1], positions, houses)


def _tone_bucket(aspect: DailyAspect | None) -> str:
    if not aspect:
        return "blend"
    if aspect.name in {"square", "opposition"}:
        return "hard"
    if aspect.name in {"trine", "sextile"}:
        return "flow"
    return "blend"


def _headline_v3(
    moon_house: int,
    anchor: DailyAspect | None,
) -> str:
    if anchor:
        pair = DAILY_HEADLINES.get(anchor.planets)
        if pair:
            return pair[_tone_bucket(anchor)]

        if "Moon" in anchor.planets:
            return HOUSE_VOICE[moon_house]["headline"]
        if anchor.name in {"square", "opposition"}:
            return "The tension is telling the truth"
        if anchor.name in {"trine", "sextile"}:
            return "The opening feels easier today"
        return "Two parts of the story are becoming one"

    return HOUSE_VOICE[moon_house]["headline"]


def _daily_trigger_sentence(anchor: DailyAspect | None) -> str:
    if not anchor:
        return (
            "The day's meaning comes mainly through the Moon's house and the way "
            "your emotional response changes the larger monthly story."
        )

    first = HOUSE_NAMES[anchor.house1]
    second = HOUSE_NAMES[anchor.house2]
    if anchor.name in {"square", "opposition"}:
        return (
            f"Today's pressure links {first} with {second}. "
            "The attraction of an immediate answer is strong, but the tension is revealing "
            "what cannot be solved by force, performance or wishful thinking."
        )
    if anchor.name in {"trine", "sextile"}:
        return (
            f"A supportive current connects {first} with {second}. "
            "The opening is real, although it still needs a choice that protects your standards."
        )
    return (
        f"Today blends {first} with {second}. "
        "What appears to be two separate concerns is really one emotional decision."
    )


def _relationship_archetype(
    anchor: DailyAspect | None,
    venus_house: int,
    moon_house: int,
) -> str:
    if not anchor:
        return (
            "The relationship story is quieter than the practical story, but it still asks a useful question: "
            "who makes you feel seen without asking you to become smaller?"
        )

    planets = anchor.planets
    tone = _tone_bucket(anchor)

    if planets == frozenset({"Venus", "Mars"}):
        if tone == "hard":
            return (
                "Chemistry is alive, and so is the temptation to chase, provoke or test it. "
                "The dangerous-looking person may be compelling, but the deeper fantasy is someone bold "
                "enough to want you and mature enough not to punish your boundaries."
            )
        return (
            "Attraction can move easily today. Let the spark be direct, playful and mutual rather than "
            "turning it into a contest over who cares less."
        )

    if planets == frozenset({"Moon", "Saturn"}):
        if tone == "flow":
            return (
                "There is something quietly seductive about steadiness. An older, reserved or highly "
                "self-controlled person may stand out, but consistency matters more than the age gap "
                "or the aura of authority."
            )
        return (
            "Emotional distance may look like strength, especially in someone older, controlled or hard to read. "
            "Do not romanticise withholding; the right person can be composed and still make you feel secure."
        )

    if planets == frozenset({"Moon", "Mercury"}):
        return (
            "A message can stir more than it says. Banter is attractive, but emotional accuracy is more intimate: "
            "notice who listens closely enough to understand the feeling beneath your words."
        )

    if planets == frozenset({"Moon", "Neptune"}):
        return (
            "Mystery, longing and the unavailable person can feel unusually cinematic. Keep the fantasy, "
            "but do not write the missing chapters for someone who has not shown up consistently."
        )

    if planets == frozenset({"Moon", "Pluto"}):
        return (
            "A connection may feel intense enough to expose jealousy, control or an old fear of being replaceable. "
            "Magnetism can be real without giving anyone ownership of your emotional world."
        )

    if planets == frozenset({"Moon", "Uranus"}):
        return (
            "The unconventional person, sudden message or rebellious choice may carry real electricity. "
            "Enjoy the surprise without abandoning the freedom and respect you will need tomorrow."
        )

    if "Venus" in planets and "Pluto" in planets:
        return (
            "The attraction has a darker gravity: secrecy, power and the wish to be unforgettable. "
            "Intensity is not proof of safety, and being desired should never require surrendering autonomy."
        )

    if "Venus" in planets and "Uranus" in planets:
        return (
            "Someone unusual, rebellious or outside your normal type may interrupt the script. "
            "The thrill is useful, but lasting chemistry still needs room for honesty and independence."
        )

    if "Venus" in planets and "Saturn" in planets:
        return (
            "This is slow-burn territory: loyalty, restraint, distance or a difference in age and status. "
            "The bond is worth taking seriously only when responsibility is mutual rather than one-sided."
        )

    if "Venus" in planets and "Neptune" in planets:
        return (
            "Romance can feel fated, poetic or almost telepathic. Enjoy the softness, then look for ordinary evidence: "
            "clear words, reliable effort and a person who is available in real life."
        )

    if "Mars" in planets and "Pluto" in planets:
        return (
            "Desire may carry a power struggle beneath it. The compelling person is not necessarily the right person; "
            "real intimacy can hold intensity without coercion, punishment or games."
        )

    if "Moon" in planets or "Venus" in planets or "Mars" in planets:
        return (
            "Attraction is revealing what you want to feel around another person. Let the desire be honest, "
            "but ask whether the connection also offers respect, emotional presence and room to remain yourself."
        )

    if venus_house in RELATIONSHIP_HOUSES or moon_house in RELATIONSHIP_HOUSES:
        return (
            "Relationships are part of today's plot even if they are not the loudest event. "
            "The meaningful connection is the one that combines attraction with emotional safety, mutual respect "
            "and the freedom to tell the truth."
        )

    return (
        "Love is not absent simply because another life area is louder. Notice who adds warmth without creating confusion, "
        "and who can hold your independence without withdrawing affection."
    )


def _forecast_paragraphs_v3(
    sun_house: int,
    moon_house: int,
    anchor: DailyAspect | None,
    relationship_story: str,
) -> tuple[str, str]:
    wider = HOUSE_VOICE[sun_house]["opening"]
    emotional = HOUSE_VOICE[moon_house]["sensitivity"]
    first = " ".join((wider, _daily_trigger_sentence(anchor), emotional))
    second = f"In love and relationships, {relationship_story[0].lower() + relationship_story[1:]}"
    return first, second


def _questions_v3(
    sun_house: int,
    moon_house: int,
    anchor: DailyAspect | None,
) -> tuple[str, str, str, str]:
    questions = [
        HOUSE_VOICE[moon_house]["questions"][0],
        HOUSE_VOICE[sun_house]["questions"][0],
    ]

    if anchor:
        if anchor.planets == frozenset({"Venus", "Mars"}):
            questions.append("Is this chemistry asking for honesty, or only a reaction?")
        elif "Saturn" in anchor.planets:
            questions.append("Is this person consistent, or merely difficult to reach?")
        elif "Uranus" in anchor.planets:
            questions.append("Does the excitement leave room for my freedom tomorrow?")
        elif "Neptune" in anchor.planets:
            questions.append("What do I know from evidence, and what am I supplying from fantasy?")
        elif "Pluto" in anchor.planets:
            questions.append("Am I drawn to intimacy, or to the feeling of being consumed by it?")
        else:
            questions.append(PLANET_QUESTION[anchor.planet2])
    else:
        questions.append("Who makes me feel seen without asking me to become smaller?")

    questions.append("What would attraction look like if it also felt emotionally safe?")

    result = []
    for question in questions:
        if question not in result:
            result.append(question)
    while len(result) < 4:
        result.append("What truth becomes easier to admit when I stop performing indifference?")
    return tuple(result[:4])  # type: ignore[return-value]


def _best_move_v3(
    anchor: DailyAspect | None,
    sun_house: int,
) -> str:
    if anchor:
        if anchor.planets == frozenset({"Moon", "Mercury"}):
            return "Pause before replying, then answer the feeling as well as the words."
        if anchor.planets == frozenset({"Venus", "Mars"}):
            return "Let the attraction breathe without chasing, testing or pretending not to care."
        if anchor.planets == frozenset({"Moon", "Saturn"}):
            return "Choose the person or plan that proves itself through calm, repeated effort."
        if "Neptune" in anchor.planets:
            return "Keep the romance or inspiration, but verify one important fact."
        if "Pluto" in anchor.planets:
            return "Name what you want without trying to control how the other person responds."
        if "Uranus" in anchor.planets:
            return "Try the unexpected option while keeping one boundary that protects your freedom."
        if "Mars" in anchor.planets:
            return "Use directness instead of pressure and let the response give you information."
    return HOUSE_VOICE[sun_house]["best_move"]


def _technical_aspect_summary(
    positions: dict[str, Position],
    houses: dict[str, int],
    anchor: DailyAspect | None,
    maximum: int = 3,
) -> tuple[str, ...]:
    selected = []
    if anchor:
        selected.append(anchor.label)

    lines: list[str] = []
    for aspect in detect_aspects(positions, include_moon=True):
        label = f"{aspect.planet1} {aspect.name} {aspect.planet2}"
        if label in selected or len(lines) < maximum:
            p1_theme = PLANET_MEANINGS[aspect.planet1]["core"]
            p2_theme = PLANET_MEANINGS[aspect.planet2]["core"]
            lines.append(
                f"**{label}** (orb {aspect.orb:.2f}°) connects house "
                f"{houses[aspect.planet1]} with house {houses[aspect.planet2]}: "
                f"{p1_theme} interact with {p2_theme}."
            )
        if len(lines) >= maximum:
            break
    return tuple(lines)


def free_daily_reading(
    sign: str,
    d: date,
    timezone_name: str = "Australia/Sydney",
) -> FreeDailyReading:
    positions = positions_for_date(d, timezone_name)
    houses = house_map(positions, sign)
    sun_house = houses["Sun"]
    moon_house = houses["Moon"]
    venus_house = houses["Venus"]

    anchor = _daily_trigger_aspect(
        d,
        timezone_name,
        positions,
        houses,
    )
    relationship_story = _relationship_archetype(
        anchor,
        venus_house,
        moon_house,
    )

    headline = _headline_v3(moon_house, anchor)
    forecast_paragraphs = _forecast_paragraphs_v3(
        sun_house,
        moon_house,
        anchor,
        relationship_story,
    )
    questions = _questions_v3(sun_house, moon_house, anchor)

    if anchor:
        daily_theme = (
            f"The date-sensitive trigger is **{anchor.label}** at an orb of "
            f"{anchor.orb:.2f}°. It connects house {anchor.house1} "
            f"({HOUSE_NAMES[anchor.house1]}) with house {anchor.house2} "
            f"({HOUSE_NAMES[anchor.house2]}). The Sun remains in house {sun_house}, "
            f"while the Moon moves through house {moon_house}."
        )
    else:
        daily_theme = (
            f"The Sun remains in house {sun_house} ({HOUSE_NAMES[sun_house]}), "
            f"while the Moon moves through house {moon_house} "
            f"({HOUSE_NAMES[moon_house]})."
        )

    opportunity = HOUSE_VOICE[sun_house]["opportunity"]
    caution = HOUSE_VOICE[moon_house]["caution"]
    best_move = _best_move_v3(anchor, sun_house)

    return FreeDailyReading(
        sign=sign,
        reading_date=d,
        sun_house=sun_house,
        moon_house=moon_house,
        headline=headline,
        forecast_paragraphs=forecast_paragraphs,
        reflection_questions=questions,
        daily_theme=daily_theme,
        wider_context=_active_convergence_context(sign, d, timezone_name),
        opportunity=opportunity,
        caution=caution,
        best_move=best_move,
        conclusion=house_aware_conclusion(sign, sun_house, moon_house),
        house_matrix=house_reference_matrix(sign, {sun_house, moon_house}),
        aspects=_technical_aspect_summary(positions, houses, anchor),
        anchor_aspect=anchor,
        love_note=relationship_story,
        work_note=_area_note("work", sun_house, moon_house, anchor),
        money_note=_area_note("money", sun_house, moon_house, anchor),
        positions=positions,
        houses=houses,
    )


def prepared_order_email(
    email_address: str,
    product: str,
    customer_name: str,
    customer_email: str,
    sign: str,
    requested_period: str,
    timezone_name: str,
    payment_reference: str = "",
    main_focus: str = "",
    personal_question: str = "",
) -> str:
    subject = quote(f"{product} order details — {sign}")
    body = quote(
        "\n".join(
            [
                f"Product: {product}",
                f"Customer name: {customer_name}",
                f"Customer email: {customer_email}",
                f"Zodiac sign: {sign}",
                f"Requested month/year: {requested_period}",
                f"Timezone: {timezone_name}",
                f"Main focus: {main_focus or 'General overview'}",
                f"Personal question: {personal_question or 'None supplied'}",
                "",
                f"Payment reference or receipt: {payment_reference}",
                "",
                "Additional note:",
            ]
        )
    )
    return f"mailto:{email_address}?subject={subject}&body={body}"
