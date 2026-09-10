# Luna v3.35.6 - Groq Rate-Limit Pacing

This patch fixes Groq HTTP 429 failures while Weekly Studio builds all twelve
sign translations under an 8,000 tokens-per-minute limit.

## What changed

- Parses Groq wait values such as `1.695s`, `7.66s`, `500ms`, and `2m59.56s`.
- Uses the `Retry-After` header first, then the response message or token-reset
  header when required.
- Adds a 0.35-second safety margin before retrying.
- Allows up to six attempts for rate-limited requests.
- Keeps the v3.35.5 completion, strict-JSON, validation, and payload protections.

No API-key or Streamlit-secret change is required. The twelve-sign build may
pause briefly between batches; that is deliberate throttling.

## Upload

Upload every file in this package to the repository root and replace the existing
files. Commit with:

`Pace Groq requests for Luna sign generation`

Wait for Streamlit to redeploy, reboot the app, and run **Build all 12 sign voices**
again in Weekly Studio.

The build label should read:

`Luna v3.35.6 — Groq Rate-Limit Pacing`

