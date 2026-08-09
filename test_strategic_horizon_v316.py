from datetime import date

from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report


def main() -> None:
    result = period_report(
        "Cancer",
        date(2026, 8, 1),
        date(2026, 8, 31),
        "Australia/Sydney",
        "August 2026",
        transition_count=12,
        nearest_city="Sydney",
        main_focus="General overview",
    )
    horizon = result.get("problem_horizon") or {}
    assert horizon.get("problem")
    assert horizon.get("if_ignored")
    assert horizon.get("highest_leverage_move")
    assert horizon.get("timing")
    forces = horizon.get("forces") or []
    assert forces
    assert any(item.get("planet") == "Jupiter" for item in forces)
    assert any(item.get("planet") == "Saturn" for item in forces)
    for force in forces:
        for key in (
            "problem",
            "if_ignored",
            "leverage",
            "active_since",
            "peak",
            "changes",
            "structural_shift",
        ):
            assert force.get(key), (force.get("planet"), key)

    narrative = build_monthly_narrative(result)
    html = build_monthly_experience_html(narrative, result, show_print=False)
    assert "The problem" in html
    assert "If you ignore it" in html
    assert "Long shift" in html
    assert "What keeps this active" in html
    assert "How long this stays live" in html
    assert "game theory" not in html.lower()
    assert "terms of the game" not in html.lower()
    assert "equilibrium" not in html.lower()
    print("Strategic Horizon v3.16 tests passed.")


if __name__ == "__main__":
    main()
