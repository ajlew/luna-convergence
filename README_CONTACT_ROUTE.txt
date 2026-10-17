Luna v3.140 — Contact Luna route hotfix

FIX: The prior Contact Luna ZIP defined CONTACT_PAGE_REF but forgot to include it in ALL_PAGES. Streamlit therefore returned Page not found.

Install: replace repository-root app.py from this ZIP. If the preceding Contact Luna patch was not installed, also add luna_customer_features.py.

Also adds a Contact Luna footer link so customers can find the page.

This is based on the previous Contact Luna changed-files app.py, including Weekly Studio social-card changes. If your app.py has since changed, merge ONLY these two edits:
  1. Add CONTACT_PAGE_REF to the ALL_PAGES array.
  2. Add an /contact-luna link to footer navigation.

Email verification, database and owner notifications still require the secrets/services documented in the prior Contact Luna README. No email provider or Groq was called.
