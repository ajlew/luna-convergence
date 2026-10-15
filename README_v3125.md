# Luna v3.125 — Groq daily tokens (TPD) guard

**Base:** v3.124. Replace only `app.py` and `paid_yearly_editorial.py`.

- Maintains the existing rolling per-minute reservation and the three annual writing acts.
- Adds a *separate* configurable daily Year Ahead token reservation (`LUNA_YEARLY_TOKENS_PER_DAY`, default 200000; `LUNA_YEARLY_DAILY_WINDOW_SECONDS`, default 86400 seconds).
- Checks estimated input + requested completion allowance *before* every Year Ahead call, for usage within the current app worker.
- On a Groq 429 explicitly mentioning TPD, remembers the provider's Used/Limit/Requested values and temporarily stops additional attempts from that same running worker with an intelligible owner error, rather than submitting another failing API request. The 24-hour guard interval is a conservative local cooldown, **not** a claim about Groq's actual reset time.
- **Limitations:** The app cannot see prior-day usage, other deployments/processes, or other Groq clients before its first request. It can still encounter its first HTTP 429 from account-wide TPD exhaustion. The local reservation is in memory (not shared/durable). This patch cannot create additional provider tokens or guarantee a complete report when the quota is nearly exhausted.
- No changed prompts, astronomical calculations, post-LLM editorial gates, output rendering, Monthly, checkout or external API calls.

**Verification:** compilation; 3 offline daily-guard tests; ZIP integrity. **Not run:** live Groq integration, cloud deployment, whole Year Ahead PDF visual inspection.
**Rollback:** restore the two v3.124 files.
