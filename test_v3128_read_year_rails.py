import ast
from pathlib import Path
p=Path(__file__).with_name('paid_yearly_editorial.py')
s=p.read_text()
ast.parse(s)
assert "'act_start_date': act_start" in s
assert "'act_end_date': act_end" in s
assert "'allowed_exact_contacts': ledger" in s
assert '"first game"' in s
assert "'major_issues': [\n                             {'number': g.get('number')" not in s
assert 'verified_dated_contacts_for_this_act supplies named contacts' not in s
# Execute isolated deterministic ledger helper without calling Groq.
tree=ast.parse(s)
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_annual_act_evidence')
module=ast.Module(body=[node],type_ignores=[])
from typing import Any
ns={'Any':Any}
exec(compile(module,str(p),'exec'),ns)
material={'major_issues':[{'primary':{'technical':'Jupiter sextile natal Venus','passes':[{'date':'2026-11-28','pass_label':'Initial'},{'date':'2027-07-09','pass_label':'Final'}], 'triggers':[{'date':'2026-12-19','planet':'Sun','aspect':'sextile','target':'Venus'}]}}]}
a=ns['_annual_act_evidence'](material,[{'number':1,'start':'2026-10-15','end':'2026-11-14'},{'number':2,'start':'2026-11-15','end':'2026-12-14'},{'number':3,'start':'2026-12-15','end':'2027-01-14'}])
assert [r['date'] for r in a]==['2026-11-28','2026-12-19'],a
assert all(r['date']!='2027-07-09' for r in a)
print('PASS: act boundaries, packet scope, dated evidence and Python compilation')
