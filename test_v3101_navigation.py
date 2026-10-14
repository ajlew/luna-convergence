from pathlib import Path
import re
s=Path(__file__).with_name('app.py').read_text()
assert 'APP_VERSION = "v3.101"' in s
m=re.search(r'    items = \[(.*?)\n    \]',s[s.index('def top_navigation('):],re.S)
assert m,m
nav=m.group(1)
paths=re.findall(r'\(\s*(?:monthly_path|"[^"]*")\s*,\s*"([^"]+)"\)',nav)
assert paths==['Daily Horoscope','Weekly Horoscope','Monthly Horoscope','Personal Reports','Your Year Ahead','Birthday Card','House Guide','Solar Year'],paths
assert '("weekly-view", "Weekly Horoscope")' in nav
assert '(monthly_path, "Monthly Horoscope")' in nav
assert 'label == "Monthly Horoscope" and nav_path == "this-month"' in s
assert 'def top_navigation(current_path: str)' in s
spec=Path(__file__).with_name('Luna_Paid_Year_Ahead.md').read_text()
assert 'Paid Monthly' in spec and '12 monthly rounds' in spec and 'One-Call Voice Contract' in spec
print('v3.101 navigation / version / plan checks PASSED')
