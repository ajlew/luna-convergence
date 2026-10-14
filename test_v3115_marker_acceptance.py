"""Offline Year Ahead annual chunk marker tolerance; never invokes Groq."""
import sys, types, re
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent))
year = types.ModuleType('year_ahead'); year.YearPacket = type('YearPacket', (), {})
sys.modules.setdefault('year_ahead',year)
voice = types.ModuleType('paid_voice_router'); voice.VoiceProvider = lambda *args: object()
mode = ['bare']
def completion(messages, **kw):
    prompt = messages[-1]['content']
    found = re.search(r'Write only these section markers and their prose, in order: (.*?)\.',prompt)
    markers = re.findall(r'<<(?:READ_YEAR|HEADLINE|DECK|CLOSING|MONTH:\d+|ISSUE:\d+)>>',found.group(1))
    if re.search(r'annual_[123]:', kw['checkpoint_id']):
        if mode[0] == 'empty': return '<<READ_YEAR>>\nShort text.'
        body = ('A substantial and specific reflection on the selected calculated transit evidence, '
                'its possible implications and the practical choices the reader can consider. ')*9
        return {'bare':body, 'extra':'<<READ_YEAR>>\n'+body+'\n<<CLOSING>>', 'standard':'<<READ_YEAR>>\n'+body}[mode[0]]
    return '\n'.join(m+'\n'+('A specific and meaningful description of the calculated yearly evidence. '*8) for m in markers)
voice.completion=completion; sys.modules['paid_voice_router']=voice
import paid_yearly_editorial as mod
compact={'period':{'start':'2026-10-14'},'reader_context':{},'natal':{},'major_issues':[{'number':1,'customer_title':'A','primary':{}}], 'monthly_rounds':[{'number':i,'phase':'opening'} for i in range(1,13)]}
with patch.object(mod,'build_paid_yearly_material',return_value=compact),patch.object(mod,'_compact_paid_yearly_material',return_value=compact),patch.object(mod,'parse_paid_yearly_editorial',side_effect=lambda raw,**kw:raw):
    for kind in ('bare','standard','extra'):
        mode[0]=kind
        text=mod.generate_paid_yearly_editorial({'period':{},'games':[]},base_url='https://x',model='mock',api_key='mock')
        assert text.count('<<READ_YEAR>>') == 1
        assert '<<CLOSING>>' in text
        assert text.count('substantial and specific reflection') == 27
    mode[0]='empty'
    try: mod.generate_paid_yearly_editorial({'period':{},'games':[]},base_url='https://x',model='mock',api_key='mock')
    except RuntimeError as e: assert 'incomplete' in str(e)
    else: raise AssertionError('Empty annual response accepted')
print('v3.115: bare prose, normal marker, extraneous marker, incomplete response verified')
