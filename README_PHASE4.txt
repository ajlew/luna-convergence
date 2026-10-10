LUNA PAID YEARLY — PHASE 4: ACCEPTANCE REFINEMENT

Replace these root files:
- year_ahead.py
- paid_yearly_editorial.py
- paid_yearly_report.py

Do NOT replace:
- app.py
- timing_map.py
- paid_yearly_pdf.py
- Paid Monthly files
- GitHub pre-generation workflow

WHAT THIS UPDATE FIXES

1. "Your year, one month at a time" now shows progression, not just repetition
Consecutive rounds with the same dominant story now change stage labels:
- MAKE THE CHOICE
- TEST THE CHOICE
- SEE WHAT HOLDS
- REVISIT
- CLOSE THE LOOP
- BUILD ON IT
- CONSOLIDATE

The story can remain Relationships & terms for several months when that is
truly dominant, but the customer can now see how that same story develops.

2. Game guidance is aligned to the actual natal life area
The clustering GameDefinition still helps organize the astrology, but its old
relationship/money/chemistry copy no longer automatically becomes customer advice.
Customer-facing guidance is now contextualized for:
- Identity & direction
- Relationships & terms
- Career & direction
- Money & obligations
- Home & family
- Work & wellbeing
- Horizons & movement
- Communication
- Love & creativity
- Friends & future
- Rest & closure

Primary transit move/watch copy takes precedence where available.

This specifically removes problems such as:
- relationship "chemistry" warnings inside an Identity story
- affection/fine-print language inside a Career story

3. Trigger language is now life-area aware
Sun / Mercury / Venus / Mars no longer use the same generic wording everywhere.

Examples:
- Identity Venus -> presentation, self-worth, response
- Relationship Venus -> reciprocity, affection, fairness
- Career Venus -> support, reputation, money, alliances
- Career Mars -> urgency, competition, delivery pressure
- Money Mercury -> numbers, paperwork, terms

4. Key Moments is compressed
The final reference list now uses concise trigger summaries instead of repeating
the full trigger paragraph already shown inside each story.

5. Seasonal wording is blocked
The one Luna prompt now tells the model not to use spring/summer/autumn/winter
unless a local season was explicitly supplied. It should use months or neutral
phrases such as "later in the year" instead.

6. Monthly voice continuity is stronger
When consecutive months share the same dominant story, the prompt now requires
the later month to show what changed, what is being tested, revisited,
consolidated or settled. It must not restart the story from zero.

ARCHITECTURE PRESERVED
- Python still owns astrology, ranking, dates, passes and monthly dominance.
- One Luna provider call only.
- No automatic retry.
- No extra calculation engine.
- Paid Monthly untouched.
- PDF untouched until web acceptance is complete.

TESTS
- year_ahead.py compile PASS
- paid_yearly_editorial.py compile PASS
- paid_yearly_report.py compile PASS
- static acceptance audit 12/12 PASS
- one provider call remains
