# Luna staged generation

Manual `all` runs now use this order:

1. Daily
2. Pause one hour
3. Weekly
4. Pause one hour
5. Monthly
6. Pause one hour
7. Weekly Studio, including its daily and meaning clips

Current readings remain cached and are skipped. A provider-limit result from one
stage is recorded, but it no longer prevents the later stages from running after
their pause.

Routine schedules stay economical:

- Evening Sydney run: Daily.
- Morning Sydney run: maintenance of incomplete current readings.
- Saturday Sydney run: Weekly, pause one hour, then Studio.
- Monthly run: Monthly only.

The manual `check_only` option skips the hour-long pauses because it makes no LLM
requests.
