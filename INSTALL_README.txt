LUNA CONVERGENCE v3.85 — CUMULATIVE READER-VALUE UPDATE

Install this one ZIP over the repository root; it retains bundled v3.79-v3.84 improvements including PDF printing, natal activation visualizations, shortcut instructions, Saturn stone icon, native-library fallback, and Epic Sky JSON.

WHAT CHANGED
- The Paid Year Ahead Groq editorial prompt now requests two grounded month-specific sentences, connecting a plausible situation to an actual choice or watch-out. Months continuing one story must show progression, not restart it.
- Each monthly printed HTML chapter separates "What this month brings into focus" from "Your decision" when distinct sentences are available; older single-sentence editorial still renders without invented filler.
- Annual stories remain in the same one-call voice service and preserve their calculated technical evidence and original dates.
- The Year Ahead SVG timeline now allocates more room to long transit labels and reduces font size, so labels do not run through bars.
- Includes a non-mutating diagnostic helper flagging unsupported raw ISO dates in generated editorial; does NOT silently rewrite unsupported statements or assume all prose chronology is validated.

LIMITATIONS / VERIFICATION
- The richer month copy requires a NEW Groq generation; cached existing reports will retain old one-sentence month copy. Redeploy and generate a fresh owner report.
- Provider token/length caps still apply. This update does not create an extra Groq call or guarantee a complete expanded paragraph per month.
- This is an incremental editorial quality improvement, not the full long-form transit intelligence architecture described in the reference document. The remaining work includes verified provenance for every natural-language transit pass and linked natal-activation narrative.
- No live Groq/Stripe/customer flow has been verified locally.

DEPLOYMENT: Copy extracted files with directories intact and redeploy. Confirm footer reads v3.85. Keep unlisted existing project modules. Use owner report on a fresh date/profile and check content/printing.

LUNA CONVERGENCE v3.84 — CUMULATIVE UPDATE

Includes v3.79–v3.83 changes and all bundled assets. Install this ZIP alone over your existing project root. Do not delete other files in your repository.

v3.84 YEAR AHEAD CHANGES
- Print HTML activation wheels label zodiac sectors and unique natal targets rather than anonymous overlapping dots.
- Exact transiting markers and connecting lines are drawn only when a dated, stored ecliptic longitude exists for the relevant chapter. Otherwise the chart explicitly explains that only natal target positions are plotted. No transit position is invented.
- Monthly print layout uses smaller chart sizing, avoids splitting the chart and its legend, and retains A4 page-break rules.
- Footer version label updated to v3.84.

Important: Story prose is not automatically rewritten. Narration vs transit-pass chronology remains subject to editorial review. Monthly report and older ReportLab fallback remain as in v3.83. If native Linux PDF dependencies are unavailable, Year Ahead falls back to ReportLab; the printed HTML is the richer chart format.

DEPLOYMENT
Copy files into repository root including assets/ and packages.txt. Redeploy Streamlit and verify Luna v3.84 appears in footer. Generate Year Ahead owner report, download HTML, and print from Chrome with Paper=A4 and Scale=100%. Browser full-page screenshot is NOT paginated A4.

LOCAL TESTS
4 existing Year Ahead/activation tests passed against extracted base repository modules; generated a 19-page synthetic HTML-derived PDF and inspected monthly chart page. This is not a live production report validation.

LUNA CONVERGENCE v3.81 — CUMULATIVE PRINT AND SHORTCUT UPDATE

INCLUDES ALL CHANGES FROM v3.79 AND v3.80. Install this ZIP alone.

INSTALLATION
Copy the ZIP contents over your repository root, preserving the assets/ and generated/epic_sky/ directories. Existing calculations, paid checkout, Groq and Epic Sky logic are retained from the consolidated base.

PRINT CHANGES
- Monthly HTML/CSS now allows lengthy content to continue rather than being cropped by fixed A4 page height.
- Printable charts, cards and table rows try to remain intact, and headings stay with following text where the print engine supports these rules.
- Empty "The opening" and "The reality check" labels are omitted unless their respective narrative values exist.
- The "What needs attention now" strategic-horizon section is omitted if all horizon content is empty.
- Both the PDF and downloadable HTML use the same Monthly renderer; the Year Ahead HTML print renderer, 12 monthly chapter breaks, and year rhythm graph from v3.78 remain included.

SHORTCUTS + ICONS
- Chrome: More (three dots) > Cast, save, and share > Create shortcut > name Luna Convergence > Create.
- Saturn black stone on corner icon assets included: brand 64px, favicon 256px, touch 192px, source-size 512px.
- Browser tab favicons are set via Streamlit page config. PWA/mobile home screen artwork is not guaranteed by Community Cloud without manifest/root asset serving. Clear caches and recreate old shortcuts after deployment.

LOCAL VALIDATION
- 7 targeted regression tests passed.
- Monthly Libra October 2026 PDF generated successfully from live local calculation; 11 pages, no blank opening/reality-check boxes.
- Existing historical Monthly fixture asserting verbatim output from older editorial code is out of date; editorial content itself has not been rewritten.
- Year Ahead synthetic HTML/PDF renderer passed existing tests, but production Groq/customer output has not been live-tested.
- Browser Print and WeasyPrint may paginate differently. Review the two paid owner PDFs on your deployed installation.

OUTSTANDING PRODUCT WORK
Editorial text quality/deduplication and narrative/evidence selection semantics are separate from the print fixes and are not claimed resolved by this release.


Native PDF dependency fix: WeasyPrint is optional on Streamlit Cloud. If libgobject/GLib is unavailable, Year Ahead falls back to the existing ReportLab PDF renderer. Downloadable print HTML is still available. No Linux packages.txt changes are required for the fallback.

v3.82 deployment steps:
1. Replace the files from v3.81 with this ZIP (full cumulative package).
2. Keep existing unlisted repository modules and secret settings.
3. Streamlit Cloud: reboot/redeploy app so it re-installs requirements.
4. Confirm footer Build reads Luna v3.82; if it still reads v3.79, the replacement app.py has not deployed.
5. Retry the Owner Year Ahead report. With no WeasyPrint native libraries, PDF uses stable ReportLab fallback; optional print-ready HTML remains downloadable.
6. Monthly uses its existing HTML->browser->ReportLab fallback path.

v3.83 NATAL CHART / ACTIVATION PRINT CORRECTION
- Keeps all v3.79–v3.82 application, Epic Sky, Monthly, shortcut and Saturn stone artwork changes.
- Fixes HTML global SVG circle rule that filled the natal outline with black.
- Monthly Year Ahead HTML pages display chart targets selected from each actual monthly transit window.
- A purple point is a known natal longitude. An orange point is displayed ONLY if the packet contains the transit's exact longitude; no inferred locations are fabricated. The month list explains which transits contact which targets.
- packages.txt and WeasyPrint in requirements.txt enable HTML-to-PDF generation on Linux deployments supporting apt system packages. Streamlit Cloud must install packages.txt; reboot the app after deployment. If these packages cannot be installed, the previous ReportLab fallback remains and will NOT show the HTML activation maps. Download the HTML and Print > Save as PDF for the full design.
- This does not certify Groq editorial chronology, nor does it replace the website's own interactive activation renderer. Those are separate implementation paths.
