# Luna v3.19.1 — Daily sign-switch fix

The lean Daily landing page now rebuilds the horoscope directly whenever the visitor changes zodiac sign.

The astrology/narrative engine was already generating distinct sign-specific Daily readings. The lean landing page had added an unnecessary session-state narrative cache. That cache has been removed so a sign change always recomputes the whole-sign house map and Daily narrative on the same Streamlit rerun.

A regression test verifies that, for 12 August 2026 in Australia/Sydney, all 12 signs produce distinct headline, first story paragraph, Your Move, and reflection question, and that the lean landing function no longer stores its narrative in session state.
