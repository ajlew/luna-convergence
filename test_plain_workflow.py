import ast
from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from plain_readings import (make_reading, load_reading, reading_html, reading_path,
                            text_errors, write_document, prompt_for, WORD_RANGES)
from plain_voice_generator import generate_text
from scripts.generate_plain_readings import run_signs


def packet(sign="Virgo", product="daily"):
    return {"product": product, "period": "2026-09-15", "sign": sign,
            "timezone": "Australia/Sydney", "calculation_header": ["Sun sextile Mars"],
            "life_areas": ["work", "communication"], "events": []}


BODY = (
    "Use the opening while it is useful. Let the conversation produce a practical next step, "
    "not another performance of enthusiasm. You can move with confidence without pretending "
    "every detail is settled. Check who will do what before you take on the whole arrangement.\n\n"
    "Keep your humour when the plan meets ordinary life. An impressive promise still needs "
    "someone to put it in the calendar. Ask for one clear commitment before you agree."
)


class PlainWorkflowTests(unittest.TestCase):
    def test_plain_prose(self):
        self.assertEqual(text_errors("daily", BODY), [])
        self.assertEqual(make_reading(packet(), BODY)["voice_body"], BODY)

    def test_empty_short_json_promises(self):
        for body in ("", "hello", "{\"text\": \"hi\"}", BODY + " You will definitely win."):
            self.assertTrue(text_errors("daily", body))

    def test_render_order_escaping_move_once(self):
        p = packet()
        p["calculation_header"] = ["<script>bad()</script>"]
        html = reading_html(p, make_reading(p, BODY))
        self.assertNotIn("<script>", html)
        self.assertEqual(html.count("Ask for one clear commitment before you agree."), 1)
        self.assertLess(html.index("Key calculations"), html.index("Luna’s reading"))
        self.assertLess(html.index("Luna’s reading"), html.index("Your move"))

    def test_no_fake_missing_reading(self):
        html = reading_html(packet(), None)
        self.assertIn("Sun sextile Mars", html)
        for text in ("Luna’s reading", "Your move", "failed", "writing service"):
            self.assertNotIn(text, html)

    def test_changed_facts_wrong_sign(self):
        with tempfile.TemporaryDirectory() as root:
            p = packet()
            path = reading_path("daily", p["period"], p["timezone"], root)
            write_document(path, {"signs": {"Virgo": make_reading(p, BODY)}})
            self.assertIsNotNone(load_reading(p, root))
            self.assertIsNone(load_reading(packet("Aries"), root))
            p["events"] = [{"aspect": "Sun square Mars"}]
            self.assertIsNone(load_reading(p, root))

    def test_failed_sign_retains_other_success(self):
        def generate(p):
            if p["sign"] == "Aries":
                raise RuntimeError("SECRET_MUST_NOT_BE_SAVED")
            return BODY
        with tempfile.TemporaryDirectory() as root:
            code = run_signs("daily", date(2026, 9, 15), "Australia/Sydney", ["Aries", "Virgo"],
                             build=lambda product, target, sign, tz: packet(sign),
                             generate=generate, root=root, pause=0)
            self.assertEqual(code, 1)
            self.assertIsNotNone(load_reading(packet(), root))
            path = reading_path("daily", "2026-09-15", "Australia/Sydney", root)
            self.assertNotIn("SECRET_MUST_NOT_BE_SAVED", path.read_text())

    def test_targeted_retry_preserves_other_sign(self):
        with tempfile.TemporaryDirectory() as root:
            for signs in (["Virgo"], ["Aries"]):
                self.assertEqual(run_signs("daily", date(2026, 9, 15), "Australia/Sydney", signs,
                    build=lambda product, target, sign, tz: packet(sign),
                    generate=lambda p: BODY, root=root, pause=0), 0)
            self.assertIsNotNone(load_reading(packet(), root))
            self.assertIsNotNone(load_reading(packet("Aries"), root))

    def test_provider_no_model_schema(self):
        class Response:
            status_code = 200
            def json(self):
                return {"choices": [{"message": {"content": BODY}, "finish_reason": "stop"}]}
        def post(url, **kwargs):
            self.assertNotIn("response_format", kwargs["json"])
            return Response()
        with patch.dict("os.environ", {"LUNA_VOICE_BASE_URL": "https://example.invalid",
                                       "LUNA_VOICE_MODEL": "test", "LUNA_VOICE_API_KEY": "test"}):
            self.assertEqual(generate_text(packet(), post=post), BODY)

    def test_no_public_provider_calls(self):
        source = Path("app.py").read_text()
        functions = {n.name: n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)}
        pending = ["_render_lean_daily", "weekly_page", "weekly_studio_page", "_render_monthly_transit_style_v3"]
        seen = set()
        forbidden = {"_guided_luna_copy", "_guided_luna_collection", "_calculated_luna_copy",
                     "load_daily_voice_candidate", "load_monthly_voice_candidate", "load_weekly_voice_candidate"}
        while pending:
            name = pending.pop()
            if name in seen:
                continue
            seen.add(name)
            calls = {n.func.id for n in ast.walk(functions[name])
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
            self.assertFalse(calls & forbidden, (name, calls & forbidden))
            pending.extend(c for c in calls if c in functions and c not in seen
                           and c != "_render_monthly_reader_calendar_streamlit")
        monthly = ast.get_source_segment(source, functions["_render_monthly_transit_style_v3"])
        self.assertIn("voice_items={}", monthly)
        self.assertNotIn("def _calculated_luna_copy", source)

    def test_word_ranges(self):
        self.assertEqual(WORD_RANGES, {"daily": (65, 100), "weekly": (130, 180), "monthly": (280, 380)})
        self.assertIn("End with one clear imperative action", prompt_for(packet()))

class GlobalRecoveryTests(unittest.TestCase):
    def test_rate_limit_waits_full_interval_for_every_product(self):
        from unittest.mock import Mock
        for product, repeats in (("daily", 1), ("weekly", 2), ("monthly", 4)):
            with self.subTest(product=product):
                body = "\n\n".join([BODY] * repeats)
                limited = Mock(status_code=429, headers={"Retry-After": "75"})
                success = Mock(status_code=200)
                success.json.return_value = {"choices": [{"message": {"content": body}, "finish_reason": "stop"}]}
                post = Mock(side_effect=[limited, success])
                sleep = Mock()
                with patch.dict("os.environ", {"LUNA_VOICE_BASE_URL": "https://example.invalid",
                    "LUNA_VOICE_MODEL": "test", "LUNA_VOICE_API_KEY": "test"}):
                    self.assertEqual(generate_text(packet(product=product), post=post, sleep=sleep), body)
                self.assertEqual(sum(c.args[0] for c in sleep.call_args_list), 75)
                for call in post.call_args_list:
                    self.assertNotIn("response_format", call.kwargs["json"])

    def test_later_run_does_not_regenerate_successful_signs(self):
        from unittest.mock import Mock
        for product, repeats in (("daily", 1), ("weekly", 2), ("monthly", 4)):
            with self.subTest(product=product), tempfile.TemporaryDirectory() as root:
                def build(prod, target, sign, tz):
                    p = packet(sign, prod)
                    if prod == "monthly":
                        p["period"] = "2026-09"
                    return p
                generate = Mock(return_value="\n\n".join([BODY] * repeats))
                for _ in range(2):
                    self.assertEqual(run_signs(product, date(2026, 9, 15), "Australia/Sydney", ["Virgo"],
                        build=build, generate=generate, root=root, pause=0), 0)
                self.assertEqual(generate.call_count, 1)

    def test_retired_workflows_cannot_generate_or_schedule(self):
        import yaml
        for name in ("daily-voice", "weekly-voice-preview", "monthly-voice"):
            data = yaml.safe_load(Path(f".github/workflows/generate-{name}.yml").read_text())
            self.assertNotIn("schedule", data.get("on", data.get(True)))
            self.assertNotIn("python", str(data["jobs"]))

    def test_all_legacy_scripts_use_shared_plain_entry(self):
        for product in ("daily", "weekly", "monthly"):
            source = Path(f"scripts/generate_{product}_voice.py").read_text()
            self.assertIn("from scripts.legacy_plain_entry import main", source)
            self.assertNotIn("guided", source)
        from scripts.legacy_plain_entry import main
        with patch("scripts.legacy_plain_entry.generate", return_value=0) as generate:
            main("weekly", ["--week", "2026-09-14"])
            self.assertIn("2026-09-14", generate.call_args.args[0])
            main("monthly", ["--year", "2026", "--month", "9"])
            self.assertIn("2026-09-01", generate.call_args.args[0])

    def test_long_rate_limit_and_secret_errors_are_safe(self):
        from plain_voice_generator import GenerationError, retry_delay
        with self.assertRaises(GenerationError):
            retry_delay({"Retry-After": "3600"}, 0)
        self.assertEqual(retry_delay({"Retry-After": "NaN"}, 0), 30)
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(GenerationError, "missing configuration"):
                generate_text(packet(), post=lambda *a, **k: self.fail("should not call provider"))


if __name__ == "__main__":
    unittest.main()
