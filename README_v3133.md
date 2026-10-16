# Luna v3.133 — Python-owned Year Ahead prose slots

Built on v3.132 with the professional print renderer **byte-for-byte unchanged**.

- No provider-authored `<<...>>` section markers in the Year Ahead generation path.
- Removed the old Year Ahead marker prompt builders, response marker parser, single-Game normalizer, and dead post-generation editorial sanitation utilities.
- Python assigns annual phases, framing headline/deck/natal portrait/closing, twelve months, and three Games **before requesting prose**.
- Each Groq completion is assigned directly to exactly one predetermined slot. No post-LLM editorial rewriting or evidence validation.
- Python-computed annual ledgers, month scope, dominant Games, and Game evidence windows continue to feed the writer.
- Cached completion, configured token budgets and pacing retained. New cache namespace avoids reusing older marker-generated completions.

## Provider budget trade-off

Former configuration: 4 annual + 1 framing + 3 monthly groups + 3 Games = **11 completions**.
Now: 4 annual + 4 framing + 12 individual months + 3 Games = **23 completions** (assuming 3 Games). This is **necessary** for guaranteed Python-owned sections when providers return unconstrained plain prose. Promising 11 requests without reintroducing provider-owned delimiters or a structured output envelope would be inaccurate. Individual monthly caps are 460 rather than 1400 for four months; framing caps are smaller per slot. Total output allowance may still be greater; usage depends on Groq reasoning/token behaviour. Rate pacing remains enabled.

## Verification and limitations

Python syntax compilation and deterministic source-contract checks passed. No live Groq run, end-to-end report PDF, or payment flow has been exercised. The standalone ZIP requires the pre-existing repository and its dependencies. No Paid Monthly, payment, astrology calculation, or print-renderer files were changed beyond the app version label.

Install the three Python files over v3.132. This ZIP includes the existing v3.130 Professional Print renderer.
