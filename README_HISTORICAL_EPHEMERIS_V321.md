# Luna v3.21 — Astronomy Memory

Luna now ships with a structured Swiss Ephemeris archive spanning **1950–2050**.

## Design

- `data/luna_ephemeris_1950_2050.sqlite3` — prebuilt archive.
- `historical_ephemeris.py` — read/query contract.
- `build_historical_ephemeris.py` — deterministic archive builder.
- Daily positions: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto and True Node at 00:00 UTC.
- Event index: sign ingresses, planetary stations and exact major aspects for Sun/Mercury through Pluto/True Node. Lunar aspects are calculated on demand rather than precomputed.
- Frame: geocentric tropical.
- Uploaded PDF ephemerides remain validation/reference artifacts; they are not transcribed into the calculation database.

The public Daily/Monthly experience is unchanged. The archive is a backend knowledge layer and is exposed only in Ephemeris Admin for QA/research.
