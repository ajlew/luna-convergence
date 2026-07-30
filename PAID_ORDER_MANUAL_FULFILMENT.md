# Paid Order Manual Fulfilment - Stage 1

## Customer form

Monthly orders now collect:

- delivery email;
- star sign;
- report month;
- timezone;
- main focus;
- optional personal question (80 characters maximum).

Year-ahead orders collect the equivalent calendar-year information and priority.

## Delivery promise

The customer sees this before checkout:

> Your personalised PDF is currently prepared and emailed manually after payment. Please allow up to 24 hours for delivery.

## Stripe handoff

The Stripe `client_reference_id` now carries:

- product type;
- sign;
- period;
- timezone;
- focus code;
- readable personal-question fragment;
- unique token.

The reference remains within 200 characters. The customer can also download a JSON order record or send a prepared order-details email before payment.

## Manual PDF

`report_pdf.py` converts the deterministic monthly or yearly report into a branded A4 PDF with:

- cover page;
- selected focus;
- optional question;
- calculated report sections;
- tables;
- page headers and page numbers;
- method and disclaimer note.

The admin console now has a **Manual fulfilment** section and a **Download print-ready personalised PDF** button.

## Real payment test

The code cannot complete a real financial transaction or send an attachment from this workspace. After deployment:

1. prepare a monthly test order;
2. verify focus and question appear in the order summary;
3. verify the Stripe payment contains the same `client_reference_id`;
4. generate the PDF in the admin console;
5. email it manually to the test address;
6. confirm receipt and record the delivery time.

Automatic generation and email remain deliberately deferred until this manual path succeeds reliably.
