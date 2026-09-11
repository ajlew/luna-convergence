# Luna v3.37 — Calculated Intelligence

Upload the contents of this package to the `luna-convergence` repository root while preserving the included folders.

## Release contract

- Luna's deterministic engine owns signs, houses, aspects, dates, orbs and evidence hashes.
- The LLM receives calculated evidence and writes interpretation in Luna's guided voice.
- Python attaches provenance, source IDs and hashes after generation.
- Daily signs generate independently; one failure no longer discards successful signs.
- A failed sign can be retried from the workflow's optional `sign` input.
- Live generation displays visible calculation, interpretation and validation progress.
- Natal Snapshot and Year Ahead derive the Sun sign from birth information.
- The footer identifies `Luna v3.37 — Calculated Intelligence`.

## Upload

1. Open the repository root on the branch deployed by Streamlit, normally `main`.
2. Choose **Add file → Upload files**.
3. Drag every file and folder from the extracted package into the repository.
4. Confirm that `.github/workflows/generate-daily-voice.yml` remains inside `.github/workflows` and `scripts/generate_daily_voice.py` remains inside `scripts`.
5. Commit with: `Upgrade Luna to v3.37 Calculated Intelligence`
6. Wait for Streamlit to redeploy.

## Daily recovery

Run **Actions → Generate and publish Daily Luna voice → Run workflow**.

- Leave `sign` blank to generate all signs.
- Select one sign, such as `Gemini`, to retry only that sign.
- Successful signs are retained even when another sign fails.

## Verification

The focused v3.37 regression group passed 38 tests and all edited Python files compiled. The complete local suite could not start because the execution image lacks the C compiler required to build the repository's pinned `pyswisseph` version.
