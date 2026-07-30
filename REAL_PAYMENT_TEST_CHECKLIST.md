# Real Payment-to-Email Test

Use a low-value live monthly order after deploying the paid-order patch.

## Before payment

- Confirm the form shows delivery email, sign, month, timezone, main focus and optional question.
- Confirm the 24-hour manual-delivery notice is visible above the payment button.
- Click **Prepare monthly checkout**.
- Confirm the order summary contains every selected detail.
- Download the JSON order record.
- Copy the Luna order reference.

## Stripe handoff

- Continue to Stripe and complete the payment.
- Open the completed payment / Checkout Session in Stripe.
- Confirm the `client_reference_id` matches the Luna order reference.
- Confirm the email in Stripe matches the delivery email.

## PDF fulfilment

- Open `admin_console.py`.
- Choose the same sign, period and timezone.
- Enter the customer email, order reference, focus and question.
- Generate the analysis.
- Download **Print-ready personalised PDF**.
- Open the PDF and verify the cover, focus, question, report period and page layout.

## Email delivery

- Attach the PDF to a normal delivery email.
- Send it to the test customer email.
- Confirm the attachment arrives and opens correctly.
- Record payment time, send time and receipt time.

## Pass condition

The manual journey passes when the correct PDF reaches the correct email within 24 hours and the Stripe reference, JSON record and PDF all match.
