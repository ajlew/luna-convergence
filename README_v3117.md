# Luna v3.117 — Year Ahead controlled regression correction

Baseline: v3.116 deployed code (whose charts were retained) with the earlier accepted Year Ahead presentation as the output reference. Application version is explicitly updated to v3.117.

Files changed:
- app.py — explicit version number only.
- yearly_print_html.py — show `NatalSignature.evidence` under each Natal Strength when calculated evidence exists. No fixed signs/aspects.
- paid_yearly_editorial.py — reject annual sections containing internal assembly markers or raw packet planning fields, rather than printing them. Keeps three-segment generation and Groq configuration unchanged.

Known limits: A successful live Groq generation, chronological coherence of the whole annual essay, cover beauty and full 35-page PDF pagination cannot be proven by offline tests. The generation now fails closed if specific prohibited planning artefacts recur; this can cause report-unavailable status rather than silently selling corrupted text. Do not claim complete production acceptance until a real owner report is reviewed.

Tests: pytest -q test_v3117.py test_v3116.py test_v3111.py -> 7 passed. Python compile and zip integrity checked.

Apply these files to v3.116. Do not overwrite Paid Monthly or other files.
