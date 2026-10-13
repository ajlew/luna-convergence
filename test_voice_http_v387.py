from paid_voice_router import VoiceProvider, completion, VoiceTransportError

class FakeResponse:
    def __init__(self, status, msg='', content='OK'):
        self.status_code=status
        self.msg=msg
        self.content=content
        self.headers={'Retry-After':'0'}
    def json(self):
        if self.status_code >= 400: return {'error':{'message':self.msg}}
        return {'choices':[{'finish_reason':'stop','message':{'content':self.content}}]}
    def raise_for_status(self): pass

class FakeSession:
    def __init__(self, results): self.results=list(results); self.calls=0
    def post(self, *args, **kwargs):
        self.calls+=1
        return self.results.pop(0)

primary=VoiceProvider('https://one.example/v1','openai/gpt-oss-20b','redacted')
secondary=VoiceProvider('https://two.example/v1','other-model','redacted')

def test_400_gives_actionable_reason():
    session=FakeSession([FakeResponse(400,'Unsupported field: foo')])
    try: completion([], primary=primary, session=session)
    except VoiceTransportError as exc:
        assert 'HTTP 400' in str(exc) and 'Unsupported field' in str(exc)
        assert 'No independent secondary' in str(exc)
    else: assert False
    assert session.calls==1

def test_401_does_not_retry():
    session=FakeSession([FakeResponse(401,'Invalid API Key')])
    try: completion([], primary=primary, session=session)
    except VoiceTransportError as exc: assert 'API key rejected' in str(exc)
    else: assert False
    assert session.calls==1

def test_secondary_after_400():
    session=FakeSession([FakeResponse(400,'Bad params'), FakeResponse(200,content='Full story')])
    assert completion([], primary=primary, secondary=secondary, session=session)=='Full story'
    assert session.calls==2

def test_429_retries_then_fallback(monkeypatch):
    monkeypatch.setattr('paid_voice_router.time.sleep',lambda x:None)
    session=FakeSession([FakeResponse(429,'TPM exceeded'),FakeResponse(429,'TPM exceeded'),FakeResponse(200,content='Recovered')])
    assert completion([],primary=primary,secondary=secondary,session=session)=='Recovered'
    assert session.calls==3

def test_truncated_primary_fallback():
    class TruncResponse(FakeResponse):
        def json(self): return {'choices':[{'finish_reason':'length','message':{'content':'partial'}}]}
    session=FakeSession([TruncResponse(200),FakeResponse(200,content='Completed')])
    assert completion([],primary=primary,secondary=secondary,session=session)=='Completed'
