LUNA CONVERGENCE - CONSOLIDATED PAID REPORT UPDATE

Copy these three files into your Luna repository root, replacing same-named files:
  app.py
  paid_yearly_pdf.py
  monthly_report_pdf_home_v3.py

DO NOT remove the existing monthly_transit_view.py, report_pdf.py,
monthly_report_pdf_v2.py, natal_snapshot.py, or other project files.

Included:
- The prior consolidated Paid Monthly voice completion/readiness fix (app.py).
- The revised Paid Year Ahead PDF design, real natal wheel, graphical Year Map,
  per-month timelines and monthly natal activation visualization.
- A paired natal-position and activation-wheel illustration on the existing
  Paid Monthly HTML/CSS print route, driven by stored natal geometry and
  ranked monthly personal contacts. Unknown birth-time angles are never added.

The Monthly PDF HTML/CSS fallback renderer remains as before; where a browser or
WeasyPrint cannot render it, the application can fall back to the pre-existing
ReportLab generator without these new chart visuals.

Verification performed:
- Python syntax compilation of all three supplied modules
- 3 PDF-related pytest tests passed
- real Year Ahead PDF smoke test created (synthetic sample data)
- separate SVG-to-PDF render of both monthly natal and activation wheels

NOT YET VERIFIED:
- production Groq/API responses
- paid checkout/email delivery
- a full actual customer PDF for both products after deployment
- exact screenshot-level font parity with website

If you publish, first use OWNER PREVIEW to generate both reports and review
both PDFs. Do not send unreviewed customer PDFs.
