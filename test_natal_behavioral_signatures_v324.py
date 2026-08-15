from datetime import date, time

from natal_snapshot import build_natal_snapshot


def _alotau_snapshot():
    return build_natal_snapshot(
        birth_date=date(1965, 12, 1),
        birth_time_known=True,
        birth_time=time(2, 0),
        timezone_name="UTC",
        location_name="Alotau, Papua New Guinea",
        latitude=-10.3167,
        longitude=150.4667,
    )


def test_personal_aspects_outrank_tight_generational_aspects():
    snapshot = _alotau_snapshot()
    titles = [item.title for item in snapshot.signatures]

    assert titles[0] == "Emotionally reserved"
    assert "What you want and what you need can pull apart" in titles
    assert "Achievement asks for patience" in titles
    assert "Your ideas become personal" in titles
    assert all("Uranus" not in item.evidence or "Pluto" not in item.evidence for item in snapshot.signatures)


def test_emotionally_reserved_signature_is_grounded_in_moon_saturn():
    snapshot = _alotau_snapshot()
    signature = next(item for item in snapshot.signatures if item.title == "Emotionally reserved")

    assert "Moon conjunction Saturn" in signature.evidence
    assert "trust" in signature.text.lower()
    assert "emotional endurance" in signature.strength.lower()
    assert "isolation" in signature.watch.lower()
    assert signature.question


def test_signature_count_stays_compact():
    snapshot = _alotau_snapshot()
    assert 1 <= len(snapshot.signatures) <= 4
