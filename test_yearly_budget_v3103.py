from pathlib import Path

def test_yearly_budget_configured_and_annual_not_fixed_to_2700():
    source = Path(__file__).with_name('paid_yearly_editorial.py').read_text()
    assert "LUNA_YEARLY_ANNUAL_OUTPUT_TOKENS" in source
    assert "LUNA_YEARLY_REQUEST_BUDGET_TOKENS" in source
    assert "intro_packet,annual_output" in source
    assert "intro_packet,2700" not in source

def test_yearly_does_not_touch_monthly_or_backend():
    source = Path(__file__).with_name('paid_yearly_editorial.py').read_text()
    assert 'Paid Yearly' in source
    assert Path(__file__).with_name('app.py').read_text().count('APP_VERSION = "v3.103"') == 1
