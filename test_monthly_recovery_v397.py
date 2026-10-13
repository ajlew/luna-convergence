import ast, pathlib, types, re
src=pathlib.Path('/mnt/data/recovery/current/app.py').read_text()
tree=ast.parse(src)
names={'_paid_monthly_clean_plain_story','_paid_monthly_publishable_prose','_monthly_natal_pattern'}
functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
mod=ast.Module(body=functions,type_ignores=[])
ns={'re':re,'_build_signatures':lambda a, limit: []}
exec(compile(ast.fix_missing_locations(mod),'<extract>','exec'),ns)
validate=ns['_paid_monthly_publishable_prose']
for refusal in ["I'm sorry, but I can't help with that.","I cannot provide this interpretation.","As an AI language model, I can't help.","I am unable to assist with this.","I’m sorry, but I cannot help with that."]:
 assert not validate(refusal)[0],refusal
story=("You are considering how to handle an agreement that asks more from you than it offers. "*40)
assert validate(story)[0]
from types import SimpleNamespace as Obj
sig=Obj(title='One skill',text='You thrive when you slow down long enough to assess the competing demands.',strength='Use your persistence for work that matters.',watch='Taking on every task alone.',evidence='Saturn square Neptune · 0.86°')
a=Obj(planet1='Saturn',planet2='Neptune',name='square')
snap=Obj(aspects=[a],signatures=[sig])
pat=ns['_monthly_natal_pattern'](snap)
assert 'You thrive when' in pat and 'persistence' in pat
assert 'The tightest calculated pattern' not in pat
from importlib.machinery import SourceFileLoader
m=SourceFileLoader('monthly_shared_view','/mnt/data/recovery/current/monthly_shared_view.py').load_module()
html=m.build_monthly_shared_html(title='Test',label='Month',intro='Overview',paragraphs=[story],natal_pattern=pat,natal_strengths=[{'title':sig.title,'text':sig.text,'evidence':sig.evidence,'remember':sig.strength}])
assert 'Read the pattern' in html and 'Your strengths' in html and 'Read the month' in html
assert html.index('Read the pattern') < html.index('Your strengths') < html.index('Read the month')
print('PASS: refusal filters, meaningful existing signature text, single report content, section ordering')
