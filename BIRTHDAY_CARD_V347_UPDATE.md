# Luna v3.47 — Birthday Card

## What this adds

- Public `/birthday-card` page and top-navigation link.
- One fixed 4:5 Luna design: white background, black typography and a gold Sun.
- Bundled Bodoni Moda, Josefin Sans and IBM Plex Mono files so PNG/PDF exports use Luna's actual typography.
- Full birth date used privately for calculation; the birth year is never printed.
- Existing Swiss Ephemeris natal engine supplies the Sun and Moon signs.
- Known birth time supported.
- Unknown-time cusp handling: Luna shows both possible Sun or Moon signs instead of guessing.
- Optional customer message; otherwise Luna creates a short Sun–Moon poem.
- Instagram PNG download at exactly 1080 × 1350 pixels.
- Matching one-page PDF at exactly 8 × 10 inches.
- Long copy produces a quality warning but does not stop generation.

## Launch state

This is the working card generator and download flow. It is intentionally not payment-gated yet. Test the product and output first. A Stripe Birthday Card product/Price ID is required before the download buttons can be placed behind a US$1 checkout.

## GitHub upload

Upload the changed files on the current `shorter-luna-copy` branch. Keep their repository paths unchanged. Run the checks, open the app route, create one known-time and one unknown-time card, then merge the branch only after both downloads open correctly.
