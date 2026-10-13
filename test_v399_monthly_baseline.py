from pathlib import Path
import ast

def test_release_and_protected_monthly_contract():
    source = Path(__file__).with_name("app.py").read_text()
    ast.parse(source)
    assert 'APP_VERSION = "v3.99"' in source
    assert '_, _, label = monthly_period_from_result(result, narrative)' in source
    assert 'date_rows.sort(key=_key_date_sort)' in source
    assert '_monthly_natal_pattern(snap)' in source
    assert 'natal_recurring = _snapshot_natal_fallback_story(snap)' in source
    assert '"natal_signature": natal_signature' in source
    assert '"natal_svg": natal_svg, "activation_svg": activation_svg' in source
    assert '"paragraphs": list(story.get("paragraphs") or [])' in source
