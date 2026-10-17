Luna v3.140 - Year Ahead context_guard initialization hotfix

Replace paid_yearly_editorial.py at repository root.
Fixes UnboundLocalError: context_guard was referenced in the annual phase loop before its assignment.
Moves the existing constant definition before its first use. Does not modify its text or Groq call settings.
No Groq calls were made for testing.
