import pytest
import sys, types
sys.modules.setdefault("year_ahead", types.ModuleType("year_ahead")).YearPacket = type("YearPacket", (), {})
from paid_yearly_editorial import _normalize_single_game_response

PROSE = ('A commitment asks you to weigh the real cost against the benefit. '
         'You can discuss the expectations with the other person before you agree. '
         'This pattern may show up in work or relationships, but neither outcome is certain. '
         'Name what you can sustain, and decide what support you need to continue. '
         'When the arrangement changes, reassess whether it remains fair and practical.')

@pytest.mark.parametrize('text', [PROSE, '<<ISSUE:2>>\n'+PROSE, '<<GAMES>>\n'+PROSE,
                                  '<<MAJOR STORY>>\n'+PROSE])
def test_single_game_marker_variation(text):
    result = _normalize_single_game_response(text, '<<ISSUE:2>>')
    assert result.startswith('<<ISSUE:2>>\n')
    assert result.count('<<ISSUE:2>>') == 1
    assert PROSE in result

@pytest.mark.parametrize('text', ['', 'Too short.', '<<MONTH:5>>\n'+PROSE,
                                  '<<ISSUE:1>>\n'+PROSE, 'Phase: DECISION\n'+PROSE])
def test_game_bad_response_rejected(text):
    with pytest.raises(RuntimeError):
        _normalize_single_game_response(text, '<<ISSUE:2>>')
