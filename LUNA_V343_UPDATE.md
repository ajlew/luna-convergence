# Luna v3.43 — complete readings and Studio

Upload the extracted files to the existing repository, preserving their folders, then commit/merge to main. Do not upload only the ZIP. No generated readings or credentials are included.

## What changed

- `all` now covers Daily, Weekly, Studio and Monthly. Studio includes the collective weekly overview/master, seven meaning-and-energy readings and seven short clips. Existing sign cards, captions and downloads remain.
- Relevant code uploads to main trigger the generation workflow. Morning/evening scheduled runs recover every current product and prepare tomorrow's Daily. Saturday prepares the coming Weekly and Studio. The monthly advance schedule remains.
- Blank manual dates use the current Sydney date. This prevents an accidental future-only Daily run.
- Each event is passed to the LLM with its own house meanings. Explicit planet-house associations are preserved where available; group house lists are not falsely paired with individual planets. Daily supporting calculation labels are now included in the brief.
- The prompt requires a capitalised imperative opening, grounded examples, dry humour and natural affirmation. It prohibits speculative profit promises and borrowing life areas from another event.
- Supplied eclipses, equinoxes, solstices and lunar turning points must appear in the prose. Full readings and the weekly overview also include supplied A+ background events. A missing event allows one draft repair, not an endless regeneration loop. These are name-coverage checks, not proof that every sentence has perfect astrological interpretation.
- A writing revision marker refreshes the old affected copy once for requested/current periods. Later runs reuse current outputs. Historical periods are not bulk regenerated. Failed refreshes preserve the previous saved text until a replacement succeeds; changed-fact text still fails the existing facts check.
- `refresh` rewrites a selected product/sign intentionally. Leave it off for ordinary recovery. `check_only` reports completeness without LLM calls or file writes.
- Key calculations remain collapsed. The overview is visible in the shared editorial style. Your move is smaller and capitalised. Existing reading, clip, card and publishing downloads remain.
- Model output remains plain prose. Python storage metadata is internal. No approved model JSON bundle, canned horoscope paragraphs, hard word-count rejection or public live LLM calls have been introduced.

## After upload

Open Actions → Generate Luna plain-text readings and inspect the automatically started run. Completion summaries count current outputs. If no run started, choose Run workflow → product `all`, leave date and sign blank, leave refresh/check_only off.

A fully empty current-period set contains 51 readings: 12 Daily, 12 Weekly, 12 Monthly, 1 collective overview, 7 daily meanings and 7 short clips. Maintenance also prepares 12 Daily readings for tomorrow. The first upgrade therefore needs new generation for missing or older-revision content. These calls use your configured LLM account; this package does not include or pretend to have generated that content.

If a provider quota stops a run, successful readings are committed. A later ordinary run resumes incomplete work. Do not tick refresh to resume: that would regenerate successful content.

Technical failures stay in GitHub Actions. Streamlit must be connected to the branch receiving generated/readings commits. This update has not been deployed from this workspace.

## Verification

37 tests pass. A full offline integration test creates 51 saved readings from real calculation packets using clearly artificial test prose, verifies completeness without further generation, then opens selected-sign Daily, Weekly and Monthly plus Weekly Studio through Streamlit's full application imports. It checks visible reading bodies, seven meaning blocks, completed clip downloads and overview content. Separate tests cover Pisces event/house associations, omitted equinox/lunar/eclipse labels, bounded draft repair, revision refresh, failed-refresh retention and Sunday rollover. Workflow YAML and shell syntax also pass. These tests do not claim that live LLM prose was generated or that every semantic statement can be verified by keyword checks.
