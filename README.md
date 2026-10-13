# Luna v3.99 — Monthly baseline preservation

Apply `app.py` over the repository with the latest approved Monthly signature renderer. Do not replace `monthly_shared_view.py`.

## Changes (only app.py)
1. `APP_VERSION = "v3.99"` and corresponding visible build label.
2. Monthly report header period resolves from the selected report start date, rather than a narrative field name such as `Midheaven`.
3. Existing calculated Key Dates, including the birthday, display chronologically.

## Protected / unchanged
The natal signature, strongest recurring pattern, natal strengths, natal wheel, activation chart, actual story, prompts, provider, shared HTML/PDF renderer, checkout, and Year Ahead.

## Deferred, not silently changed
The introductory `price/payment/purchase` wording comes from the generated narrative. Fixing it properly requires validating/updating editorial inputs; this release does **not** rewrite customer copy. Any apparent sky date mismatch remains for a separate evidence audit.

Installation: replace only `app.py`, rerun Streamlit, and verify footer `v3.99`. No Groq calls required to inspect a saved report.
