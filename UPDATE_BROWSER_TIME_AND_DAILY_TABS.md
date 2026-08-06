# Luna Convergence — browser time and Daily topic tabs

## Files to replace in GitHub

1. `app.py`
2. `daily_narrative_v3.py`
3. `requirements.txt` only if the repository does not already contain the corrected Streamlit/Starlette pins included here.

## What changed

- Uses `st.context.timezone` to detect the visitor's browser timezone.
- Converts a trusted UTC clock into the visitor's local date and time.
- Defaults Daily Horoscope and Solar Convergence dates to the visitor's local calendar date.
- Defaults Luna timezone selectors to the detected timezone when it exists in `TIMEZONES`.
- Adds Daily reading tabs: `TODAY`, `LOVE`, `WORK & MONEY`, and `FRIENDS & FAMILY`.
- Keeps the evidence and technical calculation inside the `TODAY` tab.
- Keeps Statcounter and GA4 integration unchanged.

## Deployment

Upload the replacement files to the repository root, commit them, and reboot the Streamlit app.
