from pathlib import Path

from date_display import human_date, human_date_range
from monthly_narrative_v1 import _date_label, _date_range


def main() -> None:
    assert human_date("2026-07-01") == "1 July 2026"
    assert human_date("2026-08-09") == "9 August 2026"
    assert human_date_range("2026-07-01", "2026-07-10") == "1-10 July 2026"
    assert human_date_range("2026-06-28", "2026-07-02") == "28 June-2 July 2026"
    assert _date_label("2026-08-01") == "1 August 2026"
    assert _date_range("2026-08-01", "2026-08-21") == "1-21 August 2026"

    source = (Path(__file__).parent / "monthly_narrative_v1.py").read_text(encoding="utf-8")
    assert 'strftime("%B %-d")' not in source

    print("Day-month-year customer date-format test passed.")


if __name__ == "__main__":
    main()
