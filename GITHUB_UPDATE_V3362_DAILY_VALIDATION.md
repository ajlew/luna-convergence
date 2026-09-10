# Luna v3.36.2 — Daily Validation Recovery

Replace these files in the Luna repository root, preserving their paths:

- `luna_guided_voice.py`
- `site_config.py`
- `test_luna_v336_atomic_reports.py`
- `test_luna_llm_first_v335.py`

Commit message:

`Fix Daily Luna validation recovery`

After committing, open **Actions → Generate and publish Daily Luna voice** and
rerun the failed workflow. Leave the date blank and keep `Australia/Sydney`.

The update adds a third model correction attempt and a final structural repair
for valid model prose returned as one paragraph or with a non-imperative action.
It does not invent astrology and does not restore canned interpretation.
