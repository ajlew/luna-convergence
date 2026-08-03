# Luna Convergence v2.9.7
## Universal Monthly Evidence Formula

The earlier game-theory model supplied a useful skeleton:

- Nature supplies the sky state.
- The sign supplies the whole-sign house map and ruling-planet sensitivities.
- The engine ranks possible strategies.
- Luna translates the strongest supported strategy into customer language.

For a Monthly product, a single action score is not enough. Luna needs a connected path through time. v2.9.7 therefore separates five jobs:

1. calculate astronomical events;
2. score their symbolic relevance;
3. gate scenario families by actual evidence;
4. assign events to chronological story roles;
5. apply the Luna editorial voice and existing report format.

---

## 1. Universal event evidence score

Every event `e`, sign `i` and customer focus `f` uses the same equation:

```text
C(e,i,f) = T × O × A × H × R × I × D × F × P
```

| Factor | Meaning |
|---|---|
| `T` | Trigger strength: eclipse, lunation, station, aspect or ingress |
| `O` | Orb and exactness |
| `A` | Applying, exact or separating phase when measured |
| `H` | Activated-house relevance |
| `R` | Native-sign ruler and activated-house ruler involvement |
| `I` | Independent supporting signals in the same convergence |
| `D` | Duration and carryover into the selected month |
| `F` | Customer-focus relevance |
| `P` | Pressure, release, opportunity, culmination or review function |

The result is a **symbolic relevance score**, not a measured probability and not a guarantee that a literal event will occur.

---

## 2. Hard scenario gate

A scenario cannot enter the report merely because its language sounds plausible.

```text
G(e,s,i) = 1 only when:
- the event activates at least one house belonging to scenario s; and
- a relevant planet is involved, except for lunations and eclipses.
```

Then:

```text
ScenarioScore(s,i) = Σ [G(e,s,i) × C(e,i,f) × scenario-match]
```

This prevents the original Aries failure, where a money/travel story was selected despite the dominant creative, romantic and work-rhythm evidence.

---

## 3. Monthly house path

The report selects a source house and a destination house from weighted evidence across the period.

```text
SourceHouse  = highest supported early/carryover house
Destination  = highest supported late-month house different from SourceHouse
```

The Sun's monthly ingress is recorded as a continuity signal, but it does not automatically override stronger independent evidence.

The complete role path remains visible in the audit:

```text
carryover → opening → complication → relationship current → climax → resolution
```

A report may therefore contain a carryover house, complication house and climax house even when the customer-facing theme uses the strongest source-to-destination axis.

---

## 4. Narrative-path selection

Luna does not choose four unrelated high-scoring events. It chooses the best coherent sequence:

```text
Arc* = argmax [
    role evidence
  + temporal continuity
  + scenario continuity
  + independent support
  - contradiction
  - unsupported scenario penalty
  - duplicate-event penalty
  - repetition penalty
]
```

The roles are universal. The events, houses, scenarios and wording vary by sign and month.

---

## 5. Luna editorial layer

The calculation engine does not control the visual product.

The existing Luna format remains intact:

- editorial hero;
- monthly overview;
- chronological acts;
- relationship question;
- Love, Work and Money;
- monthly strategy;
- key dates;
- Solar Convergence;
- explainable evidence;
- technical appendix;
- isolated PDF production.

The former twelve hand-written August profiles are retained only as an editorial calibration archive in:

```text
monthly_story_profiles_v296_calibration.py
```

Production now uses one dynamic profile generator based on:

```text
sign element/modality
+ source house
+ destination house
+ mapped scenario family
+ chronological role
```

---

## 6. Relationship differentiation

Relationship language is generated from the same universal matrix:

```text
Element × Modality × active relationship house × relationship evidence
```

This produces twelve distinct relationship currents without maintaining twelve fixed monthly stories.

---

## 7. Release gates

A Monthly report fails when:

- a scenario has no supporting house overlap;
- a non-lunation scenario has no relevant planetary support;
- an active beat has no evidence or scenario key;
- the same astronomical event creates duplicate customer date cards;
- the selected source and destination cannot be traced to weighted evidence;
- the report falls back to a fixed sign/month narrative;
- the PDF contains another sign, merged words or stale print clones;
- customer-facing copy becomes materially identical across signs.

---

## 8. Production status

v2.9.7 is a Monthly-engine build.

- Daily remains unchanged.
- Monthly preview remains available.
- Yearly remains hidden.
- Luna's HTML and PDF design remains unchanged.
- The technical appendix now records the formula version and evidence-to-story mapping.

---

## 9. Role-local evidence rule

The source/destination axis organises the month, but each act is translated from the house activated by that act's own evidence cluster. This prevents a broad monthly axis from overwriting the local meaning of the opening, complication, relationship current or climax.

Scenario selection follows the same universal priority for every report:

```text
evidence strength
+ activated-house specificity
+ narrative-role fit
```

A narrow house-specific scenario may outrank a broad umbrella scenario when both are supported at comparable strength. The relationship role remains a relationship interpretation whenever the evidence supports a relationship, agreement or shared-trust family.

## 10. Full-year validation

The final v2.9.7 audit covers all 144 Monthly combinations for 2026:

- 144 reports generated;
- zero audit failures;
- highest same-month cross-sign similarity: 60.41%;
- no customer-calendar duplicate triggers;
- no active role without an evidence path and scenario key;
- every sign produced at least 11 distinct headlines across 12 months.

A repeated headline is allowed only when a connected evidence pattern genuinely persists. The anti-template gate requires at least 80% distinct headlines across the selected period rather than forcing artificial novelty.
