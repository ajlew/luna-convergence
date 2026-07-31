from pathlib import Path

from monthly_narrative_v1 import _date_label


def main() -> None:
    assert _date_label("2026-08-01") == "August 1"
    assert _date_label("2026-08-09") == "August 9"
    assert _date_label("2026-08-21") == "August 21"

    source = (
        Path(__file__).parent / "monthly_narrative_v1.py"
    ).read_text(encoding="utf-8")
    assert 'strftime("%B %-d")' not in source

    print("Windows-safe monthly date-format test passed.")


if __name__ == "__main__":
    main()
