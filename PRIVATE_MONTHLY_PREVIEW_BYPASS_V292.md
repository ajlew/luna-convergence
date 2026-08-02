# Private Monthly Preview Bypass v2.9.2

## Purpose

This restores a safe way to inspect the complete Monthly customer report before the payment and delivery flow is approved. It does not expose or enable the Yearly product.

## Windows

Double-click:

```text
run_monthly_preview_windows.bat
```

The launcher opens:

```text
http://localhost:8514/monthly-preview
```

Choose the sign, year, month, timezone, city and focus, then select **Generate customer report**. The complete Monthly report appears with Print/Save controls. Stripe is not opened.

## Streamlit Community Cloud

Add these temporary values to **App settings → Secrets**:

```toml
LUNA_MONTHLY_PREVIEW_BYPASS = "1"
LUNA_MONTHLY_PREVIEW_PIN = "choose-a-private-pin"
```

Reboot the app, then open:

```text
https://luna-convergence.streamlit.app/monthly-preview
```

Enter the private PIN. The route is hidden from navigation and Monthly-only.

## Disable after review

Delete the two preview values from Streamlit Secrets, or set:

```toml
LUNA_MONTHLY_PREVIEW_BYPASS = "0"
```

The public Reports page remains the normal paid Monthly checkout. Yearly remains hidden throughout.
