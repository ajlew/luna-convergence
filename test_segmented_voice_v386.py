from paid_voice_router import VoiceProvider, completion, VoiceTransportError
from unittest.mock import Mock


def test_secondary_provider_on_truncation():
    first=Mock(status_code=200)
    first.json.return_value={'choices':[{'message':{'content':'partial'},'finish_reason':'length'}]}
    first.raise_for_status.return_value=None
    second=Mock(status_code=200)
    second.json.return_value={'choices':[{'message':{'content':'Complete paragraph.'},'finish_reason':'stop'}]}
    second.raise_for_status.return_value=None
    session=Mock()
    session.post.side_effect=[first,second]
    out=completion([{'role':'user','content':'hello'}],primary=VoiceProvider('https://one','main','secret-a'),secondary=VoiceProvider('https://two','backup','secret-b'),session=session)
    assert out=='Complete paragraph.'
    assert session.post.call_count==2
    assert session.post.call_args_list[0].kwargs['headers']['Authorization']=='Bearer secret-a'
    assert session.post.call_args_list[1].kwargs['headers']['Authorization']=='Bearer secret-b'


def test_no_incomplete_single_provider():
    response=Mock(status_code=200)
    response.json.return_value={'choices':[{'message':{'content':'short'},'finish_reason':'length'}]}
    response.raise_for_status.return_value=None
    session=Mock();session.post.return_value=response
    import pytest
    with pytest.raises(VoiceTransportError):
        completion([{'role':'user','content':'hello'}],primary=VoiceProvider('https://one','model','secret'),session=session)
