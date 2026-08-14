from pathlib import Path

APP = Path(__file__).with_name("app.py").read_text(encoding="utf-8")


def _landing_source() -> str:
    start = APP.index("def _render_lean_daily(path: str) -> None:")
    end = APP.index("\n\ndef home_page() -> None:", start)
    return APP[start:end]


def test_daily_selector_starts_neutral_without_saved_or_bookmarked_sign():
    source = _landing_source()
    assert 'saved_sign = st.session_state.get("landing-daily-sign-v3195") or _query_daily_sign()' in source
    assert 'saved_index = SIGNS.index(saved_sign) if saved_sign in SIGNS else None' in source
    assert 'index=saved_index' in source
    assert 'placeholder="Choose your star sign"' in source
    assert 'key="landing-daily-sign-v3195"' in source
    assert 'persist_state="session"' in source
    assert 'if sign is None:' in source
    assert 'Choose your star sign to open today' in source


def test_no_default_sagittarius_daily_is_generated_before_choice():
    source = _landing_source()
    selector_end = source.index('if sign is None:')
    selector_source = source[:selector_end]
    assert 'SIGNS.index(DEFAULT_SIGN)' not in selector_source
    assert 'free_daily_reading(' not in selector_source


def test_sign_choice_remains_the_engagement_event():
    source = _landing_source()
    guard = source.index('if sign is None:')
    event = source.index('"daily_reading_generated"')
    assert event > guard
