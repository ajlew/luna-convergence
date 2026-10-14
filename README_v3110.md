# Luna v3.110 — complete Year Ahead print delivery

Apply over v3.109. Only `app.py` is modified. The explicitly hard-coded version is v3.110.

Both owner and paid Year Ahead now expose (1) complete PDF and (2) standalone printable HTML using the existing Year Ahead renderer, with explicit printing instructions. The paid route builds printable HTML from the **same validated product** without another Groq call. Paid Monthly path and its buttons remain unchanged.

**Printing:** Download/open PDF, then Ctrl+P (all pages), or download/open standalone HTML then Ctrl+P. Ctrl+P on a Streamlit app shell is not reliable and cannot be made equivalent to printing a standalone document via Streamlit's widget iframe. Do not promise it will print the complete report.

PDF and HTML download buttons depend on a successfully completed paid report. No fallbacks, astrology, charts, narrative or provider modifications.

Regression test: `python -m pytest -q test_v3110.py` and `python -m py_compile app.py`.
