from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Literal
from luna_life_scenes import (
    domain_command as _domain_command,
    domain_key as _domain_key,
    human_focus as _human_focus,
    life_scene_line as _life_scene_line,
    scene_repository_size,
)


ProductType = Literal["daily", "weekly", "monthly", "yearly", "timing", "natal", "solar"]
VOICE_VERSION = "Luna Narrator v4.0 — Human Scenes + Imperative Contract"


@dataclass(frozen=True)
class LunaVoiceProfile:
    product: ProductType
    narrator_role: str
    purpose: str
    pace: str
    preferred_length: str
    narrator_cues: tuple[str, ...]
    must_do: tuple[str, ...]
    must_not: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


_SHARED_MUST_DO = (
    "Speak directly to the reader in second person: you / your.",
    "Use active voice, concrete verbs and imperative mood when a decision is required.",
    "Identify the human consequence before explaining the astrology.",
    "Connect every interpretation to what came before and what changes next.",
    "Translate planetary structure into recognisable human situations.",
    "Use short sentences, sharp juxtapositions, negative space and grounded emotional realism.",
    "Start or end substantial interpretation with a command.",
    "Keep customer-facing prose visually plain: do not use inline bold to tell the reader what matters.",
    "Pair large emotional or existential stakes with ordinary physical reality when it clarifies the point.",
    "Keep the reader as the decision-maker and author of the next move.",
    "Keep technical evidence behind Why Luna sees this unless the reader asks for it.",
)

_SHARED_MUST_NOT = (
    "Narrate the machinery of the report in customer-facing interpretation.",
    "Use third-person labels such as the reader or this person when speaking about the customer.",
    "Use preambles such as Luna reads, Luna separates, or here is how this connects when the interpretation itself can do the work.",
    "Repeat a headline or idea merely to prove continuity.",
    "Use exclamation points, emojis, enthusiastic adverbs or filler such as just, really, maybe or hope.",
    "Convert third-person templates into second person by pronoun substitution; write the sentence natively for you.",
    "Use passive applicant language such as waiting to be selected.",
    "Frame the reader as waiting, receiving permission or letting the month decide for her.",
    "Repeat technical house descriptions in customer-facing prose.",
    "Use vague spiritual filler or moral judgement.",
    "Promise a guaranteed event or measured probability.",
    "Pretend Luna is a human psychic or speak about Luna's personal life.",
)


VOICE_PROFILES: dict[ProductType, LunaVoiceProfile] = {
    "daily": LunaVoiceProfile(
        product="daily",
        narrator_role="Brutalist Oracle · sharp observer",
        purpose="Identify today's strongest move, emotional consequence and one useful response.",
        pace="Quick, sharp and punchy.",
        preferred_length="One hook, one short interpretation, one Do and one Don't.",
        narrator_cues=("What matters now", "Your move"),
        must_do=_SHARED_MUST_DO + (
            "Lead with the five-second emotional hook.",
            "End before the insight becomes a lecture.",
        ),
        must_not=_SHARED_MUST_NOT + (
            "Build a large plot from one day.",
            "Expose technical evidence before the customer asks for it.",
        ),
    ),
    "monthly": LunaVoiceProfile(
        product="monthly",
        narrator_role="Brutalist Oracle · storyteller",
        purpose="Connect carryover, opening, complication, relationship test, climax and resolution.",
        pace="Narrative, selective and emotionally intelligent.",
        preferred_length="A substantial story with three or four acts, key dates and practical consequences.",
        narrator_cues=("The story", "What changes now", "Your move", "Watch this"),
        must_do=_SHARED_MUST_DO + (
            "Show how one development creates the next.",
            "Give the strongest relationship test its own place when the evidence supports it.",
            "Use concrete scenarios without presenting them as promises.",
        ),
        must_not=_SHARED_MUST_NOT + (
            "Treat the month as unrelated transit notes.",
            "Assign the same planetary cluster to several repetitive story roles.",
        ),
    ),
    "yearly": LunaVoiceProfile(
        product="yearly",
        narrator_role="Brutalist Oracle · strategist",
        purpose="Map the players, board, dominant games, rule changes, twelve rounds and final position.",
        pace="Strategic, panoramic and decisive.",
        preferred_length="Three to five annual acts plus twelve concise monthly moves.",
        narrator_cues=("The year", "What changes", "Your leverage", "Watch this"),
        must_do=_SHARED_MUST_DO + (
            "Explain which planets hold initiative and where the reader has leverage.",
            "Treat months as rounds whose outcomes change later options.",
            "Validate the top-down annual map against all twelve monthly arcs.",
        ),
        must_not=_SHARED_MUST_NOT + (
            "Join twelve monthly reports into one long document.",
            "Give every month equal strategic importance.",
        ),
    ),
}


# The same voice contract applies at different zoom levels.
VOICE_PROFILES["weekly"] = LunaVoiceProfile(
    product="weekly",
    narrator_role="Brutalist Oracle · sequence editor",
    purpose="Show one changing sky across seven days without resetting the story every morning.",
    pace="Compact, causal and selective.",
    preferred_length="One weekly thread plus seven concise moves.",
    narrator_cues=("The week", "What changes", "Your move"),
    must_do=_SHARED_MUST_DO + ("Carry one decision thread across the week.",),
    must_not=_SHARED_MUST_NOT + ("Write seven unrelated miniature horoscopes.",),
)
VOICE_PROFILES["timing"] = LunaVoiceProfile(
    product="timing",
    narrator_role="Brutalist Oracle · personal timing strategist",
    purpose="Connect natal pattern, repeated transits, timing windows and consequences.",
    pace="Personal, strategic and direct.",
    preferred_length="One human annual argument followed by evidence-rich transit chapters.",
    narrator_cues=("The story", "What changes", "Your move"),
    must_do=_SHARED_MUST_DO + ("Tell the human story before the transit catalogue.",),
    must_not=_SHARED_MUST_NOT + ("Use transit titles as a substitute for interpretation.",),
)
VOICE_PROFILES["natal"] = LunaVoiceProfile(
    product="natal",
    narrator_role="Brutalist Oracle · portraitist",
    purpose="Describe one person, not a list of placements.",
    pace="Observant, intimate and unsentimental.",
    preferred_length="A few connected contradictions and behavioural patterns.",
    narrator_cues=("The pattern", "Watch this"),
    must_do=_SHARED_MUST_DO + ("Connect placements into one recognisable human pattern.",),
    must_not=_SHARED_MUST_NOT + ("Write six disconnected placement definitions.",),
)
VOICE_PROFILES["solar"] = LunaVoiceProfile(
    product="solar",
    narrator_role="Brutalist Oracle · natural-clock translator",
    purpose="Translate the solar clock into one grounded life-area emphasis.",
    pace="Brief and concrete.",
    preferred_length="One clock statement and one move.",
    narrator_cues=("The clock", "Your move"),
    must_do=_SHARED_MUST_DO + ("Keep astronomy as context and the human consequence in front.",),
    must_not=_SHARED_MUST_NOT + ("Turn the solar clock into a lecture.",),
)


BANNED_PHRASES = (
    "waiting to be selected",
    "you are not waiting to be selected",
    "everything happens for a reason",
    "the universe guarantees",
    "this will definitely happen",
    "a soulmate is coming",
    "your manifestations are arriving",
    "let the month come toward you",
)


# ---------------------------------------------------------------------------
# GLOBAL CUSTOMER-PROSE LAYER
# Every product should pass reader-facing interpretation through this layer.
# Product engines may differ in scale. The grammatical and editorial contract
# does not.
# ---------------------------------------------------------------------------

_EDITORIAL_SCAFFOLD_SENTENCES = (
    "Start with the argument, not the planets.",
    "Follow the sequence. What opens early changes what you can choose later.",
    "Do not solve each chapter in isolation.",
    "Treat this as continuation, not a separate horoscope.",
    "How this connects:",
    "How this fits the month",
    "How this fits the larger story",
    "Luna reads it as one changing board.",
    "Luna keeps the recurrence calculation behind the scenes.",
)

_TECHNICAL_TO_HUMAN = {
    "Natal Midheaven": "the job, role or public responsibility with your name on it",
    "natal Midheaven": "the job, role or public responsibility with your name on it",
    "Natal Ascendant": "how you show up and what you are willing to carry",
    "natal Ascendant": "how you show up and what you are willing to carry",
    "identity, energy and personal direction": "how you show up and what you are willing to carry",
    "identity and direction": "how you show up and what you are willing to carry",
    "travel, publishing, law, education and foreign markets": "the trip, course, application or outside opportunity in front of you",
    "travel, study and the wider world": "the trip, course, application or outside opportunity in front of you",
    "relationships, clients, contracts and competitors": "the person across the table and the promises between you",
    "relationships and agreements": "the person across the table and the promises between you",
    "work routines, health, service and operations": "the workload and routine your ordinary week has to sustain",
    "work and daily routines": "the workload and routine your ordinary week has to sustain",
    "shared money, debt, tax, inheritance and intimacy": "money, trust and responsibility you share with someone else",
    "shared money and obligations": "money, trust and responsibility you share with someone else",
    "career, public direction, reputation and authority": "the job, role or public responsibility with your name on it",
    "career and authority": "the job, role or public responsibility with your name on it",
    "friends, communities and future plans": "the friends, groups and plans shaping what you build next",
    "friends and future plans": "the friends, groups and plans shaping what you build next",
}

_YOU_GRAMMAR = {
    "you thinks": "you think",
    "you needs": "you need",
    "you acts": "you act",
    "you reacts": "you react",
    "you processes": "you process",
    "you remembers": "you remember",
    "you looks": "you look",
    "you values": "you value",
    "you shows": "you show",
    "you contains": "you contain",
    "you absorbs": "you absorb",
    "you recovers": "you recover",
    "you gains": "you gain",
    "you loses": "you lose",
    "you has": "you have",
    "you is": "you are",
    "you does": "you do",
    "you wants": "you want",
    "you carries": "you carry",
    "you keeps": "you keep",
    "you makes": "you make",
}

_ARC_WORDS = {
    "support": "Build",
    "stabilise": "Set terms",
    "stabilize": "Set terms",
    "define": "Define",
    "decision": "Choose",
    "choose": "Choose",
    "opening": "Open",
    "open": "Open",
    "change": "Change",
    "expand": "Expand",
    "test": "Test",
    "verify": "Check",
    "release": "Release",
    "close": "Close",
    "integrate": "Integrate",
    "protect": "Protect",
    "act": "Act",
}

_DRY_TRUTHS = {
    "work": (
        "A title cannot carry the workload for you.",
        "The inbox will survive a boundary.",
        "A full calendar is not a personality.",
    ),
    "relationship": (
        "Chemistry is not a contract.",
        "Attention is cheap. Consistency costs something.",
        "A good conversation is not yet a good agreement.",
    ),
    "money": (
        "Numbers remain rude enough to be useful.",
        "A budget has no interest in your preferred storyline.",
        "The spreadsheet is less charming than hope and usually more informative.",
    ),
    "routine": (
        "Tuesday morning is where grand plans go for verification.",
        "The body keeps receipts.",
        "A broken routine does not become noble because you endured it.",
    ),
    "uncertainty": (
        "A convincing story still has to survive Tuesday.",
        "Fog is atmospheric. It is not evidence.",
        "The missing fact will not become less missing because the story is elegant.",
    ),
    "general": (
        "The calendar is where possibility becomes a bill.",
        "Reality has an irritating habit of asking for details.",
        "A good idea still has to fit through the front door.",
    ),
}


def _editorial_title_case(value: str) -> str:
    raw = re.sub(r"\s+", " ", str(value or "")).strip()
    letters = "".join(ch for ch in raw if ch.isalpha())
    if not letters or not letters.isupper():
        return raw

    small_words = {
        "a", "an", "and", "as", "at", "but", "by", "for", "in",
        "nor", "of", "on", "or", "the", "to", "up", "via", "with",
    }
    words = raw.lower().split()
    result = []
    for index, word in enumerate(words):
        core = re.sub(r"[^a-z]", "", word)
        if index not in {0, len(words) - 1} and core in small_words:
            result.append(word)
        else:
            result.append(word[:1].upper() + word[1:])
    return " ".join(result)


def inline_story_title(value: str) -> str:
    """Use Title Case when a standalone ALL-CAPS story title enters prose."""
    return _editorial_title_case(value)


def simplify_life_area(value: str) -> str:
    raw = re.sub(r"\s+", " ", str(value or "")).strip()
    if raw in _TECHNICAL_TO_HUMAN:
        return _TECHNICAL_TO_HUMAN[raw]
    return _human_focus(raw)


def life_domain(value: str) -> str:
    """Return Luna's ordinary-life domain key without exposing house taxonomy."""
    return _domain_key(value)


def life_scene(value: str, seed_text: str = "", count: int = 2) -> str:
    """Ground an abstract life area in conditional ordinary-life scenes."""
    return _life_scene_line(value, seed_text=seed_text, count=count)


def imperative_for(value: str, seed_text: str = "") -> str:
    """Return one stable domain-specific command."""
    return _domain_command(value, seed_text=seed_text)


def convergent_bridge(
    current_area: str,
    *,
    seed_text: str = "",
    include_scene: bool = True,
) -> str:
    """One global bridge: command first, ordinary life second. No report narration."""
    command = imperative_for(current_area, seed_text=seed_text)
    if not include_scene:
        return command
    scene = life_scene(current_area, seed_text=seed_text, count=1)
    return f"{command} {scene}".strip()



def human_arc(values) -> tuple[str, ...]:
    """Translate engine-state labels into a short human sequence."""
    result = []
    for value in values or ():
        raw = str(value or "").strip()
        if not raw:
            continue
        key = raw.lower()
        human = _ARC_WORDS.get(key, raw.title() if raw.isupper() else raw)
        if not result or result[-1].lower() != human.lower():
            result.append(human)
    return tuple(result[:5])


def human_arc_sentence(values) -> str:
    """Turn engine-state arrows into short human commands."""
    arc = human_arc(values)
    commands = {
        "Build": "Build what has support.",
        "Set terms": "Set the terms.",
        "Define": "Define the responsibility.",
        "Choose": "Choose what deserves more time.",
        "Open": "Use the opening.",
        "Change": "Change what no longer fits.",
        "Expand": "Expand only what your actual life can carry.",
        "Test": "Test what survives ordinary life.",
        "Check": "Check the facts.",
        "Release": "Release what is finished.",
        "Close": "Close the loop.",
        "Integrate": "Make the change liveable.",
        "Protect": "Protect what has to last.",
        "Act": "Act while the opening is usable.",
    }
    return " ".join(commands.get(item, f"{item}.") for item in arc)


def luna_dry_truth(topic: str = "general", seed_text: str = "") -> str:
    """Return one stable dry observation. Humour stays sparse and grounded."""
    key = str(topic or "general").strip().lower()
    bank = _DRY_TRUTHS.get(key, _DRY_TRUTHS["general"])
    seed = sum(ord(ch) for ch in str(seed_text or key))
    return bank[seed % len(bank)]


def _titlecase_inline_caps(text: str) -> str:
    # Two or more all-cap words inside prose are treated as a story/reference,
    # not as an acronym. Standalone headings are rendered separately and do not
    # pass through customer-prose finalisation.
    pattern = re.compile(r"\b(?:[A-Z][A-Z'’\-]*\s+){1,}[A-Z][A-Z'’\-]*\b")
    return pattern.sub(lambda match: _editorial_title_case(match.group(0)), text)


def finalize_customer_prose(
    value: str,
    product: ProductType | str = "timing",
) -> str:
    """Apply Luna's global reader-facing prose contract.

    This function deliberately performs conservative editorial normalisation.
    It does not invent astrology or rewrite the underlying calculation.
    """
    text = str(value or "")
    text = text.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    text = text.replace("**", "").replace("__", "")

    for phrase in _EDITORIAL_SCAFFOLD_SENTENCES:
        text = text.replace(phrase, " ")

    for technical, human in _TECHNICAL_TO_HUMAN.items():
        text = text.replace(technical, human)

    ordinary_replacements = (
        ("preserve optionality", "keep the hard-to-reverse part open"),
        ("Preserve optionality", "Keep the hard-to-reverse part open"),
        ("until this pressure separates", "until the immediate pressure passes"),
        ("until the pressure separates", "until the immediate pressure passes"),
        ("partnership energy", "the connection"),
        ("Partnership energy", "The connection"),
        ("future plans", "what you are building next"),
        ("shared obligations", "what you share or owe"),
        ("career and authority", "the job and responsibility"),
        ("public direction", "public responsibility"),
    )
    for old, new in ordinary_replacements:
        text = text.replace(old, new)

    # Remove staging language that tells the reader how the paragraph was assembled.
    text = re.sub(r"(^|(?<=[.!?])\s+)(?:This is where|This is when)\s+", r"\1", text, flags=re.I)

    # Keep the voice active and second-person where legacy templates leaked
    # third-person verb endings.
    lowered = text.lower()
    for wrong, right in _YOU_GRAMMAR.items():
        if wrong in lowered:
            text = re.sub(re.escape(wrong), right, text, flags=re.I)
            lowered = text.lower()

    # Remove exuberant punctuation. Luna does not shout.
    text = text.replace("!", ".")

    text = _titlecase_inline_caps(text)

    # Strip obvious meta-narration that survived old templates.
    text = re.sub(r"\bLuna (?:reads|separates|therefore combines|keeps)\b[^.]*\.\s*", "", text, flags=re.I)
    text = re.sub(r"\bthe reader-facing question is simpler:?\s*", "", text, flags=re.I)
    text = re.sub(r"\bthe current report ranks the transit as\b", "Treat this as", text, flags=re.I)
    text = re.sub(
        r"You have already been dealing with\s+(.+?)\.\s+Now the pressure reaches\s+(.+?)\.",
        r"Carry the standard forward. Act on \2.",
        text,
        flags=re.I,
    )
    text = re.sub(r"\bthe reader\b", "you", text, flags=re.I)
    text = re.sub(r"\bthis person\b", "you", text, flags=re.I)

    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"([.!?])\s*([.!?])+", r"\1", text)
    text = text.strip(" \n\t")

    return text

def voice_profile(product: ProductType) -> LunaVoiceProfile:
    return VOICE_PROFILES[product]


def narrator_cue(product: ProductType, index: int = 0) -> str:
    cues = VOICE_PROFILES[product].narrator_cues
    return cues[index % len(cues)]


def validate_luna_voice(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    return tuple(phrase for phrase in BANNED_PHRASES if phrase in lowered)


def narrator_principle() -> str:
    return (
        "Speak to the human. Connect the pattern. Name the consequence. "
        "Give the reader a clean move."
    )
