# Luna Convergence v3.33 — Voice Composer Preview

## Safety boundary

- The public Weekly View is unchanged and continues to use v3.32 deterministic copy.
- Natal, Timing Map, calculations, payments, email fulfilment and public routes are unchanged.
- Streamlit never calls a language model.
- Missing, stale or invalid candidates fall back to v3.32 automatically.
- Set `LUNA_VOICE_MODE = "off"` in Streamlit secrets to hide the Studio comparison.

## Files changed

- `app.py`
- `site_config.py`

## Files added

- `.github/workflows/generate-weekly-voice-preview.yml`
- `generated/weekly/README.md`
- `GITHUB_UPDATE_V333_VOICE_PREVIEW.md`
- `luna_voice_provider.py`
- `requirements-voice.txt`
- `scripts/generate_weekly_voice.py`
- `test_weekly_voice_composer_v333.py`
- `weekly_voice_composer.py`

## Architecture

1. Luna's existing engine calculates the week and approved interpretations.
2. `weekly_voice_composer.py` creates and hashes a closed evidence packet.
3. The external generator sends only that packet to an OpenAI-compatible model.
4. A strict validator rejects changed evidence, missing/reordered events, invented planets or numbers, prohibited certainty, questions, repetition and truncated actions.
5. Only a validated JSON candidate is written.
6. Weekly Studio compares the candidate with the unchanged v3.32 fallback.

## GitHub configuration

Create these repository variables:

- `LUNA_VOICE_BASE_URL`
- `LUNA_VOICE_MODEL`
- `LUNA_VOICE_PROVIDER` (optional audit label)

Create this GitHub Actions secret:

- `LUNA_VOICE_API_KEY`

Run **Generate weekly Luna voice preview** manually from the Actions tab. Download
the validated JSON artifact, review it, and place it in `generated/weekly/` on a
separate preview branch. The workflow does not commit or publish anything.

## Local generation

```bash
export LUNA_VOICE_BASE_URL="https://provider.example/v1"
export LUNA_VOICE_MODEL="provider-model-id"
export LUNA_VOICE_API_KEY="..."
python scripts/generate_weekly_voice.py \
  --week 2026-08-31 \
  --timezone Australia/Sydney
```

Use `--packet-only` to inspect the closed evidence without calling a model.

## Verification

- Python compilation passed for the app, composer, provider and generator.
- 21 focused weekly, precision, integration, validation and fallback tests passed.
- Streamlit's application test completed with zero runtime exceptions.
- Packet-only generation confirmed Saturn as the controlling planet for the
  31 August 2026 example through reusable influence scoring, not pair-specific
  output text.
