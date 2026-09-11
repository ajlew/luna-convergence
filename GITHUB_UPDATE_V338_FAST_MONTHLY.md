# Luna v3.38 — Fast Monthly

## Product split

- Free Monthly asks only for the reader's Sun sign.
- It covers the current month using shared ephemeris data and whole-sign houses.
- It does not calculate a natal chart or promise exact personal contacts.
- Personal Monthly remains A$3.30 and derives the Sun sign from the paid natal details.
- Year Ahead remains A$14.95.

## Performance change

The public Monthly reads a validated file from `generated/monthly/`. It does not
call Groq during a normal `published` page visit. Calculated sign/month reports
are cached across visitors for 31 days.

## First deployment

Upload the changed files, then run:

`Actions → Generate and publish Monthly Luna voice → Run workflow`

For the first run choose the current year and month, use `Australia/Sydney`, and
leave sign blank. The workflow checkpoints every completed sign. If one sign
fails, rerun with that sign selected; already validated material is retained.

## Automatic schedule

On the 25th of each month, GitHub Actions generates the following month's twelve
sign forecasts. Visitors only read the published JSON.

## Files

- `app.py`
- `site_config.py`
- `monthly_voice_publisher.py`
- `scripts/generate_monthly_voice.py`
- `.github/workflows/generate-monthly-voice.yml`
- `test_fast_monthly_v338.py`

