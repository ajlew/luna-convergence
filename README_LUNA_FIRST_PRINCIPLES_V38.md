# Luna Convergence v3.8 — First-Principles Constitution

This update is additive. It does not remove the existing monthly, daily, yearly,
payment, print, preview, historical ephemeris, convergence, scenario, romance,
or Truth-Gate functionality.

## Permanent method module

`luna_first_principles.py` is deliberately separate from the narrator and UI.
It defines Luna's stable method contract:

`Nature → Pattern → Convergence → Meaning → Choice → Experience → Learning`

Key guardrails include:

- Nature before narrative.
- Pattern before prediction.
- Convergence before scenario.
- Correspondence, not literal determinism.
- Convergence does not imply positivity.
- Inaction and Unknown are legitimate outcomes.
- The narrator may explain a calculation but may not overrule it.
- Every public claim should be traceable to evidence.
- Historical tests remain blind; expected results are not hard-coded.
- Engineering errors are fixed; interpretive mismatches become calibration evidence.

## Integration

- `monthly_decision_engine.py` attaches a first-principles version, plain-English
  climate label, capacity label, evidence balance, correspondence note and
  Nature→Choice trace to every monthly decision.
- `synthesis.py` attaches the methodology metadata to both monthly and yearly
  report results for future reuse.
- `monthly_narrative_v1.py` explains that support/friction/uncertainty are
  normalized symbolic evidence shares rather than probabilities, and that
  capacity pressure is a separate decision-load index.
- Existing Truth-Gate and domain strategy behavior remains intact.

## Calibration policy

`build_calibration_record()` records what Luna calculated versus what was later
observed. It deliberately does **not** auto-reweight the model from a single
outcome and never rewrites astronomical facts.

## Regression protection

`test_luna_first_principles_contract_v38.py` verifies the method contract,
climate/capacity labels, calibration policy and production monthly integration.
