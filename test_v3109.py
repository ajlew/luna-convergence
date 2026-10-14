import importlib.util, sys, types
from pathlib import Path
from unittest.mock import patch
root=Path(__file__).parent
sys.path.insert(0,str(root/'luna-convergence-main'))
sys.path.insert(0,str(root))
# Base repository has the project engine.
sys.modules["year_ahead"] = types.SimpleNamespace(YearPacket=type("YearPacket", (), {}))
import paid_yearly_editorial as y

def test_yearly_jobs_keep_every_section_and_split_annual(monkeypatch):
    material={'period':{'start':'2026-10-14','end':'2027-10-13'},'reader_context':{},'natal':{},
      'monthly_rounds':[{'number':i,'phase':'progress','strongest_date':'2027-03-01'} for i in range(1,13)],
      'major_issues':[{'number':1,'customer_title':'Actual Game','primary':'Saturn trine natal Sun'}]}
    monkeypatch.setattr(y,'build_paid_yearly_material',lambda *a,**k:material)
    monkeypatch.setattr(y,'_compact_paid_yearly_material',lambda data,level: data)
    monkeypatch.setattr(y,'_calculated_dates',lambda *a:{'2026-10-14','2027-10-13','2027-03-01'})
    calls=[]
    def fake_completion(messages,*,max_output,checkpoint_id,**kwargs):
        calls.append((checkpoint_id,max_output))
        markers=[line.strip() for line in messages[1]['content'].split('Write only these section markers and their prose, in order: ')[1].split('.\n',1)[0].split(', ')]
        return '\n\n'.join(f'{x}\n'+ ('This is connected to the calculated transit and gives the reader a concrete decision to consider.' if 'MONTH' in x or 'ISSUE' in x else 'This is a verified annual theme that explains the linked events and provides a useful overview.') for x in markers)
    import paid_voice_router
    monkeypatch.setattr(paid_voice_router,'completion',fake_completion)
    monkeypatch.setattr(y,'parse_paid_yearly_editorial',lambda body,**kwargs: (body,kwargs))
    body,kw=y.generate_paid_yearly_editorial({},base_url='https://example.invalid',model='openai/gpt-oss-20b',api_key='test')
    assert '<<READ_YEAR>>' in body and '<<HEADLINE>>' in body and '<<DECK>>' in body and '<<CLOSING>>' in body
    for i in range(1,13): assert f'<<MONTH:{i}>>' in body
    assert '<<ISSUE:1>>' in body
    assert len(calls)==6  # essay + framing + 3 groups of months + 1 Game group
    assert calls[0][0].startswith('yearly:annual_essay:')
    assert calls[1][0].startswith('yearly:annual_framing:')
    assert calls[0][1]==3300 and calls[1][1]==1200

def test_version_and_no_monthly_changes():
    app=(root/'app.py').read_text()
    assert 'APP_VERSION = "v3.109"' in app
