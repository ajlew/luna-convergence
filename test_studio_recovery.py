import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch
from plain_readings import make_reading, split_move, reading_html, reading_path
from plain_voice_generator import generate_text, RateLimitError, retry_delay
from scripts.generate_plain_readings import run_signs
from studio_readings import publishing_copy, sign_card
from test_plain_workflow import BODY, packet

ENV = {'LUNA_VOICE_BASE_URL': 'https://example.invalid', 'LUNA_VOICE_MODEL': 'test', 'LUNA_VOICE_API_KEY': 'test'}

class RecoveryTests(unittest.TestCase):
    def test_revises_actual_invalid_draft_after_429(self):
        oversized = '{"story": "This is the wrong output format."}' 
        corrected = BODY + '\n\n' + BODY
        def reply(text):
            r = Mock(status_code=200)
            r.json.return_value = {'choices': [{'message': {'content': text}, 'finish_reason': 'stop'}]}
            return r
        responses = iter([reply(oversized), Mock(status_code=429, headers={'retry-after': '65'}), reply(corrected)])
        requests = []
        def post(*a, **kw):
            requests.append(copy.deepcopy(kw['json']))
            return next(responses)
        sleep = Mock()
        with patch.dict('os.environ', ENV):
            self.assertEqual(generate_text(packet(product='weekly'), post=post, sleep=sleep), corrected)
        self.assertEqual(requests[1]['messages'][2], {'role': 'assistant', 'content': oversized})
        self.assertIn('Revise the draft', requests[1]['messages'][3]['content'])
        self.assertEqual(sum(c.args[0] for c in sleep.call_args_list), 95)

    def test_rate_limit_stops_batch_preserves_successes(self):
        with tempfile.TemporaryDirectory() as root:
            generate = Mock(side_effect=[BODY, RateLimitError('quota exhausted')])
            with redirect_stderr(io.StringIO()):
                result = run_signs('daily', date(2026,9,15), 'Australia/Sydney', ['Aries','Taurus','Gemini'],
                    build=lambda product,target,sign,tz: packet(sign), generate=generate, root=root, pause=0)
            self.assertEqual(result, 2)
            self.assertEqual(generate.call_count, 2)
            doc = json.loads(reading_path('daily','2026-09-15','Australia/Sydney',root).read_text())
            self.assertIn('Aries',doc['signs'])
            self.assertNotIn('Gemini',doc['jobs'])

    def test_move_label_not_repeated(self):
        body = BODY.rsplit('Ask for',1)[0] + 'Your move: Ask for one clear commitment before you agree.'
        self.assertEqual(split_move(body)[1], 'Ask for one clear commitment before you agree.')
        self.assertEqual(reading_html(packet(), make_reading(packet(),body)).lower().count('your move'),1)

    def test_publishing_uses_saved_prose_and_selected_dates(self):
        day = date(2027,1,4)
        package = publishing_copy(day, BODY, 'https://example.invalid')
        self.assertIn('2027',package['YouTube title'])
        self.assertIn(BODY,package['YouTube description'])
        self.assertIn('https://example.invalid/weekly-view',package['YouTube description'])
        card = sign_card('Virgo',day,BODY)
        self.assertEqual(card.count('Ask for one clear commitment before you agree.'),1)
        self.assertNotIn('2026',card)

    def test_word_counts_never_reject_or_trigger_retries(self):
        from plain_readings import text_errors
        for product in ('daily', 'weekly', 'monthly', 'studio_weekly', 'studio_daily'):
            for count in (183, 218, 227):
                body = ' '.join(['Word'] * count) + '.'
                self.assertEqual(text_errors(product, body), [])
                response = Mock(status_code=200)
                response.json.return_value = {'choices': [{'message': {'content': body}, 'finish_reason': 'stop'}]}
                post = Mock(return_value=response)
                with patch.dict('os.environ', ENV):
                    self.assertEqual(generate_text(packet(product=product), post=post), body)
                self.assertEqual(post.call_count, 1)

    def test_provider_header_durations(self):
        self.assertEqual(retry_delay({'Retry-After':'1m15s'},0),75)
        self.assertEqual(retry_delay({'x-ratelimit-reset-tokens':'2m'},0),120)
        with self.assertRaises(RateLimitError):
            retry_delay({'Retry-After':'1h'},0)

if __name__ == '__main__':
    unittest.main()
