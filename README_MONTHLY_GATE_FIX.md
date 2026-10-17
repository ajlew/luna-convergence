# Luna v3.140 — Paid Monthly no-post-LLM editorial gate

Files: `app.py` and `test_paid_monthly_no_editorial_gate.py` only.

Replace repository-root `app.py` with this copy. It includes the previous owner diagnostic fix.

Changes:
- Removes content-based minimum-word and refusal classification gates from Paid Monthly provider handling, story generation, owner export, PDF delivery, and display.
- Removes the post-Groq Sun-sign wording correction and paragraph count/word-count-driven sentence regrouping.
- Keeps technical checks for no text, invalid provider response, transport failure, and `finish_reason=length`.
- Does not introduce retries, fallback providers, or Groq calls.
- Preserves `luna_release.json` and version v3.140.

Tests: `python -m pytest -q test_paid_monthly_no_editorial_gate.py` (4 passed offline). `python -m py_compile app.py` (passed).

Limitations: No live Groq request, purchase, complete Monthly PDF, or full repository regression suite was executed. A provider refusal with text will now be displayed; that is the explicit consequence of forbidding content-based rejection.
