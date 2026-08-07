# Luna Monthly v3.3 — Print filename fix

This update restores Luna's sortable print-to-PDF filename convention.

Example:

`2026-08_Virgo_Monthly.pdf`

The on-page report identity still shows the generated local time, e.g. `Virgo 9:03pm August 2026`, but the browser print/save dialog is primed with the stable report filename instead of the time-based name.

The print script sets both the printable document title and the outer Streamlit document title before opening Chromium print preview, then delays restoring the titles so the filename is not lost while the dialog is being prepared.
