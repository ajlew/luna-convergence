# Luna v3.47 — Birthday Card

## What this adds

- `/birthday-card` page and top-navigation link. In v3.48, generation is owner-only until the customer Stripe product is connected.
- One fixed 9:16 Luna design: white background, black typography and a small gold Sun beside the calculated Sun position.
- Bundled Bodoni Moda, Josefin Sans and IBM Plex Mono files so PNG/PDF exports use Luna's actual typography.
- Full birth date used privately for calculation; the birth year is never printed.
- Existing Swiss Ephemeris natal engine supplies the Sun and Moon signs.
- Known birth time supported.
- Unknown-time cusp handling: Luna shows both possible Sun or Moon signs instead of guessing.
- Optional customer message; otherwise Luna creates a short Sun–Moon poem.
- Instagram Reel/Story PNG download at exactly 1080 × 1920 pixels.
- Matching one-page 9:16 PDF.
- Long copy produces a quality warning but does not stop generation.

## Launch state

This is the working card generator and download flow. Owner access is protected by `LUNA_ADMIN_KEY`; non-admin visitors cannot generate a card yet. A Stripe Birthday Card product/Price ID is required before customer ordering can open at US$1.

## GitHub upload

Upload the changed files on the current `shorter-luna-copy` branch. Keep their repository paths unchanged. Run the checks, open the app route, create one known-time and one unknown-time card, then merge the branch only after both downloads open correctly.
