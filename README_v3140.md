# Luna v3.140 — Bodoni chart text

Required base: v3.139. Replace `yearly_print_html.py` and `luna_release.json`.

The activation-wheel centre now reads `Natal` / `Activations` (both Title Case). The existing Bodoni Moda CSS for planet and centre labels is retained, and three-letter planet labels remain title-cased (`Sun`, `Ven`, `Mar`, `Plu`). Zodiac glyphs retain the symbol font.

Only source inspection, Python compilation and archive checks were performed. PDF font embedding and live production render were **not** verified. A PDF may fall back to Georgia if Bodoni Moda resources are unavailable to the renderer; check the actual PDF's embedded fonts.

Rollback: restore both files from v3.139. No Groq, Python calculations, Game Theory or Paid Monthly change.
