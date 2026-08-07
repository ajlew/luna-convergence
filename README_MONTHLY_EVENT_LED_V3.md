# Luna Monthly Narrative v3 — Event-Led Story Engine

This update changes the monthly reasoning layer while preserving the existing Luna Streamlit interface, browser-time detection, monthly preview route/fallback, Stripe flow and daily engine.

## What changed

1. **Event-led plot selection**
   - Eclipses, lunations, stations, exact aspects and ingresses are normalized into one event-importance score.
   - Event clusters, not the fixed solar-house transition, now choose the primary and secondary monthly plots.
   - A late eclipse automatically controls the late-month reversal/resolution.

2. **Deterministic scenario database**
   - `scenario_library.json` stores scenario families, house/planet/event rules and positive/friction examples.
   - Scenario selection is evidence-ranked. There is no random selection.
   - The first calibration set uses concept-level scenario associations drawn from the August 2026 Aries, Leo and Sagittarius benchmark readings plus Luna's house matrix. No benchmark prose is copied.

3. **Rulership / sign amplification**
   - Sign rulers contribute to event importance without multiplying the same astronomical signal several times.

4. **Narrative reconciliation**
   - Monthly arcs now expose a `selection_rationale`, `supporting_house` and QA result so the public story can be traced back to the calculation layer.

5. **Love / Work / Money mini-engines**
   - These sections re-rank scenario families by domain instead of rotating a small fixed card library.

6. **Local date transparency**
   - The report header and technical appendix state the selected/browser timezone used for event dates.

7. **Print placement**
   - `Print / Save PDF` now appears directly below the report hero instead of at the bottom.

8. **QA circuit breakers**
   - `monthly_qa.py` checks eclipse coverage, story-house traceability and scenario output.
   - `test_monthly_event_led_v3.py` confirms all 12 August 2026 signs generate, include both eclipses in narrative evidence and produce 12 unique event-led headlines.

## Files to upload to GitHub root

Replace:
- `app.py`
- `scenario_engine.py`
- `monthly_arc_engine.py`
- `monthly_narrative_v1.py`
- `monthly_experience_v1.py`
- `synthesis.py`
- `site_config.py`

Add:
- `scenario_library.json`
- `monthly_qa.py`

Optional test file:
- `test_monthly_event_led_v3.py`

No change is required to `requirements.txt` for this update.
