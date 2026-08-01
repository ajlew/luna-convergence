# Unified Luna Reports v2.2

## One customer interface

Normal local report generation now uses the same `app.py` interface as
the deployed website.

- `run_admin_windows.bat` opens `/reports` on port 8511.
- `run_customer_windows.bat` opens the website on port 8512.
- `run_editor_preview_windows.bat` opens `/reports` on port 8513.
- `run_engine_windows.bat` opens the old developer diagnostics on port 8514.

The former admin console has been renamed **Luna Engine Diagnostics**.
It remains available only for ephemeris uploads, raw calculations,
troubleshooting and manual-fulfilment diagnostics.

## Website report generation

While `EDITOR_PREVIEW_ENABLED = True`, `/reports` directly contains the
complete Monthly / Year-ahead generator. There is no intermediate link
and no Stripe checkout.

The generated report uses the customer layout and provides:

- A4 / A3;
- Portrait / Landscape;
- Include evidence;
- Print or save report.

## Launch mode

Before paid launch, set:

```python
EDITOR_PREVIEW_ENABLED = False
```

This restores the paid ordering workflow. The private local reports
launcher can later use a separate authentication or local-only setting.
