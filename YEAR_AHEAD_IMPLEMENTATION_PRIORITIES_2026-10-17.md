# Luna Convergence — Year Ahead implementation priorities

Baseline: uploaded `luna-convergence-main(5).zip`, 17 October 2026.
Reference: Libra Paid Year Ahead, 17 Oct 2026–16 Oct 2027 (30-page PDF).
Cost rule: Offline checks first; **no Groq calls to verify Python changes**.

| Priority | Change | Acceptance test | Status in this patch |
|---|---|---|---|
| P0 | Lock ZIP baseline, identify deployed commit and isolate Paid Yearly changes | Exact version and rollback known | Uploaded ZIP is frozen as rollback; deployed commit cannot be established offline |
| P0 | Audit pre-LLM phase/month/Game packets | Every date, event, period and section assignment consistent | Pending full fixture audit |
| P0 | Make retry and provider policy explicitly cost-controlled | No unintended second chargeable request | Pending; do not deploy unrelated payment changes |
| P0 | Make completed sections and reports durable | Refresh/restart does not trigger fresh generation | Pending persistent storage design |
| P1 | Improve Python's sequential Game decisions | Each month advances the previous strategic state | Pending evidence-model change |
| P1 | Improve natal narrative instructions | Specific calculated strengths, not mechanical wording | Pending packet adjustment; no post-LLM rewrite |
| P1 | Repair Year Ahead PDF pagination | No isolated chart pages or avoidable overflow | Pending; isolated spill pages confirmed in supplied report |
| P1 | **Print the Natal Activation wheel's internal labels in Bodoni** | Centre 'Natal / Activations' and planet abbreviations have the same Bodoni typographic character as the Major Game heading, with vector-safe rendering | **Implemented in `yearly_print_html.py`**, offline tested; existing font in repo only |
| P1 | Verify screen/HTML/PDF parity | Same content, correct ordering and dates | Pending complete fixture verification |
| Regression | Protect Paid Monthly | Existing voice, strengths, charts and PDF unchanged | No Paid Monthly writer files changed |

## Typography change and constraints

The supplied PDF's page 6 has Bodoni heading text but the SVG wheel's text spans resolve to DejaVu Sans. The chart's font CSS alone was not enough because HTML @font-face does not carry through reliably to embedded SVG rendering. The wheel now uses glyph outlines from the **existing project BodoniModa-SemiBold.ttf**, only for the centre words and natal planet abbreviations. Zodiac symbols remain independent vector drawings. No astronomy, ranking, Game data, prompts, LLM outputs, or paid Monthly logic changed. `fonttools` is declared as a runtime dependency.

## Verification

1. Syntax compile `yearly_print_html.py`.
2. Render a small offline SVG/PDF sample and confirm no DejaVu fallback on targeted wheel text (it is outlines).
3. For production acceptance, generate one already-paid/locally-cached Year Ahead PDF **without Groq** and visually compare chart on page 6 and all 12 monthly wheels. Check activation-marker positions are unchanged.
4. Do not claim deployed readiness until rendered production fixture checked.
