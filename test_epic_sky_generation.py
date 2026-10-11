from datetime import date
import pytest
from studio_readings import weekly_sky_cards
from epic_sky import generate_week

CARDS=weekly_sky_cards(date(2026,10,12),'Australia/Sydney')
TEXT='\n'.join(f'DAY {i}\nTITLE: Chapter {i}\nSTORY: '+('Ares held the gate until the travellers returned to negotiate their next move. '*7)+'\nYOUR MOVE: Take one deliberate step.' for i in range(1,8))

class FakeResponse:
    def raise_for_status(self): pass
    def json(self): return {'choices':[{'finish_reason':'stop','message':{'content':TEXT}}]}

def test_single_call_and_calculated_metadata():
    calls=[]
    def post(*args,**kwargs):
        calls.append(kwargs)
        return FakeResponse()
    data=generate_week(date(2026,10,12),CARDS,base_url='https://example.invalid/v1',model='demo',api_key='fake',post=post)
    assert len(calls)==1
    assert len(data['days'])==7
    assert all(d['event']==c['event'] for d,c in zip(data['days'],CARDS))
    assert data['status']=='generated_draft'

def test_short_provider_response_fails_cleanly():
    class Short:
        def raise_for_status(self): pass
        def json(self): return {'choices':[{'finish_reason':'length','message':{'content':'DAY 1'}}]}
    with pytest.raises(RuntimeError, match='token limit'):
        generate_week(date(2026,10,12),CARDS,base_url='https://example.invalid/v1',model='demo',api_key='fake',post=lambda *a,**k:Short())
