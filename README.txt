Luna Convergence v3.17 Google Ads base-tag hotfix

Replace app.py only.

Adds Google Ads destination AW-18379683881 alongside the existing GA4 destination G-TE5HPKV94D.
Existing Daily renderer hotfix remains preserved.

Optional Streamlit secret:
GOOGLE_ADS_ID = "AW-18379683881"

If omitted, app.py defaults to AW-18379683881.

This connects the base Google Ads tag only. A purchase conversion event/label is a separate next step.
