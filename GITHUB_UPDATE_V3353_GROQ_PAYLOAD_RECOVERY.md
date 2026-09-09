# Luna v3.35.3 - Groq Payload Recovery

## Confirmed fault

Groq returned HTTP 413 `Payload Too Large` when Weekly Studio sent all twelve sign translations in one request. The API key was accepted; the request size and 8,000-token output reservation were the failure.

## Correction

- Sign and daily collections are sent in batches of no more than three items.
- Each batch receives a right-sized output-token allowance instead of 8,000 tokens.
- A batch that still receives HTTP 413 is split in half until Groq accepts it.
- The accepted batches are restored to their calculated order and validated as one complete collection.
- A validation failure is also isolated to smaller batches instead of erasing every sign.
- Weekly View requests only the visitor's selected sign.
- Source IDs, planets, dates, numbers and evidence hashes remain locked.
- HTTP 400/401/413 errors are no longer retried three times as if they were temporary server failures.

## Upload

Upload every file in this package to the repository root and commit:

```text
Fix Groq 413 for Luna sign collections
```

Wait for Streamlit to redeploy, reboot the app, open Weekly Studio and click **Build weekly sky + 12 signs** once. The initial generation now uses four bounded requests for twelve signs rather than one oversized request.

## Expected result

- All twelve sign expanders receive Luna copy.
- Monday-Sunday cards receive Luna copy in three bounded requests.
- No `413 Payload Too Large` diagnostic appears.
- Later views reuse Streamlit's validated 24-hour cache.
