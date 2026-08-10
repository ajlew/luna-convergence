# Luna v3.18.2 — Checkout Simplification

Changes:
- Removed the promotional heading and explanatory copy above the report checkout.
- Removed the Monthly and Year-ahead marketing cards from that section.
- Monthly public price changed from A$4.95 to A$3.30.
- Checkout forms and report selection remain intact.

Important Stripe note:
The public display price is now A$3.30, but Stripe Prices are immutable. The live Stripe Monthly Price used by Checkout must also be replaced with a new A$3.30 AUD Price and its `price_...` ID stored as `STRIPE_MONTHLY_PRICE_ID` in Streamlit Secrets.
