from pathlib import Path

def test_annual_chunks_have_explicit_continuity():
    source = Path('paid_yearly_editorial.py').read_text()
    assert "previous_context = ''" in source
    assert "previous_context = ' '.join(prose.split())[-650:]" in source
    assert 'Do not restart the year' in source
    assert 'Follow ONLY the supplied four rolling months' in source
    assert 'not a list, outline, report summary or numbered Games' in source

def test_annual_keeps_strict_validation_and_original_assembly():
    source = Path('paid_yearly_editorial.py').read_text()
    assert 'contains internal planning content' in source
    assert "year_segments.append(prose)" in source
    assert "'<<READ_YEAR>>\\n' + '\\n\\n'.join(year_segments)" in source
    assert "['<<HEADLINE>>','<<DECK>>','<<CLOSING>>']" in source

def test_explicit_version():
    assert 'APP_VERSION = "v3.118"' in Path('app.py').read_text()
