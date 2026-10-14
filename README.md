# Luna v3.106 — Year Ahead monthly chart presentation

**Install over v3.105.** Replace only `app.py`, `paid_yearly_report.py`, and `yearly_print_html.py`.

- `yearly_print_html.py`: match each of twelve monthly transit bars and exact-hit dots to its calculated parent Game's annual colour; add brief how-to-read text for natal, annual, monthly and activation graphics; reduce A4 monthly chart/spacing to avoid unnecessary carry-over pages.
- `paid_yearly_report.py`: clarify the on-screen annual timeline caption (no structural changes).
- `app.py`: explicitly set `APP_VERSION = "v3.106"`.

No changes to Monthly, natal/ephemeris calculations, yearly event selection, Groq, checkout, report copy generation or the live report architecture. The HTML/PDF share the print renderer. The print spacing adjustment reduces but cannot guarantee elimination of splits for arbitrarily long report copy.

Verified: Python compilation, chart colour/exact-hit SVG and guidance assertions. Full live Streamlit and real-customer rendered-PDF parity were not tested; no Groq calls.
