# Luna Convergence — Paid Year Ahead
## Updated Build Plan & Product Architecture — v3.86 Revised
### Consolidated from:
- `Luna_Year_Ahead_Simplified_Build_Plan(2).md`
- `Luna_Year_Ahead_Reader_Guide(1).md`
- `Guideline year.pdf`
- `Transits of the Year(3).pdf`

---

# 1. Product Identity — Lock This First

**Paid Year Ahead is the strategic Year Map product.**

It answers:

> **What is the larger story of my next 12 months, where are the main pressures and openings, when do they peak or return, and what should I do with that timing?**

It is **not** a dense transit catalogue.

It is also **not** the same product as the detailed interactive **12-Month Timing Map**, which answers:

> **What is hitting my personal chart, and exactly when?**

The two products share the same calculation engine but present different customer jobs.

### Paid Year Ahead
- narrator-led;
- 3–5 major Games;
- year arc;
- rule changes;
- strategic choices;
- concise exact timing;
- evidence collapsed underneath.

### 12-Month Timing Map
- chronology-led;
- exact transits;
- passes;
- pressure/opportunity windows;
- Chart in Motion;
- more evidence-heavy.

**Rule:** Paid Year Ahead may use exact transit timing, but timing supports the Game. It does not become the product.

---

# 2. Canonical Architecture

```text
PREBUILT SHARED SKY
GitHub automation
• rolling shared ephemeris horizon
• collective slow-moving sky
• reusable monthly yearly-base cache

        ↓

NATAL SNAPSHOT
canonical Natal Player
• planets
• natal aspects
• Sun / Moon
• Ascendant / MC only when birth time supports them
• houses only when valid
• strongest natal signatures

        ↓

TIMING MAP ENGINE
personal transit intelligence
• rolling 365-day window
• Jupiter / Saturn / Uranus / Neptune / Pluto → natal targets
• conjunction / sextile / square / trine / opposition
• active windows
• exact dates/times
• D/R state
• Pass 1 / Pass 2 / Pass 3
• importance score
• fast-planet triggers
• month intensity

        ↓

YEAR AHEAD COMPOSER
• rank strongest 8–12 transit arcs
• group repeated passes
• cluster arcs into 3–5 Games
• calculate turning points
• calculate rule changes
• build twelve monthly rounds
• build one chronology
• build collapsed evidence
• build bounded section-specific voice packets

        ↓

BOUNDED LUNA VOICE JOBS
• annual narrative + monthly groups + major Games
• each section validated before combining
• second person
• one strategic story
• no calculation
• no ranking
• no invented timing
• no JSON
• retry transient provider failure once, then optional independent provider

        ↓

PAID YEAR AHEAD
web first
PDF second
```

---

# 3. Locked Calculation Rules

Python owns all of the following before Luna is called:

- natal chart and birth-time precision;
- rolling 365-day period;
- transit positions;
- transit-to-natal aspects;
- active windows;
- exact contacts;
- direct / retrograde state;
- repeated passes;
- importance ranking;
- supporting fast triggers;
- Game clustering;
- turning points;
- rule changes;
- monthly intensity;
- monthly period type;
- boundary state: already active / starts inside year / continues beyond year;
- technical evidence.

The LLM never decides whether any of those facts exist.

---

# 4. Background vs Trigger Hierarchy

Retain the strongest idea from `Guideline year.pdf`.

## Background planets
- Jupiter
- Saturn
- Uranus
- Neptune
- Pluto

These create the long-running annual structures.

## Trigger planets
- Sun
- Mercury
- Venus
- Mars

A fast transit appears in the paid report only when it meaningfully activates or sharpens one of the selected slow-moving Games.

Moon transits remain excluded from the main annual map.

### Reader-facing rule

Never present a fast trigger as an independent annual chapter unless it has been promoted by a separate deterministic importance rule.

Instead:

```text
MAIN GAME
The Agreement Gets Tested

BACKGROUND
Saturn square natal Venus

TRIGGER
15 February — Venus brings the relationship question to the surface.
```

Technical trigger detail stays underneath in evidence.

---

# 5. Product Hierarchy

## A. Editorial opening

```text
BIG YEAR HEADLINE
short deck
rolling date range
```

The headline states the central tension or opportunity of the year in human language.

---

## B. Your natal foundation

Reuse the exact same visual grammar as Paid Monthly:

```text
YOUR NATAL SIGNATURE
READ THE PATTERN
NATAL CHART
YOUR STRENGTHS
```

No second natal engine.

---

## C. The year at a glance

Add a compact orientation block:

```text
3 major Games
8 turning points
2 rule changes
```

Then show:

### Year intensity strip
How concentrated the selected natal activity is.

### Period type
Use reader-facing labels such as:
- OPENING
- DECISION
- STRUCTURE
- POWER SHIFT
- CHANGE
- RETURN
- ENDING

These labels describe character, not good/bad.

---

## D. Read the Year

One connected Luna narrative.

### Target
- roughly 700–900 words;
- 6–8 substantial paragraphs;
- chronological;
- second person;
- human consequences first;
- no report-meta language such as “the first issue” or “the second Game”;
- no exact clock times in flowing prose;
- no transit-by-transit textbook definitions;
- no repetition of the natal inventory.

### Required narrative movement

```text
opening condition
→ first pressure / opportunity
→ complication
→ return / revision
→ rule change
→ later opening or consequence
→ final strategic position
```

The Game structure organises the narrative invisibly.

---

# 6. The Year Map

Replace the weak bar strip with a real strategic timing map.

Use one lane per Game.

Example:

```text
                 OCT NOV DEC JAN FEB MAR APR MAY JUN JUL AUG SEP OCT

OUTER SHELL      ━━━━━━━━━●━━━━━━━━━━━━
                          P1

AGREEMENT        ━━━━━━━━━━━━━━━━━━━●━━━━━━●━━━━
                                      P1     P2

DOOR BIGGER                                  ━━━━━●━━━━━━
                                                 P1

INTENSITY        ▂   ▃   ▂   ▂   █   █   ▂   ▃   █   █   ▅   ▂
```

### Required information
- true active window;
- exact-pass markers;
- return markers;
- trigger ticks;
- monthly intensity underneath;
- already-active and continues-beyond-year states when applicable.

The timeline is an information tool, not decoration.

---

# 7. Twelve Monthly Rounds

Paid Year Ahead should include a compact 12-month strategic index.

This is how the Yearly Game Map retains month-by-month usability without becoming a second Monthly report.

For each month show:

```text
MONTH
dominant Game
period type
strongest date if one exists
one-line strategic focus
```

Example:

```text
FEBRUARY 2027
THE OUTER SHELL HARDENS
STRUCTURE
27 Feb — exact Saturn contact
Hold the boundary you have already started defining.
```

### Ownership

Python owns:
- dominant Game;
- phase / period type;
- strongest date.

Luna supplies focused monthly narrative in three separate 4-month jobs; retain deterministic monthly focus if narrative unavailable.

If token budget is tight, use a deterministic line derived from the Game move.

---

# 8. The Major Games

Target: **3–5 Games**.

Each Game should read as a human situation, not a transit interpretation.

## Required Game structure

```text
MAJOR GAME 01
THE AGREEMENT GETS TESTED

What is changing
2–3 paragraphs

What this may look like
2–4 concrete real-life manifestations

What can trip you up
the trade-off / blind spot / risk

Your move
specific strategic action

TIMING
Already active / Begins
Strongest
Eases / Continues beyond your year

HOW IT DEVELOPS
Pass 1
Return
Final pass

TRIGGER DATES
human-language meaning of each useful trigger

Also working underneath
maximum 1–2 genuinely important supporting slow arcs

WHY LUNA SEES THIS
collapsed technical evidence
```

---

# 9. Pass Storytelling

Do not show pass labels without interpretation.

## Pass 1 — Initial activation
Explain what first becomes visible or unavoidable.

## Pass 2 — Retrograde return
Explain what comes back for review, renegotiation, correction or deeper understanding.

## Pass 3 — Final pass
Explain what can now be settled, clarified or integrated.

If only one or two exact contacts occur inside the selected year, show only those contacts.

Never manufacture a third pass.

---

# 10. Trigger Translation

Replace engine language such as:

> Venus activates the pattern — sharpens Pass 1

with customer language such as:

> **15 February — Venus brings the relationship question into the foreground.**

Then place the technical wording in collapsed evidence:

```text
Venus trigger
supports Saturn–Venus Pass 1
exact time
orb
```

---

# 11. Boundary Handling

Audit every Game against the selected 365-day window.

A report must distinguish:

### Already active
The transit began before the customer's Year Ahead start date.

### Begins inside the year
The active window truly opens during the selected year.

### Continues beyond the year
The transit remains active after the report end date.

Do not display the selected Year Ahead start date as “Begins” when it is merely the clipped report boundary.

---

# 12. Historical Context — Optional, Not Core

The Reader Guide's “Have you been here before?” concept is valuable, but it should not delay the core Paid Year Ahead.

Add only after the main product is stable.

When implemented:

- compare only a defensible repeat/cycle family;
- show approximate age when the earlier date was during the reader's lifetime;
- never imply the same event will repeat;
- ask:
  - What do you remember?
  - What is different now?

This is a reflection layer, not a prediction layer.

---

# 13. Chart in Motion — Keep Separate From the Main Paid Report

The interactive:

```text
Now
30 Days
90 Days
12 Months
```

Chart in Motion is excellent for the detailed Timing Map product.

Do not make it a mandatory core section of Paid Year Ahead.

Paid Year Ahead may link to it or show a simplified static activation visual, but the paid product's main job is the strategic year story.

---

# 14. Final Strategic Position

Replace a generic closing paragraph with a deliberate final synthesis:

```text
WHAT THE YEAR LEAVES YOU WITH
```

It should answer:

- What has changed by the end of the year?
- What has been tested?
- What has become clearer?
- What has opened?
- What should the reader carry forward?
- What should they stop carrying?

This is the Yearly Game Map's final strategic position.

---

# 15. Key Dates

Keep this short.

Target: **8–15 dates**.

Include only:
- major exact passes;
- meaningful returns;
- decisive trigger dates;
- true rule-change dates.

Do not duplicate every date already shown inside the Games.

---

# 16. Evidence

Every Game gets its own collapsed **Why Luna sees this**.

Show:

- transiting planet;
- aspect;
- natal target;
- natal position;
- transit position;
- house only when birth time supports it;
- exact pass date/time;
- direct/retrograde;
- orb;
- active window.

Then retain one optional full technical appendix at the end.

The reader gets the story first and authority one click underneath.

---

# 17. Segmented Voice Contract — replaces one-call limit

The final voice workflow uses bounded packets containing only what each section needs to write.

Do not send raw ephemeris tables or redundant prose.

The combined validated calls produce:

```text
HEADLINE
DECK
READ_YEAR
MONTHLY_ROUNDS (optional short lines)
GAME_1_NARRATIVE
GAME_2_NARRATIVE
GAME_3_NARRATIVE
...
FINAL_POSITION
```

Plain text section markers are acceptable.

No JSON response.

At most one retry for transient HTTP 429 / 5xx within a provider; then route to an independently configured fallback. Validation failures must never be published as complete.

Major Games are written in separate bounded jobs, grouped up to two per call.

No post-LLM style validator that causes another call.

---

# 18. Pre-Generation

Retain GitHub pre-generation for the reusable shared-sky layer.

GitHub builds the reusable sky.

Runtime adds:
- natal chart;
- exact personal transit intersections;
- ranking;
- Games;
- pass structure;
- personal evidence.

Do not attempt to pre-generate customer-specific natal transits.

---

# 19. Implementation Order

## Phase 1 — Freeze the engine
Do not redesign:
- natal_snapshot.py
- timing_map.py
- yearly ranking
- pass detection
- GitHub pre-generation

Only fix demonstrated calculation defects.

## Phase 2 — Boundary and packet audit
Add/verify:
- already active;
- continues beyond;
- true active window;
- monthly dominant Game;
- monthly phase;
- strongest date;
- 1–2 supporting arcs max in reader-facing payload.

## Phase 3 — Voice contract
Rewrite Paid Yearly editorial instructions around:
- one connected annual arc;
- human Game meaning;
- pass development;
- concrete manifestations;
- Your move;
- final strategic position;
- optional monthly one-liners.

## Phase 4 — Web report
Implement:
- Year at a glance;
- upgraded Year Map;
- 12 monthly rounds;
- structured Game chapters;
- Game-level evidence;
- final strategic position.

## Phase 5 — Acceptance testing
Test:
1. known birth time + houses + multi-pass;
2. unknown birth time — no houses/angles;
3. already-active transit at start;
4. transit continuing beyond end;
5. one-pass Game;
6. two-pass Game;
7. three-pass Game;
8. overlapping Games;
9. voice unavailable — deterministic product still exists;
10. mobile layout.

## Phase 6 — PDF
Only after web approval.

Mirror the accepted Paid Year Ahead hierarchy exactly.

Do not independently redesign the PDF.

---

# 20. Definition of Done

Paid Year Ahead is finished when:

1. It is unmistakably a strategic Year Map rather than a transit catalogue.
2. The same canonical Natal Player used by Paid Monthly feeds it.
3. The selected date creates a true rolling 365-day product.
4. The shared sky can be pre-generated, but personal transits remain exact to the reader.
5. Only roughly 8–12 important transit arcs survive.
6. Those arcs become 3–5 coherent human Games.
7. Slow movers form the background and fast movers act only as relevant triggers.
8. Multi-pass transits read as development: activation → return → resolution.
9. The Year Map shows Game duration plus exact timing markers.
10. Twelve monthly rounds make the year easy to navigate.
11. Read the Year is one connected strategic narrative.
12. Each Game includes:
    - what is changing;
    - real-life manifestations;
    - risk;
    - Your move;
    - timing;
    - pass development.
13. Boundary conditions are truthful:
    - already active;
    - begins inside year;
    - continues beyond year.
14. Exact technical evidence is available underneath every Game.
15. Unknown birth time never creates houses or angles.
16. Luna uses bounded plain-prose calls with section completeness validation and optional independent-provider fallback.
17. Luna never calculates, ranks, groups or invents astrology.
18. Voice failure does not destroy the calculated report.
19. Paid Monthly remains untouched.
20. The PDF mirrors the approved web product.

---

# Reference Principle

```text
CALCULATE FIRST
SELECT SECOND
ORGANISE THIRD
LET LUNA SPEAK IN VERIFIED SECTIONS
SHOW THE HUMAN GAME FIRST
KEEP THE TECHNICAL PROOF UNDERNEATH
```

---

# 21. Production Capacity and Paid Monthly — v3.86 amendment (13 October 2026)

## Why the former token architecture failed

Paid Monthly demanded 1,350–1,600 words in one response. Earlier deployed generation reached `finish_reason=length` and withheld the owner's report. Enlarging a single cap cannot guarantee delivery across providers or account quotas. Paid Year Ahead also exceeded the practical editorial space of a single ~2,500-token completion.

## Revised bounded editorial jobs

**Paid Monthly:** three chronological acts (days 1–10, 11–20, 21–month end); each receives the relevant dated timeline, context, and last-section continuity. Each targets 380–520 words with an 1,850 completion-token allowance, producing one joined article in chronological order. Do not expose act boundaries to the customer. Source chronology and natal facts remain deterministic.

**Paid Year Ahead:** separate annual narrative and closing; three batches of four monthly rounds; up to two Major Games per bounded job. One final parser enforces complete markers for every monthly round and every Game. The model never calculates dates, rankings, aspect contacts, or house placements.

**Provider fallback:** `LUNA_VOICE_BASE_URL`, `LUNA_VOICE_MODEL`, and `LUNA_VOICE_API_KEY` remain primary. Optional `LUNA_SECONDARY_VOICE_BASE_URL`, `LUNA_SECONDARY_VOICE_MODEL`, `LUNA_SECONDARY_VOICE_API_KEY` configure a different provider. Only nonempty, nontruncated responses qualify. Do not present technical outage messages or account secrets to customers. A provider change is not a permission to invent facts.

**Per-job guards:** estimate prompt size and cap each completion; verify the expected section labels and nonempty prose; validate ISO dates against the selected packet before publication; a failed job blocks a paid report rather than delivering a partial one. Unit tests must mock HTTP 429/5xx, truncated completions, empty prose, and missing sections. Preserve the stable natal/transit engine, checkout and report formats.

## Scaling beyond a single Streamlit process — deployment prerequisites

**Not yet included in v3.86 code:** a durable, external customer report store; background workers; payment-webhook idempotency; transactional queue; email-on-completion; a cost/usage dashboard. These require a configured managed database/queue and external worker service; Streamlit local disk or `st.cache_data` is not acceptable persistence for paid orders.

**Required production design:** Stripe-paid webhook → idempotent durable order record (unique Stripe event and order IDs) → leased generation job → saved intermediate validated sections → final HTML/PDF artifacts in persistent object storage → email/return URL. Retries must resume only unfinished sections and must not charge or generate duplicate orders. Enforce per-provider token and request throttles and capture rate-limit telemetry. Keep the owner mode separate from real paid delivery.

**Acceptance gates:** Paid Monthly owner run with real provider; Paid Year Ahead owner run with real provider; 429 failover drill; no invented dates; full 12 rounds and all Games; stable PDF output; network interruption drill; correct duplicate-webhook handling once a durable store is installed. **Do not call the whole production capacity plan complete until all these checks have passed.**


## v3.87 — Provider Failure Diagnostics and Operational Runbook

When an owner report fails, record the provider's HTTP status and safe error summary.
Do not collapse every provider failure into `HTTPError`.

- HTTP 400/422: inspect model/parameter errors and reduce invalid requests; do not blindly retry.
- HTTP 401/403: verify provider credentials, access and model availability.
- HTTP 402: resolve billing or credits.
- HTTP 429: inspect Groq's live rate-limit dashboard, wait for the returned window and use an independent provider if configured.
- HTTP 5xx: bounded retry then alternate provider.
- `finish_reason=length`: the specific section exceeds its response allowance; do not publish truncated prose.

**Architecture note:** This release improves diagnostics and bounded transport recovery. It does **not** implement a durable queue, external database or confirmed live second-provider access. Paid customer orders must eventually be handed to an idempotent job queue to survive rate-limit windows longer than a web request.

---

# v3.88 — Single-Groq Token-Aware Production Rules

The historic one-call voice rule in sections 2, 17 and 20 is superseded: segmented, bounded sections are required for complete paid prose. The first active provider remains Groq. Secondary-provider development is deferred.

**Runtime steps:** deterministic evidence → section jobs → provider-aware pacing → retry after 429 respecting Retry-After/reset information → checkpoint successful sections → validate calculated evidence → assemble HTML/PDF.

**Observed limit:** 8,000 Groq tokens per minute. Conservative local pacing targets 7,200 estimated tokens/minute. This is an approximate reservation, not the authoritative provider counter. HTTP 429 can still occur.

**Wait duration:** honor provider's seconds/reset information; when absent allow 60 seconds initially. Cap accumulated waiting at 180 seconds per section and fail clearly after that limit rather than looping forever. A Year Ahead with multiple segments can take several minutes on a free plan.

**State:** v3.88 local SQLite checkpoints are best-effort and temporary on Streamlit Cloud. They survive ordinary reruns on the same instance but not host/container replacement. Production acceptance requires durable external order records, persistent section checkpoints, deduplicated job claims across instances, an asynchronous worker and fulfillment recovery. Do not claim this capability is implemented in v3.88.

**Acceptance:** 429→wait→retry, retry limit, saved section reuse, malformed placeholder ignored, model truncation rejected, no unsupported date fabrication. Live tests still required.
