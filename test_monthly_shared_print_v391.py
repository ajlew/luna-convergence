"""Regression checks without any live Groq requests."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def test_paid_monthly_shares_voice_across_download_and_screen():
    app=(ROOT/'app.py').read_text()
    assert app.count('monthly_story = _paid_monthly_longform(narrative, result, paid_snapshot)') == 2
    assert 'prebuilt_story=monthly_story' in app
    assert 'prebuilt_story=output.get("story")' in app
    assert 'story=monthly_story' in app

def test_monthly_activation_visible_without_expander():
    app=(ROOT/'app.py').read_text()
    start=app.index('def _render_snapshot_monthly_report(')
    fragment=app[start:app.index('def natal_snapshot_page()',start)]
    assert fragment.index('st.markdown("## Your natal activation")') < fragment.index('with st.expander("Slower planets')
    assert fragment.count('_monthly_activation_wheel_svg(')==1

def test_html_pdf_uses_same_story_and_real_page_counter():
    pdf=(ROOT/'monthly_report_pdf_home_v3.py').read_text()
    assert 'story: dict | None = None' in pdf
    assert 'if story_page:' in pdf
    assert 'content: counter(page)' in pdf
    assert 'refusing to deliver a PDF without the paid interpretation' in pdf
