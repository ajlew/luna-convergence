from __future__ import annotations

PLANET_MEANINGS = {
    "Sun": {
        "core": "purpose, visibility and conscious direction",
        "opportunity": "take ownership and make the central objective visible",
        "risk": "ego, overexposure or confusing attention with achievement",
    },
    "Moon": {
        "core": "mood, instinct and rapidly changing conditions",
        "opportunity": "read the room and respond to immediate reality",
        "risk": "reacting before the emotional weather settles",
    },
    "Mercury": {
        "core": "communication, analysis, trade and decisions",
        "opportunity": "clarify language, improve systems and verify information",
        "risk": "misunderstanding, rushed messages or incomplete facts",
    },
    "Venus": {
        "core": "relationships, value, attraction and money preferences",
        "opportunity": "improve appeal, negotiate and strengthen useful alliances",
        "risk": "people-pleasing, weak pricing or confusing attraction with suitability",
    },
    "Mars": {
        "core": "action, pressure, competition and conflict",
        "opportunity": "act decisively and remove delay",
        "risk": "forcing the issue, hostility or wasted effort",
    },
    "Jupiter": {
        "core": "growth, confidence, reach and excess",
        "opportunity": "expand a proven strength into a larger field",
        "risk": "overpromising, overextension or believing scale proves quality",
    },
    "Saturn": {
        "core": "limits, responsibility, discipline and durable structure",
        "opportunity": "formalise, simplify and build something that can survive pressure",
        "risk": "fear, rigidity, delay or carrying obligations without redesign",
    },
    "Uranus": {
        "core": "disruption, freedom, innovation and sudden change",
        "opportunity": "break an obsolete pattern and use technology intelligently",
        "risk": "instability, rebellion without a replacement system or abrupt separation",
    },
    "Neptune": {
        "core": "imagination, ideals, uncertainty and blurred boundaries",
        "opportunity": "use vision, symbolism and creative intuition",
        "risk": "wishful thinking, unclear commitments or avoiding measurable facts",
    },
    "Pluto": {
        "core": "power, elimination, compulsion and irreversible transformation",
        "opportunity": "remove what is obsolete and concentrate power deliberately",
        "risk": "obsession, manipulation, secrecy or escalating every issue into a control struggle",
    },
    "True Node": {
        "core": "developmental direction and unfamiliar growth",
        "opportunity": "move toward the less familiar but more developmental path",
        "risk": "mistaking novelty for destiny",
    },
}

HOUSE_STRATEGY = {
    1: {
        "opportunity": "redefine identity, improve energy and initiate a personal direction",
        "risk": "self-absorption or acting as though every situation is a referendum on you",
        "action": "choose one identity-level commitment and make your behaviour match it",
    },
    2: {
        "opportunity": "improve income, pricing, ownership and practical self-reliance",
        "risk": "confusing turnover, credit or possessions with financial strength",
        "action": "measure cash, margin and recurring cost separately",
    },
    3: {
        "opportunity": "build leverage through writing, selling, learning and digital communication",
        "risk": "noise, argument, misinformation or compulsive communication",
        "action": "reduce the message to one claim supported by evidence",
    },
    4: {
        "opportunity": "stabilise home, family and the private base supporting public growth",
        "risk": "dragging unresolved private pressure into every external decision",
        "action": "repair the foundation before demanding more expansion",
    },
    5: {
        "opportunity": "create, launch, perform, teach or turn pleasure into disciplined enterprise",
        "risk": "speculation, romantic projection or treating inspiration as a finished product",
        "action": "convert one creative idea into a repeatable production process",
    },
    6: {
        "opportunity": "improve health, routines, operations, service and reliability",
        "risk": "burnout, micromanagement or being trapped by low-value maintenance",
        "action": "remove one recurring operational failure",
    },
    7: {
        "opportunity": "form useful partnerships and negotiate stronger agreements",
        "risk": "dependency, unstable contracts or turning every difference into opposition",
        "action": "put responsibilities, payment and exit terms in writing",
    },
    8: {
        "opportunity": "restructure debt, shared resources, tax, trust and financial obligations",
        "risk": "dependency, hidden liabilities or confusing borrowing capacity with wealth",
        "action": "make every obligation visible and assign ownership",
    },
    9: {
        "opportunity": "expand through travel, publishing, education, law and foreign markets",
        "risk": "grand claims, ideology or expansion without operational capacity",
        "action": "take one proven idea into a larger territory",
    },
    10: {
        "opportunity": "gain authority, improve reputation and produce visible professional results",
        "risk": "status anxiety, public overreach or confusing activity with achievement",
        "action": "finish one result that can be seen and evaluated",
    },
    11: {
        "opportunity": "strengthen audiences, alliances, communities and long-term plans",
        "risk": "group pressure, weak networks or chasing reach without loyalty",
        "action": "identify the few relationships that actually create leverage",
    },
    12: {
        "opportunity": "complete, recover, research privately and remove hidden sabotage",
        "risk": "avoidance, secrecy, exhaustion or repeating an unconscious pattern",
        "action": "reduce noise and finish the unresolved matter privately",
    },
}

RETROGRADE_MEANINGS = {
    "Mercury": {
        "review": "messages, documents, contracts, trade, software, transport and decisions",
        "risk": "acting on incomplete information or assuming everyone heard the same agreement",
        "best_use": "reconcile facts, retrieve missing information and revise the process",
    },
    "Venus": {
        "review": "relationships, pricing, aesthetics, alliances and value judgments",
        "risk": "returning to an old attachment without evidence that the structure changed",
        "best_use": "revalue what and whom receives time, money and attention",
    },
    "Mars": {
        "review": "effort, conflict, competition, desire and the use of force",
        "risk": "pushing harder at the wrong target",
        "best_use": "redirect energy, repair strategy and decide which battle is worth the cost",
    },
    "Jupiter": {
        "review": "growth plans, beliefs, education, legal matters and expansion",
        "risk": "assuming delay means the opportunity is false or assuming optimism replaces proof",
        "best_use": "test the expansion model and correct excess",
    },
    "Saturn": {
        "review": "obligations, boundaries, systems, authority and long-term structure",
        "risk": "carrying an obsolete responsibility merely because it is familiar",
        "best_use": "redesign the structure, standard and boundary",
    },
    "Uranus": {
        "review": "freedom, technology, disruption and unfinished change",
        "risk": "rebellion without a workable replacement",
        "best_use": "make innovation operational rather than theatrical",
    },
    "Neptune": {
        "review": "ideals, imagination, boundaries, sacrifice and uncertainty",
        "risk": "using spirituality, creativity or hope to avoid facts",
        "best_use": "separate genuine vision from projection",
    },
    "Pluto": {
        "review": "power, control, compulsion, buried material and irreversible change",
        "risk": "repeating a destructive power strategy because it once worked",
        "best_use": "remove the hidden dependency or obsolete identity",
    },
}

COMBINATION_MEANINGS = {
    frozenset({"Saturn", "Neptune"}): {
        "title": "Dream versus reality",
        "meaning": "The vision must acquire structure or dissolve under its own vagueness.",
        "opportunity": "turn imagination into a disciplined system",
        "risk": "building around hope, ambiguity or undefined responsibility",
    },
    frozenset({"Jupiter", "Pluto"}): {
        "title": "Expansion versus control",
        "meaning": "Growth exposes questions of power, ownership, information and scale.",
        "opportunity": "use influence to expand a proven system",
        "risk": "overreach, ideological conflict or mistaking dominance for success",
    },
    frozenset({"Jupiter", "Saturn"}): {
        "title": "Controlled expansion",
        "meaning": "Opportunity and discipline can support each other when growth has limits and sequence.",
        "opportunity": "formalise a larger but sustainable operation",
        "risk": "expanding too slowly from fear or too quickly from confidence",
    },
    frozenset({"Jupiter", "Uranus"}): {
        "title": "Rapid opening",
        "meaning": "An unexpected route can enlarge the field quickly.",
        "opportunity": "use technology, novelty or a new alliance to access a larger market",
        "risk": "scaling before reliability is proven",
    },
    frozenset({"Uranus", "Pluto"}): {
        "title": "Structural breakthrough",
        "meaning": "Innovation and deep power change combine to make the old arrangement difficult to restore.",
        "opportunity": "replace an obsolete system rather than merely criticising it",
        "risk": "destruction without a stable successor",
    },
    frozenset({"Jupiter", "Neptune"}): {
        "title": "Expanded vision",
        "meaning": "Imagination, faith and reach increase together.",
        "opportunity": "publish, teach or create around a compelling vision",
        "risk": "inflated fantasy, misleading claims or weak due diligence",
    },
    frozenset({"Mars", "Saturn"}): {
        "title": "Force meets resistance",
        "meaning": "Action encounters a limit that demands better timing and technique.",
        "opportunity": "concentrate effort and build endurance",
        "risk": "frustration, injury, hostility or wasted force",
    },
    frozenset({"Venus", "Mars"}): {
        "title": "Attraction and friction",
        "meaning": "Desire and preference are active at the same time, increasing both chemistry and disagreement.",
        "opportunity": "create, negotiate and state what is genuinely wanted",
        "risk": "confusing intensity with compatibility",
    },
}
