from social_card_voice import social_card_prompt, generate_social_card

CARD = {'date':'2026-10-17', 'event':'Pluto stations direct', 'timing':'Exact station', 'technical':'Pluto in Aquarius', 'has_event': True}


def test_prompt_uses_calculated_data_and_canva():
    prompt = social_card_prompt(CARD)
    assert '2026-10-17' in prompt and 'Pluto stations direct' in prompt
    assert 'four short stanzas' in prompt and 'Canva' in prompt


def test_missing_event_fails_before_provider():
    try:
        social_card_prompt({'date':'2026-10-17'})
    except ValueError:
        return
    raise AssertionError('Must reject missing event before provider call')


def test_prose_returned_unchanged_even_if_short():
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'choices':[{'finish_reason':'stop','message':{'content':'One small line.'}}]}
    output = generate_social_card(CARD, base_url='https://example.test', model='test', api_key='test', post=lambda *a, **k: Response())
    assert output == 'One small line.'


def test_truncation_is_technical_failure():
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'choices':[{'finish_reason':'length','message':{'content':'Partial'}}]}
    try:
        generate_social_card(CARD, base_url='https://example.test', model='test', api_key='test', post=lambda *a, **k: Response())
    except RuntimeError as exc:
        assert 'truncated' in str(exc)
        return
    raise AssertionError('Expected transport truncation exception')
