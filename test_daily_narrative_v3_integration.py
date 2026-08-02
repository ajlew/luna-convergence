from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    app = (root / "app.py").read_text(encoding="utf-8")
    module = (root / "daily_narrative_v3.py").read_text(encoding="utf-8")

    assert "from daily_narrative_v3 import" in app
    assert "render_daily_narrative_v3(" in app
    assert "monthly_price=MONTHLY_PRICE" in app
    assert 'monthly_url=f"/reports?sign={sign}"' in app
    assert "Today's convergence" in module
    assert "Why this matters today" in module
    assert "Weather / today" in module
    assert "Climate / longer current" in module
    assert "Sky Snapshot" in module
    assert "Convergence strength" in module
    assert "It is not the probability" in module
    assert "Explainable Astrology" in module
    assert "Editorial translation" not in module
    assert "_story_is_duplicate" in module
    assert "daily-monthly-offer" in module
    assert "HOUSE_RELATIONSHIP_OPENINGS" in module
    assert "_sign_specific_questions" in module
    print("Daily v2.9 customer/technical boundary integration check passed.")


if __name__ == "__main__":
    main()
