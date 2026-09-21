# Luna v3.50 — Birthday Card Studio Calculation

## What changed

- The generated or customer-supplied poem now renders in IBM Plex Mono, Luna's typewriter face.
- A timed card shows the strongest calculated natal contact for the Sun and for the Moon beneath their sign placements.
- Calculation evidence follows the Weekly Studio rhythm: `Sun sextile Jupiter · applying · 0.48° orb at birth`.
- Calculation lines use Josefin Sans, matching the Sun and Moon placement typography.
- Applying/separating is derived from the Swiss Ephemeris planetary speeds at birth.
- Date-only cards omit natal aspect, phase and orb lines because those values are not safe without a birth time.

## Files

- `birthday_card.py`
- `natal_snapshot.py`
- `test_birthday_card.py`

## Release

This package is cumulative from the current Birthday Card branch. Upload it over the existing branch, preserve the `assets/fonts/` directory, run checks, and merge only after reviewing a known-time and unknown-time card.
