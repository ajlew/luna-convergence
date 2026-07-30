from pathlib import Path


def main() -> None:
    root = Path(__file__).parent
    app = (root / "app.py").read_text(encoding="utf-8")
    admin = (root / "admin_console.py").read_text(encoding="utf-8")
    requirements = (root / "requirements.txt").read_text(encoding="utf-8")

    assert '"Main focus"' in app
    assert '"Optional personal question"' in app
    assert '"Main priority for the year"' in app
    assert '"Optional decision or transition"' in app
    assert "Please allow up to 24 hours for delivery" in app
    assert "main_focus=main_focus" in app
    assert "personal_question=personal_question" in app
    assert "order_payload_json(order)" in app
    assert "order_details_mailto(CONTACT_EMAIL, order)" in app

    assert "Download print-ready personalised PDF" in admin
    assert "build_report_pdf" in admin
    assert "Customer main focus" in admin
    assert "Customer personal question" in admin
    assert "reportlab" in requirements.lower()

    print("Paid-order app integration checks passed.")


if __name__ == "__main__":
    main()
