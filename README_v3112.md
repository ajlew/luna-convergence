# Luna v3.112 — Year Ahead Print Integrity

Install over the repository running v3.111. Replace only `app.py` and `yearly_print_html.py`.

Changes: hard-coded application version `v3.112`; evidence (calculated natal aspect/orb labels where provided by natal signatures) beneath Year Ahead strengths; denser collision avoidance for activation-wheel planet names, retaining true natal coordinates; print page-break protection around the activation heading/chart; slight A4 margin adjustment.

Not changed: Paid Monthly, calculation engine, Groq, checkout, narrative prompts, annual and monthly transit curve maths, and full natal wheel.

Verification: targeted PDF production and 12-month synthetic report render, Python compilation, targeted tests. Full live Libra and unknown-time customer report signoff remains necessary. A pre-existing full-suite test has an incompatible `_serialize_story` call signature; it was not modified. No LLM calls.

Other editorial issues found in the supplied PDF (chronological Read the Year, duplicated monthly insights and trigger wording) are **not fixed in this release** and need separate writer validation. Do not assume they were corrected by presentation-only updates.
