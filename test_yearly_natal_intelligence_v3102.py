from types import SimpleNamespace as S
from yearly_natal_intelligence import natal_year_links, year_core_thread_evidence

def test_structured_target_and_no_mutation():
    aspect = S(planet1='Venus',planet2='Saturn', name='opposition',orb=1.3,strength=0.9)
    snap = S(aspects=(aspect,))
    packet = {'games':[{'title':'Agreement','primary_transit':{'transiting_planet':'Saturn','natal_target':'Venus','aspect':'square'}, 'supporting_transits':[]}]}
    before=repr(packet)
    links=natal_year_links(snap,packet)
    assert links[0]['contacts'][0]['natal_target']=='Venus'
    assert 'Venus opposition Saturn' in year_core_thread_evidence(snap,packet)
    assert repr(packet)==before

def test_no_false_matches_in_titles():
    snap=S(aspects=(S(planet1='Venus',planet2='Saturn',name='square',orb=1,strength=.8),))
    packet={'games':[{'title':'Saturn-Venus story', 'primary_transit':{'natal_target':'Moon','technical_label':'Venus Saturn'},'supporting_transits':[]}]}
    assert natal_year_links(snap, packet)==()
    assert year_core_thread_evidence(snap,packet)==''

def test_unknown_inputs_and_multiples():
    snap=S(aspects=())
    assert natal_year_links(snap, {'games':[]})==()
    snap=S(aspects=(S(planet1='Moon',planet2='Mercury',name='conjunction',orb=2.1,strength=.7),))
    packet={'games':[{'primary_transit':{'natal_target':'Moon'},'supporting_transits':[{'natal_target':'Mercury'}]},{'primary_transit':{'natal_target':'Moon'}}]}
    assert natal_year_links(snap,packet)[0]['distinct_games']==2
