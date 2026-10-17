Luna v3.140 Contact Luna SMTP secret compatibility fix

Replace only luna_customer_features.py at the repository root.

Uses your existing Streamlit Cloud secrets:
  SMTP_USER
  SMTP_APP_PASSWORD
  SMTP_FROM
Defaults: smtp.gmail.com port 587 (STARTTLS), support inbox SMTP_USER.
LUNA_* SMTP values still take precedence if provided.

No app.py replacement, no version change, no provider requests.
This is offline-tested only. A live send is required to verify provider connectivity.
Do not put credentials in GitHub.
