# Luna Monthly v3.7 — Truth Gate + Asymmetric Strategy

This update adds a permanent decision layer between astronomical/convergence evidence and Luna's narrator.

## Core rule

Every monthly report now resolves the strategic question in two stages:

1. `ACT` or `NOT ACT`
2. If `NOT ACT`: `QUESTION`, `NEGOTIATE`, `HOLD`, or `PASS`

Only `ADVANCE` resolves to `ACT`.

The decision engine is isolated in `monthly_decision_engine.py`. The narrator and renderer consume its result but cannot override it.

## Evidence used

The truth gate weighs:

- event importance;
- actual event polarity;
- square/opposition versus trine/sextile geometry;
- sign-ruler involvement;
- primary/secondary/tertiary narrative houses;
- uncertainty (especially Neptune/review states);
- volatility (especially Uranus/eclipses);
- accumulated capacity pressure.

These are internal evidence weights, not probabilities.

## Romance hierarchy

Romance is separately classified as:

- PRIMARY
- SECONDARY
- BRIDGE
- ACTIVE
- BACKGROUND
- NOT MATERIAL

A romance subplot can no longer outrank the convergent monthly hierarchy merely because Venus is active.

If romance is `NOT MATERIAL`, Luna keeps a short Love section but treats the absence lightly and ends with a `Maybe next month` style line. The humour is selected from the actual dominant house, so a career month receives career-based wit, a money month receives money-based wit, and so on.

If romance is active, it gets its own domain truth gate and can differ from the overall monthly posture. This allows genuinely asymmetric advice—for example, `MONTH = NOT ACT / NEGOTIATE` while `ROMANCE = ACT / ADVANCE` if the relationship evidence is independently constructive.

## Report changes

- `Your Move` now displays `ACT`/`NOT ACT` plus the selected posture.
- The three action steps are generated from the selected posture rather than defaulting to "act on the opportunity".
- Love / Work / Money rows display their own truth/posture labels.
- Romance presentation reflects its hierarchy role.
- Technical evidence now includes support, friction, uncertainty, volatility, capacity pressure, romance hierarchy and decision QA.

## Historical testing

Ephemeris Admin continues to call the same production monthly pipeline. Re-run Sagittarius September 2017 and compare it like-for-like with 2026.

The engine contains no hard-coded Sagittarius/2017 exception.
