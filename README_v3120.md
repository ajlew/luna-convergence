# Luna v3.120 — Single-Game marker reliability

**Required baseline:** v3.119. Overlay only `app.py` and `paid_yearly_editorial.py`.

## Narrow change
- Year Ahead generates each Major Game in an individual bounded request. Its destination is already determined by Python; the model's optional marker is now normalized before the existing report parser runs.
- Accepts full single-Game prose with no marker, an exact `<<ISSUE:n>>` marker, or a generic `<<GAMES>>` / `<<MAJOR STORY>>` heading.
- Still rejects empty, excessively short, foreign-section responses and obvious internal planning fields.
- Updates the explicit app release label to v3.120.

## Unchanged
- Read the Year, monthly chapters, natal profile/Strengths, calculation engine, chart/PDF renderers, Paid Monthly, checkout, voice provider configuration.

## Tests
- 9 focused offline cases pass; both modified Python files compile. No live Groq or full rendered report verification; provider quality/astrological truth not guaranteed by these tests.

## Rollback
Replace `app.py` and `paid_yearly_editorial.py` with their v3.119 counterparts.
