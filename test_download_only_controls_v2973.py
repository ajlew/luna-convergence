from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    monthly = (root / "monthly_experience_v1.py").read_text(encoding="utf-8")
    daily = (root / "daily_narrative_v3.py").read_text(encoding="utf-8")

    # Monthly: remove the broken browser-print block; retain one black download.
    assert '<button id="luna-print-report"' not in monthly
    assert "Print or save report" not in monthly
    assert '"Download searchable A4 Monthly PDF"' in monthly
    monthly_download = monthly.split('"Download searchable A4 Monthly PDF"', 1)[1]
    assert 'type="primary"' in monthly_download
    assert 'on_click="ignore"' in monthly_download

    # Daily: do not render either print control; keep both black downloads.
    assert "_daily_print_controls_html(narrative, solar)" not in daily
    assert '"Download Daily Reading PDF"' in daily
    assert '"Download Full Daily + Evidence PDF"' in daily
    assert daily.count('type="primary"') >= 2
    assert daily.count('on_click="ignore"') >= 2

    print("Download-only report control tests passed.")


if __name__ == "__main__":
    main()
