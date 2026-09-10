# Luna v3.36 Page Integration Audit

**Audit date:** 10 September 2026  
**Evidence reviewed:** deployed Home/Daily, Weekly View, Monthly and Timing Map screenshots, plus the current v3.35.6 application source.

## Executive verdict

Luna's LLM has not disappeared everywhere. The deployed app currently has a **fragmented generation problem**:

- the Weekly main story and selected-sign story are reaching the page;
- the Daily narrative is not reaching the page;
- the Monthly main story fails while separately generated dated-event prose succeeds;
- the Year Ahead form unnecessarily asks for a Sun sign even though its natal calculation can determine it;
- some lower or collapsed sections cannot be certified from the supplied captures;
- the Weekly sign output repeats its action because the model places an action inside the story and the renderer prints the separate action field again.

The next release should be **v3.36 - Atomic Guided Reports**. Its governing rule should be:

> Calculate once, generate in paced sections, validate the complete report, then display one coherent document.

## Page-by-page evidence

| Page or section | Observed state | Evidence | Required correction |
| --- | --- | --- | --- |
| Home / Daily | **LLM failed** | The page displays “CALCULATIONS READY. LUNA'S VOICE IS PAUSED.” Calculated Moon square Uranus remains visible. | Pre-generate and persist all public Daily sign readings. A visitor should read cached copy, not initiate generation. |
| Home featured video | **Stale fixed content** | On 10 September, the embedded video still advertises 31 August-6 September. | Add a week identifier to the video configuration and hide an expired embed automatically. |
| Weekly shared story | **LLM succeeded** | “LET THE INNER REVOLUTION FINISH ITS SENTENCE” appears as a connected narrative. | Preserve this path and cache it as a published weekly asset. |
| Weekly selected-sign story | **LLM succeeded with duplication** | Sagittarius receives a sign-specific headline and story, but “Your move” appears inside the story and again in the dedicated `YOUR MOVE` field. | Reject section labels inside story fields and compare the final story sentence with `your_move` for semantic duplication. |
| Weekly seven-day cards | **Not verifiable from capture** | The “Seven calculated days” panel is collapsed. | Add an admin status table that reports generated, cached, failed or missing for every day. |
| Monthly main story | **LLM failed** | The page states that Luna's writing service is unavailable. | Do not publish a partial Monthly report. Regenerate or show calculated evidence only. |
| Monthly dated events | **LLM succeeded separately** | Six extensive event interpretations appear below the failed main story. | Assemble these into the same Monthly report bundle and publish them atomically with the main story. |
| Monthly personal contacts | **Not verifiable from capture** | The relevant panel is not shown expanded. | Include its status in the Monthly bundle manifest and test it explicitly. |
| Year Ahead input | **Incorrect redundant question** | The form asks for both Sun sign and full natal information. | Remove the Sun-sign selector. Derive the sign from the natal snapshot. |
| Year Ahead generated report | **Not verifiable from capture** | The supplied capture shows the input page before a completed report. | Test main narrative, natal contacts and transit cards as one report bundle. |

## Why the Monthly page looks contradictory

The Monthly page currently makes independent calls for:

1. the main month narrative;
2. the dated-event collection;
3. personal transit contacts.

One call can fail or hit a rate limit while another succeeds. The page then combines incompatible states: a failure banner at the top and apparently complete Luna prose below it. This is technically possible but editorially unacceptable.

The fix is **not** one oversized Groq request, because that would reintroduce the earlier 413 and truncation failures. Monthly should use:

1. one canonical calculated fact packet;
2. several small, paced LLM requests;
3. one report manifest recording every required section;
4. validation of the assembled document;
5. one atomic publication decision.

Until every required section is valid, the public page should display calculated evidence and generation status, not a mixture of completed and missing prose.

## Correct authority for Sun sign

| Product | User supplies natal data? | Correct source of Sun sign | Selector decision |
| --- | ---: | --- | --- |
| Daily public horoscope | No | User choice | Keep selector |
| Weekly public horoscope | No | User choice | Keep selector |
| Monthly personalised report | Yes; birth date is required | Natal calculation | Remove selector |
| Year Ahead / Timing Map | Yes; natal data is required | Natal calculation | Remove selector |
| Natal Snapshot | Yes | Natal calculation | No separate selector |

The Year Ahead selector is currently only a duplicate validation step. The application derives the Sun sign from the natal snapshot and rejects a mismatch. That creates work for the customer without adding astronomical accuracy.

### Birth-time edge case

Unknown birth time does not normally prevent the Sun sign from being calculated. A special rule is needed only when the Sun changes signs during the recorded birth date:

- if the Sun remains in one sign for the whole local date, derive it automatically;
- if the date contains a solar ingress and the time is unknown, ask for an approximate time or present a targeted two-sign clarification;
- never silently choose a sign on an ingress date.

## v3.36 required changes

### Priority 0 - customer-facing correctness

1. Remove the Year Ahead Sun-sign selector in `timing_map_page()` and use the calculated natal Sun sign.
2. Remove the Monthly Sun-sign selector in `_free_monthly_profile()` because the form already requires birth data.
3. Introduce a complete Monthly report bundle containing:
   - calculated identity and date range;
   - main narrative;
   - dated events;
   - personal contacts when available;
   - affirmation;
   - one final monthly action;
   - facts hash, model version and validation status.
4. Generate the bundle through small paced requests, but display it only when the full required bundle validates.
5. Apply the same atomic-report rule to Year Ahead: main story, natal contacts and transit cards must share one report identity and status.
6. Pre-generate public Daily outputs and persist them. Page visits must read the published cache.
7. Add component-level diagnostics to Studio/admin pages without exposing provider errors to ordinary customers.
8. Prevent stale featured videos from appearing after their configured week.

### Priority 1 - editorial quality

1. Reject `YOUR MOVE`, `REMEMBER`, `AFFIRMATION` and similar section labels inside narrative paragraphs.
2. Reject a collection item when its story already repeats the dedicated `move` field.
3. Tighten sign translations so affirmation is evidence-linked, not generic first-person encouragement.
4. Ensure each page has one action hierarchy: one primary move, with subordinate event advice only where necessary.
5. Add a page-level completeness badge in Studio: `complete`, `partial`, `failed` or `stale`.

## Recommended Monthly document structure

```json
{
  "report_type": "monthly",
  "report_id": "facts-hash",
  "identity": {
    "calculated_sun_sign": "Libra",
    "month": "2026-09",
    "houses_available": true
  },
  "main": {
    "headline": "...",
    "opening": "...",
    "story": ["...", "...", "..."],
    "affirmation": "...",
    "your_move": "..."
  },
  "dated_events": [
    {
      "source_id": "...",
      "date": "2026-09-10",
      "headline": "...",
      "story": "...",
      "move": "..."
    }
  ],
  "personal_contacts": [],
  "validation": {
    "complete": true,
    "required_sections": ["main", "dated_events"],
    "facts_hash": "...",
    "voice_version": "v3.36"
  }
}
```

This is one document contract even if the provider work is divided into several rate-limited calls.

## Likely implementation files

| File | Change |
| --- | --- |
| `app.py` | Remove redundant selectors; render atomic bundles; add status handling; suppress stale featured video. |
| `luna_guided_voice.py` | Add bundle validation and duplication rules. |
| `luna_voice_provider.py` | Reuse v3.35.6 pacing; expose structured retry metadata to internal diagnostics. |
| `luna_report_bundle.py` | New assembler for Monthly and Year Ahead report parts. |
| `site_config.py` | Advance version and add optional featured-video week key. |
| `tests/test_luna_v336_atomic_reports.py` | Add form, completeness, caching and editorial regression tests. |

## Acceptance tests

The release is complete only when all of these pass:

1. Year Ahead contains no manual Sun-sign selector.
2. Monthly personalised input contains no manual Sun-sign selector.
3. Both pages display the sign calculated from natal data after generation.
4. An unknown birth time on a non-ingress date still calculates a sign safely.
5. An unknown birth time on a solar-ingress date triggers an explicit clarification.
6. Monthly never displays a voice-failure banner above successful event prose.
7. Monthly publishes either one complete validated document or calculated evidence only.
8. Year Ahead publishes either one complete validated document or calculated evidence only.
9. Weekly sign output contains one action, not the same action twice.
10. Daily reads a published cached result without a visitor-triggered Groq call.
11. Studio shows a status for every weekly sign, every day, Monthly section and Year Ahead section.
12. A featured video outside its configured week is hidden or replaced.
13. Existing ephemeris, natal, house, aspect, payment and privacy tests remain unchanged and pass.

## Release sequence

1. Deploy the v3.35.6 rate-limit pacing fix first.
2. Implement v3.36 form simplification and report-bundle assembly.
3. Run unit and integration tests using mocked Groq responses, including 400, 413, 429 and truncated JSON cases.
4. Generate a full Daily, Weekly, Monthly and Year Ahead test set.
5. Inspect the rendered pages, including all collapsed panels.
6. Publish v3.36 only after the completeness matrix is entirely green.

## Final recommendation

Do not pay for a higher Groq tier yet. The current 8,000-token-per-minute limit is enough for Luna's present traffic if generation is paced, cached and assembled away from visitor rendering. The immediate priority is reliable report orchestration, not more capacity.

The correct next-round decision is therefore:

> Remove redundant Sun-sign questions from natal-driven products, make Monthly and Year Ahead complete documents rather than collections of unrelated calls, and never show customers a partially generated report.
