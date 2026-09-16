# Luna v3.41: Studio error and reading clarity

## Findings from your screenshots

| Area | Luna screenshot | Google screenshot | Correction |
| --- | --- | --- | --- |
| Interpretation | Daily Taurus and Monthly Leo show calculations only | Explains the symbolic meaning of the supplied aspects | Missing saved readings must be generated; new `all` option covers Daily, Weekly and Monthly in one run |
| Weekly explanation | Pisces reading emphasises a few positive signals, adds speculative money examples, and omits much of the week's pressure | Groups communication, drive and relationship themes; explains early-week to weekend changes | Writing brief now explicitly asks for progression, aspect meaning, support and pressure, and practical responses tied to supplied life areas |
| Action | A whole paragraph appears under Your move | Guidance is easier to distinguish from the explanation | Sentence extraction now recognises lowercase final actions |
| Monthly evidence | Dates appear out of order, with duplicate opposite/opposition labels | The comparison provided is Weekly, not Monthly | Sort Monthly evidence chronologically and remove equivalent duplicate labels without changing calculation data |
| Weekly Studio | NameError at week_label(monday) | Not applicable | Use the existing week-label helper; full-app regression test exercises actual imports and globals |

The Google screenshot is a writing comparison, not verification of its astrology or predictions. Its statements about particular personal outcomes are not evidence. Luna should explain the same calculated facts clearly, in Luna's imperative, humorous and affirming voice, with examples presented as choices rather than promised events. Free readings do not ask for personal birth data.

## What this patch changes

Eight changed files, building on the previous recovery upload. Upload them to their matching paths. It preserves calculation logic and saved readings. Word ranges remain guidance only. No LLM calls, remote edits or deployment were performed while making this patch.

The stronger prompt affects newly generated readings. Existing saved prose is deliberately reused to avoid paying to regenerate it; its display formatting is corrected immediately by this patch. A prompt update alone does not rewrite already saved text.

The previous content-repair branch also had an unused word-range lookup after word gating was removed; that NameError is fixed here.

## One generation run for the missing website readings

Actions → Generate Luna plain-text readings → Run workflow:

- Product: `all`
- Date: the desired Daily reading date, YYYY-MM-DD, using Sydney's date
- Sign: blank for all twelve

`all` uses that date for Daily, its Monday for Weekly, and its first day of the month for Monthly. For the supplied screenshots, 2026-09-16 means Daily 16 September, Weekly 14 September, Monthly September. Use today's Sydney date when filling the live Daily page.

Matching completed readings are skipped. Persistent provider limits stop the batch and preserve progress; a later run resumes incomplete work. This does not remove provider quotas.

Studio uses its existing separate `studio` product and the selected week's Monday. Its twelve sign cards reuse Weekly readings. The collective master and seven clips are additional generated scripts; opening the page makes no model calls. This patch fixes Studio's crash even before those scripts exist.

## Verification

26 tests passed, including the complete app's Studio imports/globals, lowercase final-action extraction, Monthly sorting/deduplication, and all-product date normalisation and quota stopping. Existing tests cover no word-count retries, preserving saved readings and provider pacing. Syntax and diff checks passed. The live provider's output quality and successful completion remain to be checked after upload and generation.
