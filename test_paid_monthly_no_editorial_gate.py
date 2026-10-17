"""Focused offline tests for the Paid Monthly no-post-LLM-editorial contract."""
import ast
import re
from pathlib import Path

SOURCE = Path(__file__).with_name('app.py').read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)
NAMES = {'_paid_monthly_transport_has_text', '_paid_monthly_clean_plain_story', '_paid_monthly_story_paragraphs'}
SELECTED = [node for node in TREE.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in NAMES]
ns = {'re': re}
exec(compile(ast.Module(body=SELECTED, type_ignores=[]), '<extracted monthly helpers>', 'exec'), ns)


def test_any_nonempty_response_accepted():
    check = ns['_paid_monthly_transport_has_text']
    assert check('Three words only')
    assert check('I cannot write this interpretation.')  # no semantic/refusal gate
    assert not check('  ')


def test_paragraph_boundaries_preserved():
    f = ns['_paid_monthly_story_paragraphs']
    assert f('One very short paragraph.') == ['One very short paragraph.']
    assert f('First paragraph.\n\nSecond paragraph.') == ['First paragraph.', 'Second paragraph.']


def test_no_editorial_gate_or_sun_sign_rewriter():
    assert '_paid_monthly_publishable_prose' not in SOURCE
    assert '_paid_monthly_correct_sun_sign_attribution' not in SOURCE
    assert 'provider returned an incomplete monthly interpretation' not in SOURCE
    assert 'Paid Monthly response rejected:' not in SOURCE


def test_transport_failures_remain():
    assert 'Voice provider truncated the Paid Monthly story at the completion limit.' in SOURCE
    assert 'Voice provider returned an empty response.' in SOURCE
