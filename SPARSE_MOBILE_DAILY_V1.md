# Sparse Mobile Daily v1

This release changes the presentation layer only. It does not remove the
daily narrative, relationship interpretation, work and money guidance,
reflection questions, Solar Convergence or technical calculations.

## Default visible view

1. Daily hero
2. Two short story paragraphs
3. Do / Don't
4. Today's Convergence

## Collapsed sections

- Why today feels different
  - three evidence points;
  - Weather versus Climate;
  - Hidden Opportunity;
  - compact Solar Position;
  - complete Sky Snapshot.
- More context
  - remaining story;
  - relationships;
  - work;
  - money.
- Questions to consider
- Detailed astrological evidence
  - aspect, orb and timing;
  - activated houses;
  - convergence context;
  - planetary positions;
  - twelve-house matrix.

## Stability and mobile changes

- Daily settings use a Streamlit form, so changing individual fields no
  longer repeatedly rebuilds the reading.
- The submitted reading request is stored as one session-state snapshot.
- The astrological reading cache no longer depends on city.
- Solar Convergence uses its own one-day cache.
- Global horizontal overflow is blocked.
- Mobile columns stack to full width.
- iPhone safe-area padding and 100dvh sizing are used.
- Mobile navigation is a compact disclosure menu.
- Streamlit owner/status controls are hidden from the presentation.
- The purchase form remains available but is collapsed at the end.
