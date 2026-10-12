from datetime import date
from natal_snapshot import build_natal_snapshot
from yearly_print_html import _month_activation_svg

def test_activation_svg_respects_natal_longitude_and_print_fill():
    snap=build_natal_snapshot(birth_date=date(1965,12,21),birth_time_known=False,timezone_name='Australia/Sydney')
    result=_month_activation_svg(snap,[{'technical_label':'Saturn square natal Venus','natal_target':'Venus','passes':[]}])
    assert 'class="activation-wheel"' in result
    assert 'Saturn square natal Venus' in result
    assert '#725aca' in result
    assert 'fill="#e58b40"' not in result

def test_no_contacts_no_fake_chart():
    assert 'No selected personal activation' in _month_activation_svg(None,[])
