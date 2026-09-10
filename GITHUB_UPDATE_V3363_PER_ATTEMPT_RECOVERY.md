# Luna v3.36.3 - Per-Attempt Voice Recovery

Upload these files to the Luna repository root, replacing the existing versions:

- `luna_guided_voice.py`
- `site_config.py`
- `test_luna_v336_atomic_reports.py`
- `test_luna_llm_first_v335.py`

Use this commit message:

`Fix Daily Luna per-attempt recovery`

Then start a new **Generate and publish Daily Luna voice** workflow run on
`main`. Leave the date blank and use `Australia/Sydney`.

This release repairs and validates every Groq response immediately. It no
longer discards an earlier usable response and attempts to repair only the
last malformed response. It also restores the deterministic facts hash and
removes unexpected schema fields without changing the generated astrology.
