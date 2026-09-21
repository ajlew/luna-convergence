from pathlib import Path


APP = (Path(__file__).parent / "app.py").read_text(encoding="utf-8")


def test_birthday_card_has_public_route_and_navigation():
    assert '("birthday-card", "Birthday Card")' in APP
    assert "BIRTHDAY_CARD_REF = st.Page(" in APP
    assert 'url_path="birthday-card"' in APP
    assert "BIRTHDAY_CARD_REF," in APP


def test_birthday_card_offers_both_matching_downloads():
    assert '"Download Instagram PNG"' in APP
    assert '"Download printable PDF"' in APP
    assert "render_birthday_card_png(card)" in APP
    assert "render_birthday_card_pdf(card)" in APP
