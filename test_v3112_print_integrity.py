from datetime import date
from natal_snapshot import build_natal_snapshot
from yearly_print_html import build_yearly_print_html, _month_activation_svg
from test_yearly_print_html_v378 import _example


def test_evidence_and_activation_block_are_printed():
    packet, snapshot, editorial = _example()
    html = build_yearly_print_html(snapshot=snapshot, packet=packet, editorial=editorial, label='Test')
    assert 'class="strength-evidence"' in html
    assert 'class="activation-section"' in html
    assert 'page-break-inside:avoid' in html


def test_planet_markers_keep_true_natal_longitudes():
    snapshot = build_natal_snapshot(birth_date=date(1965, 12, 21),birth_time_known=False,timezone_name='Australia/Sydney')
    svg = _month_activation_svg(snapshot, [{'technical_label':'Saturn square natal Venus', 'natal_target':'Venus','passes':[]}])
    assert 'class="natal-marker"' in svg
    assert 'class="planet-label"' in svg
    assert 'class="zodiac-symbol"' in svg
