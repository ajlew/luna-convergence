from dataclasses import dataclass
from pathlib import Path

from birthday_card_voice import (
    BirthdayPoemError,
    build_birthday_poem_facts,
    facts_hash,
    generate_birthday_poem,
    validate_birthday_poem,
)


@dataclass(frozen=True)
class _Position:
    planet: str
    sign: str
    degree: float


@dataclass(frozen=True)
class _Aspect:
    planet1: str
    planet2: str
    name: str
    orb: float
    strength: float


@dataclass(frozen=True)
class _Snapshot:
    positions: tuple[_Position, ...]
    aspects: tuple[_Aspect, ...]
    birth_time_known: bool
    sun_uncertain: tuple[str, ...]
    moon_uncertain: tuple[str, ...]


def _snapshot(known: bool) -> _Snapshot:
    return _Snapshot(
        positions=(
            _Position("Sun", "Virgo", 28.42),
            _Position("Moon", "Libra", 8.75),
        ),
        aspects=(_Aspect("Sun", "Moon", "sextile", 0.4, 2.0),),
        birth_time_known=known,
        sun_uncertain=() if known else ("Virgo",),
        moon_uncertain=() if known else ("Libra",),
    )


def test_unknown_time_excludes_unsafe_degrees_and_aspects():
    facts = build_birthday_poem_facts(
        snapshot=_snapshot(False),
        variation_key="case-one",
    )
    assert facts["sun_sign_options"] == ["Virgo"]
    assert facts["moon_sign_options"] == ["Libra"]
    assert facts["exact_positions"] is None
    assert facts["strongest_luminary_aspects"] == []


def test_known_time_includes_exact_calculated_evidence():
    facts = build_birthday_poem_facts(
        snapshot=_snapshot(True),
        variation_key="case-two",
    )
    assert facts["exact_positions"]["Sun"] == {"sign": "Virgo", "degree": 28.42}
    assert facts["strongest_luminary_aspects"][0]["aspect"] == "sextile"


def test_generated_poem_must_echo_the_closed_evidence_contract():
    facts = build_birthday_poem_facts(
        snapshot=_snapshot(False),
        variation_key="case-three",
    )

    def fake_generate(_prompt, **_kwargs):
        return {
            "facts_hash": facts_hash(facts),
            "sun_evidence": ["Virgo"],
            "moon_evidence": ["Libra"],
            "poem": "Careful hands only shape the quiet harmony waiting to become visible.",
        }

    poem = generate_birthday_poem(facts, generate_json=fake_generate)
    assert poem == "Careful hands only shape the quiet harmony waiting to become visible."


def test_wrong_hash_or_astrology_jargon_is_rejected():
    facts = build_birthday_poem_facts(
        snapshot=_snapshot(False),
        variation_key="case-four",
    )
    payload = {
        "facts_hash": "wrong",
        "sun_evidence": ["Virgo"],
        "moon_evidence": ["Libra"],
        "poem": "Careful hands only shape the quiet harmony waiting to become visible.",
    }
    try:
        validate_birthday_poem(payload, facts)
    except BirthdayPoemError:
        pass
    else:
        raise AssertionError("A mismatched facts hash must be rejected.")

    payload["facts_hash"] = facts_hash(facts)
    payload["poem"] = "Virgo only reveals the quiet harmony waiting to become beautifully visible."
    try:
        validate_birthday_poem(payload, facts)
    except BirthdayPoemError:
        pass
    else:
        raise AssertionError("Astrology jargon must be rejected.")


def test_no_fixed_sign_pair_sentence_tables_remain():
    source = Path(__file__).with_name("birthday_card.py").read_text(encoding="utf-8")
    assert "SUN_WORD" not in source
    assert "MOON_ENDING" not in source
    assert "suggested_poem" not in source
