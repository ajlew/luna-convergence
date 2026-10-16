# Luna v3.134 — Groq truncated-completion recovery

Based on v3.133, including the v3.130 Professional Print renderer, unchanged byte-for-byte.

The diagnostic `completion limit reached` comes from `finish_reason=length`: the provider output was truncated at the requested max_completion_tokens. It does **not** identify a daily 200k token exhaustion or a TPM 429.

- All 23 Python-owned prose slots remain. No markers, output parsing or post-LLM rewriting.
- Only a technically truncated section is retried, **at most once**, with a larger completion allowance bounded by configured single-request and minute token budgets. Normal successful jobs still use one request.
- Technical failure diagnostics now include `annual_4`, `month_7`, `game_2` etc. and the attempted completion allowance.
- Cached sections remain usable on retried owner runs subject to the configured checkpoint storage.
- No changes to Paid Monthly, ephemeris, checkout, renderer or report contents.

**Limits:** Additional completion room cannot guarantee success. The initial truncated call consumes quota; an eligible retry can require a minute-budget wait. The SQLite checkpoint is local and may be lost on a Streamlit Cloud container restart. This has not been tested against a live Groq account or a complete customer PDF.
