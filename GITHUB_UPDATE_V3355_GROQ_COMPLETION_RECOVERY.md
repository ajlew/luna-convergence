# Luna v3.35.5 - Groq Completion Recovery

This patch fixes incomplete Groq responses such as:

`The provider did not return valid JSON: Unterminated string...`

## What changed

- Uses `max_completion_tokens`, replacing Groq's deprecated `max_tokens` field.
- Sets GPT-OSS reasoning effort to low and excludes reasoning from the response.
- Reserves 2,400-3,600 completion tokens for small collection batches.
- Detects malformed or truncated JSON, increases the completion allowance, and
  asks for a shorter complete replacement.
- Retains strict JSON Schema generation, HTTP 413 batch splitting, source locks,
  calculation hashes, and Luna's deterministic factual validator.

No Streamlit secret or API-key change is required.

## Upload

Upload every file in this package to the repository root and replace the existing
files. Commit with:

`Fix truncated Groq responses for Luna signs`

Wait for Streamlit to redeploy, reboot the app, and run **Build all 12 sign voices**
again in Weekly Studio.

The build label should read:

`Luna v3.35.5 — Groq Completion Recovery`

