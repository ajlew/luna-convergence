# Luna Convergence — Customer MVP

A clean customer-facing Streamlit website built on the tested hybrid Swiss Ephemeris horoscope engine.

## Public site

Run:

```powershell
streamlit run app.py
```

The public site includes:

- large responsive homepage;
- free daily horoscope;
- active-house explanations;
- full twelve-house reference matrix;
- monthly and year-ahead product cards;
- Stripe Payment Link placeholders;
- manual-fulfilment order-details flow;
- sample report;
- transparent methodology and disclaimer.

## Local admin console

Run:

```powershell
streamlit run admin_console.py
```

The admin console retains:

- daily, monthly and yearly generation;
- ephemeris PDF upload;
- technical JSON;
- convergence details;
- retrograde cycles;
- optional Ollama enhancement;
- downloadable reports.

## Working brand

The working name is:

```text
Luna Convergence
```

Change the brand, prices and tagline in:

```text
site_config.py
```

## Payment setup

Set the following Streamlit secrets:

```toml
STRIPE_MONTHLY_URL = "..."
STRIPE_YEARLY_URL = "..."
REPORT_REQUEST_URL = ""
NEWSLETTER_URL = ""
CONTACT_EMAIL = "..."
```

See `.streamlit/secrets.toml.example`.

## Files

| File | Purpose |
|---|---|
| `app.py` | Public customer website |
| `admin_console.py` | Local report-generation console |
| `customer_experience.py` | Free daily summary and order helpers |
| `site_config.py` | Brand, prices and navigation |
| `astrology_engine.py` | Planetary calculations and event detection |
| `synthesis.py` | Detailed interpretation and convergence synthesis |
| `interpretation_library.py` | House, planet and retrograde meanings |
| `DEPLOYMENT.md` | Public launch instructions |

## Limitation

The public forecast is a general Sun-sign or rising-sign reading using whole-sign houses.
Astrology is presented as a symbolic interpretive framework rather than scientifically established causal prediction.

## Visual direction

The public site uses:

- a full white page background;
- Josefin Sans as the primary elegant display and reading font;
- IBM Plex Mono for typewriter-style labels, buttons and navigation;
- crisp black lines and black reading panels;
- a custom Saturn/hexagon black-box favicon and brand mark;
- square editorial cards rather than rounded corporate cards.

The design is inspired by restrained black-and-white astrology editorial sites without copying their branding, illustrations or wording.


## Typography update

- Bodoni Moda for large editorial headings
- Josefin Sans for body copy and brand name
- IBM Plex Mono for labels, navigation and buttons
- Explicit black header styling so the brand remains visible on white pages


## Header and Bodoni reliability fix

The Streamlit fixed header previously sat over the custom brand row and made
the logo and name appear faded. The public app now hides that overlay and
restores normal top spacing.

Large titles now use a direct editorial-title class plus a strong Bodoni/Didot/
Georgia fallback stack. This prevents Streamlit's generated heading CSS from
silently reverting the titles to the sans-serif body font.
