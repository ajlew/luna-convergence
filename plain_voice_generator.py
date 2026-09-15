"""Scheduled-job-only provider client. The model returns prose, never a JSON object."""
from __future__ import annotations

import os
import time
import math

from plain_readings import prompt_for, text_errors


class GenerationError(RuntimeError):
    """Only controlled, credential-free diagnostics may reach job logs."""


def retry_delay(headers, attempt):
    raw = str(headers.get("Retry-After", "")).strip()
    try:
        delay = float(raw)
    except ValueError:
        delay = 30 * (attempt + 1)
    if not math.isfinite(delay) or delay < 0:
        delay = 30 * (attempt + 1)
    # Do not retry before the provider's requested delay or wait past job budget.
    if delay > 300:
        raise GenerationError("rate limit requires a later run; completed signs are retained")
    return max(1, delay)


def generate_text(packet: dict, *, post=None, sleep=time.sleep) -> str:
    if post is None:
        import requests
        post = requests.post
    required = ("LUNA_VOICE_BASE_URL", "LUNA_VOICE_MODEL", "LUNA_VOICE_API_KEY")
    missing = [name for name in required if not os.environ.get(name, "").strip()]
    if missing:
        raise GenerationError("missing configuration: " + ", ".join(missing))
    base = os.environ["LUNA_VOICE_BASE_URL"].strip().rstrip("/")
    model = os.environ["LUNA_VOICE_MODEL"].strip()
    key = os.environ["LUNA_VOICE_API_KEY"].strip()
    prompt = prompt_for(packet)
    for attempt in range(3):
        payload = {"model": model, "messages": [
            {"role": "system", "content": "Write Luna's interpretation from the supplied calculations. Return plain prose only."},
            {"role": "user", "content": prompt}],
            "temperature": 0.72,
            "max_completion_tokens": int(os.environ.get("LUNA_VOICE_MAX_TOKENS", "4000"))}
        if model.startswith("openai/gpt-oss"):
            payload.update(reasoning_effort="low", include_reasoning=False)
        try:
            response = post(base + "/chat/completions",
                            headers={"Authorization": "Bearer " + key}, json=payload,
                            timeout=float(os.environ.get("LUNA_VOICE_TIMEOUT", "120")))
        except Exception:
            if attempt < 2:
                sleep(2 ** attempt)
                continue
            raise GenerationError("provider connection failed") from None
        if response.status_code == 429 or response.status_code >= 500:
            if attempt < 2:
                delay = retry_delay(response.headers, attempt)
                while delay > 0:
                    chunk = min(60, delay)
                    sleep(chunk)
                    delay -= chunk
                continue
        if response.status_code >= 400:
            raise GenerationError(f"provider HTTP {response.status_code}")
        try:
            choice = response.json()["choices"][0]
            body = choice["message"]["content"]
            errors = text_errors(packet["product"], body)
            if choice.get("finish_reason") == "length":
                errors.append("response truncated")
        except (KeyError, IndexError, TypeError, ValueError):
            errors = ["missing response text"]
        if not errors:
            return body.strip()
        prompt = prompt_for(packet) + "\nCorrect these issues: " + "; ".join(errors)
    raise GenerationError("text check failed: " + "; ".join(errors))
