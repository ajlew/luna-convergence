# Luna Monthly Narrative v3.5 — Corrective Build

This build is a corrective pass over v3.4. It does not expand the Susan Miller calibration library. It fixes the runtime and editorial issues exposed by sequential Aries -> Pisces printing.

## P0 fixes

- **Print isolation:** every rendered monthly gets a unique DOM/print instance. The Print / Save PDF button clones only that instance into a child print frame.
- **Print JavaScript syntax:** corrected the generated JavaScript newline escape that could prevent the custom print handler from running.
- **Relationship gating:** a Love subplot enters the monthly chronology only when House 5/7 has material monthly support (>= 70% of the strongest house weight and >= 45 points). Love remains in the dedicated Love section for every sign.
- **Legacy fixed copy:** v3.5 QA rejects the older generic relationship/Do-Don't lines if they reappear.

## P1 fixes

- **PDF pagination:** print layout places Do / Don't directly after the Luna Says headline before long prose, preventing a nearly blank page containing only the Do / Don't strip.
- **Exact event date vs influence window:** How the month unfolds shows the exact local date for matching events and a separate influence window.
- **Explainability:** technical evidence now distinguishes **Story-driver events** from **Monthly background weight**.
- **Solar hierarchy:** Solar Convergence is presented as **Solar background**, explicitly subordinate to the event-led monthly story.
- **Dynamic solar copy:** opportunity/risk/action language now follows the actual start-house -> end-house movement rather than universal visibility copy.
- **Health wording:** scenario examples are softened toward wellbeing/care/recovery possibilities rather than literal diagnostic predictions.

## Acceptance checks

The build was tested for:

1. Aries retains an evidence-supported relationship subplot; Pisces does not.
2. Aries and Pisces have different Do / Don't guidance.
3. Every monthly HTML render gets a unique print scope.
4. A browser-level sequential test with Aries and Pisces mounted together prints **Pisces only** from the Pisces Print / Save PDF button.
5. Pisces print output renders to 11 A4 pages in headless Chromium with Do / Don't on page 1 rather than a blank page 2.
6. The Leo solar eclipse is shown as **13 August 2026** (Sydney local date) with a separate sign-specific influence window.
7. All 12 August 2026 reports pass monthly QA.
8. Existing customer MVP, admin monthly preview, monthly webpage and paid-order handoff tests pass.

## GitHub upload

Upload all production files in this package to the repository root, replacing the files with the same names. Do not upload only one or two monthly modules; v3.5 is intended to remove the mixed-version state seen in the v3.4 output.
