LUNA CONVERGENCE v3.93 — PAID MONTHLY SHARED VIEW

Apply this cumulative ZIP over the repository, preserving folder paths.
Paid Monthly screen, downloaded HTML and PDF now use monthly_shared_view.py.
The legacy monthly_report_pdf_home_v3.py remains packaged for backwards compatibility but is not used by these paid delivery routes.
Year Ahead generation and layouts have not been changed.

The LLM-written Monthly narrative is generated once and reused. No separate generation is made for printing.
Offline A4 proof: Luna_v393_Monthly_Same_View_Proof.pdf (distributed separately).
Validation: test_monthly_unified_v393.py; python -m pytest -q test_monthly_unified_v393.py

KNOWN LIMITATIONS:
- This does not retrospectively fix potentially incorrect dates or astrological claims already stored in an LLM story.
- On-screen styling is now defined by the unified HTML/CSS rather than legacy Streamlit components.
- Live Streamlit Cloud appearance and live Groq generation have not been verified.
- On-demand PDF relies on WeasyPrint and host OS libraries.
