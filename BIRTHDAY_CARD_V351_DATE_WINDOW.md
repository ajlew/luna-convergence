# Luna v3.51 — Date-only Birthday Calculations

## Correction

Birthday cards without a known birth time now use the same date-window principle as Weekly Studio instead of leaving the Sun and Moon calculation lines blank.

- The local birth date is sampled in 15-minute intervals.
- Luna finds the strongest qualifying Sun aspect and Moon aspect across that date.
- A non-exact contact is labelled with phase and closest-approach orb.
- An exact contact is labelled `exact on birth date` with an approximate local time.
- The app never presents a date-window result as an exact natal aspect at birth.
- Known-time cards retain the exact `orb at birth` format.

## Display distinction

- Known time: `Sun opposition Saturn · applying · 1.61° orb at birth`
- Unknown time: `Sun opposition Saturn · applying · 0.42° orb at closest approach`
