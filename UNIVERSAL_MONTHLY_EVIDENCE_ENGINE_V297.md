# Universal Monthly Evidence Engine v2.9.7

## New production files

- `universal_monthly_evidence.py` — universal evidence equation, house-path ranking and mapping audit.
- `monthly_story_profiles.py` — dynamic Luna editorial profile generator.
- `monthly_story_profiles_v296_calibration.py` — archived August calibration copy; not used as the production engine.
- `test_universal_monthly_evidence_v297.py` — 36-report July/August/September test.
- `sanity_check_universal_monthly.py` — command-line audit tool.

## Modified files

- `astrology_engine.py` — preserves aspect orb, aspect name and exact/applying state fields.
- `scenario_engine.py` — applies the universal score after a hard house/planet scenario gate; adds missing identity, creativity, routine, trust, community and closure scenario families.
- `monthly_arc_engine.py` — uses the universal event score, derives the evidence path and stores the formula/mapping audit.
- `monthly_narrative_v1.py` — reads the generated profile from the arc and exposes formula evidence in the technical appendix.
- `site_config.py` — build label updated to v2.9.7.

## Compatibility

The public layout, navigation, Daily product, private Monthly preview, print portal and PDF renderers are preserved.

## Test command

```powershell
python test_universal_monthly_evidence_v297.py
```

Batch audit:

```powershell
python sanity_check_universal_monthly.py --year 2026 --months 7 8 9 --json Luna_v297_universal_monthly_audit.json
```

## Final validation

```powershell
python test_universal_monthly_evidence_v297.py
python test_universal_monthly_full_year_v297.py
```

Results:

- 36-report three-month integration test: PASS;
- 144-report full-year audit: PASS;
- highest cross-sign similarity: 60.41% against a 65% limit;
- three isolated nine-page PDF checks: PASS;
- legacy Daily, Monthly preview, payment handoff and PDF compatibility tests: PASS.
