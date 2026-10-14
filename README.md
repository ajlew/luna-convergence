Luna v3.104 — Year Ahead annual graphics

Apply app.py and yearly_print_html.py to the existing v3.103 repository.

Changes:
- Year Ahead annual section now renders all selected Game curves and their combined curve in a single SVG/date axis.
- The curves are derived from each Game's already-recorded transit active windows and exact-pass dates. No sine-wave periodicity or fixed customer dates.
- Colour differentiates Games; precise contacts appear as dots; start/end and monthly ticks use actual dates.
- app.py explicit application version is v3.104.

Not modified: Monthly report, natal calculation engine, writing/provider configuration, checkout, PDF generator architecture.

Verification: Python compilation and synthetic two-Game SVG structure checked. No live provider call, no full app integration test or real customer report visual comparison. Rollback: restore previous two files.
