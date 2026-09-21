from dataclasses import dataclass
from datetime import date
from io import BytesIO

from PIL import Image
from pypdf import PdfReader

from birthday_card import (
    SOCIAL_SIZE,
    birthday_card_filename,
    build_birthday_card,
    render_birthday_card_pdf,
    render_birthday_card_png,
)


@dataclass(frozen=True)
class _Position:
    planet: str
    sign: str


@dataclass(frozen=True)
class _Snapshot:
    positions: tuple[_Position, ...]
    birth_time_known: bool
    sun_uncertain: tuple[str, ...]
    moon_uncertain: tuple[str, ...]


def _snapshot(known: bool = False):
    return _Snapshot(
        positions=(_Position("Sun", "Libra"), _Position("Moon", "Virgo")),
        birth_time_known=known,
        sun_uncertain=() if known else ("Libra",),
        moon_uncertain=() if known else ("Virgo",),
    )


def test_card_uses_private_year_but_hides_it_from_design():
    card = build_birthday_card(
        recipient_name="Fiona",
        birth_date=date(1995, 9, 23),
        snapshot=_snapshot(),
    )
    assert card.date_label == "23 SEPTEMBER"
    assert "1995" not in card.date_label
    assert card.sun_sign in {"Virgo", "Libra"}
    assert card.poem.endswith(".")


def test_png_is_exact_instagram_portrait_size():
    card = build_birthday_card(
        recipient_name="Fiona",
        birth_date=date(1995, 9, 23),
        snapshot=_snapshot(True),
    )
    image = Image.open(BytesIO(render_birthday_card_png(card)))
    assert image.size == SOCIAL_SIZE
    assert image.mode == "RGB"


def test_unknown_cusp_time_does_not_guess_a_sun_or_moon_sign():
    snapshot = _Snapshot(
        positions=(_Position("Sun", "Libra"), _Position("Moon", "Virgo")),
        birth_time_known=False,
        sun_uncertain=("Virgo", "Libra"),
        moon_uncertain=("Virgo", "Libra"),
    )
    card = build_birthday_card(
        recipient_name="Fiona",
        birth_date=date(1995, 9, 23),
        snapshot=snapshot,
    )
    assert card.sun_sign == "Virgo / Libra"
    assert card.moon_label == "Virgo / Libra"
    assert card.poem.startswith("The sky only reveals")


def test_pdf_is_one_eight_by_ten_page():
    card = build_birthday_card(
        recipient_name="Fiona",
        birth_date=date(1995, 9, 23),
        snapshot=_snapshot(True),
    )
    reader = PdfReader(BytesIO(render_birthday_card_pdf(card)))
    assert len(reader.pages) == 1
    page = reader.pages[0]
    assert round(float(page.mediabox.width)) == 576
    assert round(float(page.mediabox.height)) == 720
    assert birthday_card_filename(card, "png") == "luna-birthday-card-fiona.png"
