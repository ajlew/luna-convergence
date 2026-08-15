# Luna v3.28.2 — Monthly Sky Map PNG rendering fix

The v3.28.1 monthly preview preserved the `<img>` element but some hosted browsers rejected the SVG data-URI source, leaving a broken-image icon and the alt text instead of the wheel.

v3.28.2 keeps the same monthly sky-map calculation and placement but renders the wheel server-side as a standard PNG using Pillow, then embeds that PNG in the preview. No new runtime dependency is required because Pillow is already part of Luna's requirements.

Preserved:
- free sign-based Monthly Sky Snapshot
- whole-sign House 1 mapping
- no ASC/MC implication in the free map
- Where the sky is gathering
- sign-specific How August unfolds chronology
- paid Natal Monthly overlay and recommendations
- Daily, Natal Snapshot, House Guide, Solar Year, Stripe, PDF/email fulfilment and historical ephemeris functionality

QA: 120 tests passed.
