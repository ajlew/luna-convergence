# Luna v3.18.3 — Paid PDF delivery correction

Paid fulfilment now treats the PDF as the product, not as a secondary control hidden after the web report.

- Payment success generates the PDF before rendering the long report.
- A prominent `Download your personalised PDF` button appears near the top of the paid page.
- Gmail SMTP and Resend emails attach the PDF itself.
- The email also keeps the private link so the buyer can reopen the paid web report.
- The old customer wording `A private return link has been emailed...` is removed.
- Monthly and Year-Ahead paid reports use the same attachment flow.

No buyer should need to make a second payment to retrieve the same paid report; the Stripe-session return link remains reusable.
