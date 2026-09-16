# Luna reading and Studio recovery

## Confirmed faults
- The Weekly run rejected usable prose for exceeding a hard word count, then exhausted rate limits.
- At the repository snapshot inspected, Daily had all twelve signs. Weekly had six saved signs (Aries, Gemini, Libra, Scorpio, Capricorn and Pisces). There was no saved Monthly file.
- The previous Studio rewrite removed publishing tools and seven-day clip sections.

## Corrections
- Word ranges are prompt guidance only, across Daily, Weekly, Monthly and Studio. No rejection, cutting or retry for word length. Existing readings remain compatible.
- At most one content-repair request for actual invalid output. It edits the returned draft rather than starting again. Empty, JSON-shaped and truncated responses still need correction.
- Requests are paced. Temporary provider limits get bounded waits. Persistent rate limits stop the batch while preserving completed work. Reruns skip matching completed readings.
- Studio again includes usage instructions, shared-sky evidence, a weekly master script, YouTube title/description/tags, Instagram caption, twelve sign cards, full narration, seven daily clips/captions and downloads. The existing background download appears if its asset is present.
- The weekly master and seven daily clips use their own collective calculated brief, not a single sign's horoscope. These are plain-text outputs stored by Python. No live LLM calls from Studio.
- Studio generation is explicitly selected; it is not silently added to Weekly runs.
- Duplicate Your move labels are removed at display time. Reading headings have a scoped size.

## Upload and run
Upload these changed files to the matching repository paths. This patch builds on Luna-Global-Workflow-Fix; it does not replace your generated readings.

After upload, start NEW runs under Generate Luna plain-text readings:

| Product | Date for the reported pages | Sign |
| --- | --- | --- |
| weekly | 2026-09-14 | Leave blank: resumes missing signs |
| monthly | 2026-09-01 | Leave blank |
| studio | 2026-09-14 | Leave blank: generates one master and seven daily clips |

Those dates are examples for your screenshots, not dates hard-coded in the app. Use the selected week's Monday or month's first day for other periods. Daily now uses the current Sydney date; regenerate today's Daily if needed.

The studio option adds up to eight model requests on its first successful run. It skips saved matching scripts on later runs. It is an owner-selected generation step, not a paid personalised feature. Website sign readings remain their own full text; a 45-second master is separate copy for all signs. Timing labels are approximate; check the actual spoken length before video export.

Do not rerun historical jobs because they use the earlier code. The retired workflows remain retired. Provider quotas still apply, and code changes cannot recover drafts that the old run discarded.

## Verification
21 focused automated tests passed. They cover word counts accepted without retries, real-draft correction, rate-limit waits and batch stopping, preserving successful readings, retired workflows, rendering order and move deduplication, publishing-copy dates, and no provider calls from free pages. Syntax and YAML checks passed. Provider responses are simulated; no live model calls or deployment were performed during this correction.

The restored Studio function also passed a Streamlit render check with test prose: 21 expanders and five download controls. All six existing saved Weekly readings were checked against real calculations and remain loadable. Collective Studio briefs were checked against the actual calculation engine.
