# Luna global workflow recovery

The supplied failed run used the old Daily JSON generator. Its schema and word checks failed, followed by HTTP 429 rate limits across signs.

Upload the extracted files, keeping their folders. This package includes the previous candidate plus the recovery changes; do not upload the ZIP itself.

CRITICAL: GitHub main currently lists only the three old workflow files. Upload .github/workflows/generate-plain-readings.yml, and replace all three other .yml files in that same directory. Uploading ordinary Python files alone does not switch GitHub Actions. Verify all four files exist at exactly those paths after upload.

The older workflows now show a retirement message and have no schedules or provider calls. Old Python generator commands use the shared plain-text pipeline. The new workflow accepts model/base URL from either Actions secrets or repository variables; the API key stays a secret. No provider/model is hard-coded.

Run Actions > Generate Luna plain-text readings > Run workflow. Select product, target date and optional sign. Daily date is the reading day; Weekly date is Monday; Monthly date is the first day. Leave sign blank for all twelve. Do not use Re-run jobs on an earlier failed run: start a new run from the uploaded branch.

The LLM returns plain prose. Python stores it. Public free pages never call the LLM. Rate limits receive bounded retries, with up to five minutes of requested waiting per retry. Longer limits require a later run. Completed matching readings are skipped and retained on reruns. Daily/Weekly/Monthly retain their agreed word ranges. Provider quotas cannot be removed by code.

Validation: 15 automated tests passed, including all three products, rate-limit recovery, retaining completed signs, legacy command routing, retired schedules, private diagnostics, and public-page isolation. Syntax and diff checks passed. These provider tests use simulated responses; real LLM prose and a successful GitHub run still need checking after upload. No remote files were changed or deployed by this task.
