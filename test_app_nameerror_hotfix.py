from pathlib import Path


def main() -> None:
    app = (Path(__file__).parent / "app.py").read_text(encoding="utf-8")
    assert "HOUSE_VOICE," in app
    assert "HOUSE_VOICE[reading.moon_house]" in app
    print("App NameError hotfix check passed.")


if __name__ == "__main__":
    main()
