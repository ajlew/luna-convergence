# Luna v3.14 — Solar Clock First

## First Principle

**The Sun is Luna's primary natural clock.**

Luna now begins its method from the universal tropical solar-zodiacal sequence:

**Aries Gate / March Equinox → Taurus → Gemini → Cancer Gate / June Solstice → Leo → Virgo → Libra Gate / September Equinox → Scorpio → Sagittarius → Capricorn Gate / December Solstice → Aquarius → Pisces → Aries again.**

The reader's location never reverses this sequence. Location is used separately to observe the physical light where the reader stands.

Examples for the same September sky:

- Sydney: daylight increasing.
- London: daylight decreasing.
- Both: the same Virgo → Libra solar movement and the same Libra Gate / September Equinox.

## Customer-facing changes

- A compact **Solar Clock** panel is visible near the beginning of Monthly reports.
- Daily readings now label the solar layer **Solar Clock** and show the reader's Sun, current Sun, local light and next solar gate.
- The Solar Year page now opens with the Sun-first principle and names the four gates as Aries, Cancer, Libra and Capricorn Gates.
- Conventional hemisphere season labels (spring/summer/autumn/winter) are removed from the live Luna solar presentation.
- Nearest city is explicitly requested **for local light**, while street addresses remain unnecessary.
- Browser-timezone coverage is expanded so more Northern and Southern Hemisphere visitors resolve to an appropriate local-light estimate.

## Method hierarchy

Sun / Solar Clock → Local Light → Planetary Weather → Pattern → Trajectory → Convergence → Meaning → Choice → Experience → Learning

The Sun establishes the annual reference frame. Faster planetary events describe the weather occurring inside that frame.

## Compatibility

The legacy `local_season` data field remains internally for backward compatibility, but its value is neutral (`Location-aware light cycle`) and it is no longer rendered as a conventional season. Existing Daily, Monthly, Yearly, payment, ephemeris, print and technical-evidence functionality is preserved.

## Validation

- Full pytest suite: **46 passed**.
- Solar calculation script: passed.
- 2026 monthly generation sweep: **144/144 reports generated successfully**.
- Explicit hemisphere test: September 2026 gives **Increasing** local light in Sydney and **Decreasing** local light in London while preserving the same Virgo → Libra solar sequence.
