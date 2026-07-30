# Order Capture and Stripe Checkout

## Customer purchase flow

Customers choose these details before payment:

- delivery email;
- star sign;
- monthly report month or year-ahead calendar year;
- timezone;
- main focus;
- optional personal question, limited to 80 characters.

The payment button appears only after a valid delivery email has been entered.

## Manual delivery promise

The form and product cards state:

> Your personalised PDF is currently prepared and emailed manually after payment. Please allow up to 24 hours for delivery.

## Stripe order reference

The app adds `prefilled_email` and `client_reference_id` to the existing Stripe Payment Link.

Example:

```text
LC-MONTHLY-SAGITTARIUS-2026-08-AUSTRALIA-SYDNEY-F-LOVE-Q-WHAT-SHOULD-I-KNOW-ABOUT-LOVE-A1B2C3D4
```

The reference contains the report type, sign, period, timezone, focus code, readable question fragment and unique token. It does not contain card details or birth details.

The customer can also download a JSON order record or open a prepared order-details email before payment.

## Manual fulfilment

The admin console collects the customer's order reference, email, focus and question. After generating the monthly or yearly calculation it provides a print-ready personalised PDF download. Attach that PDF to the customer's delivery email and send it within 24 hours.

## Earlier payment without details

On the Reports page, expand:

```text
Already paid without selecting a star sign or report period?
```

The recovery form now includes sign, period, timezone, focus, optional question and the Stripe payment reference.
