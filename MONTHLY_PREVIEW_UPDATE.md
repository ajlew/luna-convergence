# Luna Convergence — Monthly Preview update

Replace only `app.py` in the GitHub repository.

After Streamlit redeploys, open:

https://luna-convergence.streamlit.app/monthly-preview

The route is intentionally hidden from normal navigation. It works independently of `EDITOR_PREVIEW_ENABLED` and shows the complete monthly customer report without Stripe.

Included behavior:
- defaults to the visitor's current local month/year;
- detects the visitor's browser timezone;
- lets the editor choose sign, month, year, timezone, city and main focus;
- renders the full monthly report;
- shows browser print/save controls;
- does not expose the Year Ahead generator;
- does not alter the normal paid Reports page.
