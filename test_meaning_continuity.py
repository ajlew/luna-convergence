import unittest
from datetime import datetime, date
from unittest.mock import patch
from plain_readings import reading_html, prompt_for
from test_plain_workflow import packet

class ContinuityTests(unittest.TestCase):
    def test_calculations_closed_for_every_reading(self):
        for kind in ('daily','weekly','monthly'):
            html=reading_html(packet(product=kind), {'voice_body':'Consider your choices. Make one useful change.'})
            self.assertIn('<details class="luna-calculations">',html)
            self.assertNotIn('<details open',html)
            self.assertIn('Consider your choices.',html)
            self.assertNotIn('<table',html)

    def test_collective_prompt_and_escaping(self):
        from luna_reading_style import meaning_html
        self.assertIn('collective meaning and energy',prompt_for(packet(product='studio_meaning')))
        html=meaning_html(date(2026,9,16),'Moon < Mars','Think <script> first.')
        self.assertNotIn('<script>',html)
        self.assertIn('Collective meaning',html)

    def test_scheduled_daily_repairs_today_before_tomorrow(self):
        from scripts.generate_plain_readings import main
        class Clock:
            @staticmethod
            def now(zone): return datetime(2026,9,16,20,0,tzinfo=zone)
        with patch('scripts.generate_plain_readings.datetime',Clock), patch('scripts.generate_plain_readings.run_signs',return_value=0) as run:
            main(['--product','daily','--pause','0'])
            self.assertEqual([c.args[1] for c in run.call_args_list],[date(2026,9,16),date(2026,9,17)])

    def test_studio_preserves_clips_and_adds_seven_meanings(self):
        from scripts.generate_plain_readings import main
        with patch('scripts.generate_plain_readings.run_signs',return_value=0) as run:
            main(['--product','studio','--date','2026-09-16','--pause','0'])
            kinds=[c.args[0] for c in run.call_args_list]
            self.assertEqual(kinds.count('studio_meaning'),7)
            self.assertEqual(kinds.count('studio_daily'),7)
            self.assertEqual(kinds.count('studio_weekly'),1)
