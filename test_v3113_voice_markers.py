from pathlib import Path
import importlib.util
import sys
sys.path.insert(0, '/mnt/data/fix3113/luna-convergence-main')
import paid_yearly_editorial as e

def test_flexible_markers_parse():
    source = ('### <<HEADLINE>>\nThe Turning Year\n\n**<<DECK>>**\nA defined story.\n'
              '<<READ_YEAR>>\nA meaningful year.\n\n<<ISSUE: 01>>\nA consequential choice.\n\nAnother insight.\n'
              '<<MONTH: 01>>\nThis month brings a choice.\n\n<<CLOSING>>\nA definite finish.')
    names = [m.group('name') for m in e._MARKER_RE.finditer(e._clean_text(source))]
    assert names == ['HEADLINE','DECK','READ_YEAR','ISSUE: 01','MONTH: 01','CLOSING'], names
    parsed=e.parse_paid_yearly_editorial(source,expected_issue_numbers=[1],expected_month_numbers=[1],issue_titles={1:'A Choice'})
    assert parsed.voice_complete
    assert parsed.issues[0].number == 1 and parsed.monthly_rounds[0].number == 1

def test_monthly_engine_untouched():
    assert 'APP_VERSION = "v3.113"' in Path('/mnt/data/fix3113/app.py').read_text()
    assert 'for first in range(0,len(games))' in Path(e.__file__).read_text()
