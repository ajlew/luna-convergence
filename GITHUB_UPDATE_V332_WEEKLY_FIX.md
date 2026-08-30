# Luna Convergence v3.32 — Weekly Precision + Sign Translation

## Files changed

- `app.py`
- `astrology_engine.py`
- `luna_life_scenes.py`
- `major_event_registry.py`
- `site_config.py`
- `weekly_view.py`
- `test_weekly_app_integration_v329.py`
- `test_weekly_view_v329.py`

## File added

- `test_weekly_precision_and_sign_translation_v333.py`

## Keep deleted from GitHub

These obsolete files were already excluded from the complete v3.31 package and must not be restored:

- `luna_convergence_app_monthly_preview.py`
- `monthly_story_profiles_v296_calibration.py`

## What changed

- Weekly aspect timing now searches the complete local day instead of treating noon as the entire day.
- Exact aspects display `exact today` with the approximate local time and timezone.
- Moon–Saturn conjunction, Moon–Uranus conjunction, Sun–Moon trine, Moon–Mercury square and Venus–True Node trine now use planet-pair-specific interpretation.
- Jupiter trine Saturn now describes controlled, sustainable growth and incorporates simultaneous Mars–Saturn pressure.
- A calculated weekly synthesis connects the opening, support and pressure into one story.
- The 12-sign layer now maps the selected weekly events through whole-sign houses instead of using broad all-planet occupancy and random house sentences.
- Every social-card action is selected as a complete short command. No command is cut at an arbitrary word limit.
- House 3 resolves to communication before the broader learning/travel keyword family.
- Weekly content headings use non-anchor elements so copied text does not acquire `[svg]` links.

## Verification

- Python compilation passed for all modified Python files.
- 34 focused weekly, major-event, convergence and integration tests passed.
- Live Streamlit smoke check returned HTTP 200 for `/weekly-studio`.
- A broader legacy run passed 169 tests. Its remaining failures concern pre-existing removed August preview behavior and unrelated older monthly/daily expectations.
