# Luna v3.135 — Evidence and Print Corrections

Based on v3.134. Install these three files in place of the existing Year Ahead files.

## P0: Python-owned exact-pass ledger
- All Read-the-Year named contacts now come from calculated exact passes in selected Games. Trigger rows lacking matching technical-appendix exact-pass evidence are excluded from the narrated planetary date ledger.
- Each monthly writing request receives only exact passes from its assigned dominant Game and chapter period. Removed redundant active transit catalogue that exposed other possible aspects and dates.
- Major Story contracts retain their own calculated bounded exact passes.
- Groq prose continues to be accepted without post-LLM editorial rewriting or marker parsing. Cached prose checkpoint namespace changed to prevent reuse of previous-format text.
- No assertion of perfect model compliance: a new live report must be checked against the evidence appendix before launch.

## P1: Print
- Order reference removed from front matter, placed at end of technical appendix in small type.
- Monthly chart blocks allowed to flow at the data boundary, with a more compact wheel/legend layout; existing SVG label collision algorithm kept.
- Major Story timing evidence moved to the story opening, so it cannot trail on a page by itself.
- Print page-break rules made less rigid; small changes in spacing and major-story typography.
- Existing neutral ink-friendly print theme and combined timeline maintained.

## P2: Copy
- Natal portrait prose instructions strengthened to connect calculated strengths to recognizable everyday choices and blind spots.
- A Game receives an introductory, qualified definition: a calculated convergence and strategic decision framework, not a calculated optimal outcome.

## Scope and verification
- Compiled: app.py, paid_yearly_editorial.py, yearly_print_html.py.
- Focused AST-isolated exact-pass / Game ownership test passed (the full module imports repository dependencies unavailable in the standalone ZIP).
- Existing sample HTML-to-PDF smoke render passed (20 pages; near-empty pages 1 and 18 remained in sample, so pagination is **not fully verified**).
- No Groq API run and no end-to-end live 28-page customer PDF generated. Do not interpret offline smoke as release-grade visual QA.
- Payments and Paid Monthly not modified.
