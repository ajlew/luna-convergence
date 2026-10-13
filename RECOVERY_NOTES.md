# Luna Paid Monthly — Integrated Recovery v3.97

Replaces the Paid Monthly regression sequence with a single tested state, not a chain of incremental patches. This ZIP is a cumulative overlay for the full Luna repository.

## Scope
- The original single-call Monthly generation flow is retained.
- Reject refusal/apology/error replies and incomplete non-narrative text in the provider and result layers before the screen, PDF, or email can be delivered. The existing owner export withholding remains intentional for genuine failures.
- Read the pattern reuses the current natal engine's calculated signature narrative and strengths; it no longer uses the newly invented planet-role template or a fixed example.
- Preserves Natal Strengths, natal/activation wheels, Key Dates, shared screen/HTML/PDF renderer, checkout and Year Ahead.
- No Groq calls, no canned fallback stories, no fabricated natal facts.

## Packaging
The 15-file package is cumulative: only app.py changes from the preceding v3.96-focused update. monthly_shared_view.py is deliberately retained unchanged from v3.94 to keep the unified screen/print pipeline. The remaining files are cumulative dependencies, not new changes.

## Tests
- Python compilation.
- Eight offline recovery assertions (refusal examples, accepted substantive article, natal signatures, shared HTML).
- Five relevant integration checks passed with full repository (v3.93 unified Monthly and v3.94 strengths suites).
- One obsolete v3.89 test expects the old alternate PDF renderer; it conflicts with the approved v3.93 single-render architecture and is not treated as a valid release gate.
- ZIP integrity verified.

Live Groq and deployed visual tests remain unverified. If provider produces a refusal, the paid output is withheld, not mislabelled as success. If the prebuilt month source is missing, this recovery does not invent it.
