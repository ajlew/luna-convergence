# Luna v3.113 — Year Ahead voice section reliability

Apply over v3.112. Changed application files: `app.py`, `paid_yearly_editorial.py`.

## Exact change
- The Year Ahead section parser accepts harmless heading decoration/spacing (e.g. `### <<ISSUE: 01>>`) and canonicalises numeric section IDs.
- Each major Game is now generated and validated separately rather than in pairs. The evidence packet, astrological calculations, selected Games, report sections and customer prose requirements are unchanged.
- Required section markers must be present **and contain content**; no canned fallback is substituted.
- App version explicitly `v3.113`.

## Scope
No changes to Paid Monthly, astrology computation, print charts, checkout or Groq transport configuration. Per-Game provider requests may increase the number of voice calls, but reduce the risk of one Game response omitting another.

## Verification
`pytest -q test_v3113_voice_markers.py` — 2 passed.
Existing `test_yearly_reader_value_v385.py` — 2 passed.
Python compilation of the changed modules — passed.
A legacy v3.103 test has a fixed version-string assertion and is not a valid current-version test.
Live Groq completion and full customer output not tested; user should first run Owner report once after deployment.
