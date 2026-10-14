# Luna v3.116 — Paid Year Ahead presentation correction

**Base:** v3.115. Apply only the listed files to the repository currently running v3.115. Do not use an older baseline.

## Source files changed
- `app.py`: explicit release version `v3.116`.
- `paid_yearly_editorial.py`: remove residual inline internal `<<...>>` assembly labels from every parsed customer text section, without changing the section parser or inventing replacement prose.
- `yearly_print_html.py`: refine monthly orb curves using six-hour Swiss Ephemeris samples rather than daily samples; show narrowing orb (applying) at 90% opacity and widening orb (separating) at 52%, 1.55 SVG units stroke; smaller exact markers, same game colours and position axes. Maintain inactive tracks and verified-date window fallback.

## No changes
Paid Monthly, natal/annual calculations, Groq configuration, annual Game graph, activation wheels, checkout and PDF delivery code.

## Verification
Python compilation and seven focused offline tests passed. No live Groq call performed. PDF browser/Streamlit rendering and full purchased report not verified in production. Do not describe as live-certified.

## Installation and rollback
Back up the three target files, overlay them, run Streamlit and generate an owner report; confirm leaked markers absent in web/HTML/PDF. Roll back the three files if regression occurs.
