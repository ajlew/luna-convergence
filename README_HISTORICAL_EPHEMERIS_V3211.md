# Luna v3.21.1 — Compact Astronomy Memory

GitHub-safe revision of v3.21.

- Same 1950–2050 geocentric tropical archive.
- Same 36,890 days / 405,790 daily body positions.
- Same historical aspect recurrence API and Swiss Ephemeris refinement.
- SQLite storage compacted to date key + body id + longitude + speed.
- Sign, degree and retrograde state are derived when read.
- Redundant secondary index removed; the database is about 19 MB rather than 56 MB.
- No Luna customer-facing functionality removed.

Use the included `data/luna_ephemeris_1950_2050.sqlite3` in GitHub. It is below GitHub's 25 MB browser-upload limit.
