import sys,types
sys.modules.setdefault('year_ahead',types.ModuleType('year_ahead')).YearPacket=type('YearPacket',(),{})
from paid_yearly_editorial import _normalize_single_game_response, parse_paid_yearly_editorial

def test_game_accepts_short_text_and_ignores_foreign_markers():
    assert _normalize_single_game_response('<<ISSUE:3>>\nShort prose.', '<<ISSUE:2>>') == '<<ISSUE:2>>\nShort prose.'

def test_game_keeps_provider_prose_unchanged_except_markers():
    text='Phase: Decision. On 2099-01-01, discuss this choice.'
    assert text in _normalize_single_game_response(text,'<<ISSUE:1>>')

def test_parser_does_not_silently_drop_invented_date_sentence():
    body='<<HEADLINE>>\nA year\n<<DECK>>\nFor you\n<<READ_YEAR>>\nOn 2099-01-01, consider your decision.\n<<CLOSING>>\nChoose wisely.\n<<ISSUE:1>>\nA possible choice.'
    result=parse_paid_yearly_editorial(body,expected_issue_numbers=[1],allowed_dates={'2027-02-27'})
    assert '2099-01-01' in ' '.join(result.read_year)
