LUNA MONTHLY TIMEZONE FIX — GITHUB ONLY

Replace these TWO files in the root of your GitHub repository:

1. paid_forecast_context.py
2. monthly_report_pipeline.py

Do not run a local installer.
Do not regenerate the October prebuilt JSON files.
Do not replace app.py for this fix.

What changes:
- Paid Monthly first looks for a prebuilt base matching the report/current timezone.
- If it does not exist, it reuses the canonical Australia/Sydney prebuilt month.
- Birth timezone remains part of the fixed Natal Player and is not replaced by the current/report timezone.
- The reader/current timezone remains available separately for personal activations and local timing.
- Duplicate customer-facing Key Date date/event pairs are removed.

Retest:
Sagittarius / October 2026 / Pacific/Port_Moresby

Expected:
- Read the month no longer fails with "found 0 Daily briefs".
- The existing 31-day Sagittarius October prebuilt background is reused.
- Full Moon in Taurus should not be listed twice in Key dates.
