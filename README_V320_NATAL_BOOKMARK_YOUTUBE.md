# Luna v3.20 — Natal Snapshot + Bookmarkable Daily + YouTube slot

## Added without removing existing functionality

### Bookmarkable Daily

After a visitor chooses a zodiac sign, Luna adds a `sign` query parameter to the current Daily URL. Example:

`/?sign=capricorn`

A normal browser bookmark or mobile Add to Home Screen action therefore reopens Luna on that sign. With no saved/query sign, the selector still starts at `Choose your star sign`.

Birth data is never placed in query parameters.

### Free Natal Snapshot

New hidden route:

`/natal-snapshot`

It is linked from Solar Year and the footer, but the main four-item navigation remains unchanged.

The snapshot calculates tropical geocentric Swiss Ephemeris positions, major aspects, dominant element/modality, a restrained black-and-white natal wheel, and three plain-language recurring patterns.

If exact birth time and a supported city are supplied, Luna also calculates the Ascendant and Midheaven and assigns whole-sign houses. If time or coordinates are not known, Luna explicitly omits those fields rather than inventing them.

### YouTube-ready Daily

Optional Streamlit Secrets:

```toml
LUNA_YOUTUBE_CHANNEL_URL = "https://www.youtube.com/@YOUR_CHANNEL"
LUNA_YOUTUBE_FEATURED_VIDEO_URL = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
```

If no featured video is configured, the Daily page remains exactly as lean as before. When a video URL is added, Streamlit's native YouTube player appears beneath the Daily reading, with an optional channel link.

### Analytics

New event:

`free_natal_snapshot_generated`

The event records only whether an exact birth time was supplied. It does not send the birth date/time/city as event parameters.

## Tests

Run:

`pytest -q`
