# Luna Convergence v3.12 — Trajectory-led strategy

This update is additive. It preserves the existing ephemeris engine, monthly arc engine,
Truth Gate, scenario library, countercurrent logic, historical testing, payment flow,
printing/PDF, daily and yearly reports.

## Constitutional change

Luna First Principles is now v1.4:

`Nature -> Pattern -> Trajectory -> Convergence -> Meaning -> Choice -> Experience -> Learning`

The monthly average remains diagnostic climate evidence, but the *direction of travel*
controls the customer strategy. A worsening month and a recovering month no longer receive
the same monthly recommendation simply because their monthly averages are similar.

## New trajectory archetypes

- `late_storm`
- `pressure_builds`
- `recovery`
- `easing`
- `support_builds`
- `support_strengthens`
- `reversal`
- `oscillating`

## New portfolio strategy

`TIMED ADVANCE` is added for months that open under material pressure and then improve.
The reader is told to preserve optionality during the difficult window and use the cleaner
window only after the sky has changed.

September 1995 Sagittarius now resolves as `recovery -> TIMED ADVANCE` rather than being
flattened into the same `DEFENSIVE HOLD` used by September 2017.

September 2017 remains `late_storm -> DEFENSIVE HOLD`.

## Window-level choices

Each early / middle / late window receives a posture using both:

1. the evidence in that window; and
2. what the trajectory says is coming next.

For example, clean mid-month support may still be handled cautiously when a verified late
storm is approaching, while a difficult opening can become `ADVANCE` once the evidence has
materially improved.

## Stronger provenance and evidence discipline

- customer chronology is aligned to chronological trajectory windows;
- customer evidence uses the life area directly supported in that window;
- aspect claims are deduplicated before counts are printed;
- the number of visible hard/support contacts matches the contacts named beside the claim;
- bridge promotion threshold rises from 0.68 to 0.75 so marginal connector scores remain
  background rather than being forced into the story.

## Domain scenario alignment

Love / Work / Money scenario wording now respects the calculated posture. A PASS or HOLD
state may still acknowledge an apparently positive manifestation, but Luna immediately
explains why the headline is not enough to justify extra exposure. NEGOTIATE explicitly
moves the reader toward better amount, timing, ownership or obligations.

## Customer presentation cleanup

- raw support/friction numbers are reduced in the narrative; qualitative language carries
  the story while exact figures remain in technical evidence;
- Decision Evidence distinguishes the `Monthly-average truth gate` from the higher-order
  `Trajectory strategy`;
- Solar Background is compressed to the parts that bring Nature to the table: solar phase,
  local light direction, seasonal gate and solar life-area movement;
- generic Solar `Opportunity / Risk / Response` mini-forecast copy is no longer rendered;
- Sydney September is clarified as `Late winter -> spring at the September Equinox` rather
  than simply `Winter`.

## Regression checks

- 36 pytest checks pass.
- 144 / 144 monthly reports for all 12 signs x all 12 months of 2026 generated successfully.
- all 12 Sagittarius months of both 1995 and 2017 generated through the new trajectory layer.

No Sagittarius-1995 or Sagittarius-2017 answer is hard-coded.
