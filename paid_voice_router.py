"""Provider-independent, evidence-only narration transport for paid reports.

Never writes fallback prose. HTTP diagnostics deliberately omit credentials and prompts.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
import time
import requests

@dataclass(frozen=True)
class VoiceProvider:
    base_url: str
    model: str
    api_key: str

class VoiceTransportError(RuntimeError):
    pass


def _safe_http_error(response):
    """Return useful server status and provider error text, no request secrets."""
    status = int(getattr(response, 'status_code', 0) or 0)
    detail = ''
    try:
        data = response.json()
        err = data.get('error', data) if isinstance(data, dict) else {}
        if isinstance(err, dict):
            detail = str(err.get('message') or err.get('code') or err.get('type') or '')
        else:
            detail = str(err)
    except (ValueError, TypeError, AttributeError):
        pass
    # Avoid returning raw body, which could contain forwarded request material.
    detail = re.sub(r'(?i)(bearer\s+\S+|sk-[A-Za-z0-9_-]{8,})', '[redacted]', detail)
    detail = ' '.join(detail.split())[:210]
    explanations = {
        400: 'request rejected', 401: 'API key rejected', 402: 'billing or credits required',
        403: 'provider access denied', 404: 'model or endpoint not found',
        408: 'provider request timed out', 413: 'request too large',
        422: 'invalid request parameters', 429: 'rate or token limit reached',
        500: 'provider internal error', 502: 'provider gateway error',
        503: 'provider temporarily unavailable', 504: 'provider timeout',
    }
    reason = explanations.get(status, 'provider HTTP error')
    return f'HTTP {status} ({reason})' + (f': {detail}' if detail else '')


def completion(messages, *, primary: VoiceProvider, secondary: VoiceProvider | None = None,
               max_output: int = 1900, timeout: int = 100, session=None):
    """One bounded retry for retryable HTTP errors, then independent fallback.

    Raise a diagnostic preserving HTTP status. Neither provider changes calculations.
    """
    http = session or requests
    providers = [primary]
    if secondary and all((secondary.base_url, secondary.model, secondary.api_key)):
        providers.append(secondary)
    errors = []
    for provider in providers:
        for attempt in range(2):
            payload = {'model':provider.model, 'messages':messages, 'temperature':0.48,
                       'max_completion_tokens':int(max_output)}
            if provider.model.startswith('openai/gpt-oss'):
                payload['reasoning_effort'] = 'low'
                payload['include_reasoning'] = False
            try:
                response = http.post(provider.base_url.rstrip('/') + '/chat/completions',
                    headers={'Authorization':'Bearer ' + provider.api_key,'Content-Type':'application/json'},
                    json=payload, timeout=timeout)
                status = response.status_code
                if status >= 400:
                    description = _safe_http_error(response)
                    if status in (408, 429, 500, 502, 503, 504) and attempt == 0:
                        raw_retry = response.headers.get('Retry-After', '1')
                        try:
                            wait = min(10.0, max(1., float(raw_retry)))
                        except (TypeError, ValueError):
                            wait = 1.
                        time.sleep(wait)
                        continue
                    errors.append(f'{provider.model}: {description}')
                    break
                response.raise_for_status()
                choice = response.json()['choices'][0]
                prose = str((choice.get('message') or {}).get('content') or '').strip()
                if choice.get('finish_reason') == 'length':
                    errors.append(f'{provider.model}: completion limit reached')
                    break
                if not prose:
                    errors.append(f'{provider.model}: empty prose')
                    break
                return prose
            except (requests.RequestException, ValueError, TypeError, KeyError, IndexError) as exc:
                errors.append(f'{provider.model}: transport or response error ({type(exc).__name__})')
                break
    if len(providers) == 1:
        errors.append('No independent secondary provider configured')
    raise VoiceTransportError('All paid voice providers failed: ' + '; '.join(errors))
