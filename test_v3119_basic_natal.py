from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
source = (ROOT / 'paid_yearly_editorial.py').read_text(encoding='utf-8')
app = (ROOT / 'app.py').read_text(encoding='utf-8')


def test_enhanced_natal_resonance_removed():
    assert 'natal_resonance' not in source
    assert '_natal_resonance_for_issue' not in source
    assert 'NATAL BRIDGE:' not in source


def test_original_natal_strength_facts_still_in_packet():
    tree = ast.parse(source)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_snapshot_material')
    body = ast.get_source_segment(source, fn)
    for field in ('dominant_element', 'dominant_modality', 'strengths', 'evidence', 'ascendant', 'midheaven'):
        assert field in body


def test_existing_year_writing_not_reworked():
    assert 'for chunk_index, start_month in enumerate((1, 5, 9), 1)' in source
    assert 'APP_VERSION = "v3.119"' in app
