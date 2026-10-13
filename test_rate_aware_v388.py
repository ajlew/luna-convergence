from paid_voice_router import VoiceProvider, completion, _wait_from_response
from unittest.mock import patch
import tempfile, os

class Resp:
    def __init__(self,status=200,retry=None):
        self.status_code=status
        self.headers={'Retry-After':str(retry)} if retry is not None else {}
    def json(self):
        if self.status_code==429: return {'error':{'message':'Rate limit reached'}}
        return {'choices':[{'finish_reason':'stop','message':{'content':'A full paragraph.'}}]}
    def raise_for_status(self): pass
class Session:
    def __init__(self,responses): self.responses=iter(responses);self.calls=0
    def post(self,*a,**kw):self.calls+=1;return next(self.responses)
provider=VoiceProvider('https://example.org/v1','openai/gpt-oss-20b','fake')

def test_retry_after_is_not_truncated_at_ten_seconds():
    assert _wait_from_response(Resp(429,44))==44

def test_429_waits_for_retry_then_succeeds():
    session=Session([Resp(429,35),Resp()])
    with patch('paid_voice_router.time.sleep') as sleep:
        result=completion([{'role':'user','content':'hello'}],primary=provider,session=session)
    assert result=='A full paragraph.'
    sleep.assert_called_once_with(35)
    assert session.calls==2

def test_sections_checkpoint_on_success():
    session=Session([Resp()])
    with tempfile.TemporaryDirectory() as d:
        path=os.path.join(d,'sections.db')
        first=completion([{'role':'user','content':'one'}],primary=provider,session=session,checkpoint_id='first',checkpoint_db=path)
        second=completion([{'role':'user','content':'one'}],primary=provider,session=session,checkpoint_id='first',checkpoint_db=path)
        assert first==second and session.calls==1

def test_no_retry_forever():
    from paid_voice_router import VoiceTransportError
    session=Session([Resp(429,100),Resp(429,100)])
    with patch('paid_voice_router.time.sleep'):
        try: completion([],primary=provider,session=session,max_wait_seconds=120)
        except VoiceTransportError as exc: assert '429' in str(exc)
        else: assert False
    assert session.calls==2

def test_placeholder_secondary_skipped():
    from paid_voice_router import VoiceTransportError
    session=Session([Resp(400)])
    try: completion([],primary=provider,secondary=VoiceProvider('https://example.org/v1','your-model-name','fake'),session=session)
    except VoiceTransportError: pass
    assert session.calls==1
