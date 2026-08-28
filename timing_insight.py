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
        "more invitations, movement, learning or responsibility can arrive at the same time",
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
        "attention can increase before the people, time or resources behind the role are ready for it",
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



_HOUSE_SCENE_FOCUS = {
    1: "how you show up",
    2: "the real number",
    3: "the message or decision",
    4: "home and family",
    5: "the person or project you want",
    6: "the workload and ordinary week",
    7: "the agreement with another person",
    8: "shared money, trust or responsibility",
    9: "the outside plan and its logistics",
    10: "the job or public responsibility",
    11: "the people and next plan",
    12: "what needs rest or closure",
}

_TARGET_HOUSE_SCENE = {
    "Sun": "Use {area} to test whether the role or direction you want still fits.",
    "Moon": "Use {area} to test whether the private life has enough capacity.",
    "Mercury": "Make {area} survive a clear message, date or document.",
    "Venus": "Use {area} to test whether the choice still holds once reciprocity and price become visible.",
    "Mars": "Use {area} to test whether the objective deserves the effort.",
    "Ascendant": "Use {area} to test whether the new version of you actually fits.",
    "Midheaven": "Use {area} to test whether authority and public responsibility have enough support.",
    "Jupiter": "Use {area} to test whether growth creates usable room rather than merely more activity.",
    "Saturn": "Give {area} a clear responsibility, limit and end point.",
    "Uranus": "Use {area} to test whether greater freedom can coexist with useful support.",
    "Neptune": "Make {area} survive the missing-facts check.",
    "Pluto": "Use {area} to test where the real leverage sits now.",
    "True Node": "Use {area} to test whether the next route is actually buildable.",
}


def _target_house_scene(target_planet: str, natal_house: int | None) -> str:
    if natal_house not in _HOUSE_SCENE_FOCUS:
        return ""
    area = _HOUSE_SCENE_FOCUS[natal_house]
    template = _TARGET_HOUSE_SCENE.get(target_planet)
    if not template:
        return ""
    return template.format(area=area)


TRANSIT_HOUSE_SCENARIOS = {
    "Jupiter": {
        1: (
            "a new role, audience or invitation gives you more room to show up differently",
            "confidence grows because more people respond to the version of you you are becoming",
        ),
        2: (
            "a pay rise, extra client, sale or useful purchase increases your options and your spending at the same time",
            "more income or value is available, but the new level works only if the ongoing cost still fits",
        ),
        3: (
            "an application, proposal or message travels further than expected and creates a larger next step",
            "a course, meeting or short trip opens a route that did not exist in the original plan",
        ),
        4: (
            "a move, family change or larger home plan gives you more room and more to maintain",
            "home expands through another person, responsibility or opportunity and the private carrying cost becomes visible",
        ),
        5: (
            "a date, creative project or child-related opportunity becomes large enough to deserve real calendar space",
            "something enjoyable gets more attention and has to prove it can survive ordinary responsibilities",
        ),
        6: (
            "a job, roster or workload expands and shows whether the ordinary week has room for the opportunity",
            "more work or responsibility can be useful if it improves the system instead of simply filling every spare hour",
        ),
        7: (
            "a relationship, client or collaboration offers more reach and immediately asks what each person is promising",
            "another person opens a door, but the value depends on whether effort and responsibility remain mutual",
        ),
        8: (
            "funding, shared money or another person's resources create more room and a larger obligation at the same time",
            "a loan, payout or shared-cost decision expands the field only if ownership and repayment stay explicit",
        ),
        9: (
            "a trip, course, application, publication or overseas opportunity becomes large enough to act on",
            "the wider option is real once the booking, deadline, paperwork and budget can all carry it",
        ),
        10: (
            "a promotion, larger client or public role opens while the workload and support still need pricing",
            "more attention arrives around work and the opportunity improves only if authority grows with responsibility",
        ),
        11: (
            "a friend, network or audience creates a larger route and reveals who can actually help build it",
            "a group opportunity grows once enthusiasm becomes a date, task, introduction or shared responsibility",
        ),
        12: (
            "more private time, recovery or behind-the-scenes support creates room to finish something properly",
            "an opportunity develops quietly before it is ready for public commitment",
        ),
    },
    "Saturn": {
        1: (
            "a role, boundary or personal responsibility stops working as an informal arrangement and needs explicit terms",
            "other people keep expecting the old version of you until your behaviour makes the new limit unmistakable",
        ),
        2: (
            "a budget, rate or recurring cost forces you to decide what is worth maintaining",
            "money gets clearer when every obligation is given a number and an end point",
        ),
        3: (
            "a document, deadline or conversation can no longer survive on goodwill and needs a precise answer",
            "a repeated message problem ends only when somebody owns the date, number or decision",
        ),
        4: (
            "a home, family or care responsibility needs a roster, boundary or longer-term structure",
            "the private arrangement becomes too expensive to keep running on somebody quietly carrying more",
        ),
        5: (
            "a relationship, child-related responsibility or creative project asks whether enjoyment can also carry commitment",
            "something you love needs a real timetable before enthusiasm becomes another duty",
        ),
        6: (
            "a workload, commute or recurring task exposes the limit of a schedule that looked acceptable on paper",
            "the ordinary week forces a choice between a better system and simply working harder",
        ),
        7: (
            "a partner, client or contract needs clearer responsibility, payment or exit terms",
            "a relationship becomes easier to judge once the inconvenient work is divided explicitly",
        ),
        8: (
            "a debt, tax, shared cost or responsibility needs a number, owner and boundary",
            "trust gets tested where one person has been carrying financial or emotional risk without clear terms",
        ),
        9: (
            "a visa, course, legal process or publication needs dates and documents before the larger plan can continue",
            "travel or study becomes real when the administrative burden can no longer be postponed",
        ),
        10: (
            "a title, manager or public responsibility asks for more work and finally needs matching authority or support",
            "recognition matters less once the actual load, reporting line and consequence are visible",
        ),
        11: (
            "a team, friendship or group plan needs fewer vague supporters and more people who own a task",
            "the next plan survives only if somebody besides you carries an inconvenient part",
        ),
        12: (
            "an old obligation, private worry or unfinished ending keeps consuming energy until it is closed properly",
            "rest becomes a responsibility when exhaustion has been treated as proof of loyalty",
        ),
    },
    "Uranus": {
        1: (
            "a new role, appearance or boundary changes how other people react before you feel fully settled in it",
            "the old version of you still works socially, but the cost of performing it has become obvious",
        ),
        2: (
            "income, spending or pricing changes unexpectedly and exposes how much flexibility the old budget really had",
            "a purchase or earning opportunity creates freedom only if it does not build a new dependency",
        ),
        3: (
            "a message, device, application or piece of information changes the route quickly",
            "a conversation breaks an old assumption and makes the previous explanation impossible to keep intact",
        ),
        4: (
            "a move, family change or home arrangement suddenly needs more freedom than the existing structure allows",
            "security starts requiring a redesign because the old arrangement no longer leaves enough air",
        ),
        5: (
            "a new attraction, creative direction or child-related change arrives faster than the old plan can absorb",
            "something enjoyable becomes more alive when the rules loosen without disappearing completely",
        ),
        6: (
            "a roster, commute or method changes abruptly and reveals which parts of the routine were needlessly rigid",
            "work becomes more sustainable only after the method changes, not after another burst of effort",
        ),
        7: (
            "a partner, client or collaborator wants different terms and the old agreement stops feeling inevitable",
            "another person asks for more freedom and forces both sides to decide which rules still protect something real",
        ),
        8: (
            "shared money, debt or access changes unexpectedly and exposes where freedom depended on somebody else's consent",
            "a financial or trust arrangement needs a new structure because the old one gives one side too much control",
        ),
        9: (
            "a trip, course, legal route or overseas opportunity appears from an unexpected direction",
            "a different route becomes possible once the old booking, institution or assumption stops being the only option",
        ),
        10: (
            "a career change, new technology or unexpected role alters what professional freedom could look like",
            "the old job can still function while no longer buying the future you want",
        ),
        11: (
            "a new group, audience or friend changes the network around the next plan",
            "a team or community reorganises quickly and shows which relationships were built on habit rather than shared direction",
        ),
        12: (
            "a private realisation breaks an old pattern before there is anything public to announce",
            "quiet time exposes which obligation survives mainly because nobody has tried another way",
        ),
    },
    "Neptune": {
        1: (
            "the image other people have of you becomes less reliable than what your actual commitments show",
            "identity feels less fixed for a while and the safest decisions stay tied to observable facts",
        ),
        2: (
            "a price, promise or financial estimate looks attractive before the full cost is known",
            "money becomes clearer only after the wishful version and the actual number are put side by side",
        ),
        3: (
            "a message, document or explanation sounds convincing but still needs independent verification",
            "a conversation stays confusing until the missing fact is asked for directly",
        ),
        4: (
            "a family story or home arrangement carries assumptions that nobody has checked recently",
            "the emotional atmosphere at home is real, but the explanation for it still needs evidence",
        ),
        5: (
            "a date, creative idea or enjoyable escape feels meaningful before follow-through proves what it can hold",
            "chemistry or inspiration stays useful only when it survives the return of ordinary life",
        ),
        6: (
            "fatigue, workload or a messy routine makes motive harder to read and small facts more valuable",
            "a schedule problem can look emotional until sleep, timing and workload are measured honestly",
        ),
        7: (
            "a partner, client or collaborator gives mixed signals and the agreement needs behaviour, not interpretation",
            "a connection feels significant while reciprocity remains unproven",
        ),
        8: (
            "a shared cost, debt or trust arrangement contains assumptions that need documents or numbers",
            "money and intimacy become easier to understand once the vague part is made measurable",
        ),
        9: (
            "an overseas offer, course or publication sounds attractive while important terms are still missing",
            "visa, legal or study advice conflicts and needs a second source before the larger move is made",
        ),
        10: (
            "a role looks attractive from the outside before the work, authority or reporting line is fully defined",
            "professional image and professional reality need to be separated before you commit",
        ),
        11: (
            "a group, audience or future plan sounds aligned while nobody has yet owned the unglamorous work",
            "a friendship or network promise needs one concrete action before you call it support",
        ),
        12: (
            "a private fear, hope or memory becomes louder and needs time before it is treated as a fact",
            "rest and solitude reveal what constant input was making harder to distinguish",
        ),
    },
    "Pluto": {
        1: (
            "a personal boundary changes and reveals which relationships depended on the old version of you",
            "the way you show up alters the balance of power before anybody explicitly discusses it",
        ),
        2: (
            "a pay rate, asset or recurring cost reveals who benefits from the current valuation",
            "money becomes a power question when one side can decide the price and the other side keeps absorbing it",
        ),
        3: (
            "a document, message or piece of information changes who can control the next decision",
            "a conversation becomes powerful because somebody finally names what the room already knew",
        ),
        4: (
            "a family role, living arrangement or property decision exposes who has been deciding for everybody else",
            "home changes when an old dependency can no longer be treated as neutral",
        ),
        5: (
            "a relationship, child-related issue or creative project reveals where desire and control have become tangled",
            "something deeply wanted becomes easier to judge once you separate attachment from leverage",
        ),
        6: (
            "a workload or routine reveals who benefits from you continuing to absorb the pressure",
            "the ordinary week becomes political when one person keeps carrying work that nobody has formally assigned",
        ),
        7: (
            "a partner, client or competitor reveals where the agreement gives one side more leverage than the other",
            "a relationship changes once both people can see who can decide, withhold or leave",
        ),
        8: (
            "a debt, shared asset or financial dependency makes the real balance of power visible",
            "trust changes when access to money, information or responsibility is no longer distributed the same way",
        ),
        9: (
            "a legal, academic, publishing or overseas decision reveals who can actually approve, delay or redirect the route",
            "a trip or application becomes a power question when somebody else controls the permission, budget or timing",
        ),
        10: (
            "authority shifts before the organisation formally acknowledges who can make the real decision",
            "a role changes once status and actual control stop belonging to the same person",
        ),
        11: (
            "a group or network reveals which relationships carry real influence and which carry only attention",
            "a future plan changes when the person who can unlock resources, access or decisions moves position",
        ),
        12: (
            "a hidden dependency or old obligation becomes visible enough to end deliberately",
            "private work changes the power of a pattern before the outside world can see the result",
        ),
    },
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
    ("Jupiter", "Venus"): "More can arrive through affection, money or social attention. The useful test is whether the extra option improves your life or merely multiplies choices.",
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
    ("Saturn", "Ascendant"): "The version of you other people meet is being asked to become more exact. Availability, boundaries and personal responsibility need clearer terms.",
    ("Uranus", "Ascendant"): "Other people can keep reacting to an old version of you after you have outgrown it. Change the signal before you change the whole life around it.",
    ("Jupiter", "Ascendant"): "More people, movement or confidence can meet you at once. Use the extra room to become more visible without turning every invitation into an obligation.",
    ("Jupiter", "Moon"): "Home and emotional capacity are getting larger at the same time. Expansion is useful only if the private life underneath it can carry the extra weight.",
    ("Uranus", "Mars"): "The urge to act changes fastest where the old method has become too restrictive. Experiment with the method before making the break irreversible.",
    ("Pluto", "Ascendant"): "The way you enter the room is changing because the old power arrangement no longer supports the same role. Stop performing the version that kept the old balance intact.",
    ("Pluto", "Moon"): "Private security and power are tied together now. Protect what is genuinely vulnerable without preserving a home or family arrangement that no longer works.",
    ("Pluto", "Saturn"): "Responsibility and leverage are moving together. Formal duty matters, but so does who can actually decide, withhold or change the terms.",
    ("Jupiter", "Saturn"): "Growth has found a structure to test. Expand only what can carry its own weight once the enthusiasm leaves the room.",
    ("Jupiter", "Uranus"): "A larger option appears because the old route is no longer the only route. Use the opening without multiplying choices faster than you can evaluate them.",
    ("Jupiter", "Neptune"): "Hope gets more room. Keep the imagination, then make the larger possibility survive dates, numbers and observable behaviour.",
    ("Jupiter", "Pluto"): "Scale and leverage are arriving together. Ask whether getting more also improves your actual position.",
    ("Saturn", "Uranus"): "The rule and the need for freedom are colliding. Keep the structure that protects something real; change the part that only protects habit.",
    ("Saturn", "Neptune"): "The dream needs a deadline, definition or factual test. Keep what survives reality and stop financing the part that depends on vagueness.",
    ("Saturn", "Pluto"): "Duty and power are no longer separable. Put the responsibility beside the real decision-maker before agreeing to carry more.",
    ("Uranus", "Saturn"): "A structure that once felt responsible may now feel restrictive. Test a freer arrangement without throwing away the support that still works.",
    ("Uranus", "Pluto"): "Disruption is exposing where the power was already moving. Use the surprise to see the leverage clearly before making the irreversible move.",
    ("Neptune", "Moon"): "The feeling is real even when the explanation is not. Protect the private life from decisions that depend on certainty you do not yet have.",
    ("Neptune", "Ascendant"): "The old identity can blur before the new one is ready. Let the image stay unfinished while practical commitments remain tied to facts.",
    ("Neptune", "Saturn"): "Uncertainty is testing the structure. Keep the boundary, deadline or responsibility that still works when the story gets quieter.",
    ("Jupiter", "Jupiter"): "A twelve-year growth cycle is resetting. Choose the expansion that increases future choice instead of simply giving you more to carry.",
    ("Saturn", "Saturn"): "The structure is auditing itself. Keep the responsibility that still has purpose; stop renewing the part that survives only through habit.",
    ("Uranus", "Uranus"): "A long freedom cycle is echoing itself. Notice where the old version of independence no longer gives you enough room.",
    ("Neptune", "Neptune"): "An old ideal is meeting a new layer of uncertainty. Keep the imagination, then test which part still survives reality.",
    ("Pluto", "Pluto"): "A long power cycle is echoing itself. Name what has changed in leverage, dependency or control before you decide what still deserves continuity.",("Neptune", "Pluto"): "A power arrangement is harder to read because motive and leverage are blurred. Slow the interpretation down; ask who can actually decide, withhold or walk away.",
    ("Neptune", "Uranus"): "The desire for freedom is mixed with uncertainty. Test whether the new route creates real room or simply gives the ambiguity a more attractive shape.",
    ("Neptune", "Jupiter"): "Possibility is expanding faster than certainty. Keep the vision, then make the larger option survive dates, numbers and observable behaviour.",
    ("Pluto", "Jupiter"): "Scale changes the balance of power. Ask whether the larger option improves your position or merely increases what somebody else can ask from you.",
    ("Saturn", "Jupiter"): "Growth has met a limit that can be useful. Keep the option that still works once cost, timing and responsibility are made explicit.",
    ("Uranus", "Jupiter"): "A larger option appears because the old route is no longer the only route. Test the freedom before multiplying commitments.",

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
        "The two demands cannot keep sharing the same priority. Choose which one the plan protects.",
        "The friction is useful because the current arrangement now has a visible cost.",
        "Something has to give. Name the part that cannot keep absorbing the compromise.",
    ),
    "opposition": (
        "The pressure is visible through another person, demand or competing priority, so balance can no longer stay theoretical.",
        "What you want and what the other side requires are easier to compare now because the difference is out in the open.",
        "Another person, deadline or competing need makes the hidden imbalance visible.",
    ),
    "conjunction": (
        "Two pressures are arriving through the same door. Treat them as one decision.",
        "The themes are fused now; changing one changes the other.",
        "The old neutral position no longer exists. Choose the terms.",
    ),
    "trine": (
        "The easier path is real. Use it on something worth keeping.",
        "Support is available. Convert it into one result before it becomes background.",
        "The door opens with less force than usual. Walk through it deliberately.",
    ),
    "sextile": (
        "An opening is available, but it needs a small move from you.",
        "The option is within reach. Put a date, message or decision behind it.",
        "Support is waiting for a response. Use it before it becomes merely pleasant.",
    ),
}


SUPPORTIVE_ASPECT_LEADS = {
    "Jupiter": {
        "trine": "The larger route needs less force than usual. Use the extra room on something that increases future choice.",
        "sextile": "The opening is close enough to use, but it still needs a message, decision or commitment from you.",
    },
    "Saturn": {
        "trine": "Structure is helping rather than blocking. Use the easier conditions to formalise what deserves to last.",
        "sextile": "A useful boundary or agreement is available if you state it clearly.",
    },
    "Uranus": {
        "trine": "Change has more room to move without breaking everything around it.",
        "sextile": "A freer option is close enough to test without making the irreversible break.",
    },
    "Neptune": {
        "trine": "The feeling and the facts are cooperating enough to test the idea gently.",
        "sextile": "A creative or intuitive opening is useful only if one practical check survives.",
    },
    "Pluto": {
        "trine": "The leverage is easier to see. Use the opening to improve the terms without overplaying your hand.",
        "sextile": "A quiet power shift gives you room to change one term before the old balance hardens again.",
    },
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


_SUPPORTIVE_WATCH = {
    "Jupiter": "More options can make a mediocre option look valuable.",
    "Saturn": "Ease can make an old obligation look healthier than it is.",
    "Uranus": "A smooth escape can still be an escape from the wrong problem.",
    "Neptune": "A pleasant feeling can still blur the evidence.",
    "Pluto": "A temporary advantage can tempt you to overplay your hand.",
}


def _watch(transit_planet: str, target_planet: str, aspect: str) -> str:
    base = WATCH_BY_TRANSIT[transit_planet].get(target_planet, WATCH_BY_TRANSIT[transit_planet]["default"])
    if aspect in {"trine", "sextile"}:
        extra = _SUPPORTIVE_WATCH.get(transit_planet, "")
        return f"{base} {extra}".strip()
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
            f"A decision around {target} has become harder to postpone. "
            "Name the practical condition that changed, then decide from what is actually happening now."
        )

    if aspect in {"trine", "sextile"}:
        lead = SUPPORTIVE_ASPECT_LEADS.get(transit_planet, {}).get(
            aspect,
            _pick(ASPECT_LEADS[aspect], seed + 1),
        )
        consequence = _pick(TRANSIT_GIFT_LINES[transit_planet], seed + 2)
    elif aspect in {"square", "opposition"}:
        lead = _pick(ASPECT_LEADS[aspect], seed + 1)
        consequence = _pick(TRANSIT_SHADOW_LINES[transit_planet], seed + 2)
    else:
        lead = _pick(ASPECT_LEADS[aspect], seed + 1)
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

    transit_house_bank = TRANSIT_HOUSE_SCENARIOS.get(transit_planet, {})
    if natal_house in transit_house_bank:
        scenarios.append(_pick(transit_house_bank[natal_house], seed + 1))
    elif natal_house in HOUSE_SCENARIOS:
        scenarios.append(_pick(HOUSE_SCENARIOS[natal_house], seed + 1))
    elif len(target_signs) > 1:
        scenarios.append(_pick(target_signs, seed + 1))

    bridge_scene = _target_house_scene(target_planet, natal_house)
    if bridge_scene:
        scenarios.append(bridge_scene)
    elif len(target_signs) > 2:
        scenarios.append(_pick(target_signs, seed + 2))
    else:
        scenarios.append("Watch where the practical consequence is already measurable; that is where the transit becomes useful before it becomes dramatic.")

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

