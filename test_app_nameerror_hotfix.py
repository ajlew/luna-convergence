from pathlib import Path


def main() -> None:
    app = (Path(__file__).parent / "app.py").read_text(encoding="utf-8")
    assert "HOUSE_VOICE," in app
    assert "house_voice=HOUSE_VOICE" in app
    assert "render_daily_narrative_v3(" in app
    assert "monthly_price=MONTHLY_PRICE" in app
    print("App HOUSE_VOICE and Daily v2.9 integration check passed.")


if __name__ == "__main__":
    main()
