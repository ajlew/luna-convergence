from pathlib import Path


def test_lean_daily_landing_v319():
    root = Path(__file__).parent
    app = (root / "app.py").read_text(encoding="utf-8")

    nav_start = app.index("def top_navigation")
    nav_end = app.index("def set_page_metadata", nav_start)
    nav = app[nav_start:nav_end]
    for label in ("Daily Horoscope", "This Month", "House Guide", "Solar Year"):
        assert label in nav
    for hidden_label in ("Reports", "Sample report", "How it works", "Forecast library"):
        assert hidden_label not in nav

    assert 'key="landing-daily-sign"' in app
    assert 'label_visibility="collapsed"' in app
    assert 'reading_date = browser_local_date()' in app
    assert 'timezone_name = browser_timezone_name()' in app
    assert 'class="lean-daily"' in app
    assert 'class="lean-daily-move"' in app
    assert 'class="lean-daily-question"' in app
    assert 'Focus Reset' in app
    assert 'See your August forecast →' in app

    assert "Today's example /" not in app
    assert "Why this is different" not in app
    assert "Learn the twelve houses while you read" not in app
    assert "Read today's free horoscope" not in app

    assert 'url_path="august-2026-horoscopes"' in app
    assert 'def monthly_index_page() -> None:' in app
