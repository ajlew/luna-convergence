# Luna Convergence v3.31 — Timing Map Human Insight Layer

## Purpose

This update improves the existing 12-Month Timing Map without changing its natal calculation, transit detection, route, price pilot, privacy model or any other Luna product.

The core change is architectural:

`transit calculation -> symbolic meaning -> human situations -> two-sided interpretation -> cross-transit synthesis -> Luna prose`

## What changed

- Added `timing_insight.py`, an original Luna semantic and rhetorical repertoire.
- Replaced planet-wide repeated prose with target-specific interpretation, questions, moves and warnings.
- Added concrete situation banks for all 12 houses plus natal targets.
- Added original pair-specific insight for the most important transit/target combinations.
- Added varied aspect and transit-language banks so repeated Saturn/Uranus/Jupiter contacts do not render as identical templates.
- Groups repeated contacts into up to three **Major Games** by dominant long-range transit.
- Adds a **Countercurrent** when another long-range planet is pulling in a different direction.
- Adds **If you remember one contact** to create hierarchy.
- Adds a closing **Where this leaves you** synthesis and three dates to keep visible.
- Keeps `Why Luna sees this` collapsed evidence and explicitly distinguishes calculation from interpretation.

## Editorial rule

The attached Astrodienst/Robert Hand report was used as a benchmark for reasoning structure only: prioritising major issues, exploring both opportunity and downside, and recognising that multiple transits can operate simultaneously. No Robert Hand or Astrodienst prose is stored in the Luna repertoire or copied into generated output.

## Preserved behaviour

- `/timing-map` remains the public route.
- Same Swiss Ephemeris natal/transit calculation.
- Same five long-range transit planets.
- Same exact/pass/retrograde detection.
- Same birth-time-known and date-only fallbacks.
- Same anonymous A$7.95 pilot price test.
- Same Daily, Weekly, Monthly, Natal Snapshot, Solar Year, payment, fulfilment, admin and SEO functions.

## QA

- v3.30 `app.py` named functions: 68
- v3.31 `app.py` named functions: 68
- Removed app functions: 0
- Full repository test suite: **133 passed**
- Added regression checks for prose uniqueness, Saturn-game synthesis, hierarchy and closing synthesis.
