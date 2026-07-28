from pathlib import Path


def main() -> None:
    app = (Path(__file__).parent / "app.py").read_text(encoding="utf-8")
    assert "HOUSE_VOICE," in app
    assert "house_voice=HOUSE_VOICE" in app
    assert "render_daily_narrative_v3(narrative)" in app
    print("App HOUSE_VOICE integration check passed.")


if __name__ == "__main__":
    main()
