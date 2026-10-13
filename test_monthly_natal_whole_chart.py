import ast, importlib.util
from pathlib import Path
from types import SimpleNamespace as N
from html.parser import HTMLParser

source=Path(__file__).with_name('app.py').read_text()
tree=ast.parse(source)
func=next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name=='_monthly_natal_pattern')
namespace={'_NATAL_CORE_THREAD_ROLES': {'Sun': ('direction', ''), 'Saturn':('structure',''), 'Venus':('values',''), 'Mars':('action','')}}
exec(compile(ast.Module(body=[func], type_ignores=[]), 'app.py','exec'), namespace)
mk=lambda p,sign:N(planet=p,sign=sign)
chart=N(positions=[mk('Sun','Leo'),mk('Moon','Pisces'),mk('Mercury','Virgo'),mk('Venus','Cancer'),mk('Mars','Gemini')],
        ascendant=N(sign='Sagittarius'),birth_time_known=True,aspects=[N(planet1='Sun',planet2='Saturn',name='opposition',orb=1.6,strength=.91)], dominant_element='Water',dominant_modality='Mutable')
text=namespace['_monthly_natal_pattern'](chart)
assert 'Sun in Leo' in text and 'Moon in Pisces' in text and 'Sagittarius rising' in text
assert 'Mercury in Virgo' in text and 'Venus in Cancer' in text and 'Mars in Gemini' in text
assert 'Sun opposition Saturn' in text and 'Water and Mutable' in text
assert 'Part of you wants movement' not in text
chart2=N(positions=[mk('Sun','Aquarius'),mk('Moon','Taurus')],ascendant=None,birth_time_known=False,
         aspects=[N(planet1='Venus',planet2='Mars',name='trine',orb=.3,strength=.95)], dominant_element='',dominant_modality='')
text2=namespace['_monthly_natal_pattern'](chart2)
assert 'Venus trine Mars' in text2 and 'rising' not in text2 and 'Sun in Aquarius' in text2
spec=importlib.util.spec_from_file_location('monthly_shared_view',Path(__file__).with_name('monthly_shared_view.py'))
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
html=mod.build_monthly_shared_html(title='title',label='period',intro='deck',paragraphs=['Real story'],natal_pattern=text,
  natal_strengths=[{'title':'Strength','text':'Different, focused point','evidence':'Test aspect','remember':'Watch'}],
  natal_svg='<svg id="natal-test"></svg>',activation_svg='<svg id="activation-test"></svg>')
assert html.count('natal-test')==1 and html.count('activation-test')==1
assert html.index('Read the pattern')<html.index('Your strengths')<html.index('natal-test')<html.index('Read the month')<html.index('activation-test')
assert len(mod.html_to_pdf(html))>1000
print('PASS: whole chart / different chart / no duplicate wheel / PDF')
