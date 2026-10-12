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
