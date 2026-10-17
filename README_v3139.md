# Luna v3.139 — Play Your Games

Required base: v3.138. Replace `app.py`, `yearly_print_html.py`; **add** `game_decision_model.py` and update `luna_release.json`. `paid_yearly_editorial.py` was not changed and is **not** included.

- The existing Python-selected Game fields (question, advantage, risk, move, don't) now form a structured decision board; dates are taken only from the supplied exact contacts.
- Board for each selected Game on screen and within the Major Story in PDF, rendered from **the same deterministic HTML builder**. On screen boards appear after the existing full Year Ahead report, rather than inside the original report renderer; visual placement parity is pending a future unified renderer change.
- No provider calls or changes to prompts. No payoffs, probabilities, observed outcomes or optimal timing are fabricated.
- Does **not** resolve the separate generated-prose aspect errors or sparse print-page pagination.

Checks: Python compilation; offline tests for calculated exact-pass ownership, user text escaping and variable Game count; archive integrity. Not checked: live Streamlit, Groq, complete production PDF, paid checkout.

Rollback: restore `app.py`, `yearly_print_html.py`, and `luna_release.json` from v3.138, remove `game_decision_model.py`.
