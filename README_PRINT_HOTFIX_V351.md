# Luna Monthly v3.5.1 — Print Button Hotfix

This hotfix fixes the v3.5 regression where **Print / Save PDF** could appear to do nothing.

## Cause

v3.5 moved printing into a hidden child iframe and waited for fonts/layout before calling `print()`. On some browsers that delayed call can lose the direct user-click activation, so no print dialog opens.

## Fix

- Printing is returned to the proven same-document print portal.
- `window.print()` is called directly inside the button click handler.
- Every report still has a unique Luna instance ID.
- Before printing, any stale print portal from an earlier sign is removed.
- Only the active report is cloned into the print portal.
- The sortable filename format remains `YYYY-MM_Sign_Monthly.pdf`.
- v3.5 narrative, scenario provenance, relationship gating, dates and QA changes are unchanged.

## Sequential print acceptance test

With Aries and Pisces mounted together, clicking the Pisces print button produced one active print portal containing Pisces and no Aries. A headless A4 render of that portal produced a 10-page Pisces-only PDF.

## GitHub

If v3.5 is already deployed, replace only `monthly_experience_v1.py`.
