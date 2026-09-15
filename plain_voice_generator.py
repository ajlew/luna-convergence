"""Scheduled-job-only provider client. The model returns prose, never a JSON object."""
from __future__ import annotations

import os
import time

from plain_readings import prompt_for, text_errors


def generate_text(packet: dict, *, post=None, sleep=time.sleep) -> str:
    if post is None:
        import requests
        post = requests.post
    base = os.environ["LUNA_VOICE_BASE_URL"].rstrip("/")
    model = os.environ["LUNA_VOICE_MODEL"]
    key = os.environ["LUNA_VOICE_API_KEY"]
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
            raise RuntimeError("provider connection failed") from None
        if response.status_code == 429 or response.status_code >= 500:
            if attempt < 2:
                try:
                    delay = float(response.headers.get("Retry-After", "30"))
                except ValueError:
                    delay = 30
                sleep(min(60, max(1, delay)))
                continue
        if response.status_code >= 400:
            raise RuntimeError(f"provider HTTP {response.status_code}")
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
    raise RuntimeError("text check failed: " + "; ".join(errors))
