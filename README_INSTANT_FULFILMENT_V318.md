# Luna v3.18 — Instant Fulfilment

## What changed

The public paid-report journey no longer asks the customer to email or download order details and no longer promises delivery within 24 hours.

Monthly / Year-Ahead checkout now works as:

1. customer selects email, sign, period, timezone, city, focus and optional question;
2. Luna creates a fresh Stripe Checkout Session server-side;
3. the exact fulfilment inputs are stored in Stripe Checkout Session metadata;
4. after payment Stripe redirects to `/payment-success?session_id={CHECKOUT_SESSION_ID}`;
5. Luna retrieves that session directly from Stripe and refuses access unless it is `complete` and `paid`;
6. Luna generates the complete report immediately;
7. Monthly includes the native server-generated PDF download;
8. Luna sends the customer a private return link immediately when an email provider is configured;
9. GA4 receives a `purchase` event; an optional Google Ads purchase conversion can also fire.

`EDITOR_PREVIEW_ENABLED` is now `False` so the public reports route no longer bypasses Stripe.

## Files added

- `stripe_checkout.py` — Checkout Session creation / verification / Price-ID discovery.
- `email_delivery.py` — immediate report-link email via Resend or Gmail SMTP.
- `fulfilment_service.py` — small framework-free WSGI Stripe webhook receiver for reliable delivery even if the customer closes the browser.
- `render.yaml` — optional Render service definition for the webhook.
- `test_instant_fulfilment_v318.py` — v3.18 regression tests.

## Files changed

- `app.py`
- `monthly_report_pipeline.py`
- `order_capture.py`
- `site_config.py`
- `requirements.txt`
- `.streamlit/secrets.toml.example`

## Streamlit Secrets required before live checkout

At minimum:

```toml
STRIPE_SECRET_KEY = "sk_live_..."
```

Luna can discover the Stripe Price attached to the existing `STRIPE_MONTHLY_URL` and `STRIPE_YEARLY_URL`. For a more explicit configuration you can add:

```toml
STRIPE_MONTHLY_PRICE_ID = "price_..."
STRIPE_YEARLY_PRICE_ID = "price_..."
```

### Immediate email — choose one

**Resend (recommended for production/webhook idempotency):**

```toml
RESEND_API_KEY = "re_..."
RESEND_FROM = "Luna Convergence <reports@your-verified-domain.com>"
```

**or Gmail App Password for paid beta:**

```toml
SMTP_USER = "lunaconvergence@gmail.com"
SMTP_APP_PASSWORD = "your-16-character-app-password"
SMTP_FROM = "lunaconvergence@gmail.com"
```

The normal success-page flow sends the email immediately. The separate webhook service is the reliability layer for customers who close the browser before Stripe returns them to Luna.

## Stripe webhook reliability layer

Deploy `fulfilment_service.py` as a small HTTPS web service. Its endpoints are:

- `GET /health`
- `POST /stripe/webhook`

In Stripe, add its `/stripe/webhook` URL as an event destination and listen for:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`

Copy the endpoint signing secret into the service environment as:

```text
STRIPE_WEBHOOK_SECRET=whsec_...
```

Also add the same email-provider environment variables used by Streamlit and:

```text
PUBLIC_SITE_URL=https://luna-convergence.streamlit.app
```

When Resend is used, the same `luna-fulfil-{CHECKOUT_SESSION_ID}` idempotency key is used by the success page and webhook so a webhook retry does not create duplicate email sends during the idempotency window.

## Google Ads purchase conversion

GA4 `purchase` fires automatically after Stripe verification.

For a dedicated Google Ads purchase conversion, add the conversion action label only:

```toml
GOOGLE_ADS_PURCHASE_LABEL = "replace_with_conversion_label"
```

The existing Ads ID remains:

```toml
GOOGLE_ADS_ID = "AW-18379683881"
```

## Privacy / data model

Luna does not store card details. Exact report fulfilment inputs are stored on the Stripe Checkout Session as metadata so the paid report can be regenerated from the verified private session link without a Luna customer database. The private report URL acts as a bearer link and should not be shared.

## Live test gate

Do not increase ad spend until all of these pass:

- checkout opens;
- payment completes;
- Stripe redirects to `/payment-success`;
- full Monthly report renders;
- `Download complete monthly PDF` works;
- email arrives immediately;
- GA4 shows `purchase`;
- optional Google Ads purchase conversion records the test sale;
- direct `/reports` access does not reveal full paid content without payment.
