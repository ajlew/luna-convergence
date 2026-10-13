from pathlib import Path
from monthly_shared_view import build_monthly_shared_html, html_to_pdf
ROOT=Path(__file__).resolve().parent

def test_single_monthly_export_source():
    source=(ROOT/'app.py').read_text()
    assert 'build_monthly_homepage_pdf(' not in source
    assert 'build_monthly_homepage_html(' not in source
    assert source.count('build_monthly_shared_html(**_monthly_shared_assets(') == 2
    assert 'st.markdown(build_monthly_shared_html(**shared, full_document=False)' in source

def test_shared_html_pdf_and_legacy_removal():
    data=dict(title='October choices',label='Libra October',intro='An opening.',paragraphs=['One unique story paragraph.', 'Second paragraph.'],
              natal_svg='<svg viewBox="0 0 10 10"></svg>', activation_svg='<svg viewBox="0 0 10 10"></svg>',
              contacts=[('10 Oct','Mars square natal Moon')],key_dates=[('11 Oct','New Moon')],evidence=['11 October 2026 · New Moon'],reference='LC-TEST')
    doc=build_monthly_shared_html(**data)
    screen=build_monthly_shared_html(**data,full_document=False)
    for text in ('One unique story paragraph.','Mars square natal Moon','New Moon','Your natal activation','LC-TEST'):
        assert text in doc and text in screen
    assert doc.count('One unique story paragraph.')==1
    for legacy in ('TRUTH GATE','PORTFOLIO STRATEGY','ROMANCE HIERARCHY','Solar Convergence evidence','The Sun sets the annual clock'):
        assert legacy not in doc
    pdf=html_to_pdf(doc)
    assert pdf[:4]==b'%PDF' and len(pdf)>3000

def test_cannot_export_without_story():
    import pytest
    with pytest.raises(ValueError):
        build_monthly_shared_html(title='',label='',intro='',paragraphs=[])
