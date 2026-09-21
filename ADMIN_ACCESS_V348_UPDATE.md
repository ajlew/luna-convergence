# Luna v3.48 — Owner Access

## What this adds

- One session-scoped owner unlock on the existing customer pages.
- The key is read only from the existing `LUNA_ADMIN_KEY` Streamlit secret.
- Password input is masked and checked with `secrets.compare_digest`.
- The key is never placed in a page URL, analytics event, order record or download.
- Personal Monthly and Year-Ahead reports can be generated and downloaded without creating a Stripe Checkout Session after owner authentication.
- Public Monthly and Year-Ahead visitors retain the existing Stripe checkout path.
- The Birthday Card stays on `/birthday-card`; it is admin-only until its customer Stripe product is connected.
- A Lock control clears owner access for the current browser session.

## How to use it

1. Open `/reports` or `/birthday-card`.
2. Expand **Luna owner access**.
3. Enter the value already stored as `LUNA_ADMIN_KEY` in Streamlit secrets.
4. Select and prepare the report or birthday card normally.
5. Generate/download the output on that same page without payment.
6. Select **Lock** when finished, or close the browser session.

## Security boundary

This is an owner convenience bypass, not a customer authentication system. The unlocked state exists only in Streamlit session state and disappears when the session ends. Never place the key in GitHub, a query string or a screenshot.
