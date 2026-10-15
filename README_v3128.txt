Luna v3.128 — Read the Year evidence rails only
Required baseline: user's v3.125 full repository with the v3.127 transport patch applied.
Changed files: app.py (explicit version), paid_yearly_editorial.py (annual three-act packet and prompt).
No changes to: Groq call count/output caps, shared transit calculation, monthly reports, Major Stories, chart/rendering, payment, transport code.
Each rolling four-month annual act receives the dynamically calculated start/end dates and only its exact contacts/triggers in the allowed-contact ledger; the prompt prohibits names/dates outside its act and game-enumeration prose.
The model still writes freely within those pre-LLM evidence rails. No post-LLM content validation added.
Verification: compilation and targeted offline ledger/scope checks. No live Groq test, no PDF regeneration.
Installation: Replace app.py and paid_yearly_editorial.py in the v3.127-applied repository, then redeploy. Rollback: restore those two files from v3.127.
