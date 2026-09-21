from pathlib import Path


APP = (Path(__file__).parent / "app.py").read_text(encoding="utf-8")


def test_admin_key_uses_secret_masked_input_and_constant_time_check():
    assert 'LUNA_ADMIN_KEY = secret("LUNA_ADMIN_KEY")' in APP
    assert 'type="password"' in APP
    assert "secrets.compare_digest(candidate, LUNA_ADMIN_KEY)" in APP
    assert 'ADMIN_SESSION_KEY = "luna-admin-authenticated-v1"' in APP


def test_owner_access_stays_on_the_customer_pages():
    assert '_admin_access_panel(f"{key_context}-paid-reports")' in APP
    assert '_admin_access_panel("birthday-card")' in APP
    assert '"Generate owner report — no payment"' in APP
    assert '"Owner copy generated. No Stripe payment was created."' in APP


def test_legacy_preview_paths_cannot_bypass_owner_authentication():
    assert '_admin_access_panel("monthly-preview")' in APP
    assert '_admin_access_panel("reports-monthly-preview")' in APP
    assert '_admin_access_panel("editorial-preview")' in APP


def test_public_paid_report_flow_still_uses_stripe():
    assert '_create_instant_checkout(order, "MONTHLY")' in APP
    assert '_create_instant_checkout(order, "YEAR")' in APP
    assert 'f"Continue to secure payment — {MONTHLY_PRICE}"' in APP
    assert 'f"Continue to secure payment — {YEARLY_PRICE}"' in APP


def test_birthday_card_has_public_paid_checkout_and_owner_bypass():
    assert '_create_instant_checkout(order, "BIRTHDAY")' in APP
    assert 'f"Continue to secure payment — {BIRTHDAY_PRICE}"' in APP
    assert '"Create owner birthday card — no payment"' in APP
    assert "Birthday Card ordering is not open yet." not in APP
