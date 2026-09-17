import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from plain_readings import split_move, reading_html, prompt_for
from test_plain_workflow import packet

class ClarityTests(unittest.TestCase):
    def test_lowercase_final_action(self):
        body='By the end of the week, responsibilities may feel heavier. Draft the plan carefully.\n\ndraft a concise action plan before sunset.'
        story,move=split_move(body)
        self.assertEqual(move,'draft a concise action plan before sunset.')
        self.assertIn('responsibilities',story)

    def test_monthly_dates_sorted_and_duplicates_removed(self):
        p=packet(product='monthly')
        p['calculation_header']=['2026-09-26 · Sun opposite Neptune','2026-09-01 · Jupiter trine Saturn','2026-09-26 · Sun opposition Neptune']
        html=reading_html(p,None)
        self.assertLess(html.index('2026-09-01'),html.index('2026-09-26'))
        self.assertEqual(html.count('2026-09-26'),1)

    def test_prompt_requests_meaning_and_progression_without_strict_count(self):
        prompt=prompt_for(packet(product='weekly'))
        self.assertIn('early-week, midweek and weekend',prompt)
        self.assertIn('symbolic meaning',prompt)
        self.assertNotIn('strictly',prompt)
        self.assertIn('no invented windfalls',prompt)

    def test_all_normalizes_dates_and_stops_on_quota(self):
        from scripts.generate_plain_readings import main
        with patch('scripts.generate_plain_readings.run_signs',return_value=0) as run:
            self.assertEqual(main(['--product','all','--date','2026-09-16','--pause','0']),0)
            self.assertEqual([(c.args[0],c.args[1]) for c in run.call_args_list],
                [('daily',date(2026,9,16)),('weekly',date(2026,9,14))]
                + [('studio_weekly',date(2026,9,14))]
                + [(kind,date(2026,9,14+i)) for i in range(7) for kind in ('studio_meaning','studio_daily')]
                + [('monthly',date(2026,9,1))])
        with patch('scripts.generate_plain_readings.run_signs',return_value=2) as run:
            self.assertEqual(main(['--product','all','--date','2026-09-16','--pause','0']),2)
            self.assertEqual(run.call_count,1)

    def test_studio_full_app_globals(self):
        import tempfile
        from streamlit.testing.v1 import AppTest
        source=Path('app.py').read_text().replace('current_page.run()', 'weekly_studio_page()')
        with tempfile.NamedTemporaryFile(mode='w',suffix='.py',dir='.',delete=False) as f:
            f.write(source)
            filename=f.name
        try:
            at=AppTest.from_file(filename).run(timeout=45)
            self.assertFalse(at.exception,[e.message for e in at.exception])
            self.assertEqual(len(at.expander),21)
        finally:
            Path(filename).unlink()

if __name__=='__main__':unittest.main()
