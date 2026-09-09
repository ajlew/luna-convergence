from __future__ import annotations

import json
import os
import time
from typing import Any

import requests


class VoiceProviderError(RuntimeError):
    pass


def _required_env(name: str) -> str:
    value = str(os.getenv(name, "") or "").strip()
    if not value:
        raise VoiceProviderError(f"Missing required environment variable: {name}")
    return value


def _json_content(value: str) -> dict[str, Any]:
    text = str(value or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise VoiceProviderError(f"The provider did not return valid JSON: {exc}") from exc
    if not isinstance(result, dict):
        raise VoiceProviderError("The provider response must be one JSON object.")
    return result


def generate_openai_compatible_json(
    prompt: str,
    *,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    timeout: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """Call any OpenAI-compatible chat-completions endpoint outside Streamlit."""
    resolved_base = str(base_url or os.getenv("LUNA_VOICE_BASE_URL", "")).strip()
    resolved_model = str(model or os.getenv("LUNA_VOICE_MODEL", "")).strip()
    resolved_key = str(api_key or os.getenv("LUNA_VOICE_API_KEY", "")).strip()
    if not resolved_base:
        resolved_base = _required_env("LUNA_VOICE_BASE_URL")
    if not resolved_model:
        resolved_model = _required_env("LUNA_VOICE_MODEL")
    if not resolved_key:
        resolved_key = _required_env("LUNA_VOICE_API_KEY")
    resolved_timeout = float(timeout or os.getenv("LUNA_VOICE_TIMEOUT", "120"))
    resolved_max_tokens = int(max_tokens or os.getenv("LUNA_VOICE_MAX_TOKENS", "8000"))

    payload = {
        "model": resolved_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Follow the closed evidence contract exactly. Return JSON only. "
                    "You are a voice layer, never an astrology calculation layer."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.72,
        "max_tokens": resolved_max_tokens,
        "response_format": {"type": "json_object"},
    }
    response = None
    for attempt in range(3):
        try:
            response = requests.post(
                f"{resolved_base.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {resolved_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=resolved_timeout,
            )
            if response.status_code == 429 or 500 <= response.status_code < 600:
                if attempt < 2:
                    retry_after = response.headers.get("Retry-After", "")
                    try:
                        delay = min(max(float(retry_after), 0.5), 8.0)
                    except (TypeError, ValueError):
                        delay = float(2**attempt)
                    time.sleep(delay)
                    continue
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            break
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
            status_code = response.status_code if response is not None else None
            retryable_request = (
                status_code is None
                or status_code == 429
                or (status_code is not None and status_code >= 500)
            )
            if attempt < 2 and isinstance(exc, requests.RequestException) and retryable_request:
                time.sleep(float(2**attempt))
                continue
            detail = ""
            if response is not None:
                body = " ".join(str(response.text or "").split())[:300]
                detail = f" HTTP {response.status_code}: {body}" if body else f" HTTP {response.status_code}."
            raise VoiceProviderError(f"Voice provider request failed.{detail} {exc}") from exc
    else:
        raise VoiceProviderError("Voice provider request failed after three attempts.")
    return _json_content(content)
