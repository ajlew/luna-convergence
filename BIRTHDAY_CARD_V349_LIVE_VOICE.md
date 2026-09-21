# Luna v3.49 - Birthday Card Live Voice

## What changed

- Removed the fixed Sun-word and Moon-ending tables.
- Removed every canned Birthday Card poem fallback.
- The Swiss Ephemeris calculation remains authoritative.
- Luna's configured OpenAI-compatible voice provider now writes one original micro-poem from a closed packet of calculated facts.
- The provider must echo the exact facts hash and Sun/Moon evidence before the poem is accepted.
- Poems must be one sentence, 10-18 words, use the approved `only` sentence architecture, and avoid astrology jargon, predictions and guarantees.
- A failed or invalid provider response creates no card.
- A second validation attempt is allowed, but no stock sentence is substituted.
- The recipient's name and birth date remain inside the app and are not sent to the voice provider.
- A random non-personal variation key prevents two equivalent sign packets from sharing a cached sentence.
- With an unknown birth time, Luna sends only Sun/Moon signs that remain safe across the local date. It does not send noon degrees or aspects as exact birth facts.
- With a known birth time, exact Sun/Moon degrees and up to three calculated luminary aspects may refine the poem.

## Existing Streamlit secrets used

No new secret is required. The Birthday Card uses:

- `LUNA_VOICE_MODE`
- `LUNA_VOICE_BASE_URL`
- `LUNA_VOICE_MODEL`
- `LUNA_VOICE_API_KEY`
- `LUNA_ADMIN_KEY`

## Owner test

1. Open `/birthday-card` and unlock Luna owner access.
2. Enter a name and full birth date.
3. Leave **Optional personal message** blank.
4. Create the card.
5. Confirm Luna pauses briefly while writing, then returns a new validated poem.
6. Repeat with the same Sun/Moon combination and confirm the sentence is not a fixed recycled line.
7. Enter a personal message and confirm it intentionally replaces Luna's poem.

Do not launch customer checkout until the live generation path has been tested successfully in Streamlit.
