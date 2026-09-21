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
