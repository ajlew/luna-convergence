from __future__ import annotations

import json
import os
import re
import time
from typing import Any

import requests


class VoiceProviderError(RuntimeError):
    pass


def _duration_seconds(value: Any) -> float | None:
    """Parse Groq retry/reset values such as 1.695s, 2m59.56s, or 500ms."""
    text = str(value or "").strip().lower()
    if not text:
        return None
    total = 0.0
    matched = False
    for amount, unit in re.findall(r"(\d+(?:\.\d+)?)\s*(ms|m|s)?", text):
        matched = True
        number = float(amount)
        total += number / 1000.0 if unit == "ms" else number * 60.0 if unit == "m" else number
    return total if matched else None


def _rate_limit_delay(response: Any, attempt: int) -> float:
    """Prefer Groq's precise retry instruction and add a small safety margin."""
    header_wait = _duration_seconds(response.headers.get("Retry-After", ""))
    if header_wait is None:
        match = re.search(
            r"try again in\s+(\d+(?:\.\d+)?(?:ms|s|m))",
            str(response.text or ""),
            flags=re.IGNORECASE,
        )
        header_wait = _duration_seconds(match.group(1)) if match else None
    if header_wait is None:
        header_wait = _duration_seconds(response.headers.get("x-ratelimit-reset-tokens", ""))
    if header_wait is None:
        header_wait = float(min(2**attempt, 30))
    return min(max(header_wait + 0.35, 0.75), 60.0)


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
        # Recover one complete leading value when a compatible model adds a
        # duplicate object or brief commentary. The evidence validator still
        # decides whether the recovered prose is safe to publish.
        try:
            start_candidates = [index for index in (text.find("{"), text.find("[")) if index >= 0]
            start = min(start_candidates) if start_candidates else 0
            result, _end = json.JSONDecoder().raw_decode(text[start:])
        except json.JSONDecodeError as recovery_exc:
            raise VoiceProviderError(
                f"The provider did not return valid JSON: {recovery_exc}"
            ) from recovery_exc
    # Some JSON-mode models wrap the requested object in a singleton array.
    # This is a harmless transport variation, not an astrology error.
    if isinstance(result, list) and len(result) == 1 and isinstance(result[0], dict):
        result = result[0]
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
    response_format: dict[str, Any] | None = None,
    rate_limit_retries: int = 5,
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
        "max_completion_tokens": resolved_max_tokens,
        "response_format": response_format or {"type": "json_object"},
    }
    if resolved_model.startswith("openai/gpt-oss"):
        # GPT-OSS reasoning shares the completion budget. Keep the hidden work
        # short so the requested JSON has enough room to finish.
        payload["reasoning_effort"] = "low"
        payload["include_reasoning"] = False
    response = None
    used_json_mode_recovery = False
    for attempt in range(6):
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
            if (
                response.status_code == 400
                and "json_validate_failed" in str(response.text or "")
                and "response_format" in payload
                and not used_json_mode_recovery
            ):
                # Some compatible providers can reject their own best-effort JSON
                # generation before returning it. Downgrade strict JSON Schema to
                # JSON Object mode rather than removing JSON enforcement entirely.
                # Luna's deterministic validator still enforces every required
                # field, facts hash and evidence rule.
                payload["response_format"] = {"type": "json_object"}
                payload["messages"][0]["content"] += (
                    " Return one syntactically valid JSON object only, with no "
                    "markdown fences or commentary."
                )
                used_json_mode_recovery = True
                continue
            if response.status_code == 429:
                if attempt < rate_limit_retries:
                    time.sleep(_rate_limit_delay(response, attempt))
                    continue
            elif 500 <= response.status_code < 600:
                if attempt < 2:
                    time.sleep(float(2**attempt))
                    continue
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = str(choice.get("finish_reason") or "")
            try:
                return _json_content(content)
            except VoiceProviderError as parse_error:
                if attempt < 2:
                    current_budget = int(payload.get("max_completion_tokens") or resolved_max_tokens)
                    payload["max_completion_tokens"] = min(
                        8000,
                        max(current_budget + 1200, int(current_budget * 1.75)),
                    )
                    payload["messages"][0]["content"] += (
                        " The previous response was incomplete or malformed. "
                        "Use shorter wording and finish the entire JSON object."
                    )
                    continue
                suffix = f" Finish reason: {finish_reason}." if finish_reason else ""
                raise VoiceProviderError(f"{parse_error}{suffix}") from parse_error
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
            status_code = response.status_code if response is not None else None
            retryable_request = (
                status_code is None
                or status_code == 429
                or (status_code is not None and status_code >= 500)
            )
            retry_window = rate_limit_retries if status_code == 429 else 2
            if attempt < retry_window and isinstance(exc, requests.RequestException) and retryable_request:
                time.sleep(float(2**attempt))
                continue
            detail = ""
            if response is not None:
                body = " ".join(str(response.text or "").split())[:300]
                detail = f" HTTP {response.status_code}: {body}" if body else f" HTTP {response.status_code}."
            raise VoiceProviderError(f"Voice provider request failed.{detail} {exc}") from exc
    else:
        raise VoiceProviderError("Voice provider request failed after six attempts.")
    raise VoiceProviderError("Voice provider returned no usable JSON response.")
