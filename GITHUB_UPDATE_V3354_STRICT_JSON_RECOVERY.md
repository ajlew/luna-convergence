# Luna v3.35.4 - Groq Strict JSON Recovery

This patch fixes Groq `json_validate_failed` HTTP 400 responses when Luna generates
the twelve-sign, seven-day, and other multi-item collections.

## What changed

- Uses Groq strict JSON Schema output for complete readings and collection batches.
- Locks required fields, source IDs, and the calculated facts hash in the schema.
- Keeps Luna's deterministic semantic and astrology validation after generation.
- If Groq still rejects constrained JSON generation, retries once in plain JSON mode
  and then applies the same parser and validator.
- Keeps the v3.35.3 small-batch protection against HTTP 413 responses.

No API key change is required.

## Upload

Upload every file in this package to the repository root and replace the existing
files. Commit with:

`Fix Groq JSON validation for Luna collections`

Wait for Streamlit to redeploy, reboot the app, and run **Build all 12 sign voices**
again in Weekly Studio.

The build label should read:

`Luna v3.35.4 — Groq Strict JSON Recovery`
