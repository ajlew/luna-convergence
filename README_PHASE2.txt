LUNA PAID YEARLY — PHASE 2: BOUNDARY + MONTHLY ROUND AUDIT

MASTER PLAN:
Luna_Paid_Year_Ahead_Updated_Build_Plan(1).md

Replace these root files:
- timing_map.py
- year_ahead.py
- paid_yearly_editorial.py
- paid_yearly_report.py

NO app.py change.
NO Paid Monthly change.
NO checkout change.
NO GitHub pre-generation change.
NO extra LLM call.

WHAT THIS PHASE COMPLETES

1. Truthful transit boundaries
- Selected slow-planet arcs touching the 365-day edge are checked outside the
  display period.
- A story can now be marked:
  already_active
  begins_inside_year
  ends_inside_year
  continues_beyond_year
- The customer's paid report remains exactly start date + 364 days.

2. Twelve rolling monthly rounds
- YearPacket now contains exactly 12 monthly_rounds.
- Each round is anchored to the customer's selected start date.
- Python owns:
  dominant story
  phase / period type
  strongest date
  strongest event type
  deterministic focus
- Exact contacts/returns/triggers can outrank a globally stronger long-running
  story inside the month where they actually happen.

3. Human timing display
- Story Timing now shows:
  Already active / Begins
  Strongest
  Eases / Continues beyond your year
- The Year Map marks edge stories as already active / continues beyond.

4. Reader-facing payload control
- Luna receives no more than two supporting slow arcs per major story.
- Full technical evidence is still retained in the YearPacket/report evidence.

TESTS COMPLETED
- Python compile: PASS for all four files.
- Boundary recovery synthetic test: PASS.
- Exactly 12 rolling monthly rounds: PASS.
- Local exact contact outranks globally stronger long-running story in its month: PASS.

NEXT MASTER-PLAN PHASE
Phase 3 — Paid Yearly voice contract:
- human-first Read the Year
- no report-meta wording
- concrete manifestations
- personalised pass development
- personalised trigger meaning
- final strategic position
