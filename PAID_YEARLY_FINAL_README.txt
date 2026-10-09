LUNA PAID YEARLY - FINAL BUILD

Replace these root GitHub files:
1. app.py
2. year_ahead_voice.py
3. year_ahead_view.py

Add this new root GitHub file:
4. year_ahead_pdf.py

Optional but recommended test file:
5. test_paid_yearly_rebuild.py

Do NOT replace timing_map.py or year_ahead.py again. The current GitHub versions are already the required deterministic calculation/composer layer.

WHAT IS NOW FINISHED
- Paid Reports -> Year Ahead checkout remains the customer entry point.
- Selected start date is a true inclusive 365-day rolling window (end = start + 364 days).
- Owner preview and post-Stripe fulfilment use the SAME rebuilt paid Year Ahead path.
- Paid Yearly no longer calls the old period_report/_prepare_paid_yearly_personal_layer/_render_snapshot_yearly_report path.
- Natal geometry from checkout feeds build_timing_map -> build_year_packet.
- Python selects/ranks/groups the year before Luna Voice.
- Paid priority + optional question are supplied only as reader context to the single voice call; they do not alter the astrology calculations.
- One cached plain-prose Luna call supplies Read the Year.
- Voice errors are cached, so Streamlit reruns do not become an automatic retry loop.
- Voice failure does not suppress the deterministic Year Ahead.
- The paid webpage shows natal signature, year-at-a-glance, year strip, Read the Year, 3-5 Games, passes, triggers and Why Luna sees this evidence.
- The downloadable PDF is built from the SAME YearPacket and SAME Read-the-Year prose as the webpage.
- The emailed attachment is that same paid Year Ahead PDF.
- PDF includes exact pass dates/times, D/R state, positions/orb/houses where known, triggers and supporting transits.
- Build label is Luna v3.73 - Paid Year Ahead Rebuild.

VERIFICATION COMPLETED
- Python AST/compile checks passed for app.py, timing_map.py, year_ahead.py, year_ahead_voice.py, year_ahead_view.py and year_ahead_pdf.py.
- Paid Yearly static architecture audit: 19/19 PASS.
- Synthetic single voice-call test: PASS.
- Paid reader-context test: PASS.
- Paid PDF generation: PASS.
- PDF rendered to four pages and visually inspected with no clipping/overlap in the sample.

NEXT ACTION AFTER COMMIT
Test from Reports -> Year-Ahead Report using owner access first. Do not test /timing-map as the paid product.
