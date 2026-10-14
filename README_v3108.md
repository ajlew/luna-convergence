# Luna v3.108 — Year Ahead charts and A4 layout

Apply over v3.107. Only `app.py` and `yearly_print_html.py` are changed.

- Hard-coded application version v3.108 and updated build label.
- Monthly transit charts calculate daily angular orbs from Swiss Ephemeris and the customer's natal longitudes; exact-hit dots use the original verified pass dates. The existing colour mapping and duration tracks remain. If calculation is unavailable, the original duration bar remains without inventing a curve.
- Monthly activation wheels use larger 90 mm print columns; zodiac glyphs are vector outlines so PDFs do not depend on missing symbol fonts; the planet labels remain small. No change to natal positions, transit selection, or chart houses.
- Natal Strengths are kept together in print where space permits; the duplicated quieter-ground descriptor is suppressed.
- Full natal wheel, annual activity graphic, Monthly product, narrative engine, LLM and checkout unchanged.

Offline checks: 3 targeted tests passed, Python compilation and sample SVG/PDF vector rendering passed. Full production customer report/live Streamlit PDF has not been tested. Run the existing repository suite and visually inspect a full 12-month A4 export before deploying.
