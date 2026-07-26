from __future__ import annotations

import json
from typing import Any
import requests


DEFAULT_URL = "http://127.0.0.1:11434"


def list_models(base_url: str = DEFAULT_URL, timeout: float = 3.0) -> list[str]:
    response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return [item["name"] for item in data.get("models", []) if item.get("name")]


def server_status(base_url: str = DEFAULT_URL) -> tuple[bool, str]:
    try:
        models = list_models(base_url)
        if models:
            return True, f"Ollama is available with {len(models)} model(s)."
        return True, "Ollama is available, but no local models were found."
    except Exception as exc:
        return False, f"Ollama is not reachable: {exc}"


def build_prompt(result: dict, style: str = "strategic") -> str:
    facts = {key: value for key, value in result.items() if key != "markdown"}
    return f"""
You are the prose synthesis layer for a deterministic astrology application.

Use only the supplied calculated facts. Do not invent dates, planetary positions,
aspects, houses, eclipse dates or retrograde periods.

Writing style: {style}.
Write a detailed, practical horoscope with:
- core theme;
- major transitions;
- convergence points and why their interaction creates meaning;
- retrograde cycles as pre-shadow, retrograde, direct and post-shadow phases;
- work, money, relationships, opportunity, risk and strategic response;
- a final one-sentence interpretation.

Treat astrology as a symbolic interpretive framework, not scientifically proven causation.
Preserve all dates and house numbers exactly.

CALCULATED FACTS:
{json.dumps(facts, indent=2)}
""".strip()


def enhance(
    result: dict,
    model: str,
    base_url: str = DEFAULT_URL,
    style: str = "strategic",
    temperature: float = 0.35,
    timeout: float = 240.0,
) -> str:
    payload = {
        "model": model,
        "prompt": build_prompt(result, style),
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }
    response = requests.post(
        f"{base_url.rstrip('/')}/api/generate",
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()
