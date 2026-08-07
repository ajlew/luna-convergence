Luna Convergence monthly preview fallback

Upload app.py to the root of the GitHub repository and replace the existing app.py.
After Streamlit redeploys, open:
https://luna-convergence.streamlit.app/reports?preview=monthly

This uses the existing /reports route, avoiding Page Not Found on /monthly-preview.
The original /monthly-preview route remains in the app as well.
