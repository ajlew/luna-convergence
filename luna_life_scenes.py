from __future__ import annotations

import re
from typing import Iterable


# Ordinary-life repository.
# These are possibilities, not predictions. The wording is deliberately mundane:
# calendars, keys, invoices, clothes, bookings, shifts, messages and actual people.
LIFE_SCENES: dict[str, tuple[str, ...]] = {
    "identity": (
        "you buy clothes because the old version of you no longer feels right",
        "you stop introducing yourself through a role you have already outgrown",
        "you change a haircut, profile, routine or habit because you want the outside to match the inside",
        "you are asked to lead before you feel completely ready",
        "you realise you keep saying yes because people expect the capable version of you",
        "you walk into a room and notice you no longer want the same approval",
        "you change the way you spend a Saturday because your priorities have moved",
        "you decide that being available is not the same as being generous",
        "you remove something from the wardrobe, calendar or identity that belonged to an earlier version of you",
        "you choose one direction instead of keeping several identities alive at once",
    ),
    "money": (
        "a bill arrives earlier than expected",
        "a purchase looks attractive until you calculate the ongoing cost",
        "a pay rise, fee or quote needs a real number attached to it",
        "you buy clothes, equipment or a ticket and have to decide what the purchase replaces",
        "a subscription or recurring charge finally looks ridiculous on the statement",
        "someone asks for a discount and you have to decide what your work is worth",
        "a refund, invoice or late payment changes the week's plan",
        "you compare the cheaper option with the one that will actually last",
        "an unexpected expense makes a vague budget suddenly specific",
        "you look at the bank balance before saying yes to the fun part",
    ),
    "communication": (
        "a text needs a direct answer instead of another hour of interpretation",
        "an email changes the tone of a negotiation",
        "a document needs signing before the idea becomes real",
        "a phone call clears up what three messages failed to settle",
        "an application, form or piece of paperwork reaches its deadline",
        "someone leaves an important sentence unfinished and you ask the obvious question",
        "a meeting reveals that two people were using the same word to mean different things",
        "a short trip or appointment forces a decision that was easier to postpone online",
        "a message arrives from someone you had stopped expecting to hear from",
        "you rewrite the sentence until it says what you actually mean",
    ),
    "home": (
        "a lease, move or flatmate arrangement needs clearer terms",
        "a repair can no longer be ignored because you have to live with it every day",
        "a family visit changes the calendar and the available space",
        "you clear a room because the next plan physically needs somewhere to go",
        "rent, mortgage or household costs force a practical conversation",
        "someone gets a key and the relationship becomes less theoretical",
        "a work plan reaches the kitchen table and starts affecting everybody else",
        "a caregiving arrangement needs a roster rather than goodwill",
        "you decide what stays in the house and what belongs to the life you are leaving",
        "home stops being background and becomes part of the decision",
    ),
    "romance": (
        "a first date turns into a second plan",
        "someone attractive starts making room for you in an actual calendar",
        "a flirtation becomes less interesting once practical effort is required",
        "a creative project starts asking for real time instead of spare time",
        "a child, hobby or passion project changes what you can promise elsewhere",
        "a date is wonderful and the next morning still needs evidence",
        "someone remembers the detail you expected them to forget",
        "a promising connection has to survive an ordinary Tuesday",
        "you choose whether pleasure belongs in the plan or only in the fantasy",
        "an invitation feels exciting until you ask what happens after the event",
    ),
    "routine": (
        "the shift roster makes the real workload impossible to ignore",
        "a commute turns a good opportunity into a different calculation",
        "an appointment, deadline or school pickup collides with the plan",
        "the fridge, laundry and inbox reveal how much spare capacity you actually have",
        "you keep fixing the same problem because nobody has changed the system",
        "a new responsibility looks manageable until Monday morning arrives",
        "your body objects to a schedule your ambition keeps defending",
        "a colleague leaves a gap and everybody quietly expects you to fill it",
        "a recurring task needs a better method, not another burst of effort",
        "the plan works on paper and fails in the ordinary week",
    ),
    "relationship": (
        "someone wants more access to your time without offering more effort",
        "a promising date becomes a conversation about exclusivity or availability",
        "a client asks for more scope without changing the fee",
        "a friend keeps waiting for you to make every plan",
        "a partner says yes but leaves the organising to you",
        "a wedding invitation, trip or event reveals who assumes you will rearrange everything",
        "someone apologises and you watch what changes afterwards",
        "a collaborator likes the idea but avoids the unglamorous work",
        "a competitor forces you to decide what you will and will not match",
        "a relationship becomes clearer when one person has to carry an inconvenient part",
    ),
    "shared": (
        "a tax bill, debt or insurance payment needs a number and an owner",
        "rent or household costs need to be split instead of vaguely shared",
        "someone borrows money and the emotional part of the agreement becomes obvious",
        "a joint account, loan or contract needs a boundary",
        "caregiving work has to be divided rather than assumed",
        "an inheritance, payout or shared asset brings old family dynamics to the table",
        "a partner's financial decision changes what you can safely promise",
        "a hidden cost appears after the exciting decision has already been discussed",
        "one person keeps absorbing the risk because nobody has written down the terms",
        "trust becomes measurable when money, access or responsibility has to be shared",
    ),
    "travel": (
        "a trip needs booking, leave approval and a budget",
        "a passport, visa or legal document needs attention before the romantic version of travel can happen",
        "a course application turns into an actual timetable",
        "an overseas opportunity becomes real once the flights have a price",
        "the manuscript, application or course suddenly has a real deadline",
        "a friend invites you away and the dates collide with work",
        "an international client or contact asks for a meeting",
        "a legal or administrative process needs paperwork rather than optimism",
        "you consider moving, studying or working somewhere unfamiliar",
        "an outside opportunity looks different once you calculate travel time, money and recovery",
    ),
    "career": (
        "a manager adds responsibility before discussing title or pay",
        "a job opportunity arrives and the commute, roster or reporting line changes the answer",
        "an interview turns a vague possibility into a date on the calendar",
        "a client wants a commitment before the scope is clear",
        "a promotion looks flattering until you price the extra hours",
        "a deadline lands in a week that is already full",
        "someone senior notices your work and asks for more of it",
        "you are asked to represent the team, present publicly or own the result",
        "a role sounds prestigious but the daily work tells a different story",
        "you decide whether the title, audience or attention is worth the responsibility attached to it",
    ),
    "friends": (
        "a friend appears with an invitation that changes the weekend",
        "a wedding, birthday or group trip makes everybody's priorities visible",
        "someone introduces you to a person who can open a useful door",
        "a group chat turns into an actual plan with dates and money attached",
        "a community or online audience starts expecting more from you",
        "a friend offers help and you find out whether the offer survives logistics",
        "a networking conversation turns into a meeting",
        "a team project needs one person to own the next step",
        "you realise one friendship is built on history while another is built on effort",
        "a future plan becomes real when another person puts their name beside yours",
    ),
    "rest": (
        "you turn the phone off because another hour of input will not improve the answer",
        "an unfinished conversation keeps following you into quiet moments",
        "sleep becomes more useful than another round of analysis",
        "a private problem needs handling before you announce the next plan",
        "you clear old messages, paperwork or objects because the unfinished story is taking up space",
        "a quiet weekend tells you what constant activity was hiding",
        "you stop explaining something to people who are not involved",
        "an old grief, resentment or obligation needs a clean ending",
        "you cancel one thing and discover the world continues",
        "privacy becomes productive rather than avoidant",
    ),
    "general": (
        "a date gets written into the calendar",
        "someone asks for a yes before all the details are clear",
        "a bill, booking or deadline makes the abstract choice physical",
        "a conversation changes what you thought the plan was",
        "the exciting version meets the ordinary week",
        "another person has to contribute instead of merely agreeing",
        "the paperwork arrives after the enthusiasm",
        "a small logistical detail exposes the real cost",
        "the plan reaches the kitchen table",
        "Tuesday morning asks whether the idea still works",
    ),
}


DOMAIN_COMMANDS: dict[str, tuple[str, ...]] = {
    "identity": (
        "Choose the version of you that gets the calendar.",
        "Stop performing the role you no longer want.",
        "Act like the decision belongs to you.",
    ),
    "money": (
        "Put the number on paper.",
        "Price the yes before you give it.",
        "Cut the cost that survives only because you stopped checking.",
    ),
    "communication": (
        "Ask the direct question.",
        "Send the clear sentence.",
        "Read the document before you read the mood.",
    ),
    "home": (
        "Fix the arrangement you have to live with every day.",
        "Make room before you add another promise.",
        "Put the household terms into words.",
    ),
    "romance": (
        "Enjoy the spark. Then inspect the follow-through.",
        "Let attraction open the door. Make consistency keep it open.",
        "Give pleasure a place in the plan, not control of it.",
    ),
    "routine": (
        "Change the method before adding effort.",
        "Make the ordinary week carry the plan.",
        "Stop rescuing the broken routine.",
    ),
    "relationship": (
        "Ask who is doing the carrying.",
        "Make the terms mutual before you make them permanent.",
        "Watch what the other person does after the easy part.",
    ),
    "shared": (
        "Give the obligation a number, an owner and an end point.",
        "Write down who carries what.",
        "Separate trust from unlimited access.",
    ),
    "travel": (
        "Check the booking, deadline and paperwork.",
        "Price the wider option before you romanticise it.",
        "Make the outside opportunity survive logistics.",
    ),
    "career": (
        "Price the responsibility before you accept the title.",
        "Define the role before you inherit the workload.",
        "Make authority come with terms.",
    ),
    "friends": (
        "Watch who turns enthusiasm into a plan.",
        "Choose the people who carry the next step with you.",
        "Stop calling applause support.",
    ),
    "rest": (
        "End the input. Let the answer get quieter.",
        "Close what is finished.",
        "Protect the private hour before you add another demand.",
    ),
    "general": (
        "Make the abstract choice physical.",
        "Name the cost before you name the dream.",
        "Choose what still works after the excitement fades.",
    ),
}


YOUTH_SCENES: dict[str, tuple[str, ...]] = {
    "identity": (
        "a school, sport or family role starts expecting a more grown-up version of you",
        "you change how you dress, speak or join in because the old version no longer fits",
    ),
    "money": (
        "pocket money, a first casual job or a family budget makes the real cost visible",
        "you learn that wanting something and being able to pay for it are different questions",
    ),
    "communication": (
        "a teacher, parent or friend asks for a clear answer instead of another explanation",
        "a school form, application, message or deadline needs a direct response",
    ),
    "home": (
        "a family rule, move, care responsibility or change at home asks more maturity from you",
        "home feels different because somebody's needs or responsibilities have changed",
    ),
    "romance": (
        "a crush, friendship, hobby or creative project starts asking for real time and courage",
        "attention feels exciting, then ordinary behaviour shows whether it means anything",
    ),
    "routine": (
        "school, training, homework or family duties show whether the schedule is sustainable",
        "you keep carrying a task because adults or teammates know you are reliable",
    ),
    "relationship": (
        "a friendship reveals who makes the plan, apologises, shares the work or keeps the promise",
        "another person wants closeness while the practical effort still falls mostly on you",
    ),
    "shared": (
        "a family responsibility, borrowed item or shared expense makes ownership and trust visible",
        "you learn that sharing something also means deciding who is responsible for it",
    ),
    "travel": (
        "a school trip, family journey, course or application needs permission, dates and paperwork",
        "an outside opportunity sounds exciting until transport, permission and timing enter the plan",
    ),
    "career": (
        "a teacher, parent, coach or school responsibility starts expecting more maturity from you",
        "you are trusted with a visible role before you feel completely ready for it",
    ),
    "friends": (
        "a friendship group shows who includes you, makes the plan and follows through",
        "a team, class or group project reveals who actually carries the next step",
    ),
    "rest": (
        "you need private time away from school, family or friends to work out what you actually feel",
        "an old worry or unfinished disagreement keeps following you into quiet moments",
    ),
    "general": (
        "an adult expectation suddenly becomes your responsibility too",
        "a school, family or friendship decision becomes harder to postpone",
    ),
}


_HUMAN_FOCUS = {
    "identity": "your appearance, boundaries and the version of you other people are meeting",
    "money": "the price, payment or purchase in front of you",
    "communication": "the message, document or conversation that needs an answer",
    "home": "home and the arrangement you live with every day",
    "romance": "the date, attraction or creative project pulling your attention",
    "routine": "the roster, workload and ordinary week you actually have to live",
    "relationship": "the other person, the agreement and who carries the inconvenient part",
    "shared": "the money, trust and responsibility you share with someone else",
    "travel": "the trip, course, application or outside opportunity that could widen your world",
    "career": "the job, role or public responsibility with your name on it",
    "friends": "the people and plan you are trying to build with",
    "rest": "what needs privacy, rest or a clean ending",
    "general": "the decision already in front of you",
}


def domain_key(value: str) -> str:
    raw = re.sub(r"\s+", " ", str(value or "")).strip().lower()

    tests = (
        ("relationship", ("relationship", "partner", "client", "contract", "competitor", "agreement", "other people", "person across the table", "promises between")),
        ("shared", ("shared money", "shared finances", "shared resources", "debt", "tax", "inheritance", "intimacy", "trust and shared", "responsibility you share", "money, trust")),
        ("career", ("career", "midheaven", "public direction", "reputation", "authority", "professional", "manager", "job")),
        # Communication must be tested before travel because House 3 contains
        # "learning" while House 9 also contains education.  The explicit
        # communication/local-movement signal is the deciding evidence.
        ("communication", ("communication", "message", "document", "local movement", "everyday decisions")),
        ("travel", ("travel", "trip", "course", "application", "outside opportunity", "publishing", "law", "legal", "education", "study", "learning", "foreign", "international", "wider world", "higher learning")),
        ("friends", ("friends", "community", "communities", "network", "future plan", "future aims", "audience", "group", "people and plan", "build with")),
        ("routine", ("work routines", "daily routines", "daily systems", "health", "wellbeing", "service", "operations", "workload", "schedule")),
        ("home", ("home", "family", "foundations", "private life", "domestic")),
        ("romance", ("romance", "creative", "creativity", "pleasure", "children", "dating", "attraction")),
        ("money", ("money", "income", "possessions", "self-worth", "price", "payment", "purchase", "value and security")),
        ("rest", ("rest", "closure", "private reflection", "inner life", "hidden matters")),
        ("identity", ("identity", "ascendant", "self-direction", "personal direction", "body", "confidence", "how you show up", "willing to carry")),
    )
    for key, needles in tests:
        if any(needle in raw for needle in needles):
            return key
    return "general"


def human_focus(value: str) -> str:
    return _HUMAN_FOCUS[domain_key(value)]


def _stable_index(seed_text: str, length: int) -> int:
    seed = sum((index + 1) * ord(ch) for index, ch in enumerate(str(seed_text or "")))
    return seed % max(length, 1)


def scene_choices(
    value: str,
    seed_text: str = "",
    count: int = 2,
    *,
    age: int | None = None,
) -> tuple[str, ...]:
    key = domain_key(value)
    if age is not None and age < 18:
        bank = YOUTH_SCENES.get(key, YOUTH_SCENES["general"])
    else:
        bank = LIFE_SCENES.get(key, LIFE_SCENES["general"])
    start = _stable_index(f"{key}|{seed_text}|{age if age is not None else 'adult'}", len(bank))
    chosen = []
    for offset in range(len(bank)):
        item = bank[(start + offset) % len(bank)]
        if item not in chosen:
            chosen.append(item)
        if len(chosen) >= max(1, count):
            break
    return tuple(chosen)


def life_scene_line(value: str, seed_text: str = "", count: int = 2, *, age: int | None = None) -> str:
    """Return lived examples directly. Never announce that an example is coming."""
    scenes = scene_choices(value, seed_text=seed_text, count=count, age=age)
    if not scenes:
        return ""

    def sentence(value: str) -> str:
        clean = re.sub(r"\s+", " ", str(value or "")).strip().rstrip(".")
        return clean[:1].upper() + clean[1:] + "." if clean else ""

    if len(scenes) == 1:
        return sentence(scenes[0])
    return f"{sentence(scenes[0])} Or {sentence(scenes[1])[:1].lower() + sentence(scenes[1])[1:]}"


def domain_command(value: str, seed_text: str = "") -> str:
    key = domain_key(value)
    bank = DOMAIN_COMMANDS.get(key, DOMAIN_COMMANDS["general"])
    return bank[_stable_index(f"{key}|{seed_text}", len(bank))]


def scene_repository_size() -> int:
    return sum(len(values) for values in LIFE_SCENES.values())
