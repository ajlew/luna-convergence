LUNA PAID YEARLY — PHASE 5 FINAL WEB POLISH

Replace these root files:
- app.py
- paid_yearly_editorial.py
- paid_yearly_report.py

Do NOT replace:
- timing_map.py
- year_ahead.py
- paid_yearly_pdf.py
- Paid Monthly data/logic files
- GitHub pre-generation workflow

WHAT THIS FIXES

1. The Core Thread now REPLACES the old Paid Yearly "Read the pattern" text.
It is no longer duplicated after Your strengths.

Paid Yearly order becomes:
- Your natal signature
- Read the pattern
- Strongest natal pattern
- The core thread: Structure meets imagination (or the reader's actual strongest aspect)
- visible calculated source line
- Why this matters this year
- natal wheel
- Your strengths
- The year at a glance

Paid Monthly remains on its existing default Read the pattern renderer.

2. The natal claim now has an immediate reference.
The page shows:
Calculated from your natal chart · [planet position] [aspect] [planet position] · [orb]

3. Adds a careful Year Ahead bridge.
Example:
Saturn appears in 2 of your 3 major annual stories. That does NOT mean those
transits recreate the natal Saturn-square-Neptune aspect; it means one side of
that lifelong natal pattern is prominent in this year's selected timing.

4. Guarantees "What this may look like" when the provider wrote multiple
sentences but omitted the blank line between its two requested issue paragraphs.
No second LLM call is added.

5. Fixes pass grammar.
No more:
"This is the clearest exact contact in the outer shell hardens."

Now:
"This is the clearest exact contact in your identity and direction story."

6. Repeated trigger planets become stage-aware.
A Venus trigger BEFORE an exact contact is described as an early clue.
A Venus trigger AFTER it asks whether the reader's response now reflects what
the exact contact made clear.
Between-pass and same-day exact-contact stages are also handled.

ARCHITECTURE PRESERVED
- One Luna provider call.
- No retries.
- Python owns astrology, timing and dates.
- Paid Monthly behavior remains the default.
- PDF remains untouched until web acceptance is complete.
