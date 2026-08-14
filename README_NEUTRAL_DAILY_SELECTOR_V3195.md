# Luna v3.19.5 — Neutral Daily sign selector

The Daily landing no longer assumes Sagittarius for a new visitor.

- First state: `Choose your star sign`.
- No horoscope is generated until the visitor makes a selection.
- After selection, sign switching remains immediate.
- The sign choice persists for the browser session.
- `daily_reading_generated` now represents an actual sign choice rather than an automatic page-load event.

This applies to `/`, `/daily-horoscope`, and `/august-2026-horoscopes` because all three use the same lean Daily renderer.
