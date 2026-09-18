import unittest
from datetime import date
from unittest.mock import patch, Mock
from plain_readings import make_reading, generation_current, current_reading, clean_prose, reading_html, prompt_for
from reading_quality import chronology_errors, grounded_brief
from plain_voice_generator import generate_text
from studio_readings import publishing_copy
from luna_reading_style import meaning_html
from test_plain_workflow import packet, BODY


def week(product='weekly'):
    p=packet(product=product)
    p['events']=[{'date':'2026-09-14','event':'Mercury trine Uranus'},
        {'date':'2026-09-18','event':'Moon trine Jupiter','supporting_events':['Mercury opposite Saturn']},
        {'date':'2026-09-19','event':'Mercury opposite Saturn'},
        {'date':'2026-09-20','event':'Moon square Saturn'}]
    return p

class ChronologyTests(unittest.TestCase):
    def test_backwards_regression(self):
        self.assertTrue(chronology_errors(week(),'Monday opens. Friday lifts. Wednesday deepens.'))
    def test_wrong_day_regression(self):
        errors=chronology_errors(week('studio_weekly'),'Saturday brings Moon square Saturn.')
        self.assertEqual(len(errors),1)
        self.assertIn('Sunday, not Saturday',errors[0])
    def test_supporting_aspect_and_aliases(self):
        self.assertFalse(chronology_errors(week(),'Friday has Mercury opposition Saturn. Saturday has Saturn opposite Mercury. Sunday brings Moon square Saturn.'))
    def test_multi_day_clause_not_guessed(self):
        self.assertFalse(chronology_errors(week(),'Saturday and Sunday contrast Mercury opposite Saturn with Moon square Saturn.'))
    def test_correct_order(self):
        self.assertFalse(chronology_errors(week(),'Friday has Moon trine Jupiter. Sunday has Moon square Saturn.'))
    def test_map_sorted(self):
        p=week();p['events'].reverse()
        self.assertEqual([r['weekday'] for r in grounded_brief(p)['chronological_day_map']],['Monday','Friday','Saturday','Sunday'])
        self.assertIn('Monday–Tuesday',prompt_for(p))
    def test_refresh_scope(self):
        for product in ('daily','monthly','studio_daily','studio_meaning','weekly','studio_weekly'):
            p=packet(product=product);r=make_reading(p,BODY)
            self.assertTrue(generation_current(r,p))
            r['writing_revision']='event-grounding-2'
            self.assertFalse(generation_current(r,p))
            self.assertIsNotNone(current_reading(r,p))
    def test_formatting_and_publishing(self):
        body='**Emotional optimism.** Keep <script> out.\n\n**Write one plan.**'
        p=packet();r=make_reading(p,body);r['voice_body']=body
        self.assertNotIn('**',current_reading(r,p)['voice_body'])
        self.assertNotIn('**',reading_html(p,r))
        self.assertNotIn('<script>',reading_html(p,r))
        self.assertNotIn('**',meaning_html(date(2026,9,18),'Moon trine Jupiter',body))
        copy=publishing_copy(date(2026,9,14),body,'https://example.test')
        for key in ('YouTube description','Instagram Reel caption'):
            self.assertTrue(copy[key].startswith(clean_prose(body)))
    def test_bounded_draft_correction(self):
        bad='Saturday brings Moon square Saturn. Make space.'
        good='Monday brings Mercury trine Uranus. Friday brings Moon trine Jupiter. Saturday names Mercury opposite Saturn as separating pressure. Sunday brings Moon square Saturn. Set one boundary list.'
        def response(body):
            r=Mock(status_code=200)
            r.json.return_value={'choices':[{'message':{'content':body},'finish_reason':'stop'}]}
            return r
        post=Mock(side_effect=[response(bad),response(good)])
        with patch.dict('os.environ',{'LUNA_VOICE_BASE_URL':'https://example.test','LUNA_VOICE_MODEL':'test','LUNA_VOICE_API_KEY':'test'}):
            self.assertEqual(generate_text(week('studio_weekly'),post=post,sleep=lambda _:None),good)
        self.assertEqual(post.call_count,2)
        messages=post.call_args.kwargs['json']['messages']
        self.assertEqual(messages[-2]['content'],bad)
        self.assertIn('Sunday, not Saturday',messages[-1]['content'])

    def test_daily_facts_do_not_run_unused_headline_writer(self):
        from reading_facts import build_packet
        with patch('daily_narrative_v3._emotional_hook',side_effect=AssertionError('unused prose')):
            p=build_packet('daily',date(2026,9,18),'Virgo','Australia/Sydney')
        self.assertTrue(p['events'])

    def test_daily_fact_parity_on_previously_working_date(self):
        from reading_facts import build_packet
        from customer_experience import free_daily_reading, HOUSE_VOICE
        from daily_narrative_v3 import build_daily_narrative
        day=date(2026,9,17)
        old=build_daily_narrative(free_daily_reading('Pisces',day,'Australia/Sydney'),
            sign='Pisces',reading_date=day,timezone_name='Australia/Sydney',house_voice=HOUSE_VOICE)
        p=build_packet('daily',day,'Pisces','Australia/Sydney')
        self.assertEqual(p['events'][0]['technical_aspects'],list(old.technical_aspects))
        self.assertEqual(p['events'][0]['aspect'],old.evidence.aspect_label)
        for label in old.supporting_events:
            self.assertIn(label,p['calculation_header'])

    def test_weekly_does_not_force_aspect_coverage(self):
        p=week()
        body='Monday has Mercury trine Uranus. Friday has Moon trine Jupiter. Sunday has Moon square Saturn. Write one boundary list before dinner.'
        from reading_quality import content_errors
        self.assertFalse(content_errors(p,body))

    def test_daily_does_not_force_aspect_coverage(self):
        p=packet(product='daily')
        p['events']=[{'event':'Moon trine Jupiter','supporting_events':['Mercury opposite Saturn']}]
        from reading_quality import content_errors
        self.assertFalse(content_errors(p,'Moon trine Jupiter opens the day. Make space.'))
