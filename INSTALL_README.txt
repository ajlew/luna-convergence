LUNA CONVERGENCE - CONSOLIDATED PRINT + YEAR RHYTHM UPDATE (v3.78)
=====================================================================

ONE PACKAGE - ALL CHANGES

Replace these project-root files with the enclosed versions:
  app.py
  paid_yearly_report.py
  paid_yearly_pdf.py
  yearly_print_html.py  (new)
  monthly_report_pdf_home_v3.py
  epic_sky.py
  requirements.txt

Also preserve the included generated/epic_sky/ example folder. It contains
an approved sample for the week beginning 12 October 2026.

IMPORTANT: This is a patch package; it does NOT contain the full project.
Do not delete other project files or secrets. The existing Swiss Ephemeris,
natal data, Groq configuration, Stripe flow, and other engines remain in
place. The app version was advanced to v3.78 so deployment is identifiable.

CHANGES
  1. Year Ahead website: unique named story lanes instead of repeated broad
     life-area headings. Better explanatory copy.
  2. Year Ahead rhythm: smooth wave THROUGH precomputed activity samples,
     rather than an arbitrary ornamental sine wave. It measures calculated
     astrological concentration and does not predict mood or success.
  3. Year Ahead monthly accordion headings: proper/title case rather than
     the old global uppercase CSS setting.
  4. Shortcut help: collapsed 'Add Luna to your device' box in the footer,
     including iPhone, Android and desktop instructions. The Saturn favicon
     continues to be supplied by st.set_page_config. Full iOS/Android PWA
     icon branding is host-dependent, not guaranteed by Streamlit alone.
  5. Year Ahead PDF: new HTML/CSS A4 renderer using Luna's Monthly typography
     families and the SAME packet/editorial as the website. It has a cover,
     natal signature, actual natal SVG, year-map bars and rhythm wave, twelve
     rolling month chapters, major stories, key dates and technical evidence.
     Each month starts on a new page; oversized content flows naturally.
  6. Monthly PDF: preserve existing HTML/CSS renderer and natal/transit chart
     changes from previous v4, now installing WeasyPrint explicitly.
  7. Owner reports: additional 'Download print-ready HTML' action for BOTH
     products, to inspect the report in a browser and Ctrl+P / Print -> PDF.
  8. Existing one-click Epic Sky integration from previous v2 is retained.

NEW REQUIREMENT
  WeasyPrint >=62,<69 was added to requirements.txt. Streamlit Cloud will
  install it on rebuild. If deployment reports missing Linux/Pango/Cairo
  libraries, those need to be installed at the host level. No browser install
  is required for normal WeasyPrint PDF rendering.

ACCEPTANCE CHECK AFTER DEPLOYMENT
  - Confirm footer 'Add Luna to your device' instructions.
  - Owner reports -> Year Ahead -> choose 12 Oct 2026 -> generate.
  - Check 'How your year unfolds': four named stories and the smooth activity
    wave; verify month labels now appear in proper case.
  - Expand monthly chapters; verify actual contact evidence is present.
  - Download Owner PDF; verify natal wheel, active transit timelines, all
    twelve month chapters, major issues and evidence pages.
  - Download print-ready HTML; open it in a browser; use Print -> Save as PDF,
    set paper size A4, backgrounds enabled and margins default/none as needed.
  - Regenerate Paid Monthly; check its PDF and print-ready HTML.
  - Confirm Epic Sky week starting 12 October still generates via Groq.

VALIDATION
  Python compilation passed for the changed modules.
  9 targeted PDF/print/Epic Sky tests passed.
  A separate Monthly HTML/CSS PDF smoke test produced a valid PDF.
  A sample Year Ahead HTML/CSS PDF was rendered and visually inspected.

LIMITATIONS / NOT VERIFIED
  - Live deployed Streamlit UI, real Groq, payment and email delivery were
    NOT tested in this offline session.
  - HTML print view shares report data, font design and visual principles;
    it is not a literal screenshot dump of Streamlit's interactive DOM.
  - Mobile home-screen icon may still show Streamlit's default mark unless
    the hosting frontend exposes a manifest and apple-touch-icon.
  - Older architecture tests referencing removed function names are stale and
    were NOT changed to conceal their failures.
