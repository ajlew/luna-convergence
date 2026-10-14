# Luna v3.109 — Year Ahead paid voice completion

Apply only to deployed **v3.108**. Back up the two application files first.

Files changed:
- `paid_yearly_editorial.py`: split the formerly combined annual writing request into two independently validated jobs: Read the Year, then Headline/Deck/Closing. All 12 monthly passages and all major Games are retained, with existing evidence selection, parser, paid voice router, checkpoints and safeguards unchanged.
- `app.py`: explicitly hard-coded release version `v3.109` and build label.

Configuration, optional environment values:
- `LUNA_YEARLY_ANNUAL_OUTPUT_TOKENS` defaults to 3300 (annual essay only).
- `LUNA_YEARLY_FRAMING_OUTPUT_TOKENS` defaults to 1200 (headline, deck, closing).
- `LUNA_YEARLY_REQUEST_BUDGET_TOKENS` retains existing default 7800; this is a local per-request guard, not a provider's guaranteed allowance.

No Paid Monthly, natal calculations, chart, HTML, PDF, checkout, Groq routing or credentials changed.

Validation: offline mock-provider assembly, complete section marker coverage, Python compilation. A live provider completion and a real customer PDF are **not verified**. Provider TPM and real-time limits may still block a run; this revision addresses output truncation of the combined annual job.

If the deployment differs from v3.108 or its paid writer is different from the v3.103 baseline, review before overlay. Roll back both files if necessary.
