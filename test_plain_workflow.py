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


if __name__ == "__main__":
    unittest.main()
