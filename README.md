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


## Google Analytics and SEO routes

This release adds:

- Google Analytics 4 ID `G-TE5HPKV94D`;
- tracked page views, daily-reading generation and Stripe clicks;
- real Streamlit page URLs using `st.Page` and `st.navigation`;
- twelve sign-specific August 2026 horoscope pages;
- unique page titles, descriptions and canonical links;
- a privacy and analytics page;
- `SEARCH_CONSOLE_URLS.txt` for Google Search Console submission.

Launch prices displayed by the site are A$4.95 monthly and A$14.95 yearly.
Stripe Payment Link prices must be kept in sync separately.


## Daily Reading Version 2

The public daily horoscope now translates the calculated astrology into:

- a human editorial headline;
- two warm forecast paragraphs;
- one practical best move;
- four reflection questions;
- compact Love, Work and Money notes;
- an expandable technical section showing the active houses, dominant aspect,
  wider convergence context and house matrix.

The prose remains deterministic and grounded in the Swiss Ephemeris calculation,
whole-sign house mapping and detected planetary aspects. It does not claim a
specific personal event that the calculation cannot support.


## Pre-payment order capture

The public purchase flow now requires the customer to choose the delivery
email, star sign, report month or calendar year, and timezone before the
Stripe payment button is shown.

The app passes a prefilled email and compact Luna order reference to Stripe.
The same panel appears below the House Guide and is prefilled with the sign
currently selected there.


## Daily Reading Version 3

The daily engine now chooses a genuinely date-sensitive trigger rather than
allowing a slow outer-planet aspect to dominate consecutive days.

It prioritises the Moon and faster personal planets, recognises the day an
aspect becomes closest to exact, and moves long-running generational aspects
into the technical background.

Every public reading now includes a prominent **Love & desire** interpretation.
Romance archetypes such as slow burn, unconventional attraction, mystery,
intensity, power and age/status difference are used only when supported by
Saturn, Uranus, Neptune, Pluto, Venus, Mars or the Moon. The language preserves
autonomy, consent, emotional safety and mutual respect.


## Daily Narrative Engine v2 production merge

The current public app now compares each daily reading with the preceding four readings. Repeated slow-moving material is moved into **Long-term current**, while the unique date-sensitive trigger leads **Today’s story**.

The buyer sees a clean narrative first. An expandable evidence section supplies the active planets, aspect, orb, applying/separating status, activated houses, active time window, convergence concentration and Sky Snapshot. The evidence strength score is an astrology concentration/exactness indicator, not an event probability.


## Explainable Astrology

The public daily reading now begins with the customer consequence rather than the transit. It presents a three-to-four paragraph story, a plain-English convergence axis, three short evidence points, a weather-versus-climate explanation and a compact Sky Snapshot. Full houses, aspects, orbs and planetary positions remain optional.

The visible strength label describes how clearly one astrological pattern dominates the day. It is not a probability that a predicted event will occur.


## Sign-specific headline layer

Daily headlines now translate a shared aspect through the activated house pair
for each selected sign. The same sky evidence can remain consistent across the
zodiac, but the public consequence, wording and headline are unique.

A regression test generates all twelve signs across four consecutive dates and
requires twelve distinct headlines per date.


## Full public-narrative uniqueness

The sign-specific layer now extends beyond the headline. Today's Story,
relationship interpretation, opportunity, caution, action and question set
all change with the houses activated for the selected sign. Genuine shared
astronomical evidence remains consistent.

The Daily Horoscope purchase panel also uses a sign-specific Streamlit widget
namespace so the report selector opens with the sign currently displayed
rather than retaining an earlier Sagittarius selection.
