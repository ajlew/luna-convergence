# Order Capture and Stripe Checkout

## New purchase flow

Customers now choose these details before payment:

- delivery email;
- star sign;
- monthly report month or year-ahead calendar year;
- timezone.

The payment button appears only after valid details have been entered.

## Stripe order reference

The app adds `prefilled_email` and `client_reference_id` to the existing
Stripe Payment Link.

Example:

```text
LC-MONTHLY-SAGITTARIUS-2026-08-AUSTRALIA-SYDNEY-A1B2C3D4
```

The reference contains the report type, sign, period and timezone. It does
not contain card details or birth details.

In Stripe, open the completed payment and inspect its Checkout Session or
client reference. Keep that reference with the manually fulfilled report.

## House Guide

The House Guide asks for the star sign because the whole-sign house map is
fixed by the sign. A month does not change the static map. The purchase panel
directly beneath it separately asks for the report month or calendar year.

## Earlier payment without details

On the Reports page, expand:

```text
Already paid without selecting a star sign or report period?
```

The recovery form prepares an email containing the missing details and the
earlier Stripe payment reference.
