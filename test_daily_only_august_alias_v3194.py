from pathlib import Path

APP = Path(__file__).with_name("app.py").read_text(encoding="utf-8")


def _monthly_index_source() -> str:
    start = APP.index("def monthly_index_page() -> None:")
    end = APP.index("\n\nAUGUST_2026_PREVIEW_HOOKS = {", start)
    return APP[start:end]


def _nav_source() -> str:
    start = APP.index("def top_navigation(current_path: str) -> None:")
    end = APP.index("\n\ndef set_page_metadata", start)
    return APP[start:end]


def test_august_legacy_url_is_daily_only():
    source = _monthly_index_source()
    assert '_render_lean_daily("/august-2026-horoscopes")' in source
    for forbidden in (
        "monthly_seo_data(sign)",
        "build_monthly_narrative",
        "Get the complete August report",
        "report_cta(",
        "sign-grid",
        "Monthly horoscope library",
    ):
        assert forbidden not in source


def test_august_alias_is_marked_as_daily_in_navigation():
    nav = _nav_source()
    assert 'path in {"", "daily-horoscope", "august-2026-horoscopes"}' in nav
    assert 'nav_path = ""' in nav


def test_this_month_links_to_selected_sign_monthly_page():
    nav = _nav_source()
    assert 'monthly_path = f"august-2026-{sign_slug(remembered_sign)}"' in nav
    assert '(monthly_path, "This Month")' in nav
    assert 'label == "This Month" and nav_path == "this-month"' in nav
