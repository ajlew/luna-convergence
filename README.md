# Luna v3.105 — Year Ahead chart parity

**Required baseline:** v3.104.

**Source changes**
- `paid_yearly_report.py`: the live Streamlit Year Ahead chart now renders the existing `_annual_timeline(packet)` chart function used by downloadable HTML/PDF, rather than the older bar-and-wave widget.
- `app.py`: explicit version updated to `v3.105`.

**Included unchanged dependency**
- `yearly_print_html.py`: exact v3.104 chart implementation required by the live renderer. This module has **not** been edited in v3.105. Included to avoid an incomplete install.

**Not modified**: Paid Monthly, natal calculations, yearly calculations, yearly editorial/Groq, checkout, print/PDF logic.

**Tests**: Python compilation; shared-chart output on two constructed Games (three SVG curves, two exact contact markers); code-path regression. No live Streamlit or Groq test; no real customer chart recomputed.

**Installation**: Overlay these Python files in the repository root. Keep a copy of the v3.104 versions to roll back if needed. Confirm footer reads `v3.105` and the on-screen chart shows coloured Game curves identical to the downloaded HTML.
