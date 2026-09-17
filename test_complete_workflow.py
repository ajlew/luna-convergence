import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from plain_readings import (make_reading, generation_current, read_document,
                            reading_path, write_document, load_reading, prompt_for)
from reading_quality import required_events, content_errors, grounded_brief
from reading_facts import build_packet
from scripts.generate_plain_readings import run_signs, main
from test_plain_workflow import packet, BODY

class CompleteWorkflowTests(unittest.TestCase):
    def test_pisces_event_scopes_are_explicit(self):
        p=grounded_brief(build_packet('monthly',date(2026,9,17),'Pisces','Australia/Sydney'))
        moon=next(r for r in p['events'] if r['event']=='New Moon in Virgo')
        self.assertEqual(moon['event_life_areas'],[{'house':7,'life_area':'relationships, clients, contracts and competitors'}])
        w=grounded_brief(build_packet('weekly',date(2026,9,17),'Pisces','Australia/Sydney'))
        friday=w['events'][4]
        self.assertEqual([x['house'] for x in friday['planet_life_areas']],[10,6])
        self.assertNotIn('home, family',str(friday['event_life_areas']))

    def test_seasonal_and_lunar_omissions_are_detected(self):
        p=build_packet('monthly',date(2026,9,17),'Pisces','Australia/Sydney')
        self.assertTrue(any('Equinox' in x for x in required_events(p)))
        self.assertTrue(any('Full Moon' in x for x in required_events(p)))
        self.assertTrue(content_errors(p,'Take one practical step.'))
        self.assertFalse(content_errors(p,'Explain the equinox, New Moon, Full Moon and Neptune sextile Pluto.'))
        eclipse={'product':'monthly','major_events':[{'event':'Partial Lunar Eclipse in Pisces'}]}
        self.assertTrue(content_errors(eclipse,'The Full Moon brings a change.'))
        self.assertFalse(content_errors(eclipse,'Consider the lunar eclipse.'))

    def test_revision_refreshes_once_and_failed_refresh_keeps_saved_text(self):
        with tempfile.TemporaryDirectory() as root:
            p=packet(); old=make_reading(p,BODY);old.pop('writing_revision')
            path=reading_path('daily',p['period'],p['timezone'],root)
            write_document(path,{'signs':{'Virgo':old}})
            generate=Mock(side_effect=RuntimeError('private failure'))
            kwargs=dict(build=lambda *a:p,generate=generate,root=root,pause=0)
            self.assertEqual(run_signs('daily',date(2026,9,15),p['timezone'],['Virgo'],**kwargs),1)
            self.assertEqual(read_document(path)['signs']['Virgo']['voice_body'],BODY)
            generate.side_effect=None;generate.return_value=BODY
            for _ in range(2):
                self.assertEqual(run_signs('daily',date(2026,9,15),p['timezone'],['Virgo'],**kwargs),0)
            self.assertEqual(generate.call_count,2) # failed attempt + one successful refresh
            self.assertTrue(generation_current(read_document(path)['signs']['Virgo'],p))

    def test_check_only_cannot_generate_or_write(self):
        with tempfile.TemporaryDirectory() as root:
            generate=Mock(side_effect=AssertionError('must not call model'))
            self.assertEqual(run_signs('daily',date(2026,9,15),'Australia/Sydney',['Virgo'],
                build=lambda *a:packet(),generate=generate,root=root,pause=0,check_only=True),1)
            generate.assert_not_called()
            self.assertFalse(list(Path(root).rglob('*.json')))

    def test_sunday_recovery_matches_visible_coming_week(self):
        class Clock:
            @staticmethod
            def now(zone): return datetime(2026,9,20,8,0,tzinfo=zone)
        with patch('scripts.generate_plain_readings.datetime',Clock), patch('scripts.generate_plain_readings.run_signs',return_value=0) as run:
            self.assertEqual(main(['--product','maintain','--pause','0']),0)
            for call in run.call_args_list:
                if call.args[0] in ('weekly','studio_weekly'):
                    self.assertEqual(call.args[1],date(2026,9,21))
            self.assertEqual(run.call_args_list[-1].args[:2],('daily',date(2026,9,21)))

    def test_missing_event_gets_one_draft_repair(self):
        from plain_voice_generator import generate_text
        p=packet(product='monthly');p['major_events']=[{'event':'September Equinox','tier':'FOUNDATION'}]
        replies=[]
        for body in ('Take stock of your choices.','Use the September equinox to reset your priorities.'):
            r=Mock(status_code=200);r.json.return_value={'choices':[{'message':{'content':body},'finish_reason':'stop'}]};replies.append(r)
        post=Mock(side_effect=replies)
        with patch.dict('os.environ',{'LUNA_VOICE_BASE_URL':'https://example.invalid','LUNA_VOICE_MODEL':'test','LUNA_VOICE_API_KEY':'test'}):
            result=generate_text(p,post=post,sleep=lambda _:None)
        self.assertIn('equinox',result)
        self.assertEqual(post.call_count,2)
        self.assertIn('September Equinox',post.call_args.kwargs['json']['messages'][-1]['content'])

    def test_all_products_are_populated_and_displayed(self):
        """Real packets -> offline writer fixture -> disk -> full Streamlit page imports."""
        from streamlit.testing.v1 import AppTest
        today=datetime.now(ZoneInfo('Australia/Sydney')).date()
        actual_run=run_signs
        actual_load=load_reading
        with tempfile.TemporaryDirectory() as root:
            def offline(p):
                labels='; '.join(required_events(p))
                return f"Choose a clear direction. Read the {p['product']} pattern in context. {labels}. Keep your next step practical."
            def run(*args,**kwargs):
                kwargs.update(root=root,generate=offline,pause=0)
                return actual_run(*args,**kwargs)
            with patch('scripts.generate_plain_readings.run_signs',side_effect=run):
                self.assertEqual(main(['--product','all','--date',today.isoformat(),'--pause','0']),0)
                self.assertEqual(main(['--product','all','--date',today.isoformat(),'--pause','0','--check-only']),0)
            # 12 daily + 12 weekly + 12 monthly + 1 overview + 7 meanings + 7 clips.
            count=sum(len(read_document(p).get('signs',{})) for p in Path(root).rglob('*.json'))
            self.assertEqual(count,51)
            source=Path('app.py').read_text()
            for call,expected in [('_render_lean_daily("/")','daily pattern'),('weekly_page()','weekly pattern'),
                                   ('monthly_sign_page()','monthly pattern'),('weekly_studio_page()','studio_weekly pattern')]:
                with tempfile.NamedTemporaryFile(mode='w',suffix='.py',dir='.',delete=False) as f:
                    f.write(source.replace('current_page.run()',call));filename=f.name
                try:
                    with patch('plain_readings.load_reading',side_effect=lambda p:actual_load(p,root)):
                        at=AppTest.from_file(filename).run(timeout=45)
                        if call != 'weekly_studio_page()':
                            at.selectbox[0].select('Pisces').run(timeout=45)
                    self.assertFalse(at.exception,[e.message for e in at.exception])
                    markup='\n'.join(x.value for x in at.markdown)
                    self.assertTrue(expected in markup, f'{call}: missing saved reading')
                    if call=='weekly_studio_page()':
                        self.assertEqual(markup.count('Collective meaning &amp; energy'),7)
                        self.assertTrue(any('7/7 meaning' in c.value for c in at.caption))
                        self.assertTrue(any('daily scripts (7/7)' in b.label for b in at.get('download_button')))
                finally:
                    Path(filename).unlink()
