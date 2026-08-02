# Luna Daily + Monthly Production Pass v2.9

## Release decision

The public product is now deliberately limited to:

- Free Daily reading;
- Paid Monthly report;
- Stripe order preparation and manual PDF delivery.

The Yearly report remains available to the internal editorial tools but is
hidden from the customer site until Daily, Monthly and payment delivery are
satisfactory.

## Environment gates

Public/customer launchers use:

```text
LUNA_EDITOR_PREVIEW=0
LUNA_PUBLIC_YEARLY=0
```

Admin and Editorial Preview launchers use:

```text
LUNA_EDITOR_PREVIEW=1
LUNA_PUBLIC_YEARLY=0
```

Yearly can later be released without rewriting the checkout by setting:

```text
LUNA_PUBLIC_YEARLY=1
```

## Daily customer boundary

The Daily page now follows this order:

1. Hero headline and today’s story;
2. Do / Don’t;
3. compact Monthly invitation;
4. optional Why Luna Sees This;
5. optional relationships, work and money;
6. optional questions;
7. collapsed Full Technical Evidence.

Changes:

- a repeated relationship paragraph is detected and omitted from “Continue
  today’s story”;
- the Monthly offer is positioned before the evidence stack;
- Editorial Translation is no longer rendered publicly;
- Planetary Positions and the 12-House Reference Matrix remain available only
  inside the collapsed technical section;
- the existing mobile CSS remains unchanged because the iPhone 13 view was
  confirmed to fill the screen without lateral movement.

## Monthly narrative spine

The Monthly report no longer presents the relationship test as an isolated
card after a three-chapter summary. It now uses a single chronological spine:

| Act | Narrative job |
|---|---|
| Act I | The opening acquires structure |
| Act II | The opportunity reveals its terms |
| Act III | Attention meets the evidence test |
| Act IV | The public result must fit private life |

For Sagittarius August 2026, the resulting periods are:

- 28 July–7 August: inherited momentum and first movement;
- 11–15 August: cost, timing and responsibility;
- 17–21 August: relationship proof;
- 24–28 August: public result and private fit.

The opening now provides orientation rather than retelling every act. The
Decision Calendar presents the required response first and the astrological
evidence second.

## Files changed

```text
app.py
site_config.py
daily_narrative_v3.py
monthly_narrative_v1.py
monthly_experience_v1.py
README.md
run_windows.bat
run_customer_windows.bat
run_admin_windows.bat
run_editor_preview_windows.bat
```

Relevant regression tests were updated and a new integrated test was added:

```text
test_daily_monthly_production_v29.py
```

## Validation completed

- Python syntax and compile validation;
- public/editorial environment gates;
- Daily relationship-copy de-duplication;
- compact Monthly CTA placement;
- public Editorial Translation removal;
- collapsed technical evidence retention;
- four-act Monthly sequence;
- relationship test integrated once in Act III;
- Monthly HTML and PDF generation;
- paid-order handoff and app integration;
- forecast inventory compatibility.
