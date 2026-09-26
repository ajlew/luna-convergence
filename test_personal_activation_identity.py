import pytest

from major_event_registry import group_serialized_personal_activations


def _activation(
    source_event_id: str,
    display_label: str,
    natal_target: str,
    personal_score: float,
) -> dict:
    return {
        "source_event_id": source_event_id,
        "event_date": "2026-09-27",
        "display_label": display_label,
        "event_class": "lunation",
        "tier": "A",
        "sky_score": 90.0,
        "personal_score": personal_score,
        "combined_score": personal_score,
        "transit_planet": "Moon",
        "natal_target": natal_target,
        "aspect": "conjunction",
        "orb": 0.5,
        "focus": "test focus",
        "interpretation": "test interpretation",
        "action": "test action",
        "opportunity": False,
    }


def test_same_source_event_id_forms_one_personal_activation_group():
    """Presentation labels must not split one astronomical event."""

    source_id = "2026-09-27|lunation|full-moon-in-aries"

    values = [
        _activation(
            source_id,
            "Full Moon in Aries",
            "Sun",
            88.0,
        ),
        _activation(
            source_id,
            "Aries Full Moon",
            "Moon",
            82.0,
        ),
    ]

    groups = group_serialized_personal_activations(values)

    assert len(groups) == 1
    assert len(groups[0]) == 2
    assert {
        item["source_event_id"]
        for item in groups[0]
    } == {source_id}


def test_different_source_event_ids_form_different_groups():
    """Different calculated sky events must remain separate."""

    values = [
        _activation(
            "2026-09-27|lunation|full-moon-in-aries",
            "Same presentation label",
            "Sun",
            88.0,
        ),
        _activation(
            "2026-09-27|aspect|jupiter|mercury|sextile",
            "Same presentation label",
            "Moon",
            82.0,
        ),
    ]

    groups = group_serialized_personal_activations(values)

    assert len(groups) == 2

    ids = {
        group[0]["source_event_id"]
        for group in groups
    }

    assert ids == {
        "2026-09-27|lunation|full-moon-in-aries",
        "2026-09-27|aspect|jupiter|mercury|sextile",
    }


def test_serialized_personal_activation_requires_source_event_id():
    """Serialized downstream data must not reconstruct identity from labels."""

    value = _activation(
        "2026-09-27|lunation|full-moon-in-aries",
        "Full Moon in Aries",
        "Sun",
        88.0,
    )
    value.pop("source_event_id")

    with pytest.raises(
        ValueError,
        match="canonical source_event_id",
    ):
        group_serialized_personal_activations([value])
