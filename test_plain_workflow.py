"""Regression tests for the current free-reading pipeline (no editorial gate)."""
from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from plain_readings import (
    WORD_RANGES, current_reading, generation_current, load_reading,
    make_reading, prompt_for, reading_html, reading_path, write_document,
)
from plain_voice_generator import GenerationError, RateLimitError, generate_text, retry_delay
from scripts.generate_plain_readings import run_signs


def packet(sign="Virgo", product="daily"):
    return {
        "product": product,
        "period": "2026-09" if product == "monthly" else "2026-09-15",
        "sign": sign,
        "timezone": "Australia/Sydney",
        "calculation_header": ["Sun sextile Mars"],
        "life_areas": ["work", "communication"],
        "events": [],
    }


BODY = (
    "Use the opening while it is useful. Let the conversation produce a practical next step, "
    "not another performance of enthusiasm. You can move with confidence without pretending "
    "every detail is settled. Check who will do what before you take on the whole arrangement.\n\n"
    "Keep your humour when the plan meets ordinary life. An impressive promise still needs "
    "someone to put it in the calendar. Ask for one clear commitment before you agree."
)


class PlainWorkflowTests(unittest.TestCase):
    def test_prose_is_preserved_without_editorial_gate(self):
        for body in (BODY, 'Short. You will definitely win.', '{"text": "hi"}'):
            with self.subTest(body=body):
                self.assertEqual(make_reading(packet(), body)["voice_body"], body)
        self.assertEqual(make_reading(packet(), '**Keep** going.')['voice_body'], 'Keep going.')

    def test_empty_prose_is_rejected_mechanically(self):
        for body in ('', '  ', '***'):
            with self.subTest(body=body), self.assertRaises(ValueError):
                make_reading(packet(), body)

    def test_render_escapes_html_and_shows_move_once(self):
        p = packet()
        p['calculation_header'] = ['<script>bad()</script>']
        html = reading_html(p, make_reading(p, BODY))
        self.assertNotIn('<script>', html)
        self.assertEqual(html.count('Ask for one clear commitment before you agree.'), 1)
        self.assertLess(html.index('Key calculations'), html.index('Luna’s reading'))
        self.assertLess(html.index('Luna’s reading'), html.index('Your move'))

    def test_missing_reading_does_not_invent_interpretation(self):
        html = reading_html(packet(), None)
        self.assertIn('Sun sextile Mars', html)
        for phrase in ('Luna’s reading', 'Your move', 'failed', 'writing service'):
            self.assertNotIn(phrase, html)

    def test_changed_facts_and_wrong_sign_invalidate_cache(self):
        with tempfile.TemporaryDirectory() as root:
            p = packet()
            path = reading_path('daily', p['period'], p['timezone'], root)
            write_document(path, {'signs': {'Virgo': make_reading(p, BODY)}})
            self.assertIsNotNone(load_reading(p, root))
            self.assertIsNone(load_reading(packet('Aries'), root))
            changed = packet()
            changed['events'] = [{'aspect': 'Sun square Mars'}]
            self.assertIsNone(load_reading(changed, root))

    def test_current_reading_checks_provenance_not_style(self):
        p = packet()
        saved = make_reading(p, 'Short. You will definitely win.')
        self.assertIsNotNone(current_reading(saved, p))
        self.assertTrue(generation_current(saved, p))
        for key, bad in [('facts_hash', 'wrong'), ('voice_version', 'old'),
                         ('status', 'failed'), ('voice_body', '   ')]:
            with self.subTest(key=key):
                self.assertIsNone(current_reading({**saved, key: bad}, p))
        self.assertFalse(generation_current({**saved, 'writing_revision': 'old'}, p))

    def test_failed_sign_retains_other_success_and_hides_exception(self):
        def generate(p):
            if p['sign'] == 'Aries':
                raise RuntimeError('SECRET_MUST_NOT_BE_SAVED')
            return BODY
        with tempfile.TemporaryDirectory() as root:
            code = run_signs('daily', date(2026, 9, 15), 'Australia/Sydney',
                             ['Aries', 'Virgo'], build=lambda prod, day, sign, tz: packet(sign),
                             generate=generate, root=root, pause=0)
            self.assertEqual(code, 1)
            self.assertIsNotNone(load_reading(packet(), root))
            path = reading_path('daily', '2026-09-15', 'Australia/Sydney', root)
            self.assertNotIn('SECRET_MUST_NOT_BE_SAVED', path.read_text(encoding='utf-8'))

    def test_targeted_retry_preserves_other_sign(self):
        with tempfile.TemporaryDirectory() as root:
            for signs in (['Virgo'], ['Aries']):
                self.assertEqual(run_signs('daily', date(2026, 9, 15), 'Australia/Sydney', signs,
                    build=lambda prod, day, sign, tz: packet(sign),
                    generate=lambda p: BODY, root=root, pause=0), 0)
            self.assertIsNotNone(load_reading(packet(), root))
            self.assertIsNotNone(load_reading(packet('Aries'), root))

    def test_no_editorial_warning_or_rewrite(self):
        short = 'Write one line. Write one line. Write one useful line before lunch.'
        with tempfile.TemporaryDirectory() as root:
            summary = Path(root) / 'summary.md'
            with patch.dict('os.environ', {'GITHUB_STEP_SUMMARY': str(summary)}):
                code = run_signs('daily', date(2026, 9, 15), 'Australia/Sydney',
                    ['Virgo'], build=lambda prod, day, sign, tz: packet(sign),
                    generate=lambda p: short, root=root, pause=0)
            saved = load_reading(packet(), root)
            self.assertEqual(code, 0)
            self.assertEqual(saved['status'], 'published')
            self.assertEqual(saved['voice_body'], short)
            self.assertNotIn('editorial_warnings', saved)
            self.assertNotIn('editorial warning', summary.read_text(encoding='utf-8').lower())

    def test_provider_does_not_request_schema_or_editorial_retry(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            'choices': [{'message': {'content': BODY}, 'finish_reason': 'stop'}]}
        post = Mock(return_value=response)
        with patch.dict('os.environ', {'LUNA_VOICE_BASE_URL': 'https://example.invalid',
                'LUNA_VOICE_MODEL': 'test', 'LUNA_VOICE_API_KEY': 'test'}):
            self.assertEqual(generate_text(packet(), post=post), BODY)
        self.assertEqual(post.call_count, 1)
        self.assertNotIn('response_format', post.call_args.kwargs['json'])

    def test_provider_rejects_empty_and_truncated_transport(self):
        with patch.dict('os.environ', {'LUNA_VOICE_BASE_URL': 'https://example.invalid',
                'LUNA_VOICE_MODEL': 'test', 'LUNA_VOICE_API_KEY': 'test'}):
            for body, finish in [('', 'stop'), (BODY, 'length')]:
                response = Mock(status_code=200)
                response.json.return_value = {
                    'choices': [{'message': {'content': body}, 'finish_reason': finish}]}
                with self.subTest(body=body, finish=finish), self.assertRaises(GenerationError):
                    generate_text(packet(), post=Mock(return_value=response))

    def test_word_ranges_are_prompt_guidance_only(self):
        self.assertEqual({k: WORD_RANGES[k] for k in ('daily', 'weekly', 'monthly')},
                         {'daily': (55, 85), 'weekly': (105, 150), 'monthly': (230, 320)})
        self.assertIn('End with one clear imperative action', prompt_for(packet()))


class GlobalRecoveryTests(unittest.TestCase):
    def test_rate_limit_waits_and_resumes(self):
        for product in ('daily', 'weekly', 'monthly'):
            with self.subTest(product=product):
                limited = Mock(status_code=429, headers={'Retry-After': '75'})
                success = Mock(status_code=200)
                success.json.return_value = {
                    'choices': [{'message': {'content': BODY}, 'finish_reason': 'stop'}]}
                post = Mock(side_effect=[limited, success])
                sleep = Mock()
                with patch.dict('os.environ', {'LUNA_VOICE_BASE_URL': 'https://example.invalid',
                        'LUNA_VOICE_MODEL': 'test', 'LUNA_VOICE_API_KEY': 'test'}):
                    self.assertEqual(generate_text(packet(product=product),
                                                   post=post, sleep=sleep), BODY)
                self.assertEqual(sum(call.args[0] for call in sleep.call_args_list), 75)
                self.assertEqual(post.call_count, 2)

    def test_later_run_skips_current_signs(self):
        for product in ('daily', 'weekly', 'monthly'):
            with self.subTest(product=product), tempfile.TemporaryDirectory() as root:
                generate = Mock(return_value=BODY)
                for _ in range(2):
                    self.assertEqual(run_signs(product, date(2026, 9, 15),
                        'Australia/Sydney', ['Virgo'], build=lambda prod, day, sign, tz: packet(sign, prod),
                        generate=generate, root=root, pause=0), 0)
                self.assertEqual(generate.call_count, 1)

    def test_long_rate_limit_and_missing_configuration_are_safe(self):
        with self.assertRaises(RateLimitError):
            retry_delay({'Retry-After': '3600'}, 0)
        self.assertEqual(retry_delay({'Retry-After': 'NaN'}, 0), 60)
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaisesRegex(GenerationError, 'missing configuration'):
                generate_text(packet(), post=lambda *a, **k: self.fail('provider should not run'))


if __name__ == '__main__':
    unittest.main()
