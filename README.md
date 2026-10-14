# Luna v3.102 — Year Ahead natal-to-transit evidence (focused)

Base version: v3.101. This is the FIRST controlled Year Ahead enhancement, not the finished Year Ahead product.

Changed application files:
- app.py: explicit APP_VERSION v3.102 only.
- paid_yearly_report.py: replaces text-search natal bridge with verified structured targets.
New application file:
- yearly_natal_intelligence.py: read-only evidence matching between existing natal aspects and Year Ahead Games.
Test: test_yearly_natal_intelligence_v3102.py (3 offline tests).

Preservation: no paid Monthly, Stripe, ephemeris, ranked Games, dates, prompts, HTML or PDF code changes. Existing report sections retained. If no natal aspect has verified annual target contacts, the bridge is omitted.

Install: apply ZIP files in the project root on top of v3.101. Rollback: restore the pre-change app.py and paid_yearly_report.py and remove yearly_natal_intelligence.py.

NOT verified: live Streamlit, full application test suite, Groq, Stripe, deployed PDF appearance. The full Year Ahead product is not complete.
