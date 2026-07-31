from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    config = (root / "site_config.py").read_text(encoding="utf-8")
    app = (root / "app.py").read_text(encoding="utf-8")

    expected = 'TAGLINE = "The universe shifts. You’ve got this."'
    assert expected in config
    assert "from site_config import" in app
    assert "TAGLINE" in app
    assert "Understand what is changing—and what to do with it." not in config

    print("Luna tagline update test passed.")


if __name__ == "__main__":
    main()
