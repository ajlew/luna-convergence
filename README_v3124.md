# Luna v3.124 — Year Ahead Groq rolling token pacing

**Base:** v3.123. Apply only `app.py` and `paid_yearly_editorial.py`.

- Retains three chronological annual acts and the Python-calculated evidence packet.
- Preflights each Groq writing job against the existing per-request budget.
- NEW: reserves estimated input plus requested maximum completion tokens in a local rolling 65-second window before each Year Ahead Groq call. Waits when total reservations would exceed configured minute capacity. Does not add LLM calls or post-LLM editorial validation.
- Default minute allowance: `LUNA_YEARLY_TOKENS_PER_MINUTE=8000` (configure to actual account/provider limit). `LUNA_YEARLY_TOKEN_WINDOW_SECONDS=65` for a small buffer. `LUNA_YEARLY_PACE_REQUESTS=1` enabled by default.
- No retry on 429. Other clients, external account activity, account daily limits, and exact provider token accounting may still trigger 429. Check actual Groq response headers for further diagnosis. The local limiter protects only requests made by this Year Ahead run.
- Does not change Paid Monthly, chart calculations, print renderer or any narrative prompts.

**Verified:** Python compilation; existing v3.123 evidence tests 2 passed; archive integrity.
**Not verified:** live Groq request, account-specific rate ceilings, end-to-end Streamlit generation (full dependency `paid_voice_router.py` not included in prior hotfix ZIP).
**Rollback:** restore the two v3.123 application files.
