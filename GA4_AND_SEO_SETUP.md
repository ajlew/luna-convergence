# Google Analytics and Search Console Setup

## Analytics installed

The public app includes Google Analytics 4 using:

```text
G-TE5HPKV94D
```

The ID is the default and can be overridden in Streamlit Secrets:

```toml
GA_MEASUREMENT_ID = "G-TE5HPKV94D"
```

Tracked events:

- `page_view`
- `daily_reading_start`
- `daily_reading_generated`
- `monthly_report_click`
- `yearly_report_click`

## Permanent URLs

The app now uses `st.Page` and `st.navigation`, creating permanent
routes for the main pages and twelve August 2026 sign pages.

The complete URL list is in:

```text
SEARCH_CONSOLE_URLS.txt
```

## Search Console

Add this URL-prefix property:

```text
https://luna-convergence.streamlit.app/
```

After verification, use URL Inspection to request indexing for the
homepage, the August 2026 index, and each sign page.

Streamlit Community Cloud does not serve arbitrary repository files
as a true `/sitemap.xml` endpoint, so this release supplies a URL list
for manual inspection rather than pretending an HTML page is an XML sitemap.

## Analytics verification

In Google Analytics, open:

```text
Reports → Realtime
```

Visit the public site in a private browser, open two or three pages,
generate a free daily reading, and click a payment button without
completing another purchase. Events can take a short time to appear.
