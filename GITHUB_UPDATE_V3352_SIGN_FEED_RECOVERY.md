# Luna v3.35.2 - Sign Feed Recovery

## Fault confirmed

The main cached Week Ahead story loaded, but the 12-sign and seven-day Groq collections were rejected as complete batches. The validator treated a repeated short field anywhere in the collection as fatal, and one malformed item discarded every otherwise valid item.

## Fix

- Weekly sign evidence is supplied once as `shared_context` instead of copying seven events into every sign.
- The public Weekly View generates only the selected sign.
- Exact duplicate protection now applies to complete stories, not short affirmations or actions.
- A collection that fails twice is recovered one calculated item at a time.
- Source IDs, planets, dates, numbers and evidence hashes remain locked.
- Provider or authentication failures do not trigger a storm of individual retry calls.

## Upload

Upload all files in this package to the repository root and commit with:

```text
Fix Luna 12-sign and seven-day LLM feed
```

After Streamlit redeploys, reboot the app and open Weekly Studio. Click **Build weekly sky + 12 signs** once. The first generation can take longer because the new evidence hashes create a clean cache. Later views reuse the validated result.

## Expected result

- Each of the 12 sign expanders contains a headline, story, affirmation, action and social-card copy.
- Each Monday-Sunday card contains guided Luna copy.
- Weekly View generates only the visitor's selected sign.
- No hard-coded forecast is substituted if the provider is genuinely unavailable.
