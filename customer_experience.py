from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
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


def _active_convergence_context(sign: str, d: date, timezone_name: str) -> str:
    year_events = period_events(
        date(d.year, 1, 1),
        date(d.year, 12, 31),
        sign,
        timezone_name,
    )
    year_clusters = convergence_points(year_events, maximum=9)
    active = next(
        (
            cluster
            for cluster in year_clusters
            if cluster.start_date - timedelta(days=14)
            <= d
            <= cluster.end_date + timedelta(days=14)
        ),
        None,
    )
    if not active:
        return (
            "No major annual convergence is at its peak today. "
            "The daily house pattern is therefore the clearest guide."
        )

    material = convergence_interpretation(active)
    return (
        f"The wider background is **{material['title']}**. "
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


def free_daily_reading(
    sign: str,
    d: date,
    timezone_name: str = "Australia/Sydney",
) -> FreeDailyReading:
    positions = positions_for_date(d, timezone_name)
    houses = house_map(positions, sign)
    sun_house = houses["Sun"]
    moon_house = houses["Moon"]

    raw_aspects = detect_aspects(positions, include_moon=True, maximum=6)
    anchor = (
        _daily_aspect(raw_aspects[0], positions, houses)
        if raw_aspects
        else None
    )

    headline = _headline(sun_house, anchor)
    forecast_paragraphs = _forecast_paragraphs(
        sun_house,
        moon_house,
        anchor,
    )
    questions = _unique_questions(sun_house, moon_house, anchor)

    daily_theme = (
        f"House {sun_house} opens the day through {HOUSE_NAMES[sun_house]}, "
        f"while house {moon_house} describes the immediate emotional pressure around "
        f"{HOUSE_NAMES[moon_house]}."
    )
    opportunity = HOUSE_VOICE[sun_house]["opportunity"]
    caution = HOUSE_VOICE[moon_house]["caution"]
    best_move = HOUSE_VOICE[sun_house]["best_move"]

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
        aspects=_aspect_summary(positions, houses),
        anchor_aspect=anchor,
        love_note=_area_note("love", sun_house, moon_house, anchor),
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
                "",
                "Payment reference or receipt:",
                "",
                "Additional note:",
            ]
        )
    )
    return f"mailto:{email_address}?subject={subject}&body={body}"
