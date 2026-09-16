Luna v3.42 — Meaning, formatting and Daily continuity

Upload the files in this ZIP into the existing repository, preserving folders, and commit. This package does not contain generated readings or credentials and does not replace your saved readings.

Changes
- Weekly Studio: a visible Day-by-day astrological breakdown with dynamically generated collective meaning and energy. It uses the calculated events and active supporting influences for the selected dates. Existing weekly master, sign cards, publishing copy, short clips and downloads remain.
- All shared Daily, Weekly and Monthly readings (including Studio sign readings): Key calculations is a closed dropdown. Interpretation remains visible.
- Shared editorial typography follows Monthly Key Dates: Bodoni headings, IBM Plex Mono labels and Josefin Sans prose; no reading tables. Global section heading sizes are aligned.
- Scheduled Daily generation repairs missing current-day signs before preparing tomorrow. An additional Sydney morning run catches incomplete work. Already-current readings are reused without LLM calls. Provider quota exhaustion still stops the batch to avoid repeated charges.
- Word ranges remain guidance only. No rejection or regeneration for a small word-count overrun. No public live generation, approved model JSON, or canned aspect meanings.

After upload
1. In Generate Luna plain-text readings, choose daily, date 2026-09-16 (or the current Sydney date), and leave sign blank. This fills the missing Daily file. The repository inspected had September 14, 15 and 18, but no September 16.
2. Choose studio with a date in the required week (2026-09-16 selects September 14–20). It generates seven meaning-and-energy readings and any missing existing master/clips; it skips saved current items. Seven meanings are new LLM calls; a completely empty Studio requires fifteen calls total.
3. Check the run succeeds and commits generated/readings. Streamlit must use that updated branch. No need to regenerate Monthly or Weekly merely for styling.

The UI reads saved prose only. This ZIP cannot itself create provider-authenticated content; do not expect missing Daily or new Studio meanings to appear before those generation runs complete.

Validation: 30 focused tests passed, including current-day catch-up, Studio product coverage, saved-reading reuse, safe formatting and no word-count rejection. Full Streamlit app checks opened Daily, Weekly, Monthly and Weekly Studio without exceptions. No live provider calls or deployment performed.
