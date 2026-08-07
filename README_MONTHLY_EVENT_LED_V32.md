# Luna Convergence — Monthly Narrative v3.2

## Print identity / Save as PDF fix

The monthly report now creates one compact report identity when the report is rendered:

`Aries 8:50pm August 2026`

This identity is printed directly inside the report so the sign, time and report month remain visible in the saved PDF.

For the browser's Save as PDF filename, Luna temporarily changes the print document title to a Windows-safe equivalent:

`Aries 8.50pm August 2026.pdf`

A dot is used instead of a colon because Windows filenames cannot contain `:`.

After printing or cancelling the print dialog, the original browser page title is restored.

The smaller line beneath the identity still records the generated calendar date and timezone, for example:

`Generated 7 August 2026 · AEST · Australia/Sydney`

## Calibration

This package retains the v3.1 12-sign August 2026 scenario calibration built from the complete Susan Miller August comparison set, while keeping Luna's wording independent and deterministic.

## GitHub upload

Upload the files in this package to the repository root, replacing existing files with the same names. The only production file changed by v3.2 itself is `monthly_experience_v1.py`; the other files are included so this can also be used as a complete v3.2 update package.
