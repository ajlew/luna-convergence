from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    admin = (root / "admin_console.py").read_text(encoding="utf-8")

    assert "build_yearly_experience_html" in admin
    assert "render_yearly_experience" in admin
    assert 'result.get("period") == "yearly"' in admin
    assert "Customer year-ahead webpage" in admin
    assert "Download customer webpage" in admin
    assert "Download legacy backup PDF" in admin

    print("Admin yearly webpage flow tests passed.")


if __name__ == "__main__":
    main()
