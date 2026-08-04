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
- monthly report product and checkout;
- Yearly report kept inside the editorial environment until release;
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

The public launch price displayed by the site is A$4.95 for the Monthly report.
The Yearly price remains configured for internal testing but is not shown publicly.


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
email, star sign, report month and timezone before the Stripe payment button is shown.

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


## Cardinal narrative refinement

Shared aspect questions, relationship archetypes and story bridges now vary
through the activated house. Convergence windows are explicitly labelled
current, approaching or recent so an expired cluster is not presented as active.


## Fixed-sign editorial refinement

Taurus, Leo, Scorpio and Aquarius now have polished relationship copy and
non-duplicative questions. The Venus-square-Mars period is calculated to the
actual configured 6° orb boundaries: July 14–August 15, 2026.


## Final twelve-sign editorial pass

Daily stories now use natural prose rather than compact house labels, filter
near-duplicate questions, and include a sign-specific evidence card naming
the two life areas activated by the shared aspect.


## Moon–Saturn customer-language refinement

Moon–Saturn reflection questions now translate patience, proof and dependable
behaviour through each sign's two activated houses. The internal phrase
“reserve, consistency and emotional restraint” no longer appears in the
customer question set.


## Paid-order manual fulfilment

The purchase forms now collect a main focus and optional personal question, state the
24-hour manual PDF delivery promise, and carry fulfilment details through Stripe's
client reference. The admin console can generate a branded print-ready PDF for manual
email delivery.

## Monthly Narrative Engine v1

Monthly PDFs now use the same consequence-first editorial method as the public daily reading. The customer sees a monthly headline, month-at-a-glance story, three practical chapters, focused love/work/money interpretation, key dates and a Monthly Sky Snapshot before the technical appendix.

Administrative placeholder values such as `No optional question supplied` are normalised to blank and omitted from the customer PDF. The Stripe order reference remains available in the technical/order appendix for fulfilment reconciliation.


## Solar Convergence v1

Luna now combines the tropical Sun's twelve-phase cycle with four equinox
and solstice gates, the customer's actual local daylight trend, the
activated whole-sign house and the selected report focus.

- Daily readings display a compact Solar Position panel.
- Monthly PDFs include a full Solar Convergence page.
- Yearly reports include four solar chapters: Emergence, Expression,
  Rebalancing and Gestation.
- Paid-order forms accept an optional nearest city; no address is required.
- Blank or unsupported cities use a representative city for the timezone
  and disclose that the result is an estimate.

The feature uses astronomical and symbolic structure only. It does not
present claims that one religion secretly copied another as historical fact.


## Sparse mobile daily experience

The free daily page now defaults to a concise hero, two-paragraph story,
Do / Don't guidance and one convergence line. All existing evidence,
Solar Convergence, practical areas, questions and calculations remain
accessible through collapsed sections. Daily controls use a form and a
submitted request snapshot to reduce unnecessary reruns.


## Emotional Hook Engine v1

The daily hero now leads with a short, witty and evidence-grounded
emotional hook. The previous serious headline remains as the interpretive
theme directly underneath. Hook tone rotates deterministically through six
editorial families and is selected from the date, sign, strongest aspect
and activated house pair.


## Windows monthly-report hotfix

Monthly date labels are now platform-independent. The admin Horoscope tab
previews the same customer-first narrative used by the personalised PDF,
while the raw technical synthesis remains available in a collapsed section.


## Monthly Editorial PDF v2

Monthly customer PDFs now use a dedicated magazine-style renderer. The emotional hook appears first, practical pages use cards and timelines, and tables are concentrated in the Explainable Evidence appendix.

## Monthly Homepage PDF v3

The monthly PDF now prints the same visual system as the Luna homepage: Bodoni Moda headings, Josefin Sans body copy, IBM Plex Mono labels, the homepage brand/navigation rows, editorial two-column heroes, black reading cards and thin bordered trust strips. Chrome or Edge renders the print file; the stable Editorial v2 report remains an automatic fallback.


## Monthly Agency Webpage v1

The monthly customer product now renders as a responsive Luna webpage
with native browser Print/Save as PDF. Luna narrates one agency-first
storyline, concrete scenarios and relationship/validation meaning, while
evidence remains in four closed disclosures.


## Unified Luna voice and print v2

The daily page is now the language and presentation master for daily,
monthly and yearly readings. All three use Luna says, Do, Don't, Your
move and the same evidence language. Monthly and yearly webpages include
A4/A3 and portrait/landscape print controls.

The visible monthly page no longer contains scenario chips, the phrase
"You remain the main character", repeated chapter-level Your Move blocks
or an explanatory disclaimer near the opening. Examples are integrated
into the story and the disclaimer appears in the footer.


## Editorial preview bypass v2.1

While the product is being edited, `/editorial-preview` generates complete
monthly and year-ahead webpages without Stripe and includes native browser
print controls. Windows launchers now use separate ports and identify the
running build and folder. Set `EDITOR_PREVIEW_ENABLED = False` before launch.


## Unified Luna Reports v2.2

The normal Windows admin launcher now opens the same Luna `/reports`
interface used by the website. The old engineering dashboard is available
separately through `run_engine_windows.bat`. While editorial preview mode
is enabled, `/reports` generates complete monthly and year-ahead reports
without Stripe.


## Automatic References and Luna Wit v2.3

All reference disclosures now open automatically for browser printing. Daily, monthly and yearly readings share one concise house-pair Do/Don't engine with dry Luna humour.


## Monthly Story + Compact Hero v2.4

Monthly reports now use a compact black hook followed by a fuller,
chronological Luna story. The paid page includes four narrative
paragraphs, three detailed acts, visible dates worth circling,
romance-active/quiet guidance, Love/Work/Money outcomes and expandable
evidence. The print toolbar is static and no longer covers report content.


## Full Report Print Portal v2.5

Monthly and year-ahead printing now clones the complete report into a
temporary top-level print portal. This prevents Streamlit page containers
from clipping the report to one page. All evidence sections open in the
print clone and the selected A4/A3 orientation settings are preserved.

## Monthly Arc Engine v2.6

Monthly reports now construct the customer story from a chronological evidence
path rather than the two largest raw house totals. The engine evaluates the
seven-day carryover window, trigger hierarchy, native-sign ruler relevance,
ranked scenario families and six temporal roles: inherited state, inciting
event, complication, pivot, climax and resolution.

The July 2026 Sagittarius calibration selects the financial Full Moon carryover,
the shared-money New Moon, Mercury's direct station, the Sun-Jupiter climax and
the Aquarius Full Moon resolution. `Why Luna sees this` displays the equation,
arc roles and ranked scenario families while the complete evidence remains
expanded automatically for printing.


## Monthly Arc Evidence Cleanup v2.7

The repeated monthly arc equation and six narrative-role cards were removed from
the customer-facing Why Luna sees this section. A concise three-anchor evidence
path now supports the story without retelling it. Ranked scenario families remain
in Full technical evidence. Monthly and yearly customer dates use day-month-year
format, such as `1 July 2026`.


## Luna Narrator + Forecast Inventory v2.8

Luna is now a shared narrator across all products: sharp observer for
Daily, storyteller for Monthly and game strategist for Yearly. Monthly
arcs preserve independent relationship tests instead of burying them
inside dense transit clusters. Year-ahead reports use a top-down game map
validated against twelve monthly rounds. The preview-only
`/forecast-library` route can precompute versioned Daily, Monthly and
Yearly report records for editorial review and later sale.


## Daily + Monthly Production Pass v2.9

The public product now concentrates on **Free Daily + Paid Monthly** while the
Yearly engine remains available only in the editorial environment.

Public defaults:

```text
LUNA_EDITOR_PREVIEW=0
LUNA_PUBLIC_YEARLY=0
```

The local admin and editorial Windows launchers set
`LUNA_EDITOR_PREVIEW=1`, preserving Yearly and Forecast Library development
without exposing them on the customer site.

### Daily changes

- the Monthly purchase invitation now appears immediately after the core Daily
  reading rather than below the complete technical appendix;
- duplicated relationship copy is filtered from the secondary story section;
- Editorial Translation is removed from the public evidence panel;
- Planetary Positions and the 12-House Reference Matrix remain inside the
  collapsed Full Technical Evidence section;
- the existing full-width mobile layout and horizontal-overflow protection are
  retained.

### Monthly changes

The report now follows one chronological four-act spine:

1. The opening acquires structure.
2. The opportunity reveals its terms.
3. Attention meets the evidence test.
4. The public result must fit private life.

The relationship test is Act III rather than a detached feature card. The
opening no longer repeats the full month, and the former Dates Worth Circling
section is now an action-first Decision Calendar.


## Private Monthly preview bypass v2.9.2

Use `run_monthly_preview_windows.bat` to open the complete Monthly customer report at `/monthly-preview` without Stripe. The preview is Monthly-only and Yearly remains hidden. Streamlit Community Cloud can enable the same hidden route with `LUNA_MONTHLY_PREVIEW_BYPASS` and protect it with `LUNA_MONTHLY_PREVIEW_PIN`. See `PRIVATE_MONTHLY_PREVIEW_BYPASS_V292.md`.

## Active Agency Monthly voice v2.9.3

Monthly customer copy now uses active verbs and positions the reader as the
author of the next move. The signature line is **From reading the future to
writing it.** See `ACTIVE_AGENCY_MONTHLY_V293.md`.


## Reflective Agency Monthly voice v2.9.4

The Monthly narrator now uses reflective active language. Four-act headings use gerunds rather than repetitive “You...” constructions, and customer copy limits second-person address to moments where intimacy or direct action adds value. See `REFLECTIVE_AGENCY_MONTHLY_V294.md`.

## v2.9.5 - Evidence-Mapped Monthly

The August 2026 Monthly engine now maps evidence and houses into sign-specific scenarios, customer chapter titles, relationship questions and final actions. Duplicate calendar events are removed, print portals are isolated between signs, and generated PDFs are checked for merged-word text-layer defects before delivery.

Run the twelve-sign release gate with:

```powershell
python sanity_check_monthly_batch.py --year 2026 --month 8 --json Luna_v295_monthly_batch_audit.json
```

See `EVIDENCE_MAPPED_MONTHLY_V295.md` for the implementation and validation details.

## v2.9.6 - Refined Evidence-Mapped Monthly

The mapped Monthly engine now keeps the sign-specific logic while removing the
most visible signs of report repetition. Aries is the calibration case for the
new customer layer:

- the House 5 to House 6 story now reads as creativity and attraction finding a
  workable rhythm;
- the customer overview, chapter story, strategy and key dates each perform a
  different job rather than repeating the same forecast paragraph;
- the late-August key date now names the Virgo ingress that carries the practical
  result instead of using the Pisces eclipse for two separate roles;
- Love, Work and Money can use sign-specific consequence and action copy;
- the final signature, **From reading the future to writing it**, belongs to the
  strategy page rather than the Love card;
- the evidence snapshot shows primary story drivers before secondary scenario
  possibilities;
- convergence tables derive house values when the source does not precompute
  them;
- the customer PDF is reduced to nine pages and retains a clean searchable text
  layer.

Run the twelve-sign release gate with:

```powershell
python sanity_check_monthly_batch.py --year 2026 --month 8 --json Luna_v296_monthly_batch_audit.json
python test_refined_mapped_monthly_v296.py
```

See `REFINED_EVIDENCE_MAPPED_MONTHLY_V296.md` for the implementation and
validation details.

---

## v2.9.7 - Universal Monthly Evidence Engine

The Monthly product now uses one evidence formula for every sign and month:

```text
C(e,i,f) = T x O x A x H x R x I x D x F x P
```

The engine calculates event strength, applies a hard evidence-to-scenario gate, derives the source/destination house path, assigns evidence to chronological roles, and then applies Luna's existing editorial voice and report layout.

Production no longer selects a hand-written sign/month story profile. The v2.9.6 profiles remain only as a calibration archive in `monthly_story_profiles_v296_calibration.py`.

Validation:

- 12 signs x 12 months = 144 Monthly reports;
- no missing evidence-to-scenario mappings in active roles;
- no duplicate customer calendar triggers;
- highest same-month cross-sign similarity: 60.41%, below the 65% review gate;
- at least 80% distinct headlines across the year for every sign;
- isolated nine-page customer PDFs with clean searchable text.

Daily remains unchanged, Yearly remains hidden, and the private Monthly preview remains available.

## v2.9.7.1 - Daily and Monthly Reliability + Evidence Traceability

- Daily emotional-hook validation now fails softly instead of crashing the public page.
- Capricorn's House 4 hook uses "The family meeting has entered the chat."
- Same-house aspects use concentration grammar rather than "X connects with X."
- Daily output exposes exactly one reflection question.
- Daily browser printing uses isolated A4 customer-only and full-evidence documents.
- Daily includes searchable A4 PDF downloads with canonical filenames.
- Monthly printing uses a isolated A4 print frame, destroys legacy clones and opens all evidence sections.
- Monthly includes a searchable A4 PDF download with a canonical filename.
- The Monthly "Why Luna sees this" panel now displays role -> house -> scenario -> supporting events.
- Canonical filenames: `2026-08-03_Aries_Daily.pdf` and `2026-08_Aries_Monthly.pdf`.


## v2.9.7.2 - Monthly Opening Typography and Copy Polish

- Reduced and widened the web `Luna Says` block so it reads as body copy rather than a second hero headline.
- Added desktop justification and preserved left alignment on mobile.
- Kept the opening block together during printing where space permits.
- Replaced repeated house labels with a shorter customer-facing storyline.
- Simplified the opening sequence line.
- Reordered final Monthly actions as identify, clarify, act.
- Preserved the v2.9.7 Universal Monthly Evidence Engine and v2.9.7.1 reliability fixes.


## v2.9.7.3 - Download-Only Report Controls

- Removed the non-working Monthly `Print or save report` control and its A4 status block.
- Removed the two browser-print controls from Daily.
- Kept only reliable server-generated PDF downloads.
- Monthly searchable A4 PDF button now uses Luna's black primary style.
- Both Daily PDF download buttons now use the same black primary style.
- Download clicks no longer rerun the Streamlit page.
