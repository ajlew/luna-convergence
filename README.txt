Luna v3.103 — Year Ahead completion budget adjustment
Base: uploaded luna-convergence-main(3).zip (v3.102).
Changed: app.py (explicit version and build label); paid_yearly_editorial.py (configurable annual response allowance and request budget).
New test: test_yearly_budget_v3103.py.
Untouched: Paid Monthly code, natal calculations, Year Ahead transit engine, HTML/PDF, provider/router.
Defaults: LUNA_YEARLY_ANNUAL_OUTPUT_TOKENS=4200; LUNA_YEARLY_REQUEST_BUDGET_TOKENS=7800. Provider account limits are not inferred from these defaults.
This corrects a too-small completion allowance but DOES NOT prove live provider completion. It does not rearchitect the existing multi-job writer into the planned single-call writer.
Offline targeted tests passed; older test_voice_http_v387.py fails on pre-existing unrelated expected wording. No Groq called.
Install the two .py files at repository root and retain original for rollback.
