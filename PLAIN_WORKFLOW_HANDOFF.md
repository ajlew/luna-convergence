# Luna free-reading workflow — implementation candidate

Authority: Final Luna workflow, in plain English - Google Docs.pdf, four pages;
clarification: unique user-input-driven live interpretation is a later paid offering.

## Implemented path

Python calculations → private sign brief → scheduled LLM plain prose → basic text check
→ saved reading → public page and Weekly Studio.

The saved container uses JSON written by Python. The model never writes JSON,
metadata, an approval bundle, evidence IDs, or separate headline/affirmation/action fields.

Free Daily: 65–100 words, one or two paragraphs. Free Weekly: 130–180 words, two
paragraphs. Free Monthly: 280–380 words, four to six paragraphs. The prompt requires
imperative-led, humorous, affirming Luna prose with grounded examples and no guarantees.
The last sentence is extracted and displayed once under Your move.

Each public reading displays sign/period, calculated header and life areas, Luna's
prose, then the final move. If no current saved prose exists, it displays calculations
only. It does not invent a substitute story, expose job/provider errors, or call the LLM.

## Scope and preservation

- Removed the canned bridge added in the earlier patch.
- Removed the free Weekly multi-request composer, duplicate shared/sign story renderers,
  seven-day generated-copy requests and separate affirmation/action-field rendering.
- Replaced free Daily and Monthly published-bundle consumption with one plain-text source.
- Free dates use Australia/Sydney, explicitly labelled, matching scheduled generation.
- Weekly Studio uses the same saved sign reading; social cards take its final-action excerpt.
- Calculation rules, major-event/seasonal-gate logic and existing charts are retained.
- Existing paid/natal/PDF/email routes are not redesigned. Earlier speculative changes to
  Year Ahead in this conversation are reverted to the checked-out base version.
- Legacy interpretation modules still exist where shared with paid/editorial paths.
  This is not a claim that all literal strings or old narrative code were deleted repository-wide.
- No new personalised live paid service is implemented.

## Installation and first-generation checks

This is a changed-files package, not a complete application. Apply every included file
to the existing repository on a new branch, preserving scripts/ and .github/workflows/.
Do not replace only app.py. Base inspected: 809d32d; reconcile changes if main has moved.

1. Confirm the existing GitHub Actions secrets LUNA_VOICE_BASE_URL, LUNA_VOICE_MODEL
   and LUNA_VOICE_API_KEY. Do not add credentials to source files.
2. Run Generate Luna plain-text readings manually, entering product/date and one sign.
   Then repeat for all signs. Run current Daily, Weekly and Monthly before switching
   customers to this reader, because old approved-bundle files are not the new format.
3. Check generated/readings/ for completed signs. A failed sign makes the job fail,
   but the final save step commits successful signs. Rerun only the failed sign.
4. Inspect actual Daily, Weekly, Monthly and Studio output on desktop and mobile.
   Confirm real generated voice quality, event/house relevance and no repeated move.
5. This recovery package replaces all three known legacy workflow files with manual-only
   retirement notices. Their scripts forward to the shared plain-text generator.
   Only generate-plain-readings.yml owns the new generation schedules.
6. Merge/deploy only after these checks. No push, merge, deployment or scheduled job
   has been performed from this session.

Schedule: tomorrow's Daily at 10:00 UTC (evening Sydney), next Monday's Weekly on
Saturday at 11:00 UTC, next Monthly on the 25th at 10:00 UTC. These remain before
their periods begin in both AEST and AEDT. GitHub scheduling can be delayed; inspect job
status before publication. Manual target dates support recovery without hard-coded forecasts.

## Verification limits

Ten focused tests exercise prose checks, hashes, sign identity, partial failure,
targeted retry, HTML escaping, output order, action deduplication, and public-route call paths.
Mock prose is test data, never production fallback copy. Actual Groq output cannot
be tested here because the provider configuration is not present.
This candidate requires the first-generation and visual checks above before deployment.

Additional checks: real Daily, Weekly and Monthly fact packets calculated successfully;
September's equinox is present in the Monthly packet. Streamlit's test runner opens
Daily and accepts a selected sign without exceptions. Missing favicon/brand images
now leave a text-only brand instead of crashing application startup.
Weekly, Monthly and Weekly Studio also pass Streamlit execution smoke checks with
no exception or error elements; Studio renders twelve calculated sign panels.
These checks are not a desktop/mobile screenshot review of real generated prose.

Broader focused run: 26 passed, 6 failed. All six failures also reproduce against
untouched base 809d32d and exercise the older JSON provider/validation pipeline.
They were not hidden, skipped, or claimed fixed by this free-reading refactor.

## Included files

- app.py
- site_config.py
- plain_readings.py
- reading_facts.py
- plain_voice_generator.py
- scripts/generate_plain_readings.py
- .github/workflows/generate-plain-readings.yml
- test_plain_workflow.py
- test_luna_llm_first_v335.py
- test_fast_monthly_v338.py
- test_weekly_precision_and_sign_translation_v333.py
- PLAIN_WORKFLOW_HANDOFF.md
