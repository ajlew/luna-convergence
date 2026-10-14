# Luna v3.101 — Navigation only + Year Ahead plan consolidation

**Required code baseline:** v3.100. Apply the included `app.py` only to that baseline.

## Exact code change
- `app.py`: hard-coded `APP_VERSION` advanced from `v3.100` to `v3.101` and corresponding build description changed.
- `app.py`: only the eight `top_navigation()` labels/order and the existing legacy `this-month` active-label check updated.
- No paid report code, ephemeris, writers, PDF renderers, auth, Stripe or natal calculations were edited.

## Menu order
Free: Daily Horoscope (`/`), Weekly Horoscope (`/weekly-view`), Monthly Horoscope (`/monthly`).
Paid: Personal Reports (`/reports`), Your Year Ahead (`/timing-map`), Birthday Card (`/birthday-card`).
Reference: House Guide (`/house-guide`), Solar Year (`/solar-year`).
All existing URLs unchanged.

## Document
`Luna_Paid_Year_Ahead.md` consolidates the full uploaded updated yearly plan with master rules, source conflict resolution, and critique acceptance tests. It is a specification only; it does **not** modify Year Ahead.

## Tests and limitations
Run: `python test_v3101_navigation.py`; `python -m py_compile app.py`.
Static tests do not verify deployment, page rendering, or live Stripe/Groq behaviour. Rollback by restoring v3.100 `app.py`.
