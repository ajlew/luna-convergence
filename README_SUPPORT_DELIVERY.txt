Luna v3.140 | Contact Luna support delivery hotfix

Install both files in repository root:
  app.py
  luna_customer_features.py

Changes:
- Existing SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY settings now work alongside LUNA_SUPABASE_* aliases.
- Verified support requests are accepted if either: (a) database storage succeeds, or (b) owner support email succeeds. The customer only sees a received confirmation if one succeeds.
- On a healthy existing Gmail SMTP configuration, no database is required to deliver requests to the configured support inbox.
- If database storage succeeds but email fails, the customer receives a clear warning (not a false email-sent success).
- Subject includes report type and issue; Reply-To is the verified customer address.
- No changes to Paid Monthly, Year Ahead, version label or Groq.

Important: Live SMTP delivery, Supabase table creation and end-to-end support form not verified here. If BOTH destinations fail, the form correctly reports that nothing was submitted. If you want persistent reporting independent of email, create the luna_support_requests table according to the existing schema or configure it separately.

No credentials are packaged. Keep Streamlit secrets private.
