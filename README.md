# Luna v3.100 — Monthly heading tidy-up

Apply over the repository containing v3.99 and the shared Paid Monthly renderer.

Changes:
- `monthly_shared_view.py`: display exactly one natal section heading. When a six-field natal signature exists, use `Your natal signature`; otherwise retain `Your natal foundation`. All fields, narrative, strengths, charts and exports remain intact.
- `app.py`: explicitly update `APP_VERSION` from `v3.99` to `v3.100`.
- `test_v3100_monthly_headings.py`: offline regression tests.

No changes to provider configuration, writing prompts, natal calculations, Year Ahead, checkout, or PDF rendering mechanics. No Groq requests made.

Offline results: 3 targeted tests passed, Python compilation passed. Live Streamlit remains unverified.
