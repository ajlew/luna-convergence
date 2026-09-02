# Validated weekly voice candidates

The Streamlit app never calls a language model. It only reads a candidate from
this directory when Weekly Studio is in preview mode.

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
Committing a validated JSON file makes it available to the private comparison
inside Weekly Studio. The public Weekly View continues using deterministic copy.

