# Luna Paid Year Ahead — offline update (17 October 2026)

## Implemented in these replacement files
- Paid yearly `yearly_preflight.py`: fail-before-Groq checks on the 365-day window, 12 contiguous monthly rounds, each month's selected exact date, unique Games, Game memberships and non-inverted Game windows.
- Paid yearly `paid_yearly_editorial.py`: invokes that contract before any paid request; passes a deterministic sequential decision stage into every month: identify → compare → test → review (advances again for prolonged Games). Improves natal-personalisation instructions and prohibits stock mechanical compound-definitions.
- Previous partial patch retained: Bodoni outline typography in `yearly_print_html.py`, tightened print spacing, no automatic paid-yearly retries/fallbacks in `paid_yearly_editorial.py`; `paid_voice_router.py` supports single-attempt control without altering the Paid Monthly call site.
- `requirements.txt` from prior partial patch retained.

## Verification performed
- Compiles all modified Python modules.
- New focused preflight/print tests: 7 passed.
- Existing selected annual tests: 9 passed, 2 failed (stale tests expecting old `_serialize_story` signature and a payment success route string no longer present).
- Unrestricted whole-repository collection blocked by legacy tests that refer to nonexistent local files and old app versions; see `TEST_RESULTS.txt`.
- No Groq requests, purchases, or live deployment.

## Unresolved release blockers
- **External durable persistence**: checkpoint path configurability is implemented; actual persistence across Streamlit restarts requires an authenticated, persistent store/volume provided by the deployment. Local `/tmp` SQLite is NOT durable across container replacement. No production credentials or supported store details were supplied; therefore this requirement cannot be represented as completed.
- **Complete verified astronomical fixtures**: new structural checks test chronology but do not independently recalculate every planetary contact from Swiss Ephemeris against the published report.
- **Complete PDF pagination**: print CSS adjusted, but no stored complete editorial payload or live-equivalent PDF generator run with that payload was supplied. Visual acceptance of all 30 pages is not established.
- **Paid Monthly end-to-end**: implementation not altered in this patch; full functional regression and live checkout not demonstrated.

**Not certified production-ready.** Do not confuse offline source update with a verified live release.
