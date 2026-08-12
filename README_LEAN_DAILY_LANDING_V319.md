# Luna Convergence v3.19 — Lean Daily Landing

## Purpose
Reduce the free Luna experience to the horoscope itself while keeping the existing August 2026 campaign landing page intact for the current advertising test.

## Public navigation
Only four items are now shown:

- Daily Horoscope
- This Month
- House Guide
- Solar Year

Checkout, payment success, report, sample, method, preview, forecast-library and admin routes remain available internally/directly but are not shown in the main navigation.

## Homepage / Daily
The root URL is now the Daily Horoscope experience. The visitor only chooses a zodiac sign. Luna automatically uses the browser-local date and timezone.

The visible reading is deliberately sparse:

1. Sign and current date
2. One headline
3. Two short story paragraphs
4. Your move
5. One reflection question
6. Focus Reset
7. Direct link to the selected sign's August forecast

The old homepage example, proof panels, trust strip, methodology explanation, house demonstration and homepage report sales block have been removed.

The established `/daily-horoscope` URL remains alive and shows the same lean Daily experience.

## August 2026
`/august-2026-horoscopes` and all twelve August sign pages are unchanged in this release so the current Google Ads landing experiment can continue until the planned weekend change.

## Footer/header
The brand header is reduced to the Luna mark/name. The footer is reduced to the symbolic-framework disclaimer and Privacy link.

## Validation
Full test suite passes, including the new v3.19 lean-landing contract test.
