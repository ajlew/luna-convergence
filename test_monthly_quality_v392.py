import ast
from pathlib import Path
from bs4 import BeautifulSoup
root=Path(__file__).parent
app=(root/'app.py').read_text()
print_html=(root/'monthly_report_pdf_home_v3.py').read_text()
for p in ('app.py','monthly_report_pdf_home_v3.py'):
 ast.parse((root/p).read_text())
assert '_paid_monthly_correct_sun_sign_attribution(paragraphs, sign)' in app
assert 'Libra is cardinal Air, not fixed Water' in app
assert 'first_rows = evidence_rows[:11]' in print_html
assert 'The month\'s supporting evidence' in print_html
assert "if title.strip().casefold() != 'read the month'" in print_html
soup=BeautifulSoup(Path('/mnt/data/Luna_v392_Actual_Monthly_Print_Proof.html').read_text(),'html.parser')
assert len(soup.select('.monthly-story-page .section-title'))==1
assert not soup.select('.monthly-story-page .story-full-text h2')
assert not any('fixed Water nature' in p.get_text() for p in soup.select('.story-full-text p'))
assert len(soup.select('.evidence-grid'))==2
assert sum(len(x.select('.evidence-card')) for x in soup.select('.evidence-grid'))==22
print('v3.92 offline regression checks passed')
