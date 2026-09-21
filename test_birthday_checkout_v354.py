from pathlib import Path

from stripe_checkout import StripeCheckoutError, order_metadata, verify_one_time_price


ROOT = Path(__file__).parent
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_birthday_fulfilment_fields_survive_stripe_metadata_round_trip():
    order = {
        "product_code": "BIRTHDAY",
        "report_name": "Personalised Astrology Birthday Card",
        "timezone": "Australia/Sydney",
        "reference": "LC-BIRTHDAY-VIRGO-1965-12-01-TEST",
        "birthday_name": "Alan",
        "birthday_date": "1965-12-01",
        "birthday_time_known": "false",
        "birthday_time": "",
        "birthday_theme": "painted_blue",
        "birthday_poem": "A quiet horizon only opens when brave wonder chooses its next dawn.",
    }
    metadata = order_metadata(order)
    for key in (
        "birthday_name",
        "birthday_date",
        "birthday_time_known",
        "birthday_theme",
        "birthday_poem",
    ):
        assert metadata[key] == order[key]


def test_customer_never_receives_download_before_verified_payment():
    public_checkout = APP.index('order["checkout_url"] = _create_instant_checkout(order, "BIRTHDAY")')
    success_fulfilment = APP.index("def _render_paid_birthday_card")
    payment_verification = APP.index("if not checkout_is_paid(session):")
    success_dispatch = APP.index('_render_paid_birthday_card(session, metadata)')
    assert public_checkout > 0
    assert success_fulfilment > 0
    assert payment_verification < success_dispatch
    assert 'st.session_state.pop("birthday-card-result-v1", None)' in APP


def test_birthday_cancel_returns_to_birthday_page():
    assert '("/birthday-card" if str(product_code).upper() == "BIRTHDAY" else "/reports")' in APP


def test_birthday_price_verification_rejects_wrong_amount(monkeypatch=None):
    import stripe_checkout

    original = stripe_checkout._request
    stripe_checkout._request = lambda *args, **kwargs: {
        "unit_amount": 595,
        "currency": "aud",
        "recurring": None,
    }
    try:
        try:
            verify_one_time_price(
                "sk_test_value",
                "price_test_value",
                expected_unit_amount=240,
                expected_currency="aud",
            )
        except StripeCheckoutError as exc:
            assert "AUD 2.40" in str(exc)
        else:
            raise AssertionError("A wrong Stripe amount must block checkout.")
    finally:
        stripe_checkout._request = original
