from pathlib import Path


ROOT = Path(__file__).resolve().parent
APP_SOURCE = (ROOT / "app.py").read_text(encoding="utf-8")
CONFIG_SOURCE = (ROOT / "site_config.py").read_text(encoding="utf-8")


def test_public_weekly_view_is_in_navigation():
    assert '("weekly-view", "Weekly View")' in APP_SOURCE
    assert 'url_path="weekly-view"' in APP_SOURCE
    assert "WEEKLY_PAGE_REF" in APP_SOURCE
    assert '"Weekly View"' in CONFIG_SOURCE


def test_weekly_studio_stays_hidden_and_contains_production_controls():
    studio_ref = APP_SOURCE.split("WEEKLY_STUDIO_REF = st.Page(", 1)[1].split(")", 1)[0]
    assert 'url_path="weekly-studio"' in studio_ref
    assert 'visibility="hidden"' in studio_ref
    assert "Download all seven scripts" in APP_SOURCE
    assert "Download 1080 × 1920 background" in APP_SOURCE
    assert "Print or save the week" in APP_SOURCE
    assert 'key="weekly-studio-copy-day-v3291"' in APP_SOURCE
    studio_source = APP_SOURCE.split("def weekly_studio_page()", 1)[1].split(
        "def render_monthly_preview_workspace()", 1
    )[0]
    assert "with st.expander(" not in studio_source


def test_weekly_background_is_exact_vertical_master():
    from PIL import Image

    background = ROOT / "assets" / "luna_weekly_video_background_1080x1920.png"
    assert background.exists()
    with Image.open(background) as image:
        assert image.size == (1080, 1920)
