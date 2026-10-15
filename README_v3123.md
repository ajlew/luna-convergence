# Luna v3.123 — Annual evidence packet and report footer (focused patch)

**Required baseline:** v3.122 (v3.117 was the most recent release modifying `yearly_print_html.py`; later releases did not modify it).

**Replace exactly:** `app.py`, `paid_yearly_editorial.py`, `yearly_print_html.py` in the repo root. Do not replace any other files.

## Changes
- `paid_yearly_editorial.py`: build one deterministic, dated ledger from precomputed exact passes and supporting triggers for each four-month Read the Year act. Supply real rolling start/end dates. Prevent future-game dates from entering the wrong act through the LLM packet. Do not fabricate unnamed trigger identities. No post-LLM editorial validator added.
- `yearly_print_html.py`: move the standalone About this report heading/body to a restrained footer of the final synthesis section; leave natal SVG, activation SVG, curves, all content renderers and existing page break CSS unchanged.
- `app.py`: central version string v3.123.
- Test: offline checks confirm act-scope isolation and unnamed trigger handling.

## Tests
- Python compilation passed on all three files.
- Five focused tests passed (two evidence-ledger and three inherited v3.122 no-post-LLM regression tests).
- Live Groq run, current deployment, complete PDF render, and Stripe were **not** tested. An output improvement is not guaranteed without a live run.
- Older v3.121 tests demanding prose rejection are superseded and not applicable to v3.122+.

## Not changed
- Monthly, natal computation, transit computation, chart drawing, activation labels, Game and month prose generation, checkout, financial pricing.
- The reported raw-LaTeX strings were **not found** on the supplied page 13. No global character stripping has been added.
- Existing orphaned Key Dates and split month activation pages require a dedicated print-pagination fix and rendered regression testing.

Rollback: restore the three named files from v3.122 (`yearly_print_html.py` from v3.117).
