import importlib.util
from pathlib import Path
import re

SOURCE = Path(__file__).with_name('monthly_shared_view.py')
spec = importlib.util.spec_from_file_location('luna_monthly_view_v3100', SOURCE)
view = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view)


def test_signature_heading_without_duplicate():
    html = view.build_monthly_shared_html(
        title='Calculated headline', label='Calculated month', intro='Intro',
        paragraphs=['A sufficiently complete test story paragraph.'],
        natal_signature=[('Sun', 'First test sign'), ('Moon', 'Second test sign')],
        natal_pattern='An aspect-specific interpretation.',
        natal_strengths=[{'title': 'A strength', 'text': 'Interpretation'}],
    )
    assert '<h2>Your natal signature</h2>' in html
    assert '<h2>Your natal foundation</h2>' not in html
    assert '<strong>First test sign</strong>' in html
    assert '<strong>Second test sign</strong>' in html
    assert '<h2>Read the pattern</h2>' in html
    assert '<h2>Your strengths</h2>' in html
    assert '<h2>Read the month</h2>' in html


def test_no_signature_keeps_fallback_heading():
    html = view.build_monthly_shared_html(
        title='Calculated headline', label='Calculated month', intro='Intro',
        paragraphs=['A sufficiently complete test story paragraph.'],
        natal_pattern='Calculated natal narrative.',
    )
    assert '<h2>Your natal foundation</h2>' in html
    assert '<h2>Your natal signature</h2>' not in html


def test_release_version():
    app = Path(__file__).with_name('app.py').read_text(encoding='utf-8')
    assert re.search(r'^APP_VERSION\s*=\s*"v3\.100"\s*$', app, re.MULTILINE)
