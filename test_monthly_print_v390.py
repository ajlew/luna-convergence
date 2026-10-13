from pathlib import Path

def test_natal_page_print_fit_rules():
    source=Path(__file__).with_name("monthly_report_pdf_home_v3.py").read_text()
    assert 'page_bodies.append((natal_page, "natal-overlay-page"))' in source
    assert '.natal-overlay-page .chapter-row {{ min-height:0;' in source
    assert '.natal-overlay-page .natal-chart-print {{ max-width:72mm;' in source
