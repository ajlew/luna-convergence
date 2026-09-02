from __future__ import annotations

import json
import os
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
        "temperature": 0.55,
        "max_tokens": 2600,
        "response_format": {"type": "json_object"},
    }
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
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        raise VoiceProviderError(f"Voice provider request failed: {exc}") from exc
    return _json_content(content)

