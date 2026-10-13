from pathlib import Path
from monthly_shared_view import build_monthly_shared_html, html_to_pdf

def test_strengths_match_screen_and_pdf():
    params=dict(title='October',label='Libra',intro='A monthly test',paragraphs=['October narrative.'],
        natal_pattern='Your Sun and Moon describe the natal foundation.',
        natal_strengths=[{'evidence':'Sun trine Moon · 0.5°','title':'Coordinating intention and instinct',
                          'text':'Use your deliberate response.','remember':'Remember the tension and the opportunity.'}],
        natal_svg='<svg viewBox="0 0 20 20"></svg>')
    web=build_monthly_shared_html(**params,full_document=False)
    download=build_monthly_shared_html(**params)
    for phrase in ('Your natal foundation','Read the pattern','Your strengths', 'Sun trine Moon',
                   'Coordinating intention and instinct','Read the month','Your natal activation'):
        assert phrase in web and phrase in download
    assert web.index('Your strengths') < web.index('Read the month')
    assert download.index('Your strengths') < download.index('Read the month')
    assert html_to_pdf(download)[:4] == b'%PDF'

def test_owner_and_paid_paths_use_one_strengths_source():
    source=(Path(__file__).parent/'app.py').read_text()
    assert '"natal_strengths": natal_strengths' in source
    assert source.count('build_monthly_shared_html(**_monthly_shared_assets(') == 2
    assert 'st.markdown(build_monthly_shared_html(**shared, full_document=False)' in source
