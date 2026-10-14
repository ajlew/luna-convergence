from unittest.mock import patch
import importlib.util, sys, types, json, re
from pathlib import Path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
# A local year_ahead module is only required for type hints and need not run calculations.
year = types.ModuleType('year_ahead')
year.YearPacket = type('YearPacket', (), {})
sys.modules.setdefault('year_ahead',year)
voice = types.ModuleType('paid_voice_router')
voice.VoiceProvider = lambda *a: object()
calls=[]
def completion(messages, **kw):
    prompt = messages[-1]['content']
    requested = re.search(r'Write only these section markers and their prose, in order: (.*?)\.',prompt).group(1)
    markers = re.findall(r'<<(?:READ_YEAR|HEADLINE|DECK|CLOSING|MONTH:\d+|ISSUE:\d+)>>',requested)
    calls.append((kw['checkpoint_id'],kw['max_output'],prompt))
    return '\n'.join(m+'\n'+('This is verified-year interpretation with practical choices and thoughtful possibilities. '*14 if m == '<<READ_YEAR>>' else 'A specific and meaningful description of the calculated yearly evidence.') for m in markers)
voice.completion=completion
sys.modules['paid_voice_router']=voice
import paid_yearly_editorial as mod
compact={'period':{'start':'2026-10-14'},'reader_context':{},'natal':{},'major_issues':[{'number':1,'customer_title':'Game A','primary':{}}], 'monthly_rounds':[{'number':i,'phase':'opening'} for i in range(1,13)]}
with patch.object(mod,'build_paid_yearly_material',return_value=compact), patch.object(mod,'_compact_paid_yearly_material',return_value=compact), patch.object(mod,'parse_paid_yearly_editorial',side_effect=lambda raw,**kw:raw):
    result=mod.generate_paid_yearly_editorial({'period':{},'games':[]},base_url='https://x',model='mock',api_key='mock')
assert len([a for a,_,_ in calls if 'annual_' in a]) == 4
assert result.count('<<READ_YEAR>>') == 1
assert result.count('verified-year interpretation') == 42
assert all(limit <= 1900 for _,limit,_ in calls)
assert len([a for a,_,_ in calls if 'games' in a]) == 1
print('Verified offline: three bounded annual chunks, assembled annual story, monthly and Game jobs.')
