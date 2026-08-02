from __future__ import annotations

LUNA_SAYS_LABEL = "Luna says"
DO_LABEL = "Do"
DONT_LABEL = "Don't"
YOUR_MOVE_LABEL = "Your move"

WHY_LUNA_LABEL = "Why Luna sees this"
SOLAR_LABEL = "Solar Convergence"
TIMING_LABEL = "Key dates and planetary timing"
TECHNICAL_LABEL = "Full technical evidence"

GATEKEEPER_LINE = "From reading the future to writing it."
ACCESS_LINE = "Choose what earns access."
VALIDATION_LINE = "Enjoy the attention. Follow the effort. Choose what grows."

FOOTER_DISCLAIMER = (
    "Luna uses concrete examples to help you recognise the pattern in your own "
    "life. They describe possibilities, not guaranteed events. Astrology is a "
    "symbolic interpretive framework, not scientifically established causal forecasting."
)


DO_HUMOUR_BY_HOUSE = {
    1: "Choose yourself. No committee meeting required.",
    2: "Check the number. Compliments are not legal tender.",
    3: "Ask the question. Telepathy remains understaffed.",
    4: "Name the issue. The walls already know.",
    5: "Enjoy the spark. Watch what happens next.",
    6: "Fix the routine. Chaos is not a personality.",
    7: "Ask for clear terms. Mixed signals are not a dialect.",
    8: "Read the fine print. Chemistry has terrible bookkeeping.",
    9: "Go bigger—with a map and a receipt.",
    10: "Finish the result. Applause can wait outside.",
    11: "Choose the circle. The group chat is not a board.",
    12: "Pause first. Fantasy has excellent marketing.",
}

DONT_HUMOUR_BY_HOUSE = {
    1: "Audition for approval. The role is beneath you.",
    2: "Spend for validation. Attention is not a currency.",
    3: "Write the sequel before they reply.",
    4: "Call silence peace. It has terrible acoustics.",
    5: "Write the whole future from one spark.",
    6: "Volunteer for emotional overtime.",
    7: "Accept hints as a contract.",
    8: "Let chemistry handle the accounts.",
    9: "Book the future before checking the gate.",
    10: "Chase the spotlight without bringing the work.",
    11: "Hand everyone a backstage pass.",
    12: "Give mystery a six-season renewal.",
}

DO_DONT_PAIR_OVERRIDES = {
    frozenset({5, 9}): (
        "Follow the effort. Chemistry can book its own flight.",
        "Write the ending from one exciting message. A boarding pass is not a relationship.",
    ),
    frozenset({4, 7}): (
        "Name the issue. The living room already knows.",
        "Call silence peace. It has terrible acoustics.",
    ),
    frozenset({3, 5}): (
        "Ask the question. Telepathy remains understaffed.",
        "Write the sequel before they reply.",
    ),
    frozenset({7, 10}): (
        "Keep the terms clear. Chemistry cannot chair the meeting.",
        "Let attraction edit the job description.",
    ),
    frozenset({2, 4}): (
        "Check the numbers. Romance still uses electricity.",
        "Let comfort put the budget on mute.",
    ),
    frozenset({8, 11}): (
        "Choose the circle. Trust does not need an audience.",
        "Hand the group chat the vault combination.",
    ),
    frozenset({2, 12}): (
        "Pause before spending. Feelings have terrible exchange rates.",
        "Let the coping mechanism keep the company card.",
    ),
    frozenset({1, 3}): (
        "Say it plainly. The press conference is cancelled.",
        "Turn one opinion into a public referendum.",
    ),
    frozenset({5, 7}): (
        "Enjoy the spark. Ask whether it can make a plan.",
        "Promote chemistry to commitment without an interview.",
    ),
    frozenset({8, 10}): (
        "Keep the receipts—emotional and otherwise.",
        "Let power dress itself up as intimacy.",
    ),
    frozenset({6, 9}): (
        "Plan the escape. Annual leave is still paperwork.",
        "Call burnout a spontaneous adventure.",
    ),
    frozenset({4, 10}): (
        "Build success somewhere you actually want to live.",
        "Let ambition redecorate your private life without asking.",
    ),
    frozenset({2, 7}): (
        "Watch the effort. Flattery cannot pay the deposit.",
        "Mistake interest for investment.",
    ),
}


def luna_do_dont(primary_house: int, secondary_house: int) -> tuple[str, str]:
    """Return the shared concise, witty Luna Do/Don't pair.

    Daily, monthly and yearly readings call this same function so the customer
    voice stays consistent across products.
    """
    primary = int(primary_house)
    secondary = int(secondary_house)
    pair = DO_DONT_PAIR_OVERRIDES.get(frozenset({primary, secondary}))
    if pair:
        return pair
    return (
        DO_HUMOUR_BY_HOUSE.get(primary, "Follow what proves itself."),
        DONT_HUMOUR_BY_HOUSE.get(secondary, "Confuse attention with evidence."),
    )
