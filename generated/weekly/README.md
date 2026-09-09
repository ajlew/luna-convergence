# Validated weekly voice candidates

The Streamlit app never calls a language model. It reads one validated, cached
weekly story from this directory. If the candidate is current, the public Weekly
View publishes it; otherwise Luna automatically uses the deterministic fallback.

Generate a candidate outside the app:

```bash
python scripts/generate_weekly_voice.py \
  --week 2026-08-31 \
  --timezone Australia/Sydney
```

Required environment variables:

- `LUNA_VOICE_BASE_URL` — an OpenAI-compatible `/v1` base URL.
- `LUNA_VOICE_MODEL` — the provider's model identifier.
- `LUNA_VOICE_API_KEY` — provider credential; never commit this value.
- `LUNA_VOICE_PROVIDER` — optional display/audit label.

Only candidates that pass the evidence and language validator are written.
The manual GitHub Action generates, validates and commits the candidate to the
branch from which it was run. Weekly Studio still provides the editorial comparison.
