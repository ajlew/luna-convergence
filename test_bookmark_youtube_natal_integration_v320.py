from pathlib import Path

APP = Path(__file__).with_name("app.py").read_text(encoding="utf-8")


def test_daily_sign_is_bookmarkable_without_exposing_birth_data():
    assert 'st.query_params["sign"] = sign_slug(sign)' in APP
    assert 'Bookmark this page in your browser and Luna will reopen on' in APP
    natal_start = APP.index("def natal_snapshot_page() -> None:")
    natal_end = APP.index("\ndef solar_year_page() -> None:", natal_start)
    natal = APP[natal_start:natal_end]
    assert 'st.query_params[' not in natal


def test_youtube_is_optional_and_does_not_clutter_empty_daily():
    assert 'LUNA_YOUTUBE_FEATURED_VIDEO_URL = secret("LUNA_YOUTUBE_FEATURED_VIDEO_URL")' in APP
    assert 'if not LUNA_YOUTUBE_FEATURED_VIDEO_URL:' in APP
    assert 'st.video(LUNA_YOUTUBE_FEATURED_VIDEO_URL)' in APP
    assert 'LUNA_YOUTUBE_CHANNEL_URL = secret("LUNA_YOUTUBE_CHANNEL_URL")' in APP


def test_free_natal_snapshot_route_is_hidden_from_primary_navigation():
    assert 'url_path="natal-snapshot"' in APP
    assert 'title="Free Natal Snapshot"' in APP
    assert 'visibility="hidden"' in APP
    nav_start = APP.index("def top_navigation(current_path: str) -> None:")
    nav_end = APP.index("\ndef set_page_metadata", nav_start)
    nav = APP[nav_start:nav_end]
    assert 'Natal Snapshot' not in nav
