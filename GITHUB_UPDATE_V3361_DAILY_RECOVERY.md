# Luna v3.36.1 — Daily Publishing Recovery

Upload the files in this package to the Luna repository, preserving their paths.

## Changed files

- `app.py`
- `site_config.py`
- `scripts/generate_daily_voice.py`
- `.github/workflows/generate-daily-voice.yml`
- `test_luna_v336_atomic_reports.py`
- `test_luna_llm_first_v335.py`

## What this fixes

- publishes all 12 Daily readings automatically after midnight in Sydney;
- calculates the Sydney date when the workflow runs on schedule;
- spaces Groq requests to reduce token-per-minute failures;
- shows an animated message while live LLM work is running;
- displays the Luna build version in every page footer;
- blocks undated YouTube videos from remaining visible indefinitely;
- exposes safe Monthly component diagnostics when an atomic report is incomplete.

## First run

After uploading, open **GitHub → Actions → Generate and publish Daily Luna voice**.
Choose **Run workflow**. Leave the date blank and keep `Australia/Sydney`.

The workflow will create the current file under `generated/daily/`. Future Daily
documents run automatically at 14:10 UTC, which is after midnight in Sydney in
both AEST and AEDT.

## Commit message

`Publish Luna v3.36.1 daily recovery`
