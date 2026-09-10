# GitHub update — Luna v3.36 Atomic Guided Reports

Upload the changed files to the repository root, preserving the `.github/workflows` and `scripts` folders.

## What changes

- Monthly calculates the Sun sign from the natal data; the duplicate sign selector is removed.
- Your Year Ahead calculates the Sun sign from the natal data; the duplicate sign selector is removed.
- Monthly and Year Ahead publish LLM interpretation only when their complete required document bundle validates.
- Partial provider success cannot leak lower prose beneath a failed main narrative.
- Weekly collection stories cannot repeat `YOUR MOVE`, `REMEMBER` or `AFFIRMATION` labels.
- Public Daily reads pre-generated sign copy in `published` mode. On-page generation is limited to explicit `live` mode.
- Featured YouTube videos can be locked to their production week.

## Streamlit secret for the weekly video

Set this beside the existing featured-video URL:

```toml
LUNA_YOUTUBE_FEATURED_VIDEO_WEEK_START = "2026-09-07"
```

Use the Monday of the video's production week. If it does not match the current week, Luna hides the video.

## Publish Daily copy

In GitHub, open **Actions → Generate and publish Daily Luna voice → Run workflow**.

Enter:

- the required reading date;
- `Australia/Sydney`.

The action generates all 12 signs sequentially, validates them, and commits one dated JSON document. With `LUNA_VOICE_MODE = "published"`, visitors read that file and do not initiate Groq calls.

## Commit message

```text
Publish Luna v3.36 atomic guided reports
```
