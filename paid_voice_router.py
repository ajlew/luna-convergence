"""Rate-aware Groq transport for paid reports, with resumable local checkpoints.

The local SQLite journal survives reruns on the same host, but not replacement of
an ephemeral Streamlit Cloud container. Production orders need external storage.
"""
from __future__ import annotations
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import sqlite3
import threading
import time
import requests

@dataclass(frozen=True)
class VoiceProvider:
    base_url: str
    model: str
    api_key: str

class VoiceTransportError(RuntimeError):
    pass

_LOCK = threading.RLock()
_NEXT_REQUEST_AT = 0.0
_DEFAULT_CHECKPOINT_DB = os.environ.get('LUNA_VOICE_CHECKPOINT_DB', '/tmp/luna_paid_voice_checkpoints.sqlite3')

def _safe_http_error(response):
    status = int(getattr(response, 'status_code', 0) or 0)
    detail = ''
    try:
        data = response.json()
        err = data.get('error', data) if isinstance(data, dict) else {}
        detail = str((err.get('message') or err.get('code') or err.get('type') or '') if isinstance(err, dict) else err)
    except (ValueError, TypeError, AttributeError):
        pass
    detail = re.sub(r'(?i)(bearer\s+\S+|sk-[A-Za-z0-9_-]{8,})', '[redacted]', detail)
    detail = ' '.join(detail.split())[:210]
    explanations = {400:'request rejected',401:'API key rejected',402:'billing or credits required',
        403:'provider access denied',404:'model or endpoint not found',408:'provider timed out',
        413:'request too large',422:'invalid request parameters',429:'rate or token limit reached',
        500:'provider internal error',502:'provider gateway error',503:'provider temporarily unavailable',504:'provider timeout'}
    return f"HTTP {status} ({explanations.get(status,'provider HTTP error')})" + (f': {detail}' if detail else '')

def _wait_from_response(response):
    """Honor Retry-After (seconds or HTTP date), then reset and Groq wait text."""
    headers = getattr(response, 'headers', {}) or {}
    for key in ('Retry-After', 'retry-after', 'x-ratelimit-reset-tokens'):
        raw = headers.get(key)
        if not raw: continue
        try:
            return max(1., float(raw))
        except (ValueError, TypeError):
            try:
                dt = parsedate_to_datetime(raw)
                return max(1., (dt - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
    try:
        body = response.json()
        message = str((body.get('error') or {}).get('message') or '')
        match = re.search(r'Please try again in\s*(?:(\d+)m)?\s*(\d+(?:\.\d+)?)s', message, re.I)
        if match: return max(1., int(match.group(1) or 0)*60+float(match.group(2)))
    except (ValueError, TypeError, AttributeError):
        pass
    return 60.0

def _journal_get(key, path):
    with _LOCK:
        with sqlite3.connect(path, timeout=15) as con:
            con.execute('CREATE TABLE IF NOT EXISTS paid_sections (key TEXT PRIMARY KEY, prose TEXT NOT NULL, saved_at TEXT NOT NULL)')
            row=con.execute('SELECT prose FROM paid_sections WHERE key=?', (key,)).fetchone()
            return row[0] if row else None

def _journal_put(key, prose, path):
    with _LOCK:
        with sqlite3.connect(path, timeout=15) as con:
            con.execute('CREATE TABLE IF NOT EXISTS paid_sections (key TEXT PRIMARY KEY, prose TEXT NOT NULL, saved_at TEXT NOT NULL)')
            con.execute('INSERT OR REPLACE INTO paid_sections VALUES (?,?,?)',(key,prose,datetime.now(timezone.utc).isoformat()))

def cached_completion(messages, *, primary: VoiceProvider, checkpoint_id: str | None = None,
                      checkpoint_db: str | None = None, max_output: int = 1900):
    """Check a successful saved section before any quota reservation or API call."""
    if not checkpoint_id:
        return None
    stable = json.dumps({'id':checkpoint_id,'model':primary.model,'messages':messages,
                         'max_output':max_output}, sort_keys=True, ensure_ascii=False)
    key = hashlib.sha256(stable.encode()).hexdigest()
    try:
        return _journal_get(key, checkpoint_db or _DEFAULT_CHECKPOINT_DB)
    except (OSError, sqlite3.Error):
        return None


def _record_usage(response, *, model: str, checkpoint_id: str | None):
    """Append provider-reported tokens; never record prompts, email or birth data."""
    try:
        data = response.json()
        usage = data.get('usage') or {}
        if not isinstance(usage, dict):
            return
        details = usage.get('completion_tokens_details') or {}
        event = {'time_utc': datetime.now(timezone.utc).isoformat(),
                 'model': model,
                 'job': (checkpoint_id or 'unlabelled').split(':')[1] if checkpoint_id and ':' in checkpoint_id else 'unlabelled',
                 'prompt_tokens': usage.get('prompt_tokens'),
                 'completion_tokens': usage.get('completion_tokens'),
                 'total_tokens': usage.get('total_tokens'),
                 'reasoning_tokens': details.get('reasoning_tokens') if isinstance(details, dict) else None}
        # Explicit opt-in required to write usage records to a local file.
        path = os.environ.get('LUNA_VOICE_USAGE_LOG', '').strip()
        if path:
            with _LOCK:
                with open(path, 'a', encoding='utf-8') as log:
                    log.write(json.dumps(event, separators=(',', ':'))+'\n')
    except (OSError, TypeError, ValueError, AttributeError, KeyError):
        pass  # Logging must never prevent delivery.


def _daily_token_429(response):
    """Only treat provider-confirmed daily-limit exhaustion as non-retryable."""
    try:
        data = response.json()
        err = data.get('error') or {}
        msg = str(err.get('message') or '') if isinstance(err, dict) else str(err)
        return bool(re.search(r'tokens per day|\bTPD\b', msg, re.I))
    except (AttributeError, TypeError, ValueError):
        return False


def completion(messages, *, primary: VoiceProvider, secondary: VoiceProvider | None = None,
               max_output: int = 1900, timeout: int = 100, session=None,
               checkpoint_id: str | None = None, checkpoint_db: str | None = None,
               max_wait_seconds: float = 180.0):
    """Generate one section. Wait for TPM reset, preserve completed sections locally.

    A rejected request has bounded retries (up to 3); no endless loops. Successful
    responses are checkpointed when given a stable job identity.
    """
    global _NEXT_REQUEST_AT
    http = session or requests
    providers=[primary]
    if secondary and all((secondary.base_url,secondary.model,secondary.api_key)) and 'your-model-name' not in secondary.model:
        providers.append(secondary)
    cache_key=None
    path=checkpoint_db or _DEFAULT_CHECKPOINT_DB
    if checkpoint_id:
        stable=json.dumps({'id':checkpoint_id,'model':primary.model,'messages':messages,'max_output':max_output},sort_keys=True,ensure_ascii=False)
        cache_key=hashlib.sha256(stable.encode()).hexdigest()
        try:
            hit=_journal_get(cache_key,path)
            if hit: return hit
        except (OSError,sqlite3.Error): pass
    errors=[]
    for provider in providers:
        waited=0.
        for attempt in range(4):
            payload={'model':provider.model,'messages':messages,'temperature':0.48,'max_completion_tokens':int(max_output)}
            if provider.model.startswith('openai/gpt-oss'):
                payload['reasoning_effort']='low'
                payload['include_reasoning']=False
            try:
                if session is None:
                    with _LOCK:
                        remaining=max(0.,_NEXT_REQUEST_AT-time.monotonic())
                        if remaining: time.sleep(remaining)
                        # Conservative pacing across threads sharing this process.
                        estimated=sum(len(str(m.get('content','')))//4 for m in messages)+int(max_output)
                        _NEXT_REQUEST_AT=time.monotonic()+60*estimated/7200
                response=http.post(provider.base_url.rstrip('/')+'/chat/completions',
                    headers={'Authorization':'Bearer '+provider.api_key,'Content-Type':'application/json'},
                    json=payload,timeout=timeout)
                status=response.status_code
                if status>=400:
                    description=_safe_http_error(response)
                    if status in (408,429,500,502,503,504) and attempt<3 and not (status == 429 and _daily_token_429(response)):
                        delay=_wait_from_response(response) if status==429 else min(8.,2.**attempt)
                        if waited+delay<=max_wait_seconds:
                            waited+=delay
                            if session is None:
                                with _LOCK: _NEXT_REQUEST_AT=max(_NEXT_REQUEST_AT,time.monotonic()+delay)
                            time.sleep(delay)
                            continue
                    errors.append(f'{provider.model}: {description}')
                    break
                response.raise_for_status()
                choice=response.json()['choices'][0]
                prose=str((choice.get('message') or {}).get('content') or '').strip()
                if choice.get('finish_reason')=='length':
                    errors.append(f'{provider.model}: completion limit reached');break
                if not prose:
                    errors.append(f'{provider.model}: empty prose');break
                _record_usage(response, model=provider.model, checkpoint_id=checkpoint_id)
                if cache_key:
                    try: _journal_put(cache_key,prose,path)
                    except (OSError,sqlite3.Error): pass
                return prose
            except (requests.RequestException,ValueError,TypeError,KeyError,IndexError) as exc:
                errors.append(f'{provider.model}: transport or response error ({type(exc).__name__})');break
    raise VoiceTransportError('Paid voice generation unavailable: '+'; '.join(errors))
