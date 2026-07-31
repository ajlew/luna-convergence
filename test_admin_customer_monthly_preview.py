from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    admin = (root / "admin_console.py").read_text(encoding="utf-8")

    assert "build_monthly_narrative" in admin
    assert "monthly_narrative_markdown" in admin
    assert "Customer-facing monthly preview" in admin
    assert "Raw calculation output" in admin
    assert 'result.get("period") == "monthly"' in admin
    assert "The customer PDF could not be generated" in admin

    print("Admin customer-monthly-preview test passed.")


if __name__ == "__main__":
    main()
