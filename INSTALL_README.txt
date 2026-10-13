Luna v3.95 — Paid Monthly error visibility ONLY
Prerequisite: v3.94 cumulative (or v3.93 plus focused v3.94).
Changed file: app.py ONLY. Replace the existing app.py.
This fixes the stale version/footer label and exposes the underlying stored Paid Monthly error in the owner diagnostic and paid delivery failure.
It does NOT claim to fix the underlying report generation failure. Do not spend Groq tokens testing until you inspect the diagnostic or prebuilt daily data.
No changes to the Monthly story prompt, LLM calls, Groq limits, natal strengths, charts, PDF, Year Ahead, or Stripe settings.
