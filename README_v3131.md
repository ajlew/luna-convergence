# Luna v3.131 — Pre-LLM evidence packet isolation

**Base:** The consolidated Luna v3.130 Professional Print ZIP (not any earlier v3.130 revision).

## Changed
- `paid_yearly_editorial.py`: Do not feed preceding Groq-produced annual prose as factual context for the next phase. Four phase boundaries and their calculated exact-contact ledgers remain unchanged.
- Monthly writing packet no longer sends separate `strongest_date` / `strongest_kind` fields that can imply an unsupported named aspect; only the authoritative month-specific calculated evidence carries exact planetary contacts.
- Major Story writing packet no longer duplicates raw transit/triggers next to the `game_evidence_contract`. Keeps Python-computed timing and exact contacts plus the calculated Game's strategic context.
- Reinforced the pre-LLM instruction to preserve the full exact contact identity and date in prose.
- `app.py`: version v3.131.

## Unchanged
- `yearly_print_html.py` is byte-for-byte identical to consolidated v3.130 Professional Print.
- The ephemeris engine, natal and monthly calculations, monthly chapter assignment, four-phase layout, Groq provider/token transport, cached checkpoints, payment, Paid Monthly and PDF design are unchanged.
- No post-LLM factual/style verification, rewriting or regeneration was added.

## Verification / limitations
- Compiled all three Python files.
- Offline tests exercised the exact-contact whitelist and Game's bounded date context, including exclusion of an unnamed Venus trigger.
- ZIP integrity checked.
- **No live Groq generation or full production output was run.** This change narrows the available evidence and strengthens instructions; it cannot guarantee that a language model will never invent a claim. The PDF output should be examined after first deployment.
