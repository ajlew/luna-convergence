# Luna v3.36.6 - Certainty Validation Recovery

Run #5 used v3.36.5, validated Aries, and then rejected Taurus only because
the generated prose contained the word `guaranteed`. The validator could not
distinguish a promise from responsible wording such as `nothing is guaranteed`.

Upload exactly these five files to the Luna repository root:

- `luna_voice_provider.py`
- `luna_guided_voice.py`
- `site_config.py`
- `test_luna_v336_atomic_reports.py`
- `test_luna_llm_first_v335.py`

Commit message:

`Allow negated guarantee language in Luna validation`

Before running the workflow, open `site_config.py` on GitHub. Line 4 must read:

`BUILD_LABEL = "Luna v3.36.6 — Certainty Validation Recovery"`

Then start a new Daily workflow run on `main`, leave the date blank, and use
`Australia/Sydney`. Do not rerun the previous failed execution.

Actual promises remain prohibited. Only clearly negated guarantee language is
accepted, and all existing facts-hash and evidence checks remain active.
