# Luna v3.54 — Paid Birthday Card launch

## Customer offer

- Price: **A$2.40**, one-time payment.
- Includes one personalised 1080 × 1920 PNG and one matching PDF.
- Midnight Painted and Ivory Letter remain selectable.
- The finished card is shown only after Stripe confirms payment.

## Fulfilment contract

1. Luna validates the customer email and birth details.
2. Luna calculates the birth sky and prepares one validated poem.
3. The poem and card facts are attached to the Stripe Checkout Session.
4. Stripe returns the customer to `/payment-success`.
5. Luna verifies the Checkout Session is complete and paid.
6. Luna rebuilds the exact prepared card and unlocks both downloads.
7. Luna emails the PDF and private return link using the existing delivery provider.

Owner access remains a no-payment test path.

## Required Streamlit secret

Create a one-time Stripe Price for **AUD 2.40** and add:

```toml
STRIPE_BIRTHDAY_PRICE_ID = "price_..."
```

Luna checks the configured Price through Stripe before opening checkout. A recurring
Price, a non-AUD Price or any amount other than 240 cents is rejected.

## Privacy and stability

Birthday fulfilment data is stored in the customer's Stripe Checkout Session so the
private paid link survives a browser refresh or a later return. The public card still
prints only the birth day and month. The prepared poem is reused exactly; Luna does not
generate a different card whenever the paid link is reopened.
