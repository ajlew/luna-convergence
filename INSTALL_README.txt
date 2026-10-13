LUNA CONVERGENCE v3.91 — MONTHLY PAID STORY + PRINT + VISIBLE ACTIVATION

Apply this entire cumulative overlay to the repository root.

Paid Monthly only:
- Generates the existing one-call paid monthly story once per report rendering.
- Shares that one validated story between on-screen Read the month, downloadable PDF, and print-ready HTML.
- Withholds incomplete PDF and email if the paid story is incomplete.
- Shows the two natal wheels directly in the paid on-screen report, outside the expandable chart evidence.
- PDF and print-ready HTML include a full Read the month chapter.
- Prints physical A4 page numbers via CSS page counter rather than incorrect logical section numbering.
- Avoids silent ReportLab fallback that would discard paid interpretation.

Does not alter natal calculations, Monthly one-call prompt or Year Ahead orchestration.
No live Groq calls or Stripe payments were made during testing.

Tests: python -m pytest -q test_monthly_shared_print_v391.py

Known production limitations: Full browser/Streamlit and external Groq production calls not verified. All HTML-to-PDF generation requires WeasyPrint or a supported headless browser. PDF previews generated with synthetic offline story content are layout proofs only.
