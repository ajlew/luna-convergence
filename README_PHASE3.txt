LUNA PAID YEARLY — PHASE 3: HUMAN-FIRST VOICE CONTRACT

MASTER PLAN:
Luna_Paid_Year_Ahead_Updated_Build_Plan(1).md

Replace ONLY these root files:
- paid_yearly_editorial.py
- paid_yearly_report.py

No app.py change.
No timing_map.py change.
No year_ahead.py change.
No Paid Monthly change.
No PDF change yet.
No extra LLM call.

WHAT THIS UPDATE FIXES

1. Read the Year becomes human-first
- prompt forbids report-meta language
- paragraphs must begin with lived situation / consequence / choice
- technical transit names may support the interpretation but cannot lead it
- raw ISO dates and active-window ranges are banned from prose

2. Deterministic date safety
- exact timing remains Python-owned
- any generated sentence containing an invented ISO date is dropped
- supplied ISO dates, if used despite the prompt, are humanised
- there is NO second LLM call and NO retry loop

3. Natal-to-year bridge
- supplied natal signatures are matched to annual stories by named-planet overlap
- Luna receives these as "natal_resonance"
- prompt tells Luna to describe resonance/familiarity, not falsely claim activation

4. Twelve monthly rounds now get one unique Luna line each
- one short line per rolling month
- no repeated title/date/phase in the voice line
- no duplicate monthly sentence
- Python still owns dominant story, phase and strongest date
- deterministic fallback remains if a monthly line is unavailable

5. Major story chapter structure
- first editorial paragraph -> What is changing
- remaining editorial paragraphs -> What this may look like
- risk, Your move, timing and evidence stay deterministic

6. Pass storytelling
- First contact / Returns / Final contact copy now references the actual story,
  life area and deterministic move instead of generic reusable boilerplate

7. Trigger translation
- Sun / Mercury / Venus / Mars now have distinct human meanings
- trigger copy is anchored to the story's life area

TESTS
- both Python files compile: PASS
- provider-safe request envelope: PASS (representative packet 2871 input + 2479 completion = 5350)
- exactly 12 monthly voice sections parse: PASS
- repeated story-title stripping: PASS
- invented-date sentence guard: PASS
- one provider call only: PASS

WHY THE CRITIQUE'S "SECONDARY PROMPT VALIDATION" WAS NOT USED
The Paid Year Ahead master architecture explicitly requires one voice call and no
automatic rewrite loop. This update uses deterministic safety checks instead,
so calculation authority remains in Python and the voice provider is not asked
to correct its own astrology.

NEXT
Run the owner Year Ahead again and inspect:
- Read the Year human-first quality
- 12 monthly lines for uniqueness
- natal resonance bridge
- absence of impossible generated years
- pass/trigger usefulness
Then Phase 4 can be treated as web-report acceptance rather than another architecture rewrite.
