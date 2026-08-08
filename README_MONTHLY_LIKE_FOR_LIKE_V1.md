# Luna monthly like-for-like historical test v1

## Purpose
Historical Ephemeris Admin tests and the ordinary Monthly Preview now use one
shared `monthly_report_pipeline.py`.

This removes the previous divergence where Ephemeris Admin rendered the
monthly experience with `preview=True`, which intentionally suppresses the
full body of the paid/customer-style report.

## Contract
Both routes call:

1. `build_production_monthly_report(...)`
2. `render_production_monthly_report(...)`

The renderer always calls Luna's monthly experience with `preview=False`.

Therefore September 2017 Sagittarius and August 2026 Sagittarius are directly
comparable: same period report calculation, same convergence logic, same
narrator, same sections, same technical appendix, and same print renderer.

The ephemeris registry remains separate and durable. It only controls whether
a historical year is permitted to run.
