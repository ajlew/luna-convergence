# Luna v3.137 — Live Hero and Natal Wheel Display

**Required base:** v3.136. Replace `app.py` and `yearly_print_html.py` only. `paid_yearly_editorial.py` and other files remain unchanged.

- `app.py`: render a display-only Year Ahead editorial projection with a clean headline and empty deck, so the live hero shows the existing report date label only; the canonical editorial text remains intact.
- `yearly_print_html.py`: expose one cover-headline display helper, use Josefin Sans for activation-wheel planet and centre labels, make wheel 106mm on screen and 88mm in print, and expand the display-only collision estimate.
- No changes to Swiss Ephemeris, Game evidence, Groq, Paid Monthly or checkout.

Checks: Python compilation; direct title-cleaning and source wiring assertions; archive integrity. No complete live Streamlit or production PDF render tested. Rollback: restore these two files from v3.136.
