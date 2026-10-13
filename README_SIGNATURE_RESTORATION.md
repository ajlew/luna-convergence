# Paid Monthly — restore natal signature and recurring-pattern display

## Installation
Apply to the codebase that already contains the **Whole Natal Recovery** release. Copy `app.py` and `monthly_shared_view.py` over the corresponding files. This is a **focused overlay**, not a full repository and not a cumulative release.

## Exact scope
- `app.py`: attach the six **existing calculated natal signature** fields to the shared Paid Monthly report model; attach the pre-existing `_snapshot_natal_fallback_story` headline, opening and Remember; retain the whole-natal synthesis and six strengths.
- `monthly_shared_view.py`: render the six-field grid and recurring-pattern heading, calculation-based introduction and Remember before Strengths. Both the screen and downloadable HTML/PDF use this same renderer.
- No changes to paid writing, Groq, astrology calculations, payment, transits, dates, charts, or Year Ahead.
- No example Sun, Moon, rising sign, element, mode or particular aspect is embedded in production report code.

## Verified
- Python compilation, two standalone offline tests (including an alternative signature and PDF rendering), and existing natal-whole-chart and Monthly recovery test modules imported without failure.
- Rendered offline seven-page PDF demonstrates the restored sections but uses previously saved October story and illustrative signature fields for proof only.
- No live Groq call or deployment was executed.

## Important
This is not a claimed full-release version change. The existing build/version metadata is unchanged because this overlay does not modify the application release-management system. A formal release should bump metadata centrally after successful integration tests.
