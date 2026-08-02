from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    app = (root / "app.py").read_text(encoding="utf-8")
    daily = (root / "daily_narrative_v3.py").read_text(encoding="utf-8")

    assert 'class="daily-primary"' in daily
    assert "LUNA_SAYS_LABEL" in daily
    assert 'class="do-dont-strip"' in daily
    assert "Today's convergence" in daily
    assert 'class="daily-hook-headline"' in daily
    assert "visible_story = tuple(narrative.today_story[:2])" in daily
    assert "_story_is_duplicate" in daily

    assert "st.expander(WHY_LUNA_LABEL, expanded=False)" in daily
    assert "Why this matters today" in daily
    assert "Weather / today" in daily
    assert "Climate / longer current" in daily
    assert "Hidden opportunity" in daily
    assert "Solar position" in daily
    assert "Sky Snapshot" in daily
    assert 'st.expander("Questions to consider", expanded=False)' in daily
    assert "st.expander(TECHNICAL_LABEL, expanded=False)" in daily
    assert "The 12-house reference matrix" in daily
    assert "### Planetary positions" in daily
    assert "Editorial translation" not in daily

    assert 'with st.form(' in app
    assert '"daily-reading-settings"' in app
    assert '"active_daily_request"' in app
    assert "st.rerun()" in app
    assert "def _daily_solar_snapshot" in app

    assert "overflow-x:hidden !important" in app
    assert "min-height:100dvh" in app
    assert "env(safe-area-inset-bottom" in app
    assert 'class="mobile-nav"' in app
    assert ".top-nav {" in app
    assert "flex:1 1 100% !important" in app

    assert "daily-monthly-offer" in daily
    assert "Choose my monthly report" in daily
    assert "Want the wider monthly story?" not in app

    print("Sparse iPhone-safe Daily v2.9 presentation checks passed.")


if __name__ == "__main__":
    main()
