# Luna v3.15 — Solar Gate Priority + London Validation

## First-principles rule

The Sun is Luna's primary natural clock. A cardinal solar gate (March Equinox, June Solstice, September Equinox, December Solstice) becomes part of the customer story only when it materially reinforces the independently calculated planetary trajectory. Otherwise it remains background context.

## What changed

- Added a `gate_convergence` calculation inside monthly Solar Clock data.
- Solar gate materiality is classified as `STRONG`, `MATERIAL`, `BACKGROUND`, or `NONE`.
- A material gate is inserted beside the one chronological window that contains the gate date.
- Result-area agreement is strongest; bridge agreement is material when nearby astronomy confirms it.
- The customer-facing solar cycle label is now `Aries Gate → 12-sign solar cycle → Aries Gate`.
- The later Solar Clock evidence panel is compressed to calculated observations and convergence status; the generic poetic solar mini-forecast is no longer rendered there.
- Browser print CSS now preserves word spacing and disables ligatures in print to improve PDF text-layer extraction.
- Conventional hemisphere season names remain excluded from structural logic.

## Controlled London validation

For Sagittarius September reports generated with `Europe/London` / `London`:

- 1995: local light decreases; Libra Gate convergence is `STRONG` and reinforces the result area (friends / future plans).
- 2017: local light decreases; Libra Gate convergence is `STRONG` and reinforces the result area (friends / future plans).
- 2026: local light decreases; Libra Gate convergence is `MATERIAL` and reinforces the bridge (friends / future plans).

The universal Solar Clock remains Virgo → Libra in all three cases. Only the local light direction changes relative to Sydney.

## Regression

`51 passed`
