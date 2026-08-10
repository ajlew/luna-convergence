from types import SimpleNamespace
import sys

import monthly_experience_v1 as monthly


class FakeStreamlit:
    def __init__(self):
        self.html_calls = []
        self.download_calls = []
        self.captions = []
        self.warnings = []
        self.exceptions = []

    def html(self, body, **kwargs):
        self.html_calls.append((body, kwargs))

    def download_button(self, *args, **kwargs):
        self.download_calls.append((args, kwargs))

    def caption(self, text):
        self.captions.append(text)

    def warning(self, text):
        self.warnings.append(text)

    def exception(self, exc):
        self.exceptions.append(exc)


def main() -> None:
    fake = FakeStreamlit()
    sys.modules["streamlit"] = fake
    sys.modules["monthly_report_pdf_home_v3"] = SimpleNamespace(
        build_monthly_homepage_pdf=lambda *args, **kwargs: b"%PDF-1.7\nLUNA"
    )

    original_builder = monthly.build_monthly_experience_html
    monthly.build_monthly_experience_html = lambda *args, **kwargs: (
        '<div>Monthly</div><script>window.print()</script>'
    )
    try:
        narrative = SimpleNamespace(
            sign="Cancer",
            label="August 2026",
            main_focus="General overview",
            personal_question="",
        )
        result = {"timezone_name": "Australia/Sydney", "start": "2026-08-01"}

        monthly.render_monthly_experience(
            narrative,
            result,
            show_print=True,
            preview=False,
            order_reference="LC-TEST",
        )
        assert len(fake.html_calls) == 1
        assert fake.html_calls[0][1].get("unsafe_allow_javascript") is True
        assert len(fake.download_calls) == 1
        args, kwargs = fake.download_calls[0]
        assert args[0] == "Download complete monthly PDF"
        assert kwargs["data"].startswith(b"%PDF")
        assert kwargs["file_name"] == "2026-08_Cancer_Monthly.pdf"
        assert kwargs["mime"] == "application/pdf"
        assert fake.captions
        assert not fake.warnings

        fake.download_calls.clear()
        monthly.render_monthly_experience(
            narrative,
            result,
            show_print=False,
            preview=True,
        )
        assert not fake.download_calls
    finally:
        monthly.build_monthly_experience_html = original_builder

    print("Monthly print/download v3.17.1 regression test passed.")


if __name__ == "__main__":
    main()
