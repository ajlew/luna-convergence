from pathlib import Path


APP = (Path(__file__).parent / "app.py").read_text(encoding="utf-8")


def test_birthday_card_has_public_route_and_navigation():
    assert '("birthday-card", "Birthday Card")' in APP
    assert "BIRTHDAY_CARD_REF = st.Page(" in APP
    assert 'url_path="birthday-card"' in APP
    assert "BIRTHDAY_CARD_REF," in APP


def test_birthday_card_offers_both_matching_downloads():
    assert '"Download Instagram Reel/Story PNG"' in APP
    assert '"Download printable PDF"' in APP
    assert "render_birthday_card_png(card)" in APP
    assert "render_birthday_card_pdf(card)" in APP


def test_birthday_card_uses_live_validated_voice_without_canned_fallback():
    assert "build_birthday_poem_facts" in APP
    assert "_cached_birthday_poem" in APP
    assert "secrets.token_hex(8)" in APP
    assert "Luna could not write a verified birthday poem" in APP
    assert "suggested_poem" not in APP


def test_unknown_birth_time_uses_date_window_luminary_calculations():
    assert "birth_date_luminary_calculations" in APP
    assert "if not time_known else None" in APP


def test_customer_can_choose_one_of_two_keepsake_backgrounds():
    assert '"Card style"' in APP
    assert '("Midnight Painted", "Ivory Letter")' in APP
    assert '"Midnight Painted": "painted_blue"' in APP
    assert '"Ivory Letter": "ivory_paper"' in APP
    assert "theme=card_theme" in APP


def test_customer_sees_matching_finished_card_samples_before_choosing():
    root = Path(__file__).parent
    assert 'st.markdown("**Choose the finished look**")' in APP
    assert '"lara-midnight-painted.png"' in APP
    assert '"lara-ivory-letter.png"' in APP
    assert '"Style samples only.' in APP
    assert (root / "assets" / "birthday-previews" / "lara-midnight-painted.png").is_file()
    assert (root / "assets" / "birthday-previews" / "lara-ivory-letter.png").is_file()


def test_public_birthday_checkout_is_fixed_at_aud_240():
    config = (Path(__file__).parent / "site_config.py").read_text(encoding="utf-8")
    assert 'BIRTHDAY_PRICE = "A$2.40"' in config
    assert 'STRIPE_BIRTHDAY_PRICE_ID = secret("STRIPE_BIRTHDAY_PRICE_ID")' in APP
    assert '_create_instant_checkout(order, "BIRTHDAY")' in APP
    assert '"value": 2.40' in APP
    assert '"currency": "AUD"' in APP


def test_paid_birthday_fulfilment_rebuilds_exact_prepared_card():
    assert 'if product_code == "BIRTHDAY":' in APP
    assert "_render_paid_birthday_card(session, metadata)" in APP
    assert 'metadata.get("birthday_poem")' in APP
    assert 'metadata.get("birthday_theme")' in APP
    assert 'key=f"paid-birthday-png-{session_id}"' in APP
    assert 'key=f"paid-birthday-pdf-{session_id}"' in APP
