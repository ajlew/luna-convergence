"""Independent provider routing for paid report fragments (no astrology decisions)."""
from __future__ import annotations
from dataclasses import dataclass
import time
import requests

@dataclass(frozen=True)
class VoiceProvider:
    base_url: str
    model: str
    api_key: str

class VoiceTransportError(RuntimeError):
    pass

def completion(messages, *, primary: VoiceProvider, secondary: VoiceProvider | None = None,
               max_output: int = 1900, timeout: int = 100, session=None):
    """Use fallback ONLY on transport failures, length, or empty output.

    No silent text substitutions; caller must validate semantic completeness.
    Single provider retry for 429/5xx after Retry-After, then independent fallback.
    """
    errors=[]
    http=session or requests
    providers=[primary]+([secondary] if secondary and all((secondary.base_url, secondary.model, secondary.api_key)) else [])
    for provider in providers:
        for attempt in range(2):
            payload={"model":provider.model,"messages":messages,"temperature":0.48,"max_completion_tokens":int(max_output)}
            if provider.model.startswith('openai/gpt-oss'):
                payload['reasoning_effort']='low'
                payload['include_reasoning']=False
            try:
                response=http.post(provider.base_url.rstrip('/')+'/chat/completions',
                    headers={'Authorization':'Bearer '+provider.api_key,'Content-Type':'application/json'},
                    json=payload,timeout=timeout)
                if response.status_code in (429,500,502,503,504) and attempt==0:
                    wait=min(2.0, max(0., float(response.headers.get('Retry-After','0') or 0)))
                    if wait: time.sleep(wait)
                    continue
                response.raise_for_status()
                choice=response.json()['choices'][0]
                result=str((choice.get('message') or {}).get('content') or '').strip()
                if choice.get('finish_reason')=='length':
                    raise VoiceTransportError('Provider completion limit reached')
                if not result:
                    raise VoiceTransportError('Provider returned empty prose')
                return result
            except (requests.RequestException, ValueError, TypeError, KeyError, IndexError, VoiceTransportError) as exc:
                errors.append(f'{provider.model}: {type(exc).__name__}')
                break
    raise VoiceTransportError('All paid voice providers failed: '+', '.join(errors))
