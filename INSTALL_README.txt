LUNA v3.89 — MONTHLY ROLLBACK + PRINT PRESERVATION
================================================
Overlay these files onto the existing repository, preserving directory structure.

Paid Monthly: restored the v3.84 ONE-CALL prose generation, prompt preparation,
and cached request logic. Removed three-act segmentation, its duplicated events,
and dependence on the secondary-provider router from Paid Monthly only.

Monthly HTML/PDF: preserved existing monthly_report_pdf_home_v3.py and the
current owner-download controls for PDF and print-ready HTML. The monthly
renderer is identical to v3.84. No changes to natal or ephemeris calculations.

Year Ahead: retains v3.88 segmented generation, pacing and existing behavior.

Important: v3.84 used a 2,500-token preferred Monthly completion allowance.
Restoring the last working path does NOT guarantee long new prompt results cannot
truncate. The deployed Monthly should be verified using an owner report before
customers rely on it. Do not simultaneously change its prompt length or sections.

Offline regression tests: 10 passed in the complete source tree using
`python -m pytest -q test_monthly_restored_v389.py test_print_v381.py test_activation_v383.py test_yearly_print_html_v378.py`.
No live Groq call or live Stripe/Streamlit delivery test was performed.

V3.90: Monthly print pagination fix: natal activation page print-only compact layout prevents orphan activation card. Monthly voice unchanged; Year Ahead unchanged.
