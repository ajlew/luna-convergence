from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

from universal_monthly_evidence import FORMULA_VERSION, SIGN_META, StoryContext


@dataclass(frozen=True)
class MonthlyStoryProfile:
    expected_pair: tuple[int, int]
    headline: str
    theme_axis: str
    central_storyline: str
    act_hooks: tuple[str, str, str, str]
    act_titles: tuple[str, str, str, str]
    opening_copy: str
    complication_copy: str
    relationship_question: str
    relationship_support: str
    climax_copy: str
    resolution_copy: str
    do_line: str
    dont_line: str
    action_plan: tuple[str, str, str]
    romance_active: str
    romance_quiet: str
    love_hook: str
    work_hook: str
    money_hook: str
    overview_copy: tuple[str, str] = ()
    strategy_hidden: str = ""
    strategy_watch: str = ""
    love_move: str = ""
    work_copy: str = ""
    work_move: str = ""
    money_copy: str = ""
    money_move: str = ""
    formula_version: str = FORMULA_VERSION
    source: str = "universal_house_scenario_formula"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["expected_pair"] = list(self.expected_pair)
        payload["act_hooks"] = list(self.act_hooks)
        payload["act_titles"] = list(self.act_titles)
        payload["action_plan"] = list(self.action_plan)
        payload["overview_copy"] = list(self.overview_copy)
        return payload


HOUSE_LANGUAGE: dict[int, dict[str, str]] = {
    1: {
        "axis": "Identity, energy & direction",
        "subject": "A new direction",
        "short": "personal direction",
        "source": "identity, confidence or a personal decision",
        "condition": "it reflects the person now taking the lead",
        "opening_action": "Name the direction that deserves real movement.",
        "destination_action": "Take the step that makes the new direction visible.",
        "risk": "Let other people's reactions define the direction before it has taken shape.",
    },
    2: {
        "axis": "Money, value & security",
        "subject": "What matters",
        "short": "value and security",
        "source": "money, value, confidence or a question of worth",
        "condition": "its value is clear enough to support",
        "opening_action": "Name the value, cost or priority shaping the choice.",
        "destination_action": "Choose the option that supports both worth and security.",
        "risk": "Treat urgency, attention or scarcity as proof of value.",
    },
    3: {
        "axis": "Communication, choices & movement",
        "subject": "The message",
        "short": "communication and choice",
        "source": "a conversation, message, application or local move",
        "condition": "the facts can be spoken and acted on",
        "opening_action": "Start the conversation that can change the available options.",
        "destination_action": "Put the decision into words, documents or a clear next move.",
        "risk": "Keep talking around the issue after the important fact is already visible.",
    },
    4: {
        "axis": "Home, family & private foundations",
        "subject": "The private foundation",
        "short": "home and emotional foundations",
        "source": "home, family, location or emotional security",
        "condition": "it has somewhere real to land",
        "opening_action": "Clarify the private condition shaping the month.",
        "destination_action": "Give the decision a home, location or emotional base.",
        "risk": "Build the public plan on a private foundation that cannot hold it.",
    },
    5: {
        "axis": "Romance, creativity & pleasure",
        "subject": "The spark",
        "short": "romance and creativity",
        "source": "a creative opening, attraction, invitation or desire",
        "condition": "joy, creativity or attraction has room to grow",
        "opening_action": "Name the spark worth developing.",
        "destination_action": "Give pleasure, creativity or attraction a clear place to grow.",
        "risk": "Mistake intensity for a direction that can continue.",
    },
    6: {
        "axis": "Work, rhythm & wellbeing",
        "subject": "The plan",
        "short": "work, rhythm and wellbeing",
        "source": "workload, routine, health or a practical system",
        "condition": "the week can carry it",
        "opening_action": "Identify the routine or workload that needs a better shape.",
        "destination_action": "Create the rhythm that can carry the result beyond the month.",
        "risk": "Call constant urgency progress when it is really draining capacity.",
    },
    7: {
        "axis": "Relationships, clients & agreements",
        "subject": "The connection",
        "short": "relationships and agreements",
        "source": "a relationship, client, agreement or shared decision",
        "condition": "effort becomes mutual",
        "opening_action": "Name what the connection or agreement needs next.",
        "destination_action": "Choose the agreement that makes effort and expectations mutual.",
        "risk": "Maintain harmony by carrying more than the other side.",
    },
    8: {
        "axis": "Trust, shared resources & obligations",
        "subject": "The shared stake",
        "short": "trust and shared resources",
        "source": "shared money, trust, intimacy or an obligation",
        "condition": "trust and resources are named clearly",
        "opening_action": "Bring the shared stake, obligation or boundary into the open.",
        "destination_action": "Choose the arrangement that makes trust, ownership and limits clear.",
        "risk": "Confuse emotional intensity with safe, shared capacity.",
    },
    9: {
        "axis": "Travel, study & wider horizons",
        "subject": "The wider horizon",
        "short": "travel, study and wider horizons",
        "source": "travel, study, publishing, belief or a wider-world opening",
        "condition": "the next path can be explored with direction",
        "opening_action": "Name the wider path worth exploring.",
        "destination_action": "Turn the wider possibility into a course, application, journey or published move.",
        "risk": "Use expansion to avoid the detail that would make it real.",
    },
    10: {
        "axis": "Career, reputation & visible results",
        "subject": "The ambition",
        "short": "career and visible results",
        "source": "career, recognition, leadership or a public result",
        "condition": "the result can stand in public",
        "opening_action": "Choose the result worth bringing into view.",
        "destination_action": "Make the strongest supported result visible and measurable.",
        "risk": "Chase recognition before the work and private capacity can support it.",
    },
    11: {
        "axis": "Friends, audiences & future plans",
        "subject": "The future",
        "short": "audiences and future plans",
        "source": "friends, audiences, alliances or a future plan",
        "condition": "the right people can help it grow",
        "opening_action": "Identify the alliance, audience or future plan with real momentum.",
        "destination_action": "Build with the people who add reach, clarity and mutual value.",
        "risk": "Confuse a large audience with genuine support.",
    },
    12: {
        "axis": "Rest, closure & private renewal",
        "subject": "The hidden chapter",
        "short": "closure and private renewal",
        "source": "rest, closure, private preparation or an unfinished matter",
        "condition": "what is ending has space to close",
        "opening_action": "Name the unfinished matter that needs space, rest or release.",
        "destination_action": "Close the private chapter before asking the next one to carry it.",
        "risk": "Force visibility while the deeper ending is still incomplete.",
    },
}


SCENARIO_LANGUAGE: dict[str, dict[str, str]] = {
    "identity_direction": {
        "noun": "a personal direction or visible change of role",
        "clarity": "the identity, boundary or direction ready to lead",
        "move": "Choose the direction that matches the person now taking the lead.",
    },
    "creative_development": {
        "noun": "a creative, romantic or entrepreneurial opening",
        "clarity": "the spark with enough response and substance to develop",
        "move": "Give the strongest spark one clear next stage.",
    },
    "routine_wellbeing": {
        "noun": "a workload, routine or wellbeing adjustment",
        "clarity": "the rhythm, workload and available energy",
        "move": "Create the rhythm that makes the promising result easier to continue.",
    },
    "shared_trust": {
        "noun": "a question of trust, intimacy or shared responsibility",
        "clarity": "the shared responsibility, boundary and level of trust",
        "move": "Make the shared stake and boundary clear before moving deeper.",
    },
    "community_future": {
        "noun": "a friend, audience, alliance or future plan",
        "clarity": "the people and plans adding real momentum",
        "move": "Build with the alliance or audience that adds mutual value.",
    },
    "private_closure": {
        "noun": "a private ending, rest period or unfinished matter",
        "clarity": "the unfinished matter, recovery need or private ending",
        "move": "Give the unfinished matter a clean ending or a protected period of rest.",
    },
    "financial_shock": {
        "noun": "a cost, amount or financial surprise",
        "clarity": "the real amount and its effect on the choice",
        "move": "Put the real number beside the decision before reacting.",
    },
    "external_money": {
        "noun": "promised, shared or institutional money",
        "clarity": "the timing, access and ownership of the resource",
        "move": "Confirm timing, ownership and access before building around the money.",
    },
    "funding_application": {
        "noun": "a loan, funding request or formal financial process",
        "clarity": "the terms, documents and level of support available",
        "move": "Make the funding conditions visible before expanding the plan.",
    },
    "paperwork_verification": {
        "noun": "paperwork, verification or revised terms",
        "clarity": "the fact, document or correction that changes the answer",
        "move": "Correct the detail that is holding the decision in place.",
    },
    "publishing_media": {
        "noun": "a writing, publishing or audience opportunity",
        "clarity": "the audience, format and next visible result",
        "move": "Give the idea a finished form and a real audience.",
    },
    "visa_legal_study": {
        "noun": "a legal, study, visa or official process",
        "clarity": "the requirement, approval or qualification that changes the path",
        "move": "Complete the requirement that makes the wider path usable.",
    },
    "travel": {
        "noun": "a trip, international contact or wider-world opening",
        "clarity": "the timing, distance and reason for making the move",
        "move": "Turn the wider possibility into a dated, workable plan.",
    },
    "career_interview": {
        "noun": "an interview, offer or visible professional result",
        "clarity": "the role, result and responsibility attached to the opportunity",
        "move": "Define the visible result before accepting the pressure around it.",
    },
    "relationship_opening": {
        "noun": "an attraction, introduction or relationship opening",
        "clarity": "mutual effort and a believable next step",
        "move": "Watch whether warmth becomes a believable next step.",
    },
    "property_home": {
        "noun": "a home, property or family decision",
        "clarity": "the location, responsibility and emotional fit of the choice",
        "move": "Choose the option that improves the private foundation, not only the appearance.",
    },
    "contracts_agreements": {
        "noun": "a contract, agreement or negotiated commitment",
        "clarity": "the expectations, ownership and terms both sides can support",
        "move": "Put the agreement into language that leaves no hidden job for either side.",
    },
}


SCENARIO_HEADLINE_SUBJECT: dict[str, str] = {
    "identity_direction": "A new direction",
    "creative_development": "The spark",
    "routine_wellbeing": "The plan",
    "shared_trust": "The shared stake",
    "community_future": "The future plan",
    "private_closure": "The hidden chapter",
    "financial_shock": "The real cost",
    "external_money": "The promised resource",
    "funding_application": "The application",
    "paperwork_verification": "The decision",
    "publishing_media": "The idea",
    "visa_legal_study": "The wider process",
    "travel": "The wider path",
    "career_interview": "The visible opportunity",
    "relationship_opening": "The attraction",
    "property_home": "The private foundation",
    "contracts_agreements": "The agreement",
}


HEADLINE_PATTERN: dict[tuple[str, str], str] = {
    ("fire", "cardinal"): "{subject} becomes real when {condition}",
    ("fire", "fixed"): "{subject} keeps its fire when {condition}",
    ("fire", "mutable"): "{subject} moves into view when {condition}",
    ("earth", "cardinal"): "{subject} gains ground when {condition}",
    ("earth", "fixed"): "{subject} holds its value when {condition}",
    ("earth", "mutable"): "{subject} becomes workable when {condition}",
    ("air", "cardinal"): "{subject} finds balance when {condition}",
    ("air", "fixed"): "{subject} changes the future when {condition}",
    ("air", "mutable"): "{subject} becomes clear when {condition}",
    ("water", "cardinal"): "{subject} feels safe enough to grow when {condition}",
    ("water", "fixed"): "{subject} deepens when {condition}",
    ("water", "mutable"): "{subject} finds a new shape when {condition}",
}


def _house(value: int) -> dict[str, str]:
    return HOUSE_LANGUAGE.get(int(value), HOUSE_LANGUAGE[1])


def _scenario(key: str, label: str, fallback_house: int) -> dict[str, str]:
    if key in SCENARIO_LANGUAGE:
        return SCENARIO_LANGUAGE[key]
    noun = label.strip().lower() if label else _house(fallback_house)["source"]
    return {
        "noun": noun,
        "clarity": f"what {noun} changes about the decision",
        "move": f"Give {noun} one clear next step.",
    }


def _relationship_language(sign: str) -> tuple[str, str, str, str]:
    meta = SIGN_META.get(sign, {"element": "air", "modality": "mutable"})
    element = meta["element"]
    modality = meta["modality"]

    questions = {
        ("fire", "cardinal"): "Does the excitement keep moving when both people need to act?",
        ("fire", "fixed"): "Does admiration stay warm once attention is no longer the only fuel?",
        ("fire", "mutable"): "Can freedom and shared direction keep moving together?",
        ("earth", "cardinal"): "Does steadiness support growth, or turn into another duty?",
        ("earth", "fixed"): "Does the connection create safety without making life smaller?",
        ("earth", "mutable"): "Is care visible in the small, reliable details?",
        ("air", "cardinal"): "Is reciprocity real, or is one person carrying the conversation?",
        ("air", "fixed"): "Is there enough space for individuality and enough effort for closeness?",
        ("air", "mutable"): "Does the conversation continue when novelty fades?",
        ("water", "cardinal"): "Does closeness feel emotionally safe and mutually protective?",
        ("water", "fixed"): "Does intimacy deepen trust—or increase uncertainty?",
        ("water", "mutable"): "Is tenderness becoming mutual, or remaining imagined?",
    }
    modality_suffix = {
        "cardinal": "Initiative matters, but mutual movement matters more.",
        "fixed": "Consistency matters, but so does enough space for both people to stay themselves.",
        "mutable": "Flexibility helps, but clarity shows whether the connection has a real direction.",
    }
    active = {
        "fire": "When attraction rises, notice whether direct interest becomes steady presence once plans become practical.",
        "earth": "When attraction rises, notice whether care becomes reliable without turning the connection into another duty.",
        "air": "When attraction rises, notice whether lively contact becomes honest, sustained communication.",
        "water": "When attraction rises, notice whether tenderness becomes mutual, safe and easier to trust.",
    }[element]
    quiet = {
        "cardinal": "When romance is quiet, begin the creative or social move that restores momentum without waiting for permission.",
        "fixed": "When romance is quiet, return to the pleasure, friendship or creative work that restores warmth and self-possession.",
        "mutable": "When romance is quiet, follow the conversation, idea or creative opening that brings fresh movement and perspective.",
    }[modality]
    return questions[(element, modality)], modality_suffix[modality], active, quiet


def _work_language(primary_house: int, secondary_house: int) -> tuple[str, str, str]:
    pair = {primary_house, secondary_house}
    if pair & {10, 11}:
        return (
            "Visibility grows when the strongest result becomes clear",
            "Bring one supported result into view, then let response and evidence refine the next stage.",
            "Finish the visible result before multiplying the audience or direction.",
        )
    if pair & {3, 9}:
        return (
            "The idea needs a message, route and destination",
            "A conversation, application, course, publication or wider contact can move the work forward once its purpose is clear.",
            "Turn the idea into one message, application or finished piece that can travel.",
        )
    if pair & {5, 6}:
        return (
            "Creative momentum needs a rhythm that can last",
            "A fast, attractive idea gains value when the working week gives it enough structure to develop.",
            "Create a repeatable rhythm before opening another direction.",
        )
    if pair & {4, 12}:
        return (
            "Private preparation protects the visible result",
            "Work progresses through a quieter foundation, better boundaries and fewer unfinished demands competing for attention.",
            "Close or organise the private task that is draining the public plan.",
        )
    return (
        "The result grows through clear ownership and follow-through",
        "Professional progress becomes easier to trust when the result, responsibility and next step are visible.",
        "Finish one supported move before expanding the plan.",
    )


def _money_language(primary_house: int, secondary_house: int) -> tuple[str, str, str]:
    pair = {primary_house, secondary_house}
    if pair & {2, 8}:
        return (
            "The numbers reveal what the opportunity can really support",
            "Money, shared resources or obligations need clear ownership, timing and limits before the larger choice can settle.",
            "Choose from visible numbers and enough room to live—not pressure or fantasy.",
        )
    if pair & {6, 10}:
        return (
            "The real price includes time, energy and capacity",
            "An opportunity can be financially sound and still cost too much of the week. Compare income with workload and recovery.",
            "Value the offer by what remains after the work is carried.",
        )
    if pair & {4, 5}:
        return (
            "Comfort and pleasure both need a deliberate budget",
            "Spending may support home, creativity or enjoyment, but the strongest choice keeps the foundation steady as well.",
            "Fund what adds warmth without weakening the base.",
        )
    return (
        "Clarity protects the pleasure of saying yes",
        "The useful question is not only what something costs, but what it asks from time, attention and future flexibility.",
        "Choose the option whose full cost still feels worthwhile.",
    )


def _profile_context(context: StoryContext | Mapping[str, object] | None) -> StoryContext:
    if isinstance(context, StoryContext):
        return context
    if isinstance(context, Mapping):
        values = dict(context)
        for key in ("opening_evidence", "complication_evidence", "relationship_evidence", "climax_evidence"):
            values[key] = tuple(values.get(key, ()) or ())
        allowed = {field.name for field in StoryContext.__dataclass_fields__.values()}
        return StoryContext(**{key: value for key, value in values.items() if key in allowed})
    return StoryContext()


def story_profile_for(
    sign: str,
    primary_house: int,
    secondary_house: int,
    context: StoryContext | Mapping[str, object] | None = None,
) -> MonthlyStoryProfile | None:
    if primary_house not in HOUSE_LANGUAGE or secondary_house not in HOUSE_LANGUAGE:
        return None

    source = _house(primary_house)
    destination = _house(secondary_house)
    ctx = _profile_context(context)
    opening_role_house = _house(ctx.opening_house or primary_house)
    complication_role_house = _house(ctx.complication_house or primary_house)
    climax_role_house = _house(ctx.climax_house or secondary_house)
    opening_scenario = _scenario(ctx.opening_scenario_key, ctx.opening_scenario_label, ctx.opening_house or primary_house)
    complication_scenario = _scenario(ctx.complication_scenario_key, ctx.complication_scenario_label, ctx.complication_house or primary_house)
    climax_scenario = _scenario(ctx.climax_scenario_key, ctx.climax_scenario_label, ctx.climax_house or secondary_house)
    relationship_question, relationship_support, romance_active, romance_quiet = _relationship_language(sign)
    work_hook, work_copy, work_move = _work_language(primary_house, secondary_house)
    money_hook, money_copy, money_move = _money_language(primary_house, secondary_house)

    fallback_key = {
        1: "identity_direction", 2: "financial_shock", 3: "paperwork_verification",
        4: "property_home", 5: "creative_development", 6: "routine_wellbeing",
        7: "contracts_agreements", 8: "shared_trust", 9: "travel",
        10: "career_interview", 11: "community_future", 12: "private_closure",
    }.get(primary_house, "")
    headline_subject = source["subject"]
    if ctx.opening_scenario_key and ctx.opening_scenario_key != fallback_key:
        headline_subject = SCENARIO_HEADLINE_SUBJECT.get(ctx.opening_scenario_key, headline_subject)
    meta = SIGN_META.get(sign, {"element": "air", "modality": "mutable"})
    headline = HEADLINE_PATTERN[(meta["element"], meta["modality"])].format(
        subject=headline_subject,
        condition=destination["condition"],
    )
    theme_axis = f"{source['axis']} x {destination['axis']}"
    central_storyline = (
        f"The first signal arrives through {opening_scenario['noun']} and touches {opening_role_house['short']}. "
        f"The month’s larger movement runs from {source['short']} toward {destination['short']}, "
        f"revealing which version can keep growing."
    )

    act_hooks = (
        f"Shaping {opening_role_house['short']} into momentum",
        f"Bringing {complication_role_house['short']} into focus",
        "Watching whether the connection keeps moving",
        f"Giving {climax_role_house['short']} a lasting form",
    )
    act_titles = (
        f"{opening_scenario['noun'].capitalize()} begins to move",
        f"{complication_scenario['noun'].capitalize()} reveals the important condition",
        "Warmth becomes meaningful through continuity",
        f"{climax_scenario['noun'].capitalize()} changes what can remain",
    )

    opening_copy = (
        f"{opening_scenario['noun'].capitalize()} gathers momentum through {opening_role_house['short']}"
    )
    complication_copy = (
        f"The middle of the month brings {complication_scenario['clarity']} into {complication_role_house['short']}"
    )
    climax_copy = (
        f"Late in the month, {climax_scenario['noun']} moves through {climax_role_house['short']} and gives the result a clearer form"
    )
    resolution_copy = (
        f"What remains should strengthen {destination['short']} without abandoning what first made the opening feel alive."
    )

    action_candidates = (
        opening_scenario["move"],
        complication_scenario["move"],
        climax_scenario["move"],
        source["opening_action"],
        destination["destination_action"],
    )
    action_items: list[str] = []
    for item in action_candidates:
        if item and item not in action_items:
            action_items.append(item)
        if len(action_items) == 3:
            break
    while len(action_items) < 3:
        action_items.append(destination["destination_action"])
    action_plan = tuple(action_items[:3])

    love_hook = {
        "fire": "The spark matters. Continuity gives it a future",
        "earth": "Care feels convincing when steadiness leaves room for desire",
        "air": "Conversation opens the door. Consistency keeps it open",
        "water": "Tenderness becomes real when it is mutual and safe",
    }[SIGN_META.get(sign, {"element": "air"})["element"]]

    overview_copy = (
        f"The opening grows through {opening_role_house['short']}; the middle reveals {complication_scenario['clarity']}.",
        f"The closing stretch moves through {climax_role_house['short']} and favours the version that gives {destination['short']} a clear, workable form.",
    )

    return MonthlyStoryProfile(
        expected_pair=(primary_house, secondary_house),
        headline=headline,
        theme_axis=theme_axis,
        central_storyline=central_storyline,
        act_hooks=act_hooks,
        act_titles=act_titles,
        opening_copy=opening_copy,
        complication_copy=complication_copy,
        relationship_question=relationship_question,
        relationship_support=relationship_support,
        climax_copy=climax_copy,
        resolution_copy=resolution_copy,
        do_line=f"{source['opening_action']} {destination['destination_action']}",
        dont_line=source["risk"],
        action_plan=action_plan,
        romance_active=romance_active,
        romance_quiet=romance_quiet,
        love_hook=love_hook,
        work_hook=work_hook,
        money_hook=money_hook,
        overview_copy=overview_copy,
        strategy_hidden=(
            f"A promising opening gains strength when {destination['condition']}."
        ),
        strategy_watch=source["risk"],
        love_move=relationship_support,
        work_copy=work_copy,
        work_move=work_move,
        money_copy=money_copy,
        money_move=money_move,
    )


def profile_from_dict(payload: Mapping[str, object] | None) -> MonthlyStoryProfile | None:
    if not payload:
        return None
    values = dict(payload)
    values["expected_pair"] = tuple(int(item) for item in (values.get("expected_pair") or ()))
    for key in ("act_hooks", "act_titles", "action_plan", "overview_copy"):
        values[key] = tuple(str(item) for item in (values.get(key) or ()))
    allowed = {field.name for field in MonthlyStoryProfile.__dataclass_fields__.values()}
    try:
        return MonthlyStoryProfile(**{key: value for key, value in values.items() if key in allowed})
    except (TypeError, ValueError):
        return None


# Compatibility view for older tests and editorial tools. These profiles are
# generated by the universal formula; they are not the production decision
# engine and contain no hand-written sign/month narratives.
_AUGUST_PAIR = {
    "Aries": (5, 6), "Taurus": (4, 5), "Gemini": (3, 4), "Cancer": (2, 3),
    "Leo": (1, 2), "Virgo": (12, 1), "Libra": (11, 12), "Scorpio": (10, 11),
    "Sagittarius": (9, 10), "Capricorn": (8, 9), "Aquarius": (7, 8), "Pisces": (6, 7),
}
PROFILES: dict[str, MonthlyStoryProfile] = {
    sign: story_profile_for(sign, pair[0], pair[1])
    for sign, pair in _AUGUST_PAIR.items()
}
