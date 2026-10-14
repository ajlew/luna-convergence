from datetime import date
from types import SimpleNamespace
from paid_yearly_editorial import parse_paid_yearly_editorial
from yearly_print_html import _transit_timeline


def test_internal_markers_are_not_printed():
    result = parse_paid_yearly_editorial('''<<HEADLINE>>
A Year of Changing Agreements
<<DECK>>
A personalised reading.
<<READ_YEAR>>
The year begins with a choice about responsibilities. <<GAMES>> Your position develops as the year goes on.
<<MONTH:1>>
Weigh mutual responsibilities. <<GAMES>> Ask what each party can offer.
<<ISSUE:1>>
The relationship between duty and independence is evolving. <<MONTHLY ROUNDS>> Decide which commitments are sustainable.
<<CLOSING>>
Carry forward the boundaries you established.''', expected_month_numbers=[1], expected_issue_numbers=[1])
    fields = [result.headline, result.deck, *result.read_year, *result.closing]
    fields += [m.focus for m in result.monthly_rounds]
    fields += [p for i in result.issues for p in i.paragraphs]
    assert all('<<' not in f and '>>' not in f for f in fields)


def test_measured_plot_has_phase_segments_and_subtle_style():
    import swisseph as swe
    natal = {'venus': 160.0}
    transit = {'technical_label':'Jupiter sextile natal Venus', 'natal_target':'Venus', 'start':'2026-11-01', 'end':'2026-11-30', 'passes':[]}
    game={'primary_transit':transit, 'supporting_transits':[]}
    chart = _transit_timeline({'start':'2026-11-01','end':'2026-11-30'}, game, natal_longitudes=natal)
    assert 'stroke-width="1.55"' in chart
    assert 'class="orb-curve orb-' in chart
    assert 'height="14"' in chart  # quiet background is retained
    assert 'stroke-width="3"' not in chart
