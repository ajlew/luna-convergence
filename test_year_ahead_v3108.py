from datetime import date
from types import SimpleNamespace
import swisseph as swe
from yearly_print_html import _month_activation_svg, _transit_timeline, _sample_transit_orb, _natal_longitudes


def test_swiss_orb_zero_and_real_daily_curve():
    jd = swe.julday(2027, 1, 16, 12)
    saturn = swe.calc_ut(jd, swe.SATURN, swe.FLG_SWIEPH)[0][0]
    natal = {'sun': (saturn - 120) % 360}
    transit = dict(technical_label='Saturn trine natal Sun', natal_target='Sun',
                   start='2026-10-05', end='2027-02-12',
                   passes=[{'date':'2027-01-16','pass_label':'Final pass'}])
    assert _sample_transit_orb(transit, natal, date(2027,1,16)) < 1e-5
    html = _transit_timeline({'start':'2027-01-14','end':'2027-02-13'},
                             {'primary_transit':transit}, color='#765577', natal_longitudes=natal)
    assert 'orb-curve' in html and 'Final pass' in html and '#765577' in html
    assert html.count('<circle') == 1


def test_zodiac_glyphs_are_print_safe_paths():
    natal = SimpleNamespace(positions=[SimpleNamespace(planet='Sun',longitude=247)],ascendant=None,midheaven=None)
    tr = dict(technical_label='Saturn trine natal Sun',natal_target='Sun',passes=[])
    svg = _month_activation_svg(natal,[tr],'2026-11-14','2026-12-13')
    assert svg.count('class="zodiac-symbol"') == 12
    assert 'SUN' in svg and '♈' not in svg


def test_no_made_up_curve_if_missing_natal_target():
    tr = dict(technical_label='Saturn trine natal Sun',natal_target='Sun',
              start='2026-10-05',end='2027-02-12',passes=[])
    html = _transit_timeline({'start':'2027-01-14','end':'2027-02-13'},
                             {'primary_transit':tr},natal_longitudes={})
    assert 'orb-curve' not in html and '<rect' in html
