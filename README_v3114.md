# Luna v3.114 — Year Ahead Voice Completion Stabilisation

**Baseline: deployed/repository v3.111.** Do not install over the failed v3.112 or v3.113 releases without first restoring the v3.111 baseline, because those releases changed other files.

Changed files:
- `app.py`: explicit `APP_VERSION = "v3.114"` and visible build label.
- `paid_yearly_editorial.py`: generates Read the Year as three chronological, separately validated segments, stitched into the existing single READ_YEAR report section; each major Game is a separately bounded job. The existing actual calculation payload remains authoritative. No stock writing or invented events.

No changes to Paid Monthly, charts, PDF, checkout, astrology computations, or natal engine.

Offline checks: compilation and test_v3114_year_voice.py (simulated provider) passed. No real Groq request, production 12-month report, or browser print was tested; completion success therefore remains **unconfirmed** until deployed against live account limits.

To install: start from v3.111, replace only the two Python files, run local tests, and deploy. If the provider still signals completion limit, collect the job checkpoint/limit and its response; do not increase every budget blindly.
