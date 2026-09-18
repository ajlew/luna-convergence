# Luna v3.44 — Weekly chronology

Changed-files update for the existing Luna repository. Based on main commit b3f8ea6c383ee912b9164201c18df6263e54ada5. No deployment or paid LLM generation was performed here.

## Install
1. Extract this ZIP. Upload its Python files to the repository root, replacing matching files. Keep the existing app.py and workflows; they do not need replacement for this update.
2. Commit all files together. The existing Generate Luna plain-text readings workflow detects these changes and starts current-period recovery.
3. Let that run finish. If it does not start, run Generate Luna plain-text readings with product all, date blank, sign blank, Refresh OFF and Check only OFF.
4. For a historical week, run weekly and studio separately with a date within that week, sign blank and Refresh OFF.
5. Inspect Weekly and Studio: weekday progression, overview agreement with dated entries, and YouTube/Instagram copy. Confirm Virgo Daily for September 18 is populated after recovery.

## What changes
- Weekly prompt follows three connected passages: Monday–Tuesday, Wednesday–Thursday, Friday–Sunday.
- Studio overview follows the same order and supplies the existing YouTube and Instagram outputs.
- Python supplies a dated weekday map. Checks detect backward named weekdays and explicit named aspects attributed to a different supplied day; supporting aspects are included.
- Uses the existing single bounded correction attempt. No word-count rejection is added.
- Only Weekly and Studio overview writing revisions change. Existing current Daily, Monthly, clips and meanings retain their revisions. Missing/stale content can still generate through normal recovery. A complete current week requires 12 Weekly replacements and one overview, plus any bounded corrections.
- Old copy remains readable until a successful replacement is saved. Successful replacements are skipped on later runs.
- Removes Markdown emphasis marks in saved/read/displayed prose, Studio meanings, captions and downloads, keeping HTML escaping.
- Prompts ask for a concrete final action rather than a vague closing.
- Daily fact preparation no longer builds unused legacy prose. This fixes September 18 Virgo failing on the discarded headline “house meeting”. Evidence, technical aspects and supporting-event selection are preserved.
- Footer updated to v3.44. Approved app layout, typography, controls and downloads are preserved.

## Validation
48 tests passed: existing workflow suite, full-app populated-page fixtures, chronology regression, aspect aliases/supporting days, one bounded provider correction, refresh scope, formatting/escaping, caption consistency, Daily fact parity and September 18 Virgo recovery. Tests used offline responses; no live provider generation was performed.

The chronology checks are deliberately narrow. They verify named weekdays and explicit named aspect/day claims; they do not prove the accuracy of every paraphrase or symbolic interpretation. Inspect the newly generated prose after the workflow succeeds.

## Files
plain_readings.py, plain_voice_generator.py, reading_quality.py, reading_facts.py, studio_readings.py, luna_reading_style.py, site_config.py, test_reading_clarity.py, test_weekly_chronology.py.
