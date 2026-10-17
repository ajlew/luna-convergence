from game_decision_model import build_game_decision_boards, render_game_decision_board


def test_asymmetric_game_three_verified_passes():
    packet = {'games':[{'number':1,'title':'The Agreement Gets Tested',
        'human_life_area':'Relationships, Money, Value and Attraction',
        'primary_transit': {'technical_label':'Jupiter sextile natal Venus',
        'passes':[{'date':'2026-11-28','pass_label':'Initial activation'},
                  {'date':'2026-12-28','pass_label':'Retrograde return'},
                  {'date':'2027-07-09','pass_label':'Final pass'}]}}]}
    board = build_game_decision_boards(packet)[0]
    assert len(board['contacts']) == 3
    assert board['contacts'][0]['decision_role'].startswith('Identify')
    assert board['contacts'][1]['decision_role'].startswith('Review')
    assert board['contacts'][2]['decision_role'].startswith('Compare')
    html = render_game_decision_board(board)
    for field in ('Resource at stake','Asymmetric opportunity','Asymmetric downside protection'):
        assert field in html


def test_single_pass_does_not_fabricate_another():
    packet = {'games':[{'number':1,'title':'The Door Gets Bigger','human_life_area':'Career and Reputation',
        'primary_transit':{'technical_label':'Jupiter trine natal Midheaven',
                           'passes':[{'date':'2027-09-30','pass_label':'Initial activation'}]}}]}
    board=build_game_decision_boards(packet)[0]
    assert len(board['contacts']) == 1
    assert 'operational capacity' in board['resource']
    assert 'larger opportunity' in board['opportunity']
