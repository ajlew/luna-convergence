Luna v3.140 — Paid Monthly diagnostic-only patch.
Replace app.py in repository root. Preserves paid Monthly generation, provider calls, and all pricing/version settings.
On failure, owner output now exposes the existing safe preflight/provider error saved by _record_voice_error instead of one generic message.
No Groq calls run. Syntax parse passed. Not a correction to an unknown provider/preflight root cause.
