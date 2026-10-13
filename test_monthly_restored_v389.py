"""Offline regression gates: Monthly narrative must stay on the restored one-call path."""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def _functions():
    tree=ast.parse((ROOT/'app.py').read_text(encoding='utf-8'))
    return {n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}

def test_monthly_one_provider_request_not_segmented():
    funcs=_functions()
    fn=funcs['_cached_paid_monthly_weave']
    code=ast.get_source_segment((ROOT/'app.py').read_text(),fn)
    assert 'requests.post(' in code
    assert 'for index,(lo,hi) in enumerate(partitions)' not in code
    assert 'completion(' not in code
    assert 'finish_reason' in code

def test_monthly_generation_uses_only_primary_signature():
    funcs=_functions()
    fn=funcs['_generate_paid_monthly_weave']
    code=ast.get_source_segment((ROOT/'app.py').read_text(),fn)
    assert '_cached_paid_monthly_weave(' in code
    assert 'LUNA_SECONDARY_VOICE_BASE_URL' not in code

def test_pdf_and_print_ready_html_retained():
    app=(ROOT/'app.py').read_text()
    pdf=(ROOT/'monthly_report_pdf_home_v3.py').read_bytes()
    assert 'build_monthly_homepage_html(' in app
    assert 'Download print-ready HTML' in app
    assert 'Download owner PDF' in app
    assert b'@page' in pdf

def test_version_is_updated():
    assert 'APP_VERSION = "v3.91"' in (ROOT/'app.py').read_text()
