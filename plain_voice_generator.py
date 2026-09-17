"""Scheduled plain-prose client with paced transport and draft-aware revisions."""
from __future__ import annotations
import math
import os
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from plain_readings import prompt_for, text_errors
from reading_quality import content_errors

class GenerationError(RuntimeError):
    """Credential-free job diagnostic."""

class RateLimitError(GenerationError):
    """Stop the batch rather than hammering a depleted account."""


def _duration(value):
    raw = str(value or "").strip()
    try:
        result = float(raw)
    except ValueError:
        pieces = re.findall(r"(\d+(?:\.\d+)?)\s*(ms|h|m|s)", raw)
        if pieces and ''.join(n + u for n, u in pieces) == raw.replace(' ', ''):
            result = sum(float(n) * {'ms': .001, 's': 1, 'm': 60, 'h': 3600}[u] for n, u in pieces)
        else:
            try:
                result = (parsedate_to_datetime(raw) - datetime.now(timezone.utc)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                return None
    return result if math.isfinite(result) and result >= 0 else None


def retry_delay(headers, attempt):
    headers = {str(k).lower(): v for k, v in headers.items()}
    delay = _duration(headers.get('retry-after'))
    if delay is None:
        resets = [_duration(headers.get(name)) for name in
                  ('x-ratelimit-reset-tokens', 'x-ratelimit-reset-requests')]
        delay = max([60 * (attempt + 1)] + [v for v in resets if v is not None])
    if delay > 300:
        raise RateLimitError('rate limit requires a later run; completed readings are retained')
    return max(1, delay)


def _wait(seconds, sleep):
    while seconds > 0:
        chunk = min(60, seconds)
        sleep(chunk)
        seconds -= chunk


def generate_text(packet: dict, *, post=None, sleep=time.sleep) -> str:
    if post is None:
        import requests
        post = requests.post
    required = ('LUNA_VOICE_BASE_URL', 'LUNA_VOICE_MODEL', 'LUNA_VOICE_API_KEY')
    missing = [name for name in required if not os.environ.get(name, '').strip()]
    if missing:
        raise GenerationError('missing configuration: ' + ', '.join(missing))
    base, model, key = [os.environ[name].strip() for name in required]
    messages = [
        {'role': 'system', 'content': "Write Luna's interpretation from the supplied calculations. Return plain prose only."},
        {'role': 'user', 'content': prompt_for(packet)}]
    errors = []
    for revision in range(2):
        payload = {'model': model, 'messages': messages, 'temperature': .72,
                   'max_completion_tokens': int(os.environ.get('LUNA_VOICE_MAX_TOKENS', '4000'))}
        if model.startswith('openai/gpt-oss'):
            payload.update(reasoning_effort='low', include_reasoning=False)
        for transport in range(4):
            try:
                response = post(base.rstrip('/') + '/chat/completions',
                    headers={'Authorization': 'Bearer ' + key}, json=payload,
                    timeout=float(os.environ.get('LUNA_VOICE_TIMEOUT', '120')))
            except Exception:
                if transport == 3:
                    raise GenerationError('provider connection failed') from None
                _wait(30 * (transport + 1), sleep)
                continue
            status = response.status_code
            if status == 429:
                if transport == 3:
                    raise RateLimitError('provider rate limit persists; rerun later to resume incomplete readings')
                _wait(retry_delay(response.headers, transport), sleep)
                continue
            if status >= 500 and transport < 3:
                _wait(retry_delay(response.headers, transport), sleep)
                continue
            if status >= 400:
                raise GenerationError(f'provider HTTP {status}')
            break
        body = None
        try:
            choice = response.json()['choices'][0]
            body = choice['message']['content']
            errors = text_errors(packet['product'], body) + content_errors(packet, body)
            if choice.get('finish_reason') == 'length':
                errors.append('response truncated')
        except (KeyError, IndexError, TypeError, ValueError):
            errors = ['missing response text']
        if not errors:
            return body.strip()
        if revision < 1:
            # Edit the rejected draft. The old loop asked for a brand-new draft each time.
            messages = messages[:2] + ([{'role': 'assistant', 'content': body}] if isinstance(body, str) else [])
            messages.append({'role': 'user', 'content':
                'Revise the draft above to resolve the listed issues. '
                'Preserve the meaning, Luna voice and required paragraph format. '
                'Keep the writing concise and complete. '
                'Return only the revised prose, with no labels. Issues: ' + '; '.join(errors)})
            _wait(float(os.environ.get('LUNA_VOICE_REQUEST_PAUSE', '30')), sleep)
    raise GenerationError('text check failed after draft revisions: ' + '; '.join(errors))
