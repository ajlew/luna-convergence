# Luna v3.25 - Natal consolidation + paid Monthly natal overlay

## Free Natal Snapshot
- Removes the visible **Three patterns that keep repeating** section.
- Keeps **What keeps repeating?** as the product idea.
- Makes **Your strongest signatures** the single behavioural interpretation layer.
- Retains the four-tier signature structure: lived behaviour, Strength, Watch, and Question where useful.
- Natal chart, Sun/Moon/Rising signature and collapsed chart evidence remain.
- Birth date now opens empty rather than defaulting to a made-up date.

## Paid Monthly
- Paid Monthly checkout now requires the same natal basis used by the free Snapshot:
  - birth date required;
  - exact birth time optional/unknown is valid;
  - birthplace/coordinates used when an exact time is supplied;
  - UTC vs local-time basis retained.
- If the customer already generated a free Natal Snapshot in the same Streamlit session, those inputs prefill the Monthly checkout.
- Raw birth date, birth time and birthplace are **not** copied into Stripe metadata.
- Luna stores a compact derived natal-geometry profile in Stripe so the paid report can be regenerated after payment.

## Monthly personalisation
- The paid Monthly now calculates a **Personal natal overlay** against the month's transits.
- It selects up to three tight, high-value natal contacts and shows:
  - date;
  - transit-to-natal signal and orb;
  - human consequence;
  - related persistent natal signature where relevant;
  - Your move.
- The overlay is included in both the paid web report and the downloadable Monthly PDF.
- The sign-level Monthly story remains intact; natal contacts add a personal second layer rather than replacing the core forecast.

## QA
- Release suite: 101/101 passed.
- Historical ephemeris suite: 2/2 passed.
- A personalised August 2026 Sagittarius Monthly PDF was generated and visually rendered successfully with the new natal page.
