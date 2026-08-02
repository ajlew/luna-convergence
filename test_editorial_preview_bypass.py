from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    app = (root / "app.py").read_text(encoding="utf-8")
    config = (root / "site_config.py").read_text(encoding="utf-8")
    admin = (root / "admin_console.py").read_text(encoding="utf-8")

    assert 'EDITOR_PREVIEW_ENABLED = _environment_flag("LUNA_EDITOR_PREVIEW", False)' in config
    assert 'PUBLIC_YEARLY_ENABLED = _environment_flag("LUNA_PUBLIC_YEARLY", False)' in config
    assert 'BUILD_LABEL = "Luna Active Agency Monthly v2.9.3"' in config

    assert "def editorial_preview_page()" in app
    assert '"editorial-preview"' in app
    assert "render_monthly_experience(" in app
    assert "render_yearly_experience(" in app
    assert "show_print=True" in app
    assert "preview=False" in app
    assert "Stripe is bypassed" in app
    assert "EDITORIAL_PREVIEW_REF" in app
    assert "if PUBLIC_YEARLY_ENABLED:" in app

    assert "Build: {BUILD_LABEL}" in admin

    bat_expectations = {
        "run_admin_windows.bat": ("8511", "1"),
        "run_customer_windows.bat": ("8512", "0"),
        "run_editor_preview_windows.bat": ("8513", "1"),
    }
    for filename, (port, flag) in bat_expectations.items():
        content = (root / filename).read_text(encoding="utf-8")
        assert f"--server.port {port}" in content
        assert f"set LUNA_EDITOR_PREVIEW={flag}" in content
        assert "Luna Active Agency Monthly v2.9.3" in content

    print("Public/editorial environment-gate tests passed.")


if __name__ == "__main__":
    main()
