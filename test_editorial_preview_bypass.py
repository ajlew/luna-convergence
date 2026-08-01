from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    app = (root / "app.py").read_text(encoding="utf-8")
    config = (root / "site_config.py").read_text(encoding="utf-8")
    admin = (root / "admin_console.py").read_text(encoding="utf-8")

    assert 'EDITOR_PREVIEW_ENABLED = True' in config
    assert 'BUILD_LABEL = "Automatic References + Luna Wit v2.3"' in config

    assert "def editorial_preview_page()" in app
    assert '"editorial-preview"' in app
    assert "render_monthly_experience(" in app
    assert "render_yearly_experience(" in app
    assert "show_print=True" in app
    assert "preview=False" in app
    assert "Stripe is bypassed" in app
    assert "Checkout is temporarily hidden" in app
    assert "EDITORIAL_PREVIEW_REF" in app

    assert "Build: {BUILD_LABEL}" in admin

    bat_expectations = {
        "run_admin_windows.bat": ("8511", "app.py"),
        "run_customer_windows.bat": ("8512", "app.py"),
        "run_editor_preview_windows.bat": ("8513", "app.py"),
    }
    for filename, (port, script) in bat_expectations.items():
        content = (root / filename).read_text(encoding="utf-8")
        assert f"--server.port {port}" in content
        assert script in content
        assert "Automatic References + Luna Wit v2.3" in content

    print("Editorial preview bypass tests passed.")


if __name__ == "__main__":
    main()
