from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Sequence


# Luna's own semantic repertoire.  This module deliberately stores concepts,
# situations and rhetorical moves rather than copied passages from published
# astrology reports or fiction.

TARGET_CORE = {
    "Sun": "identity, direction and the standard you answer to",
    "Moon": "home, belonging, care and emotional security",
    "Mercury": "decisions, conversations, paperwork and agreements",
    "Venus": "relationships, money, value, attraction and reciprocity",
    "Mars": "effort, conflict, initiative and how hard you push",
    "Jupiter": "growth, confidence, opportunity and the size of the bet",
    "Saturn": "commitment, responsibility, limits and what must endure",
    "Uranus": "freedom, independence, reinvention and room to move",
    "Neptune": "hope, imagination, uncertainty and what you want to believe",
    "Pluto": "power, trust, dependency, control and irreversible change",
    "Ascendant": "identity, presentation, autonomy and personal direction",
    "Midheaven": "career, reputation, authority and public responsibility",
    "True Node": "developmental direction, unfamiliar choices and the route ahead",
}

TARGET_QUESTION = {
    "Sun": "Which version of you still deserves authority?",
    "Moon": "What actually makes life feel secure rather than merely familiar?",
    "Mercury": "What needs to be said, decided or put into writing?",
    "Venus": "Is this worth what it now requires?",
    "Mars": "What deserves your effort, and where is effort becoming waste?",
    "Jupiter": "Which opening deserves to become larger?",
    "Saturn": "What responsibility is genuinely yours to carry?",
    "Uranus": "Where has freedom become more important than continuity?",
    "Neptune": "What remains true after hope, fear and projection are removed?",
    "Pluto": "Where has influence quietly become control?",
    "Ascendant": "What changes when you stop presenting the old version of yourself?",
    "Midheaven": "What does the next level of authority actually cost?",
    "True Node": "Which future becomes more available when you stop defending the old route?",
}

TARGET_SIGNS = {
    "Sun": (
        "a role that once fitted can begin to feel narrower than the person inside it",
        "recognition can arrive at the same time as a harder question about direction",
        "an old identity may still work socially after it stops working privately",
    ),
    "Moon": (
        "a living arrangement, family role or pattern of care can become harder to keep on autopilot",
        "security can start asking for a different shape rather than simply more protection",
        "the emotional cost of keeping the peace may become easier to notice",
    ),
    "Mercury": (
        "a decision that survived on goodwill may now need dates, numbers or a clear no",
        "a conversation can stop being theoretical once another person needs an answer",
        "paperwork, study, sales, travel or a contract can expose the condition hidden inside the plan",
    ),
    "Venus": (
        "a relationship or financial arrangement can need clearer reciprocity",
        "attraction may remain while the practical terms become harder to ignore",
        "something desirable can reveal a price that was not obvious at the beginning",
    ),
    "Mars": (
        "effort can become useful only when it is attached to a limit and a purpose",
        "a conflict may reveal where you are spending force without gaining position",
        "a deadline, workload or competition can show whether your current pace is sustainable",
    ),
    "Jupiter": (
        "an opening can become valuable precisely because it enlarges the field of choice",
        "more attention, travel, learning or responsibility can arrive together",
        "confidence can make a larger move possible, but it can also hide the cost of scale",
    ),
    "Saturn": (
        "a responsibility can become clearer once the informal version stops working",
        "an old structure may prove durable, or simply expensive to keep",
        "a boundary can become useful when it prevents duty from becoming indefinite",
    ),
    "Uranus": (
        "a system can still function while giving you too little room to move",
        "the first sign of change may be impatience with a rule you used to tolerate",
        "an unexpected option can reveal that the old choice was never as fixed as it looked",
    ),
    "Neptune": (
        "a compelling story can become less convincing once details are requested",
        "intuition may be useful, but it needs evidence before it becomes a decision",
        "an ideal can survive reality, or dissolve when reality finally gets a vote",
    ),
    "Pluto": (
        "a dependency or power arrangement can become too visible to call neutral",
        "a situation may look unchanged while the leverage inside it has already moved",
        "the useful question can shift from how to restore the old order to what the new order requires",
    ),
    "Ascendant": (
        "other people may respond differently once you stop signalling the old role",
        "a change in appearance, pace or personal direction can alter the reactions around you",
        "the practical test is whether the life around you still fits the person you are becoming",
    ),
    "Midheaven": (
        "a role, promotion, client or public responsibility can become more serious than its title suggests",
        "visibility can increase before the support system is ready for it",
        "authority may arrive with conditions that matter more than status",
    ),
    "True Node": (
        "an unfamiliar direction can become more relevant because the old route no longer answers the same question",
        "a new person, place or obligation can pull attention toward a future you had not planned in detail",
        "the signal is often developmental rather than comfortable: the choice asks for capacity you are still building",
    ),
}

HOUSE_SCENARIOS = {
    1: (
        "a haircut, profile, boundary or role changes how other people respond to you",
        "you stop presenting the version of yourself that keeps earning the same old expectations",
    ),
    2: (
        "a pay rate, quote, purchase or recurring bill forces the real value question into numbers",
        "you decide whether the thing you want is still worth it once the ongoing cost is visible",
    ),
    3: (
        "an email, contract, application or short trip turns a vague possibility into a practical decision",
        "a phone call or document exposes the sentence that still needs a clear yes or no",
    ),
    4: (
        "a lease, repair, family responsibility or living arrangement makes the private cost visible",
        "someone needs space, care or a key and the home arrangement has to become explicit",
    ),
    5: (
        "a date, child, hobby or creative project starts asking for real time instead of spare time",
        "a promising connection has to survive an ordinary Tuesday before you call it durable",
    ),
    6: (
        "a roster, commute, appointment or recurring task shows whether the plan survives the ordinary week",
        "your body or workload objects to a schedule that looked manageable on paper",
    ),
    7: (
        "a partner, client or collaborator asks for more access, time or scope and the terms have to become mutual",
        "a date, contract or alliance becomes clearer when the other person has to carry an inconvenient part",
    ),
    8: (
        "a tax bill, loan, shared cost or joint account needs a number and an owner",
        "trust becomes measurable when money, access or responsibility has to be shared",
    ),
    9: (
        "a trip needs booking, leave approval and a budget",
        "a course, visa, legal process or overseas opportunity needs paperwork before the romantic version can happen",
    ),
    10: (
        "a manager adds responsibility before discussing title, pay or support",
        "an interview, promotion or public role becomes real once the hours, reporting line and result belong to you",
    ),
    11: (
        "a friend, group or audience turns enthusiasm into a date, task or next step",
        "a wedding, group trip or shared plan reveals who actually reorganises life to make it happen",
    ),
    12: (
        "an unfinished conversation, old obligation or private burden keeps taking up space after its useful life is over",
        "you cancel one thing, turn off the phone or close an old loop and discover the world continues",
    ),
}

TRANSIT_FRAME = {
    "Jupiter": {
        "opening": "Jupiter increases room, reach or confidence",
        "gift": "The opening is real when it creates usable capacity rather than simply more activity.",
        "shadow": "The trap is treating possibility as proof that every expansion is wise.",
        "game": "HOW MUCH MORE CAN ACTUALLY WORK?",
        "game_question": "Which opening deserves scale, and which one merely creates more to carry?",
    },
    "Saturn": {
        "opening": "Saturn makes cost, duty and consequence harder to keep implicit",
        "gift": "Pressure can be useful when it turns a vague arrangement into something measurable.",
        "shadow": "The trap is confusing endurance with proof that the arrangement still deserves to continue.",
        "game": "WHAT DESERVES A COMMITMENT?",
        "game_question": "What is worth formalising, and what has survived mainly because nobody ended it?",
    },
    "Uranus": {
        "opening": "Uranus exposes where freedom and flexibility have become non-negotiable",
        "gift": "Disruption can reveal an option that the old structure kept invisible.",
        "shadow": "The trap is destroying something useful simply to prove that you can escape it.",
        "game": "WHAT NEEDS MORE ROOM?",
        "game_question": "What must change so freedom does not require chaos?",
    },
    "Neptune": {
        "opening": "Neptune weakens false certainty and enlarges imagination",
        "gift": "Ambiguity can create insight when it slows a premature conclusion.",
        "shadow": "The trap is allowing hope, chemistry, fear or projection to do the work of evidence.",
        "game": "WHAT STORY SURVIVES THE FACTS?",
        "game_question": "What remains convincing after the details are checked?",
    },
    "Pluto": {
        "opening": "Pluto reveals where leverage, dependency or control has already shifted",
        "gift": "Seeing the real power structure makes a cleaner decision possible.",
        "shadow": "The trap is gripping the old arrangement harder after its leverage has already moved.",
        "game": "WHO OR WHAT HOLDS THE LEVER?",
        "game_question": "Where does power actually sit now, rather than where it used to sit?",
    },
}

TRANSIT_OPENINGS = {
    "Jupiter": (
        "You have more room than before",
        "A larger option is becoming visible",
        "Confidence is rising; use it on something that creates future choice",
        "More is available, but more is not automatically better",
    ),
    "Saturn": (
        "What you have carried informally now needs terms",
        "Responsibility is getting heavier; make the cost explicit",
        "Stop treating the obligation as background noise",
        "The structure now has to prove it can carry its own weight",
    ),
    "Uranus": (
        "What felt fixed is becoming negotiable",
        "You can see where the arrangement has too little room",
        "The cost of staying unchanged is getting harder to ignore",
        "A different route is becoming possible",
    ),
    "Neptune": (
        "The story is getting louder while the evidence gets thinner",
        "Do not confuse a compelling feeling with proof",
        "Imagination is useful here; certainty is not",
        "Slow the interpretation down before you make the irreversible move",
    ),
    "Pluto": (
        "The real power structure is becoming harder to ignore",
        "Leverage has shifted; stop negotiating with the old balance",
        "Neutrality is becoming less believable",
        "Look at who can actually decide, withhold or redirect the outcome",
    ),
}

PAIR_INSIGHT = {
    ("Saturn", "Sun"): "The standard you answer to is becoming harder to outsource. A role can remain respectable after it stops being a direction.",
    ("Saturn", "Moon"): "Care has a cost. The issue is not whether you can carry it, but whether the current arrangement is the only way to care.",
    ("Saturn", "Mercury"): "A decision that once survived on goodwill may now need a date, a number, a signature or a clear no.",
    ("Saturn", "Venus"): "The question is not simply whether you still want it. It is whether you want what comes with it.",
    ("Saturn", "Mars"): "Effort becomes leverage only after you decide what is worth the strain and where the effort stops.",
    ("Saturn", "Midheaven"): "Recognition and responsibility are travelling together. The title matters less than the load attached to it.",
    ("Uranus", "Sun"): "A role can still function after it stops feeling like yours. The tension is between continuity and aliveness.",
    ("Uranus", "Moon"): "A living arrangement can be safe and still leave too little air. Security may need a redesign, not a demolition.",
    ("Uranus", "Mercury"): "A new fact, message or idea can make the old explanation impossible to defend with the same confidence.",
    ("Uranus", "Venus"): "Attraction and attachment do not always change at the same speed. New freedom can clarify what was preference and what was dependence.",
    ("Uranus", "Midheaven"): "The career question may not be whether you can continue. It may be whether continuing still buys the future you want.",
    ("Uranus", "True Node"): "A future route can appear suddenly enough to feel disruptive. The point is not novelty itself, but whether the new route creates more authentic room to develop.",
    ("Jupiter", "Sun"): "Confidence is useful here, but the real opportunity is enlarging your field without making size the measure of success.",
    ("Jupiter", "Mercury"): "A message, idea or agreement can travel further than usual. The advantage belongs to the version that survives practical questions.",
    ("Jupiter", "Venus"): "More affection, money, pleasure or social opportunity can arrive; the useful test is whether more also means better.",
    ("Jupiter", "Mars"): "Momentum has backing. The risk is spending tomorrow's capacity because today's road feels unusually open.",
    ("Jupiter", "Midheaven"): "A larger public opening can be real without being free. Growth becomes valuable when the support underneath it can carry the visibility.",
    ("Neptune", "Sun"): "Identity can feel less fixed for a while. That can be creative, provided uncertainty is not mistaken for a command to abandon everything.",
    ("Neptune", "Mercury"): "The first interpretation may be emotionally persuasive and still be wrong. Ask what would change your mind.",
    ("Neptune", "Venus"): "Chemistry can be information without being evidence of compatibility, reciprocity or future behaviour.",
    ("Neptune", "Mars"): "Motivation is harder to read when desire, fatigue and projection are mixed together. Delay the irreversible move until motive clears.",
    ("Neptune", "Midheaven"): "A public story can look attractive before the role itself is defined. Ask what the work actually requires once the image is removed.",
    ("Pluto", "Sun"): "A change in power can force a more exact answer to who you are when approval, status or an old role no longer carries the same weight.",
    ("Pluto", "Mercury"): "Words have leverage now. The useful distinction is between naming the truth and using information to control the room.",
    ("Pluto", "Venus"): "Attachment becomes revealing when value, money, trust or desire gives one side more leverage than the other.",
    ("Pluto", "Mars"): "Force can meet force. The strategic question is whether winning the immediate contest improves your actual position.",
    ("Pluto", "Midheaven"): "Authority may be moving before the organisation admits it. Watch who can actually decide, withhold or redirect resources.",
    ("Pluto", "True Node"): "The route ahead becomes clearer when an old dependency or power arrangement stops choosing on your behalf.",
}

MOVE_BY_TRANSIT = {
    "Jupiter": {
        "Sun": "Choose the expansion that gives you more range without making applause the objective.",
        "Moon": "Create more room without spending the security you will need afterward.",
        "Mercury": "Send the proposal, ask the larger question, then test the details before committing.",
        "Venus": "Enjoy the opening, but separate genuine value from the excitement of having more options.",
        "Mars": "Use the tailwind on one concrete objective instead of multiplying the workload.",
        "Midheaven": "Take the larger opening only after you know what support, time and responsibility come with it.",
        "default": "Expand the option that increases future choice, not merely present activity.",
    },
    "Saturn": {
        "Sun": "Name the standard you are willing to live by, then remove the duties that exist only to preserve an old role.",
        "Moon": "Define what care requires and where care turns into indefinite carrying.",
        "Mercury": "Put the decision into dates, numbers, responsibilities or a clear no.",
        "Venus": "Define what is mutual, what it costs and what happens if the terms stay unequal.",
        "Mars": "Set the workload, deadline and stopping point before effort becomes its own justification.",
        "Midheaven": "Price the authority: decide what responsibility the role deserves before accepting the status around it.",
        "default": "Turn the vague obligation into explicit terms, then decide whether those terms are worth carrying.",
    },
    "Uranus": {
        "Sun": "Change the part of the identity that has become costume before changing everything around it.",
        "Moon": "Redesign the living or care arrangement so safety and breathing room can coexist.",
        "Mercury": "Test the new explanation quickly; keep what survives contact with facts.",
        "Venus": "Give the relationship or money arrangement enough space to show what is preference and what is dependency.",
        "Mars": "Break the pattern with a controlled experiment, not an irreversible reaction.",
        "Midheaven": "Prototype the next career shape before burning the bridge to the current one.",
        "default": "Create a reversible experiment that increases freedom before making the irreversible break.",
    },
    "Neptune": {
        "Sun": "Let identity stay unfinished for a moment, but keep practical commitments tied to verifiable facts.",
        "Moon": "Treat strong feeling as information, then check whether the environment actually supports the feeling.",
        "Mercury": "Write down what you know, what you assume and what would change your conclusion.",
        "Venus": "Separate chemistry from reciprocity and promises from observed behaviour.",
        "Mars": "Delay the irreversible action until motive, energy and evidence point in the same direction.",
        "Midheaven": "Ask for the actual duties, money, authority and timetable before buying the public story.",
        "default": "Slow the interpretation down and force the story to survive a factual check.",
    },
    "Pluto": {
        "Sun": "Stop negotiating with an identity that depends on a power arrangement already changing underneath it.",
        "Moon": "Protect what is genuinely vulnerable without using protection to freeze the old family or home dynamic.",
        "Mercury": "Use information to clarify the decision, not to dominate the conversation.",
        "Venus": "Name the leverage inside the attachment before deciding what is still mutual.",
        "Mars": "Choose the contest that improves your position; refuse the one that only proves you can fight.",
        "Midheaven": "Map who can actually decide, reward, block or redirect the work before making the public move.",
        "default": "Act from the power structure that exists now, not the one you wish still existed.",
    },
}

WATCH_BY_TRANSIT = {
    "Jupiter": {
        "Sun": "Mistaking confidence for evidence that every direction is equally good.",
        "Moon": "Expanding faster than the private base can support.",
        "Mercury": "Promising more than the details can carry.",
        "Venus": "Treating abundance of options as proof of value.",
        "Mars": "Turning a tailwind into overcommitment.",
        "Midheaven": "Taking visibility without pricing the workload behind it.",
        "default": "More can quietly become too much.",
    },
    "Saturn": {
        "Sun": "Keeping a role because it still earns approval.",
        "Moon": "Calling exhaustion loyalty or care.",
        "Mercury": "Letting an undecided issue consume time because nobody wants to state the terms.",
        "Venus": "Keeping an arrangement because history makes the exit feel expensive.",
        "Mars": "Using effort to avoid deciding whether the objective still matters.",
        "Midheaven": "Accepting authority whose obligations exceed its real power or reward.",
        "default": "Endurance is not automatic proof that the structure deserves to continue.",
    },
    "Uranus": {
        "Sun": "Changing everything when one role is the real problem.",
        "Moon": "Confusing disruption with freedom.",
        "Mercury": "Replacing one rigid explanation with another fashionable one.",
        "Venus": "Using novelty to avoid an honest conversation about attachment.",
        "Mars": "Making the irreversible move in the first burst of impatience.",
        "Midheaven": "Burning a career bridge before the alternative has structural support.",
        "default": "Burning the bridge just to prove you are free.",
    },
    "Neptune": {
        "Sun": "Letting uncertainty become evidence that nothing is real or worth choosing.",
        "Moon": "Letting mood write the whole story.",
        "Mercury": "Treating a compelling explanation as a verified one.",
        "Venus": "Treating chemistry as evidence of reciprocity.",
        "Mars": "Acting before motive is clear.",
        "Midheaven": "Buying the image of the role before reading the job itself.",
        "default": "Hope, fear or intensity can impersonate evidence.",
    },
    "Pluto": {
        "Sun": "Trying to keep control by performing the old identity harder.",
        "Moon": "Protecting the old arrangement after the needs inside it have changed.",
        "Mercury": "Using information as a weapon when clarity would work better.",
        "Venus": "Calling possession, dependency or leverage love.",
        "Mars": "Winning the confrontation while losing the larger position.",
        "Midheaven": "Assuming the formal hierarchy is the same as the real power structure.",
        "default": "Trying to restore control by gripping harder.",
    },
}

ASPECT_LEADS = {
    "square": (
        "The friction matters because postponement starts to cost more.",
        "Two needs are rubbing against each other, and compromise without a decision is losing efficiency.",
        "The obstacle is useful information: it shows exactly where the present arrangement has too little tolerance left.",
    ),
    "opposition": (
        "The pressure is visible through another person, demand or competing priority, so balance can no longer stay theoretical.",
        "What you want and what the other side requires are easier to compare now because the difference is out in the open.",
        "The issue tends to arrive through contrast: another person, deadline or competing need makes the hidden imbalance visible.",
    ),
    "conjunction": (
        "The two themes are concentrated enough that the old default becomes difficult to treat as neutral.",
        "This is a reset point: two parts of the chart are speaking through the same door at once.",
        "The concentration is strong enough that the issue stops behaving like background noise.",
    ),
    "trine": (
        "There is support here, but support becomes useful only when you convert it into a decision or result.",
        "The road is smoother than usual, which makes selection more important than force.",
        "This contact lowers resistance; the opportunity is real, but it can still be wasted through passivity.",
    ),
    "sextile": (
        "An opening is available, though it can pass quietly if you do nothing with it.",
        "A useful option is within reach, provided you make the small move that brings it into play.",
        "The support is conditional rather than automatic: it rewards initiative more than waiting.",
    ),
}

TRANSIT_GIFT_LINES = {
    "Jupiter": (
        "The opening is real when it creates usable capacity rather than simply more activity.",
        "Growth is useful when it widens future choice instead of only enlarging the present workload.",
        "The best version of this transit creates range: more people, knowledge, reach or confidence without losing proportion.",
    ),
    "Saturn": (
        "Pressure can be useful when it turns a vague arrangement into something measurable.",
        "The advantage is clarity: duties, limits and standards become easier to price honestly.",
        "Structure becomes helpful when it tells you what can last and what has only been surviving through tolerance.",
    ),
    "Uranus": (
        "Disruption can reveal an option that the old structure kept invisible.",
        "The useful surprise is the discovery that one fixed assumption was never as fixed as it looked.",
        "Change creates leverage when it gives you a reversible way to test a freer arrangement.",
    ),
    "Neptune": (
        "Ambiguity can create insight when it slows a premature conclusion.",
        "Imagination is useful here when it generates possibilities that can later be tested.",
        "Sensitivity can detect what rigid logic missed, provided the impression is eventually checked against reality.",
    ),
    "Pluto": (
        "Seeing the real power structure makes a cleaner decision possible.",
        "The gain is precision about leverage: who can decide, withhold, redirect or walk away.",
        "Deep change becomes less frightening once the actual dependency is named rather than merely felt.",
    ),
}

TRANSIT_SHADOW_LINES = {
    "Jupiter": (
        "The trap is treating possibility as proof that every expansion is wise.",
        "Optimism can hide the carrying cost of a larger commitment.",
        "More can become noise if scale arrives before selection.",
    ),
    "Saturn": (
        "The trap is confusing endurance with proof that the arrangement still deserves to continue.",
        "Duty becomes expensive when nobody revisits whether the original agreement still makes sense.",
        "A structure can look responsible while quietly consuming more than it returns.",
    ),
    "Uranus": (
        "The trap is destroying something useful simply to prove that you can escape it.",
        "Restlessness can make any change look intelligent before its consequences are priced.",
        "Freedom loses value when the new arrangement has no structure strong enough to hold it.",
    ),
    "Neptune": (
        "The trap is allowing hope, chemistry, fear or projection to do the work of evidence.",
        "A beautiful explanation can become dangerous when it is protected from disconfirming facts.",
        "Uncertainty can invite projection, especially when the desired answer is emotionally convenient.",
    ),
    "Pluto": (
        "The trap is gripping the old arrangement harder after its leverage has already moved.",
        "Control becomes self-defeating when it is used to preserve a balance of power that no longer exists.",
        "Intensity can tempt you to dominate the immediate contest instead of improving the long-term position.",
    ),
}


COUNTERCURRENT = {
    ("Saturn", "Uranus"): "Saturn asks for terms while Uranus refuses terms that remove all room to move.",
    ("Uranus", "Saturn"): "Uranus wants movement, but Saturn makes sure the change has to survive practical reality.",
    ("Jupiter", "Saturn"): "Growth is available, but only what can carry its own weight deserves scale.",
    ("Saturn", "Jupiter"): "Limits are becoming clearer at the same time another part of life is trying to grow.",
    ("Jupiter", "Uranus"): "The opening is larger because the old route is no longer the only route.",
    ("Uranus", "Jupiter"): "Freedom creates options, but Jupiter can turn options into excess if every door is treated as the door.",
    ("Neptune", "Saturn"): "Uncertainty is active, so Saturn's demand for facts, terms and dates becomes unusually valuable.",
    ("Saturn", "Neptune"): "Saturn wants a definition while Neptune keeps exposing what the definition cannot yet prove.",
    ("Pluto", "Saturn"): "Power is shifting while responsibility is becoming explicit; formal rules and real leverage may not be identical.",
    ("Saturn", "Pluto"): "The structure is being tested at the same time the leverage inside it is changing.",
    ("Pluto", "Uranus"): "The urge to break free is strongest where the old power arrangement has already lost legitimacy.",
    ("Uranus", "Pluto"): "Disruption exposes the power structure; what looked like restlessness may actually be a leverage problem.",
}


@dataclass(frozen=True)
class StoryLanguage:
    summary: str
    scenarios: tuple[str, ...]
    insight: str
    question: str
    move: str
    watch: str


@dataclass(frozen=True)
class MajorGame:
    rank: int
    transit_planet: str
    title: str
    summary: str
    question: str
    players: tuple[str, ...]
    countercurrent: str
    first_date: date
    last_date: date


@dataclass(frozen=True)
class RememberDate:
    exact_date: date
    label: str
    reason: str


def _pick(items: Sequence[str], seed: int) -> str:
    if not items:
        return ""
    return items[seed % len(items)]


def _seed(transit_planet: str, target_planet: str, aspect: str, house: int | None) -> int:
    token = f"{transit_planet}|{target_planet}|{aspect}|{house or 0}"
    return sum((index + 1) * ord(char) for index, char in enumerate(token))


def _move(transit_planet: str, target_planet: str, aspect: str) -> str:
    base = MOVE_BY_TRANSIT[transit_planet].get(target_planet, MOVE_BY_TRANSIT[transit_planet]["default"])
    if aspect in {"trine", "sextile"}:
        return base
    if aspect == "conjunction":
        return base
    if aspect == "opposition":
        return base + " Make the competing demand explicit rather than trying to satisfy both invisibly."
    return base + " Remove the part of the plan that depends on endless tolerance."


def _watch(transit_planet: str, target_planet: str, aspect: str) -> str:
    base = WATCH_BY_TRANSIT[transit_planet].get(target_planet, WATCH_BY_TRANSIT[transit_planet]["default"])
    if aspect in {"trine", "sextile"}:
        return base + " Easy conditions can hide weak selection."
    return base


def build_story_language(
    *,
    transit_planet: str,
    target_planet: str,
    aspect: str,
    natal_house: int | None,
) -> StoryLanguage:
    seed = _seed(transit_planet, target_planet, aspect, natal_house)
    frame = TRANSIT_FRAME[transit_planet]
    target = TARGET_CORE.get(target_planet, target_planet.lower())
    pair = PAIR_INSIGHT.get((transit_planet, target_planet))
    if not pair:
        pair = (
            f"{target.capitalize()} is under pressure. "
            "Name what has become harder to ignore. Decide from the fact in front of you, not from the label on the transit."
        )

    lead = _pick(ASPECT_LEADS[aspect], seed + 1)
    if aspect in {"trine", "sextile"}:
        consequence = _pick(TRANSIT_GIFT_LINES[transit_planet], seed + 2)
    elif aspect in {"square", "opposition"}:
        consequence = _pick(TRANSIT_SHADOW_LINES[transit_planet], seed + 2)
    else:
        consequence = (
            _pick(TRANSIT_GIFT_LINES[transit_planet], seed + 2)
            + " "
            + _pick(TRANSIT_SHADOW_LINES[transit_planet], seed + 3)
        )
    summary = f"{pair} {lead} {consequence}"

    target_signs = TARGET_SIGNS.get(target_planet, ())
    scenarios: list[str] = []
    if target_signs:
        scenarios.append(_pick(target_signs, seed))
        if len(target_signs) > 1:
            scenarios.append(_pick(target_signs, seed + 1))
    if natal_house in HOUSE_SCENARIOS:
        scenarios.append(_pick(HOUSE_SCENARIOS[natal_house], seed + 2))
    elif len(target_signs) >= 3:
        scenarios.append(_pick(target_signs, seed + 2))
    else:
        scenarios.append("watch the area of life already asking for the clearest decision; the transit usually becomes recognisable there before it becomes dramatic")

    # Keep exactly three lines and avoid accidental repeats from small banks.
    deduped: list[str] = []
    for item in scenarios:
        item = item.strip()
        if item and item not in deduped:
            deduped.append(item)
    while len(deduped) < 3:
        fallback = frame["gift"] if len(deduped) == 1 else frame["shadow"]
        if fallback not in deduped:
            deduped.append(fallback)
        else:
            deduped.append("The signal is strongest where the practical consequence is already measurable.")

    return StoryLanguage(
        summary=summary,
        scenarios=tuple(deduped[:3]),
        insight=pair,
        question=TARGET_QUESTION.get(target_planet, "What becomes harder to ignore now?"),
        move=_move(transit_planet, target_planet, aspect),
        watch=_watch(transit_planet, target_planet, aspect),
    )


def _story_span(story) -> tuple[date, date]:
    return story.first_date, story.last_date


def _targets_sentence(stories: Sequence) -> str:
    labels = []
    for story in stories:
        label = TARGET_CORE.get(story.natal_target, story.natal_target.lower())
        head = label.split(",")[0].strip()
        if head not in labels:
            labels.append(head)
    if not labels:
        return "several parts of life"
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"


def build_major_games(stories: Sequence, max_games: int = 3) -> tuple[MajorGame, ...]:
    if not stories:
        return ()
    grouped: dict[str, list] = {}
    for story in stories:
        grouped.setdefault(story.transit_planet, []).append(story)

    ranked = sorted(
        grouped.items(),
        key=lambda pair: (-sum(story.score for story in pair[1]), min(story.first_date for story in pair[1])),
    )[:max_games]

    games: list[MajorGame] = []
    for rank, (planet, planet_stories) in enumerate(ranked, start=1):
        planet_stories = sorted(planet_stories, key=lambda story: (story.first_date, -story.score))
        frame = TRANSIT_FRAME[planet]
        first = min(story.first_date for story in planet_stories)
        last = max(story.last_date for story in planet_stories)
        targets = _targets_sentence(planet_stories)
        if len(planet_stories) == 1:
            summary = (
                f"Use the pressure around {targets}. {frame['gift']} "
                "Make the next move concrete."
            )
        else:
            summary = (
                f"Keep one standard while {targets} change around you. {frame['gift']} "
                "Carry the lesson forward. Do not restart the decision at every date."
            )

        other_groups = [item for item in ranked if item[0] != planet]
        counter = ""
        if other_groups:
            other_planet = other_groups[0][0]
            counter = COUNTERCURRENT.get(
                (planet, other_planet),
                f"Keep {other_planet} in view as well. One clean answer does not remove every other obligation.",
            )

        players = tuple(
            f"{story.transit_planet} {story.aspect} {story.natal_target}"
            for story in planet_stories[:5]
        )
        games.append(
            MajorGame(
                rank=rank,
                transit_planet=planet,
                title=frame["game"],
                summary=summary,
                question=frame["game_question"],
                players=players,
                countercurrent=counter,
                first_date=first,
                last_date=last,
            )
        )
    return tuple(games)


def strongest_story(stories: Sequence):
    if not stories:
        return None
    return max(stories, key=lambda story: (story.score, len(story.hits), -story.first_date.toordinal()))


def dates_to_remember(stories: Sequence, limit: int = 3) -> tuple[RememberDate, ...]:
    candidates: list[tuple[float, date, object]] = []
    for story in stories:
        for hit in story.hits:
            score = story.score * (1.08 if hit.retrograde else 1.0)
            candidates.append((score, hit.exact_date, story))
    candidates.sort(key=lambda item: (-item[0], item[1]))

    chosen: list[RememberDate] = []
    used_story_keys: set[tuple[str, str, str]] = set()
    for _, exact_date, story in candidates:
        key = (story.transit_planet, story.natal_target, story.aspect)
        if key in used_story_keys:
            continue
        if any(abs((exact_date - item.exact_date).days) < 10 for item in chosen):
            continue
        chosen.append(
            RememberDate(
                exact_date=exact_date,
                label=story.headline,
                reason=f"{story.transit_planet} {story.aspect} natal {story.natal_target}",
            )
        )
        used_story_keys.add(key)
        if len(chosen) >= limit:
            break
    return tuple(sorted(chosen, key=lambda item: item.exact_date))


def year_closing(stories: Sequence, games: Sequence[MajorGame]) -> str:
    if not stories:
        return "Nothing needs forcing. No single long-range pattern dominates this map at Luna's current threshold."
    dominant = games[0] if games else None
    strongest = strongest_story(stories)
    if dominant is None or strongest is None:
        return "Choose the pressures that deserve attention first. Ignore the rest until the board changes."

    frame = TRANSIT_FRAME[dominant.transit_planet]
    second = games[1] if len(games) > 1 else None
    bridge = ""
    if second is not None:
        bridge = COUNTERCURRENT.get(
            (dominant.transit_planet, second.transit_planet),
            f"{second.transit_planet} is active at the same time, so one answer will not solve every part of the year.",
        )

    return (
        f"Keep returning to this question: {frame['game_question']} "
        f"The strongest single contact is {strongest.transit_planet} {strongest.aspect} natal {strongest.natal_target}. "
        f"{bridge} Choose what still makes sense after both opportunity and cost are visible."
    )

