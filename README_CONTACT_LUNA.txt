Luna v3.140 — Contact Luna support improvements (changed files only)

Replace app.py and luna_customer_features.py in the root of your GitHub repository.
Baseline app.py: prior Weekly Studio Instagram Story Social Card patch.
If app.py has changed since that patch, merge the contact_luna_page() function only.

Route: /contact-luna
- Select report/product and issue in separate dropdowns
- Enter email, optional order reference and message
- Send six-digit email verification code
- Verify code and save request to luna_support_requests
- Then send notification email to owner with descriptive subject and Reply-To customer

SMTP Streamlit secrets (do NOT commit secrets):
LUNA_SMTP_HOST
LUNA_SMTP_PORT (default 587; STARTTLS)
LUNA_SMTP_USER
LUNA_SMTP_PASSWORD
LUNA_SUPPORT_FROM_EMAIL (verified SMTP sender)
LUNA_SUPPORT_TO_EMAIL (owner email inbox)

Persistent storage secrets:
LUNA_SUPABASE_URL
LUNA_SUPABASE_SERVICE_ROLE_KEY

Existing luna_support_requests table schema expected:
email, topic, order_reference, message, status
Product and email subject are prefixed inside message without a database migration.
This patch does not provision SMTP or Supabase. Both need configuring before real requests work.
Verification codes are stored temporarily in Streamlit session; they expire after 10 minutes and accept 5 attempts.
No Groq calls, no version bump.
Offline tests: python -m unittest test_contact_luna.py
