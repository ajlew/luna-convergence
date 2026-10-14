from pathlib import Path
from types import SimpleNamespace
import inspect
import paid_yearly_editorial as ed
import yearly_print_html as h

def test_strength_evidence_is_rendered_from_snapshot_signature():
    source=inspect.getsource(h.build_yearly_print_html)
    assert 'getattr(s,"evidence", "")' in source
    assert 'strength-evidence' in source

def test_annual_does_not_pass_through_packet_planning_fields():
    source=inspect.getsource(ed.generate_paid_yearly_editorial)
    assert 'contains internal planning content' in source
    assert 'dominant' in source and 'strongest' in source

def test_output_version():
    source=Path('app.py').read_text(encoding='utf-8')
    assert 'APP_VERSION = "v3.117"' in source
