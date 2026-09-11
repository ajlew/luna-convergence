from pathlib import Path
import re

from luna_guided_voice import (
    build_guided_collection_prompt,
    collection_facts_hash,
    generate_guided_collection_copy,
    validate_guided_collection_copy,
)
from luna_voice_provider import VoiceProviderError
import luna_voice_provider


def _facts():
    return {
        "items": [
            {
                "source_id": "2026-09-08",
                "technical_label": "Uranus stations retrograde",
                "supporting_events": ["Moon sextile Uranus"],
            },
            {
                "source_id": "2026-09-09",
                "technical_label": "Mercury opposite Neptune",
                "orb": 0.19,
                "supporting_events": ["Mercury trine Pluto"],
            },
        ]
    }


def _copy():
    facts = _facts()
    return {
        "items": [
            {
                "source_id": "2026-09-08",
                "headline": "CHANGE THE RULE WITHOUT BURNING THE MAP.",
                "story": "Uranus turns the pressure inward while the Moon supplies a usable opening. Notice what suddenly feels too small, then separate a real need for freedom from a passing refusal to be told anything.",
                "affirmation": "You can revise the rule without wrecking the structure.",
                "your_move": "Name the stale rule. Test one cleaner alternative.",
            },
            {
                "source_id": "2026-09-09",
                "headline": "CHECK THE BEAUTIFUL EXPLANATION.",
                "story": "Mercury opposite Neptune can make a polished story feel true before it has earned the privilege. Mercury trine Pluto supports a deeper check, so follow the detail that survives scrutiny.",
                "affirmation": "Uncertainty can sharpen your judgement.",
                "your_move": "Verify the message. Then answer the evidence.",
            },
        ],
        "facts_hash": collection_facts_hash("weekly_days", facts),
    }


def test_guided_collection_preserves_all_sources_and_validates():
    valid, errors = validate_guided_collection_copy("weekly_days", _copy(), _facts())
    assert valid, errors


def test_guided_collection_rejects_source_and_numeric_invention():
    copy = _copy()
    copy["items"][0]["source_id"] = "invented"
    copy["items"][1]["story"] += " It becomes exact at 9:99."
    valid, errors = validate_guided_collection_copy("weekly_days", copy, _facts())
    joined = " ".join(errors).lower()
    assert not valid
    assert "source ids" in joined
    assert "invented numeric" in joined


def test_voice_prompt_requires_human_story_and_earned_hope():
    prompt = build_guided_collection_prompt("weekly_days", _facts()).lower()
    for phrase in ("emotional", "earned hope", "dryly cheeky", "ordinary language", "your_move"):
        assert phrase in prompt


def test_customer_pages_do_not_call_legacy_interpretation_fallbacks():
    app = Path("app.py").read_text(encoding="utf-8")
    assert 'headline = "CALCULATIONS READY. LUNA\'S VOICE IS PAUSED."' in app
    assert '_guided_luna_collection("weekly_days"' in app
    assert '"weekly_signs"' in app
    assert re.search(r'_guided_luna_collection\(\s*"monthly_events"', app)
    assert re.search(r'_guided_luna_collection\(\s*"natal_signatures"', app)
    assert re.search(r'_guided_luna_collection\(\s*"yearly_transits"', app)
    assert '_guided_luna_copy("solar"' in app


def test_build_label_advances_beyond_v3356():
    config = Path("site_config.py").read_text(encoding="utf-8")
    assert "Luna v3.36.6 — Certainty Validation Recovery" in config


def test_collection_generation_uses_groq_strict_json_schema(monkeypatch):
    facts = _facts()
    captured = {}

    def fake_provider(prompt, **kwargs):
        captured.update(kwargs)
        payload = __import__("json").loads(
            prompt.split("CALCULATED COLLECTION:\n", 1)[1].split("\n\nCORRECTION REPORT:", 1)[0]
        )
        result = _copy()
        result["facts_hash"] = payload["facts_hash"]
        return result

    monkeypatch.setattr("luna_guided_voice.generate_openai_compatible_json", fake_provider)
    generate_guided_collection_copy(
        "weekly_days",
        facts,
        base_url="https://example.invalid",
        model="openai/gpt-oss-20b",
        api_key="test-key",
    )
    response_format = captured["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    schema = response_format["json_schema"]["schema"]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"items", "facts_hash"}


def test_provider_recovers_from_groq_json_validate_failed(monkeypatch):
    calls = []

    class FakeResponse:
        def __init__(self, status_code, body, data=None):
            self.status_code = status_code
            self.text = body
            self.headers = {}
            self._data = data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise luna_voice_provider.requests.RequestException(
                    f"{self.status_code} Client Error"
                )

        def json(self):
            return self._data

    responses = iter(
        [
            FakeResponse(400, '{"error":{"code":"json_validate_failed"}}'),
            FakeResponse(
                200,
                "",
                {"choices": [{"message": {"content": '{"status":"recovered"}'}}]},
            ),
        ]
    )

    def fake_post(_url, **kwargs):
        calls.append(__import__("copy").deepcopy(kwargs["json"]))
        return next(responses)

    monkeypatch.setattr(luna_voice_provider.requests, "post", fake_post)
    result = luna_voice_provider.generate_openai_compatible_json(
        "Return the object.",
        base_url="https://example.invalid",
        model="openai/gpt-oss-20b",
        api_key="test-key",
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "test",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {"status": {"type": "string"}},
                    "required": ["status"],
                    "additionalProperties": False,
                },
            },
        },
    )
    assert result == {"status": "recovered"}
    assert calls[0]["response_format"]["type"] == "json_schema"
    assert "response_format" not in calls[1]
    assert calls[0]["reasoning_effort"] == "low"
    assert calls[0]["include_reasoning"] is False
    assert "max_completion_tokens" in calls[0]
    assert "max_tokens" not in calls[0]


def test_provider_retries_a_truncated_json_completion(monkeypatch):
    calls = []

    class FakeResponse:
        status_code = 200
        text = ""
        headers = {}

        def __init__(self, content, finish_reason):
            self.content = content
            self.finish_reason = finish_reason

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {"content": self.content},
                        "finish_reason": self.finish_reason,
                    }
                ]
            }

    responses = iter(
        [
            FakeResponse('{"status":"cut off', "length"),
            FakeResponse('{"status":"complete"}', "stop"),
        ]
    )

    def fake_post(_url, **kwargs):
        calls.append(__import__("copy").deepcopy(kwargs["json"]))
        return next(responses)

    monkeypatch.setattr(luna_voice_provider.requests, "post", fake_post)
    result = luna_voice_provider.generate_openai_compatible_json(
        "Return the object.",
        base_url="https://example.invalid",
        model="openai/gpt-oss-20b",
        api_key="test-key",
        max_tokens=950,
    )
    assert result == {"status": "complete"}
    assert calls[1]["max_completion_tokens"] > calls[0]["max_completion_tokens"]
    assert "shorter wording" in calls[1]["messages"][0]["content"]


def test_provider_obeys_groq_decimal_retry_after(monkeypatch):
    calls = []
    sleeps = []

    class FakeResponse:
        text = ""

        def __init__(self, status_code, content=None, retry_after=None):
            self.status_code = status_code
            self.content = content
            self.headers = {"Retry-After": retry_after} if retry_after else {}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise luna_voice_provider.requests.RequestException(
                    f"{self.status_code} Client Error"
                )

        def json(self):
            return {
                "choices": [
                    {"message": {"content": self.content}, "finish_reason": "stop"}
                ]
            }

    responses = iter(
        [
            FakeResponse(429, retry_after="1.695s"),
            FakeResponse(200, content='{"status":"paced"}'),
        ]
    )

    def fake_post(_url, **kwargs):
        calls.append(kwargs["json"])
        return next(responses)

    monkeypatch.setattr(luna_voice_provider.requests, "post", fake_post)
    monkeypatch.setattr(luna_voice_provider.time, "sleep", sleeps.append)
    result = luna_voice_provider.generate_openai_compatible_json(
        "Return the object.",
        base_url="https://example.invalid",
        model="openai/gpt-oss-20b",
        api_key="test-key",
    )
    assert result == {"status": "paced"}
    assert len(calls) == 2
    assert sleeps == [2.045]


def test_shared_week_context_is_valid_evidence_for_each_sign():
    facts = {
        "shared_context": {
            "events": [
                {
                    "technical_label": "Mercury opposite Neptune",
                    "planets": ["Mercury", "Neptune"],
                    "orb_degrees": 0.19,
                }
            ]
        },
        "items": [
            {
                "source_id": "Libra",
                "sign": "Libra",
                "houses": [1, 7],
                "life_areas": ["identity", "relationships"],
            }
        ],
    }
    copy = {
        "items": [
            {
                "source_id": "Libra",
                "headline": "CHECK THE MESSAGE BEFORE YOU REACT.",
                "story": "Mercury opposite Neptune puts a 0.19 degree blur around messages affecting identity and relationships. Verification gives you room to respond cleanly.",
                "affirmation": "You can trust yourself enough to check the evidence.",
                "your_move": "Verify the message. Then state the clean answer.",
            }
        ],
        "facts_hash": collection_facts_hash("weekly_signs", facts),
    }
    valid, errors = validate_guided_collection_copy("weekly_signs", copy, facts)
    assert valid, errors


def test_invalid_full_batch_recovers_each_item_independently(monkeypatch):
    facts = _facts()

    def fake_provider(prompt, **_kwargs):
        payload = __import__("json").loads(prompt.split("CALCULATED COLLECTION:\n", 1)[1].split("\n\nCORRECTION REPORT:", 1)[0])
        supplied = payload["facts"]["items"]
        items = [
            {
                "source_id": item["source_id"],
                "headline": "USE THE SIGNAL WITHOUT INVENTING A STORY.",
                "story": f"For {item['source_id']}, the calculated pattern names a real pressure point. Stay close to the supplied evidence and make the practical choice available now.",
                "affirmation": "You can meet clear evidence with a clear response.",
                "your_move": "Check the evidence. Choose the useful next step.",
            }
            for item in supplied
        ]
        if len(items) > 1:
            items.reverse()
        return {"items": items, "facts_hash": payload["facts_hash"]}

    monkeypatch.setattr("luna_guided_voice.generate_openai_compatible_json", fake_provider)
    copy = generate_guided_collection_copy(
        "weekly_days",
        facts,
        base_url="https://example.invalid",
        model="test-model",
        api_key="test-key",
    )
    assert [item["source_id"] for item in copy["items"]] == [
        item["source_id"] for item in facts["items"]
    ]
    valid, errors = validate_guided_collection_copy("weekly_days", copy, facts)
    assert valid, errors


def test_public_weekly_page_requests_only_the_selected_sign():
    app = Path("app.py").read_text(encoding="utf-8")
    match = re.search(
        r"def _render_weekly_sign_layer\([\s\S]+?(?=\ndef _weekly_choice_options)",
        app,
    )
    assert match
    body = match.group(0)
    assert "_weekly_single_sign_voice" in body
    assert "_weekly_sign_voice_collection" not in body


def test_413_collection_is_split_until_groq_accepts_it(monkeypatch):
    facts = {
        "items": [
            {"source_id": name, "technical_label": f"signal {name}"}
            for name in ("Aries", "Taurus", "Gemini", "Cancer")
        ]
    }
    request_sizes = []
    token_budgets = []

    def fake_provider(prompt, **kwargs):
        payload = __import__("json").loads(prompt.split("CALCULATED COLLECTION:\n", 1)[1].split("\n\nCORRECTION REPORT:", 1)[0])
        supplied = payload["facts"]["items"]
        request_sizes.append(len(supplied))
        token_budgets.append(kwargs["max_tokens"])
        if len(supplied) > 1:
            raise VoiceProviderError("413 Payload Too Large")
        item = supplied[0]
        return {
            "items": [
                {
                    "source_id": item["source_id"],
                    "headline": "USE THE CALCULATED SIGNAL.",
                    "story": f"For {item['source_id']}, stay with the supplied pattern and turn its pressure into one practical response.",
                    "affirmation": "You can respond without inventing certainty.",
                    "your_move": "Check the signal. Make the useful move.",
                }
            ],
            "facts_hash": payload["facts_hash"],
        }

    monkeypatch.setattr("luna_guided_voice.generate_openai_compatible_json", fake_provider)
    copy = generate_guided_collection_copy(
        "weekly_signs",
        facts,
        base_url="https://example.invalid",
        model="test-model",
        api_key="test-key",
    )
    assert [item["source_id"] for item in copy["items"]] == [
        "Aries", "Taurus", "Gemini", "Cancer"
    ]
    assert max(request_sizes) <= 3
    assert 1 in request_sizes
    assert max(token_budgets) < 8000
