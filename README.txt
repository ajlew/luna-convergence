LUNA PAID YEARLY — v1.2 PROVIDER-FIT FALLBACK

Replace only:
    /paid_yearly_editorial.py

WHY
The latest owner run reached the new Phase 4 code but failed before the provider call:
    "Paid Yearly preflight still exceeds the provider-safe token envelope after
     ultra compaction (3678 estimated input tokens)."

With the locked 5,350-token total envelope and 1,800-token minimum completion,
3,678 input tokens leaves only 1,672 completion tokens, so Python correctly
blocked the call.

FIX
- Keep the full Phase 4 prompt unchanged when it fits.
- Only when all four normal compaction levels fail, use a shorter provider-fit
  prompt around the already ultra-compacted YearPacket.
- Same facts.
- Same markers.
- Same one-call architecture.
- No retry.
- No second model.
- No change to the 5,350 safe ceiling.
- No change to the 1,800 minimum completion floor.
- No change to timing_map.py / year_ahead.py / report renderer.
- Also fixes the internal word-count regex.

This removes repeated instruction overhead instead of deleting calculated
astrology or lowering the publication safety floor.
