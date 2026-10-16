# Luna v3.136 — Cover and Natal Activation Typography

Based on v3.135. Complete replacement package; install `app.py`, `paid_yearly_editorial.py`, `yearly_print_html.py` over v3.135.

- Print headline: remove only wrapping literal Markdown bold markers (`**...**`) in the renderer, leaving the authored headline words intact.
- Cover: show the year range only under the headline. The generated multi-paragraph deck remains stored in editorial data and is not printed in the cover slot.
- Monthly natal activation labels: change planet abbreviations from uppercase (SUN, VEN, MAR, PLU) to title case (Sun, Ven, Mar, Plu). Centre becomes `Natal activations`. Position/collision logic and calculated coordinates unchanged.
- Increment build version to v3.136.

Checks: Python compilation and renderer source assertions. Live Groq and complete paid-PDF visual output not run. All other architecture retained from v3.135.
