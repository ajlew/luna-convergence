import ast
from pathlib import Path

def test_print_scope_and_version():
    src = Path(__file__).with_name('app.py').read_text()
    ast.parse(src)
    assert 'APP_VERSION = "v3.110"' in src
    assert src.count('def _yearly_complete_document_downloads(')==1
    assert 'if output["product_code"] in {"YEAR", "YEARLY"}' in src
    assert 'Download complete Year Ahead PDF' in src
    assert 'Download printable Year Ahead HTML (open, then Ctrl+P)' in src
    assert 'from yearly_print_html import build_yearly_print_html' in src

def test_paid_monthly_untouched():
    before=Path('/mnt/data/v3109_audit/app.py').read_text()
    after=Path(__file__).with_name('app.py').read_text()
    anchor='        if product_code == "MONTHLY":'
    assert before.count(anchor)==after.count(anchor)
    assert 'Paid Monthly did not return a complete interpretation' in after
