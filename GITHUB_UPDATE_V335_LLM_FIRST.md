# Luna v3.35 — LLM First

## What changed

Luna's deterministic engine still owns planetary positions, aspects, houses, dates, phases, orbs, rankings and timing.

Customer-facing astrology interpretation now comes from the guided Luna writing layer across:

- Daily and Home;
- Weekly View;
- Weekly Studio main story, 12 sign translations, seven daily cards and publishing copy;
- Monthly main story and dated events;
- Natal integrated reading and strongest aspects;
- Your Year Ahead main story, natal contacts and detailed transits;
- Solar Year personalised interpretation.

If generated copy is missing, unavailable or rejected, Luna shows calculated evidence and a temporary writing-service message. It does not silently substitute the old canned forecast.

Fixed interface instructions, legal/privacy text, payment language and technical evidence remain deterministic.

## Required Streamlit secrets

```toml
LUNA_VOICE_MODE = "published"
LUNA_VOICE_BASE_URL = "https://api.groq.com/openai/v1"
LUNA_VOICE_MODEL = "openai/gpt-oss-20b"
LUNA_VOICE_API_KEY = "your Groq API key"
```

Do not commit the API key to GitHub.

## GitHub upload

Upload the changed-files package into the repository root, preserving folders. Replace files with the same names. Commit the update, then wait for Streamlit to redeploy.

## Verification

1. Open Daily and choose a sign.
2. Open Weekly View and choose a week/sign.
3. Open Weekly Studio and confirm the active output, 12 signs, daily cards and publishing copy use generated Luna prose.
4. Generate Monthly, Natal, Your Year Ahead and Solar Year samples.
5. Temporarily remove `LUNA_VOICE_API_KEY` in a preview deployment and confirm pages show calculated evidence plus the unavailable message—not legacy interpretation.
