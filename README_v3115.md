# Luna v3.115 — Year Ahead annual marker tolerance

Base: v3.114 (itself based on v3.111). Apply these changed files over v3.114.

Changed production files:
- `paid_yearly_editorial.py`: Only annual four-month writing jobs accept marker-free prose and discard stray standalone provider markers. A minimum content requirement remains; other section marker validation is unchanged.
- `app.py`: explicit release version `v3.115`.

Offline tests: `python test_v3115_marker_acceptance.py` and `python test_v3114_year_voice.py`.

No live Groq call or paid report end-to-end verification performed. Monthly, charts, PDF and checkout unchanged.
