from datetime import date, timedelta
from test_paid_yearly_rebuild import _packet
from natal_snapshot import build_natal_snapshot
from paid_yearly_editorial import PaidYearlyEditorial, PaidYearlyIssue, PaidYearlyMonth
from yearly_print_html import build_yearly_print_html, smooth_wave_path
from paid_yearly_pdf import build_paid_yearly_pdf


def _example():
    packet = _packet()
    start = date(2026, 10, 12)
    packet['period'] = {'start':str(start),'end':str(start+timedelta(days=364))}
    packet['year_strip'] = [{'month':f'M{n}', 'intensity': n/13, 'phase':'OPENING'} for n in range(1,14)]
    packet['monthly_rounds'] = [
        {'number':n+1,'start':str(start+timedelta(days=30*n)),
         'end':str(start+timedelta(days=30*n+29)),
         'label':f'Month {n+1}', 'phase':'OPENING',
         'dominant_game_number':1, 'focus':f'Focus for month {n+1}'}
        for n in range(12)
    ]
    snapshot = build_natal_snapshot(birth_date=date(1965,12,21),birth_time_known=False,timezone_name='Australia/Sydney')
    editorial = PaidYearlyEditorial(
        headline='A Year of Deliberate Choices', deck='Your calculated sky',
        read_year=('Your first year paragraph.',),
        issues=(PaidYearlyIssue(number=1,paragraphs=('First major issue paragraph.', 'Second major issue paragraph.')),),
        closing=('An ending worth keeping.',), word_count=30,
        monthly_rounds=(PaidYearlyMonth(number=1,focus='First authored focus.'),),
    )
    return packet, snapshot, editorial


def test_shared_html_keeps_content_and_pagination():
    packet, snapshot, editorial = _example()
    html=build_yearly_print_html(snapshot=snapshot,packet=packet,editorial=editorial,label='2026–27')
    assert html.count('class="month page"') == 12
    assert 'class="natal-svg"' in html
    assert 'First major issue paragraph.' in html
    assert 'Saturn square natal Venus' in html
    assert 'Key dates' in html and 'Why Luna sees this' in html
    assert 'month-timeline' in html
    assert '@page {size:A4' in html
    assert 'First authored focus.' in html
    assert '<path d="M' in html
    assert smooth_wave_path([(0, 40), (10, 20), (20, 30)]).count('C') == 2


def test_browser_rendered_year_ahead_pdf():
    packet, snapshot, editorial = _example()
    pdf=build_paid_yearly_pdf(snapshot=snapshot,packet=packet,editorial=editorial,sign='Sagittarius',label='2026–27')
    assert pdf.startswith(b'%PDF') and len(pdf)>12000
