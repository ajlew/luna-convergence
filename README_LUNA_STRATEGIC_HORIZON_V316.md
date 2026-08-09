# Luna v3.16 — Strategic Horizon

## Purpose

Luna now follows a material warning beyond the current page boundary. If the underlying condition changes next month or next year, the customer sees that timing.

## Public reasoning sequence

1. **The problem** — state the real-life pressure first.
2. **If you ignore it** — state the default trajectory.
3. **Best response** — give an active counter-move.
4. **The long pressure behind it** — surface only relevant Jupiter, Saturn, Uranus, Neptune and Pluto conditions.
5. **Timing** — show:
   - Active since
   - Current phase / return
   - Peak
   - Changes
   - Structural shift

The report does not use game-theory terminology in customer-facing prose. The strategic model remains internal.

## Slow-planet roles

- **Jupiter** — expansion, opportunity and excess.
- **Saturn** — obligation, structure, limits and permanence.
- **Uranus** — instability, independence and alternative routes.
- **Neptune** — ambiguity, idealisation and missing information.
- **Pluto** — control, dependence, leverage and irreversible consequences.

A slow planet enters the visible strategic section only when its house or events materially overlap the report's dominant areas.

## Timing rule

A monthly report no longer assumes the problem ends on the last day of the month.

- The next station is searched up to 18 months ahead.
- The structural house exit is searched up to three years ahead.
- A structural exit is only called final when the planet stays out of the current sign for at least 180 days; this avoids treating a short retrograde return as a clean ending.
- If no structural exit occurs inside three years, Luna says so rather than inventing an ending.

## Voice rules added

- No warning without a move.
- No astrology without consequence.
- Name the problem before the astrology.
- Separate the immediate trigger from the long-cycle pressure.
- Do not use `game`, `player` or `equilibrium` as customer-facing labels when a direct problem statement is clearer.

## Files changed

- `strategic_horizon.py` — new.
- `synthesis.py` — adds `problem_horizon` to monthly report payloads.
- `monthly_narrative_v1.py` — adds the problem/horizon layer to Markdown output.
- `monthly_experience_v1.py` — adds the visible problem/horizon section to customer webpages and print output.
- `daily_narrative_v3.py` — long-term current now states the next material station and structural shift.
- `monthly_arc_engine.py` — removes customer-facing “terms of the game” wording.
- `customer_experience.py` — removes residual “game” wording in relationship copy.
- `yearly_experience_v1.py`, `yearly_game_engine.py`, `luna_voice.py` — public labels move from “game” language to pressure/problem language while internal structures remain stable.
- `site_config.py` — build label updated to v3.16; existing customer tagline preserved.
- `test_strategic_horizon_v316.py` — new regression test.
- `monthly_decision_engine.py` — removes residual customer-facing “game” wording without changing decision logic.
- `forecast_inventory.py` — metadata label updated to the strategic yearly naming; inventory behaviour is unchanged.

## Validation

Validated with:

- full Python compile pass;
- Monthly Narrative test;
- Monthly webpage test;
- Daily integration test;
- Luna narrator/inventory test;
- new Strategic Horizon v3.16 test using Cancer, August 2026.

The base v2.8 bundle contains two legacy regression scripts that already fail before this patch (`test_app_nameerror_hotfix.py` and `test_automatic_reference_print_and_wit.py`); those failures are not introduced by v2.9.


## v3.15 preservation

This update is additive on top of the supplied v3.15 backup. Solar Gate priority, trajectory strategy, monthly decision truth-gate, relief windows, print/PDF behaviour, payment/order flow, Forecast Inventory, Daily and Yearly functions are preserved. Strategic Horizon reads the existing results and adds cross-month/cross-year timing; it does not replace those engines.
