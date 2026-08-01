from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    admin = (root / "admin_console.py").read_text(encoding="utf-8")

    assert "build_monthly_narrative" in admin
    assert "render_monthly_experience" in admin
    assert "Customer webpage preview" in admin
    assert "Internal backup and calculation output" in admin
    assert 'result.get("period") == "monthly"' in admin

    print("Admin customer-monthly-webpage test passed.")


if __name__ == "__main__":
    main()
