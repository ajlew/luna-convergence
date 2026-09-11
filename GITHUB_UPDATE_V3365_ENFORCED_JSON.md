# Luna v3.36.5 - Enforced JSON Recovery

## Important

Run #4 used commit `0a4d618`, which reverted Luna to v3.35.6. Delete or ignore
all earlier extracted Luna update folders before using this package.

Upload exactly these files to the repository root, replacing the versions
already there:

- `luna_voice_provider.py`
- `luna_guided_voice.py`
- `site_config.py`
- `test_luna_v336_atomic_reports.py`
- `test_luna_llm_first_v335.py`

Commit message:

`Keep Groq JSON enforcement during recovery`

Before running the workflow, open `site_config.py` on GitHub. Line 4 must read:

`BUILD_LABEL = "Luna v3.36.5 — Enforced JSON Recovery"`

Then start a new **Generate and publish Daily Luna voice** workflow run on
`main`. Leave the date blank and use `Australia/Sydney`.

This release downgrades a rejected strict JSON Schema request to Groq's JSON
Object mode. It never removes JSON enforcement. The complete result still must
pass Luna's facts-hash, schema and evidence validators before publication.
