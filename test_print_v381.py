from pathlib import Path
from monthly_report_pdf_home_v3 import _optional_timing_strip


def test_empty_glance_boxes_not_rendered():
    assert _optional_timing_strip({}) == ''
    assert 'The opening' not in _optional_timing_strip({'Strongest window': 'None'})
    assert 'The opening' in _optional_timing_strip({'Strongest window': '11 October'})
    assert 'The reality check' not in _optional_timing_strip({'Strongest window': '11 October'})


def test_print_styles_allow_continuation_and_keep_charts():
    src=Path(__file__).with_name('monthly_report_pdf_home_v3.py').read_text()
    assert 'height:auto; min-height:0; overflow:visible' in src
    assert '.monthly-chart-pair, .natal-chart-print' in src
    assert 'if horizon_has_content:' in src
    assert 'thead {{ display:table-header-group; }}' in src
