from monthly_shared_view import build_monthly_shared_html, html_to_pdf
from pypdf import PdfReader
from io import BytesIO

def test_full_natal_signature_recurring_and_rest_of_month():
    kwargs=dict(title='Heading',label='This month',intro='Intro',paragraphs=['Actual saved story.'],
        natal_pattern='Whole chart reading covering personal planets.',
        natal_signature=[('Sun','Gemini'),('Moon','Capricorn'),('Rising','Not calculated'),('Dominant element','Earth'),('Dominant mode','Cardinal'),('Midheaven','Not calculated')],
        natal_recurring={'headline':'Mars and Venus set the strongest recurring pattern',
                         'opening':'The calculated pattern is Mars trine Venus.',
                         'affirmation':'Recognise the pattern and choose your response.'},
        natal_strengths=[{'title':'Distinct strength','text':'Separate evidence.','evidence':'Mars trine Venus','remember':'Be deliberate.'}],
        natal_svg='<svg role="img" aria-label="Natal reference"></svg>',
        activation_svg='<svg role="img" aria-label="Monthly activation"></svg>',
        contacts=[('02 Oct','Personal transit')],key_dates=[('03 Oct','Date')])
    html=build_monthly_shared_html(**kwargs)
    for phrase in ('Your natal signature','DOMINANT ELEMENT','Mars and Venus set the strongest recurring pattern',
                   'Whole chart reading','Recognise the pattern','Your strengths','Natal reference','Read the month',
                   'Monthly activation','Personal transit','03 Oct'):
        assert phrase.lower() in html.lower(), phrase
    assert html.index('Your natal signature') < html.index('Read the pattern') < html.index('Your strengths') < html.index('Read the month')
    assert html.count('Distinct strength') == 1
    pdf=PdfReader(BytesIO(html_to_pdf(html)))
    text=' '.join(page.extract_text() for page in pdf.pages).lower()
    assert 'dominant element' in text and 'mars and venus set the strongest recurring pattern' in text

def test_no_constant_personal_astrology_in_renderer():
    html=build_monthly_shared_html(title='X',label='Y',intro='Z',paragraphs=['Z'],
        natal_signature=[('Sun','Virgo'),('Moon','Pisces')],
        natal_recurring={'headline':'Pluto conjunct Moon','opening':'Actual verified contact'})
    assert 'Virgo' in html and 'Pisces' in html and 'Pluto conjunct Moon' in html
    assert 'Saturn square Neptune' not in html
