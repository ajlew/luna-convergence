from datetime import date

from astrology_engine import Event
from monthly_decision_engine import evaluate_monthly_decision, validate_monthly_decision
from monthly_report_pipeline import build_production_monthly_report


def _event(day, title, polarity, houses=(10,), planets=("Saturn",), importance=8.5, kind="aspect"):
    return Event(
        event_date=date(2030, 1, day),
        kind=kind,
        title=title,
        detail="test",
        importance=importance,
        planets=tuple(planets),
        houses=tuple(houses),
        polarity=polarity,
    )


def test_truth_gate_can_advance_hold_pass_question_and_negotiate():
    weights = {1: 80.0, 4: 70.0, 10: 100.0}
    arc = {"primary_house": 10, "secondary_house": 4, "tertiary_house": 1}

    advance = evaluate_monthly_decision(
        sign="Sagittarius",
        events=[
            _event(2, "Jupiter trine Sun", "opportunity", houses=(10,), planets=("Jupiter", "Sun"), importance=9.0),
            _event(8, "Venus sextile Jupiter", "opportunity", houses=(10,), planets=("Venus", "Jupiter"), importance=8.0),
        ],
        monthly_arc=arc,
        house_weights=weights,
    ).to_dict()
    assert advance["posture"] == "ADVANCE"
    assert advance["action_truth"] == "ACT"

    hold = evaluate_monthly_decision(
        sign="Sagittarius",
        events=[
            _event(2, "Saturn square Mars", "pressure", planets=("Saturn", "Mars"), importance=9.0),
            _event(5, "Mars square Neptune", "pressure", planets=("Mars", "Neptune"), importance=9.0),
            _event(8, "Mercury stations retrograde", "review", planets=("Mercury",), importance=8.5, kind="station"),
        ],
        monthly_arc=arc,
        house_weights=weights,
    ).to_dict()
    assert hold["action_truth"] == "NOT ACT"
    assert hold["posture"] in {"HOLD", "PASS"}

    negotiate = evaluate_monthly_decision(
        sign="Sagittarius",
        events=[
            _event(2, "Jupiter sextile Sun", "opportunity", houses=(10,), planets=("Jupiter", "Sun"), importance=7.5),
            _event(9, "Saturn square Venus", "pressure", houses=(4,), planets=("Saturn", "Venus"), importance=9.5),
        ],
        monthly_arc=arc,
        house_weights=weights,
    ).to_dict()
    assert negotiate["action_truth"] == "NOT ACT"
    assert negotiate["posture"] in {"NEGOTIATE", "HOLD"}

    assert validate_monthly_decision(advance)["status"] == "pass"


def test_romance_not_material_gets_comedic_luna_line():
    decision = evaluate_monthly_decision(
        sign="Sagittarius",
        events=[_event(2, "Saturn square Mars", "pressure", houses=(10,), planets=("Saturn", "Mars"), importance=9.0)],
        monthly_arc={"primary_house": 10, "secondary_house": 4, "tertiary_house": None},
        house_weights={10: 100.0, 4: 80.0, 5: 20.0, 7: 15.0},
    ).to_dict()
    romance = decision["domain_decisions"]["romance"]
    assert romance["relevance"] == "NOT MATERIAL"
    assert romance["posture"] == "PASS"
    assert "Maybe next month" in romance["luna_line"]
    assert "Work" in romance["luna_line"]


def test_2017_historical_path_uses_truth_gate_and_full_narrative():
    narrative, result = build_production_monthly_report(
        sign="Sagittarius",
        year=2017,
        month=9,
        timezone_name="Australia/Sydney",
        nearest_city="Sydney",
    )
    assert result["monthly_decision"]["action_truth"] in {"ACT", "NOT ACT"}
    assert result["monthly_decision"]["posture"] in {"ADVANCE", "QUESTION", "NEGOTIATE", "HOLD", "PASS"}
    assert len(narrative.chapters) >= 3
    assert narrative.strategic_posture == result["monthly_decision"]["posture"]
    assert len(narrative.action_plan) == 3
