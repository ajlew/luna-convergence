from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    admin = (root / "admin_console.py").read_text(encoding="utf-8")

    assert "render_monthly_experience" in admin
    assert "Customer webpage preview" in admin
    assert "Download customer webpage" in admin
    assert "Print or save report" in admin
    assert "Internal backup and calculation output" in admin
    assert "Download legacy backup PDF" in admin
    assert "customer webpage or printed report" in admin

    monthly_section = admin.split(
        'if result.get("period") == "monthly":',
        1,
    )[1].split("else:", 1)[0]
    assert "render_monthly_experience" in monthly_section
    assert "Download print-ready personalised PDF" not in monthly_section

    print("Admin monthly webpage flow tests passed.")


if __name__ == "__main__":
    main()
