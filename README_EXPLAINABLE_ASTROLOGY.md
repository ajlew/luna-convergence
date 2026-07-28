# Luna Convergence — Explainable Astrology

## Product principle

The customer sees the consequence before the calculation.

```text
Customer
→ Today’s story
→ Everyday examples
→ Compact evidence
→ Optional calculations
```

The astrology remains the engine, but it does not interrupt the reading.

## Public daily structure

1. Today’s Theme — one large headline.
2. Today’s Story — three or four consequence-first paragraphs.
3. Today’s Convergence — two plain-English life areas.
4. Why This Matters Today — three short evidence points.
5. Weather / Today — the fast emotional pattern.
6. Climate / Longer Current — the slow background.
7. Hidden Opportunity.
8. Watch Out.
9. Action Today.
10. Sky Snapshot.
11. Reflection questions.
12. Optional calculations, work, money and relationship detail.

## Sky Snapshot

The visible panel contains:

- primary theme;
- emotional weather;
- strongest influence;
- long-term current;
- convergence strength;
- active window.

The public strength label is High, Medium or Low. A numerical score is shown for transparency. It measures how clearly one pattern dominates, not the probability that an event will occur.

## Weather versus climate

- **Weather** uses the Moon and faster personal planets to describe the next day or two.
- **Climate** uses slower planets and active convergence patterns to describe the longer season.

This explains why some themes change daily while others remain relevant for weeks or months.

## Consequence-first safeguards

The story may mention plausible areas such as a message, payment, child, partner, work decision, trip, family matter or creative opportunity only when the activated house supports that category. The language remains conditional: “may,” “could” and “might.”

The app does not claim that a specific event must happen.

## Deployment

Upload these files to the repository root:

```text
app.py
daily_narrative_v3.py
test_daily_narrative_v3.py
test_daily_narrative_v3_integration.py
test_app_nameerror_hotfix.py
README_EXPLAINABLE_ASTROLOGY.md
sample_explainable_astrology_sagittarius_july_27_to_30_2026.md
```

The new `app.py` replaces the earlier Daily Narrative v2 integration and imports `daily_narrative_v3`.

The older `daily_narrative_v2.py` is no longer required.
