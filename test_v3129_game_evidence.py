import ast
from pathlib import Path
from typing import Any
p=Path(__file__).with_name('paid_yearly_editorial.py')
s=p.read_text()
tree=ast.parse(s)
fn=next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name=='_game_voice_evidence')
ns={'Any':Any}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),'exec'),ns)
months=[{'number':i+1,'start':a,'end':b,'phase':'Decision','focus':'Boundaries'} for i,(a,b) in enumerate([('2026-10-16','2026-11-15'),('2026-11-16','2026-12-15'),('2026-12-16','2027-01-15'),('2027-01-16','2027-02-15'),('2027-02-16','2027-03-15'),('2027-03-16','2027-04-15'),('2027-04-16','2027-05-15'),('2027-05-16','2027-06-15'),('2027-06-16','2027-07-15'),('2027-07-16','2027-08-15'),('2027-08-16','2027-09-15'),('2027-09-16','2027-10-15')])]
game={'start':'2027-06-06','end':'2027-10-17','primary':{'technical':'Saturn opposition natal Venus','passes':[{'date':'2027-07-02','pass_label':'Initial activation'},{'date':'2027-09-17','pass_label':'Retrograde return'},{'date':'2027-11-17','pass_label':'Outside'}]}}
out=ns['_game_voice_evidence'](game,months)
assert out['narrative_start']=='2027-06-06' and out['narrative_end']=='2027-10-15'
assert [x['date'] for x in out['allowed_exact_contacts']]==['2027-07-02','2027-09-17']
assert all(x['start'] <= '2027-10-15' and x['end'] >= '2027-06-06' for x in out['overlapping_months'])
game2={'start':'2026-07-23','end':'2027-07-12','primary':{'technical':'Uranus opposition natal Pluto','passes':[{'date':'2026-06-01'},{'date':'2027-06-08'}]}}
out2=ns['_game_voice_evidence'](game2,months)
assert out2['narrative_start']=='2026-10-16' and out2['narrative_end']=='2027-07-12'
assert [x['date'] for x in out2['allowed_exact_contacts']]==['2027-06-08']
assert 'annual_instruction=game_instructions' in s
assert 'APP_VERSION = "v3.129"' in Path(__file__).with_name('app.py').read_text()
print('PASS: two bounded Games, clipped windows, supported passes, pre-LLM Game instructions, explicit version')
