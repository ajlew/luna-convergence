# Luna v3.45 - Evidence Precision

This update tightens Luna's generated plain-text readings globally. It does not hard-code customer copy.

## What changed

- Daily readings must name the main calculated aspect and supplied support aspect.
- Weekly and Weekly Studio readings must cover supplied main weekly events and keep named weekdays in order.
- Weekly prompts ask for three connected passages: Monday-Tuesday, Wednesday-Thursday, Friday-Sunday.
- Monthly readings reject internal labels such as "first area" or "seventh area".
- Monthly readings reject loose timing such as "a week later" when exact event dates are supplied.
- Final action sentences are checked for concrete task verbs instead of vague advice such as "make space" or "trust the process".
- All free/plain products use writing revision `evidence-precision-3`, so current saved prose can be refreshed by the scheduled generator or a manual workflow run.
- Footer label is now `Luna v3.45 - Evidence Precision`.

## Upload

Upload the changed files in this package to the same paths in GitHub, then commit to `main`.

After upload, run the GitHub Action manually for any period you want refreshed immediately. Leave Refresh OFF for missing/stale readings; use Refresh ON only when deliberately replacing existing prose.

For the current empty next-week Studio capture, run:

- `studio` with date `2026-09-21`
- `weekly` with date `2026-09-21`

Both should use Refresh OFF and Check only OFF unless you intentionally want to rewrite existing current prose.
