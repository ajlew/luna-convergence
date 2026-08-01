from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    app = (root / "app.py").read_text(encoding="utf-8")
    daily = (root / "daily_narrative_v3.py").read_text(
        encoding="utf-8"
    )

    # Sparse default view.
    assert 'class="daily-primary"' in daily
    assert "LUNA_SAYS_LABEL" in daily
    assert 'class="do-dont-strip"' in daily
    assert "DO_LABEL" in daily
    assert "DONT_LABEL" in daily
    assert "Today's convergence" in daily
    assert 'class="daily-hook-headline"' in daily
    assert "narrative.hook_headline" in daily
    assert "Today's theme" in daily
    assert "narrative.hook_subline" in daily
    assert "visible_story = tuple(narrative.today_story[:2])" in daily

    # All prior work remains available.
    assert "st.expander(WHY_LUNA_LABEL)" in daily
    assert "Why this matters today" in daily
    assert "Weather / today" in daily
    assert "Climate / longer current" in daily
    assert "Hidden opportunity" in daily
    assert "Solar position" in daily
    assert "Sky Snapshot" in daily
    assert 'st.expander("Questions to consider")' in daily
    assert "st.expander(TECHNICAL_LABEL)" in daily
    assert "The 12-house reference matrix" in daily
    assert "Explainable Astrology" in daily

    # Stability.
    assert 'with st.form(' in app
    assert '"daily-reading-settings"' in app
    assert '"active_daily_request"' in app
    assert "st.rerun()" in app
    assert "def _daily_solar_snapshot" in app
    assert "cache_key = (sign, reading_date.isoformat(), timezone_name)" in app

    # Mobile fill and overflow protection.
    assert "overflow-x:hidden !important" in app
    assert "min-height:100dvh" in app
    assert "env(safe-area-inset-bottom" in app
    assert 'class="mobile-nav"' in app
    assert ".top-nav {" in app
    assert "flex:1 1 100% !important" in app

    # Purchase journey remains available without filling the page.
    assert 'with st.expander("Want the wider monthly story?"' in app
    assert 'context=f"daily-{sign.lower()}"' in app

    print("Sparse mobile daily presentation checks passed.")


if __name__ == "__main__":
    main()
