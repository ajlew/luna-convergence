# Luna Convergence v3.30 — 12-Month Timing Map Pilot

## What was added

- New public route: `/timing-map`
- New navigation item: **12-Month Map**
- New `timing_map.py` engine using the existing tropical geocentric Swiss Ephemeris stack
- Personal natal-to-transit scan across 365 days
- Transit planets: Jupiter, Saturn, Uranus, Neptune and Pluto
- Natal targets: Sun through Pluto, plus Ascendant and Midheaven when exact birth time/location are available
- Aspects: conjunction, sextile, square, trine and opposition
- Direct/retrograde repeated-pass detection
- 8–10 ranked story windows instead of an unfiltered transit dump
- Relative timing-intensity strip across every calendar month touched by the 365-day window
- Collapsed **Why Luna sees this** evidence for every story
- Anonymous A$7.95 pilot demand test: Yes / Maybe / No
- Free Natal Snapshot now links directly into the Timing Map
- Privacy copy updated for Timing Map birth-data handling
- Search Console URL list updated for `/timing-map`

## What was not changed

- Daily Horoscope engine
- Weekly View or Weekly Studio
- Monthly forecast engine or Monthly pricing
- Existing Monthly Stripe checkout / fulfilment
- Year-ahead checkout / fulfilment
- Solar Convergence / Solar Year
- House Guide
- Forecast Library / admin routes
- Existing Natal Snapshot calculation
- Existing analytics integrations

The original v3.29.1 `app.py` contained 62 named functions. v3.30 contains all 62 plus five Timing Map integration helpers. No existing named function was removed.

## Demand measurement

The pilot records these new analytics events:

- `timing_map_generated`
  - birth-time-known boolean
  - number of ranked stories
  - number of turning points
- `timing_map_price_test`
  - response: yes / maybe / no
  - pilot price: 7.95 AUD
  - birth-time-known boolean

Birth date, birth time, birthplace, coordinates and natal longitudes are not added to those analytics events.

## Pricing / checkout status

The A$7.95 element is deliberately a demand test only. No new Stripe product or Price ID is required for v3.30, and no payment is collected from the Timing Map page. This avoids changing the working paid-report stack before demand is observed.

## Calculation boundary

The map uses day-level timing. The displayed exact date is the closest local calendar day to the exact natal transit contact found in the 365-day scan. It does not claim minute-level event timing.

Birth-time unknown:
- planetary natal positions are used;
- Ascendant, Midheaven and houses are omitted;
- Luna does not invent angular precision.

## Deployment

### Safest route

Replace the repository with the contents of the complete v3.30 GitHub-safe backup.

### Small patch route

Upload/replace these files at repository root:

- `app.py`
- `site_config.py`
- `SEARCH_CONSOLE_URLS.txt`
- `test_ga_seo.py`
- `timing_map.py` (new)
- `test_timing_map_v330.py` (new)

No change is required to `requirements.txt`; `pyswisseph` is already present in the existing app requirements.

## QA

- New Timing Map tests: passed
- Existing targeted integration tests: passed
- Full repository test suite: **130 passed**
- Python syntax compilation: passed
- Existing named `app.py` functions removed: **0**
