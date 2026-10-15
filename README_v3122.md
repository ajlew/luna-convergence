# Luna v3.122 — Remove Year Ahead post-LLM editorial gates

Base: v3.121. Replace only `app.py` and `paid_yearly_editorial.py`.

- Removed Game section-number, length and planning-label rejections.
- Removed annual-act minimum-length and planning-label rejections.
- Treat a singly requested section marker as transport structure and assign it to its Python-owned slot.
- Stopped deleting returned sentences whose ISO dates are absent from a post-LLM whitelist.
- Kept true technical failures (no provider text, no configured provider, input token budget) and existing multi-section structural parsing.
- No changes to astronomy, packet selection, Monthly, natal, charts, printing or payment.

Offline: py_compile passed; three focused pytest cases passed; single-Game transport smoke tests passed.
Not tested: live Groq, full deployed app/PDF end-to-end, other repository tests.
Rollback: restore two files from v3.121.
