from pathlib import Path


def test_private_monthly_preview_is_monthly_only_and_hidden():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "def monthly_preview_page()" in source
    assert "render_report_generator_workspace(monthly_only=True)" in source
    assert 'url_path="monthly-preview"' in source
    assert 'visibility="hidden"' in source
    assert "Yearly is hidden" in source


def test_preview_flag_defaults_off_and_local_launcher_enables_it():
    config = Path("site_config.py").read_text(encoding="utf-8")
    launcher = Path("run_monthly_preview_windows.bat").read_text(encoding="utf-8")
    assert '"LUNA_MONTHLY_PREVIEW_BYPASS",\n    False' in config
    assert "set LUNA_MONTHLY_PREVIEW_BYPASS=1" in launcher
    assert "set LUNA_PUBLIC_YEARLY=0" in launcher
    assert "http://localhost:8514/monthly-preview" in launcher


def test_cloud_preview_supports_pin_protection():
    source = Path("app.py").read_text(encoding="utf-8")
    assert 'secret("LUNA_MONTHLY_PREVIEW_BYPASS", "0")' in source
    assert 'secret("LUNA_MONTHLY_PREVIEW_PIN", "")' in source
    assert "secrets.compare_digest" in source
