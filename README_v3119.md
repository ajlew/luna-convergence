# Luna v3.119 — Restore basic Year Ahead natal bridge

**Apply over v3.118 only.** Two production files changed: `paid_yearly_editorial.py` and `app.py` (version `v3.119`).

This is a deliberately narrow rollback of the *experimental enhanced natal resonance overlay* within the Year Ahead writing packet:
- Removed the automatic `natal_resonance` matching of natal Strengths to Games.
- Removed its prompts forcing psychological links into Read the Year and Game narratives.
- Kept the original calculated natal signature, planet placements, chart, four Strengths, aspect/orb evidence and printable report untouched.
- No changes to Year Ahead transit calculations, Monthly, Groq settings, annual writing segmentation, charts, checkout, or PDF.

**Important:** This does *not* implement the separate evidence-ledger correction for Groq's incorrect dates/aspect claims. Do not treat this as acceptance of the live Year Ahead report.

Checks: static regression tests, Python compile, archive integrity. Full customer PDF and live Groq generation not tested. Roll back by restoring the two original v3.118 files.
