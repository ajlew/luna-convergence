from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    app = (root / "app.py").read_text(encoding="utf-8")
    admin = (root / "admin_console.py").read_text(encoding="utf-8")
    config = (root / "site_config.py").read_text(encoding="utf-8")

    assert 'BUILD_LABEL = "Full Report Print Portal v2.5"' in config
    assert "def render_report_generator_workspace()" in app
    assert "def reports_page()" in app
    assert "Generate the complete report" in app
    assert "render_report_generator_workspace()" in app
    assert "Generate customer report" in app
    assert "render_monthly_experience(" in app
    assert "show_print=True" in app
    assert "preview=False" in app
    assert "render_yearly_experience(" in app

    assert "Luna Engine Diagnostics" in admin
    assert "Developer-only" in admin

    launchers = {
        "run_admin_windows.bat": ("app.py", "8511", "/reports"),
        "run_customer_windows.bat": ("app.py", "8512", "/"),
        "run_editor_preview_windows.bat": ("app.py", "8513", "/reports"),
        "run_engine_windows.bat": ("admin_console.py", "8514", ""),
    }
    for filename, (script, port, route) in launchers.items():
        content = (root / filename).read_text(encoding="utf-8")
        assert script in content
        assert f"--server.port {port}" in content
        if route:
            assert f"http://localhost:{port}{route}" in content

    print("Unified reports entry tests passed.")


if __name__ == "__main__":
    main()
