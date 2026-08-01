# Editorial Preview Bypass v2.1

## Why the old page kept appearing

All earlier Windows launchers used Streamlit's default port 8501. An old
Streamlit process could therefore remain visible while a newer folder was
launched, or the user could double-click the BAT file in an older extracted
directory.

The launchers now use distinct ports:

- Admin: http://localhost:8511
- Customer website: http://localhost:8512
- Editorial preview: http://localhost:8513/editorial-preview

Each launcher prints the build name and exact folder path in the Windows
terminal. The admin page also displays the build name at the top.

## Why the website did not print

The public August sign page intentionally used:

```python
show_print=False
preview=True
```

That supplied only a shortened pre-payment sample.

While `EDITOR_PREVIEW_ENABLED = True`, August sign pages now use the full
customer report with native Print/Save controls, and checkout is hidden.

## Editorial preview route

`/editorial-preview` generates a complete monthly or year-ahead customer
report using:

- sign;
- month/year;
- timezone;
- nearest city;
- main focus.

It bypasses Stripe and provides the same A4/A3, portrait/landscape and
evidence-print options used by the customer report.

## Before launch

Change in `site_config.py`:

```python
EDITOR_PREVIEW_ENABLED = False
```

This removes the preview navigation item, restores the abbreviated public
samples and restores checkout on the sign pages.
