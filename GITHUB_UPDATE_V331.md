# Luna Convergence v3.31 — GitHub update

This edition replaces campaign-specific public defaults with one dynamic forecast context.

## Production behaviour

- Public sign selectors start neutral. Luna waits for the visitor to choose a star sign or verifies it from birth data.
- The free Monthly page now includes forecast month and forecast year controls.
- The selected sign, month and year drive the calculation, page metadata, headings, event chronology, historical comparisons, chart controls and share title.
- Monthly event cards come from the production chronology engine. They are no longer restricted to four events from one campaign month.
- Daily and report-generator dates default from the visitor's current date/timezone instead of a fixed development date.
- The former static sample page now generates a live sample from selected inputs.
- The old August campaign URLs remain hidden redirects to `/monthly` so existing ads, bookmarks and indexed links do not break.

## Necessary constants retained

- the twelve zodiac signs and their order;
- whole-sign house mappings and sign traits;
- planetary names, aspect rules, solar gates and date boundaries;
- the 1950–2100 supported forecast range;
- legacy URL strings used only for backward-compatible redirects.

## GitHub upload

Upload the contents of this folder to the repository root. The deployed Streamlit entry point remains `app.py`. Do not restore `luna_convergence_app_monthly_preview.py`; it was an obsolete duplicate and is intentionally excluded from this release.

## Verification completed

- Python compilation passed.
- Streamlit home page smoke test passed with no runtime exceptions.
- Neutral sign selection and a generated Aries Daily passed.
- Dynamic Monthly calculations passed for August 2026, September 2026, February 2027 and December 2031.
- The focused global-context regression suite passed: 47 tests, including all twelve signs across multiple months and years.
