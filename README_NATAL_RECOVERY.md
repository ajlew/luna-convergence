# Luna Paid Monthly — Whole Natal Foundation Recovery

## Install
Apply to a repository already running the integrated v3.97 Paid Monthly recovery. Replace only `app.py` and `monthly_shared_view.py` at repository root. No files for Year Ahead, Groq or checkout are changed. Do not overlay this on an older, unverified branch without diffing.

## Exact production differences
1. `app.py`: `_monthly_natal_pattern(snapshot)` no longer copies the first `Your strengths` signature verbatim. Synthesizes calculated Sun, Moon, Mercury, Venus, Mars, Ascendant (only if exact birth time known), nearest natal aspect, and the chart's computed element/modality weighting. No zodiac sign or customer outcome is hard-coded.
2. `monthly_shared_view.py`: renders the original calculated natal SVG once beneath `Your natal foundation` / `Your strengths`, before `Read the month`. `Your natal activation` retains the monthly activation SVG only, avoiding two instances of the same natal wheel. Both HTML and PDF still come from the same renderer.

## Untouched
Monthly story/Groq generation, validation, checkout, key dates, natal aspect signature selection, Year Ahead, other reports, provider configuration.

## Tests
`python test_monthly_natal_whole_chart.py` checks two dissimilar calculated charts, unknown birth time, aspect-specific text, single natal/activation wheel, print order and PDF rendering.

## Limitations
The local test uses simulated natal snapshot objects and does not prove a live customer natal calculation or verify the factual accuracy of an existing LLM story. Do not spend another Groq call solely to test static natal/report layout changes.
