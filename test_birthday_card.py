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
    longitude: float = 0.0
    speed: float = 0.0


@dataclass(frozen=True)
class _Aspect:
    planet1: str
    planet2: str
    name: str
    orb: float
    strength: float


@dataclass(frozen=True)
class _Snapshot:
    positions: tuple[_Position, ...]
    birth_time_known: bool
    sun_uncertain: tuple[str, ...]
    moon_uncertain: tuple[str, ...]
    aspects: tuple[_Aspect, ...] = ()


def _snapshot(known: bool = False):
    return _Snapshot(
        positions=(_Position("Sun", "Libra"), _Position("Moon", "Virgo")),
        birth_time_known=known,
        sun_uncertain=() if known else ("Libra",),
        moon_uncertain=() if known else ("Virgo",),
    )


def _timed_snapshot_with_luminary_aspects():
    return _Snapshot(
        positions=(
            _Position("Sun", "Libra", 0.0, 1.0),
            _Position("Moon", "Virgo", 60.48, 13.0),
            _Position("Jupiter", "Sagittarius", 120.8, 0.1),
        ),
        birth_time_known=True,
        sun_uncertain=(),
        moon_uncertain=(),
        aspects=(
            _Aspect("Sun", "Jupiter", "trine", 0.8, 0.9),
            _Aspect("Sun", "Moon", "sextile", 0.48, 0.8),
        ),
    )


def test_card_uses_private_year_but_hides_it_from_design():
    card = build_birthday_card(
        recipient_name="Fiona",
        birth_date=date(1995, 9, 23),
        snapshot=_snapshot(),
        poem="Words only reveal the wider possibilities waiting to be spoken.",
    )
    assert card.date_label == "23 SEPTEMBER"
    assert "1995" not in card.date_label
    assert card.sun_sign in {"Virgo", "Libra"}
    assert card.poem.endswith(".")


def test_png_is_exact_instagram_reel_size():
    card = build_birthday_card(
        recipient_name="Fiona",
        birth_date=date(1995, 9, 23),
        snapshot=_snapshot(True),
        poem="Words only reveal the wider possibilities waiting to be spoken.",
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
        poem="Questions only reveal the quiet possibilities waiting to take form.",
    )
    assert card.sun_sign == "Virgo / Libra"
    assert card.moon_label == "Virgo / Libra"
    assert card.poem.startswith("Questions only reveal")


def test_pdf_matches_the_nine_by_sixteen_card():
    card = build_birthday_card(
        recipient_name="Fiona",
        birth_date=date(1995, 9, 23),
        snapshot=_snapshot(True),
        poem="Words only reveal the wider possibilities waiting to be spoken.",
    )
    reader = PdfReader(BytesIO(render_birthday_card_pdf(card)))
    assert len(reader.pages) == 1
    page = reader.pages[0]
    assert round(float(page.mediabox.width)) == 405
    assert round(float(page.mediabox.height)) == 720
    assert birthday_card_filename(card, "png") == "luna-birthday-card-fiona.png"


def test_known_time_card_exposes_weekly_style_sun_and_moon_calculations():
    card = build_birthday_card(
        recipient_name="Fiona",
        birth_date=date(1995, 9, 23),
        snapshot=_timed_snapshot_with_luminary_aspects(),
        poem="Words only reveal the wider possibilities waiting to be spoken.",
    )
    assert card.sun_calculation == "Sun trine Jupiter · applying · 0.80° orb at birth"
    assert card.moon_calculation == "Moon sextile Sun · separating · 0.48° orb at birth"


def test_unknown_time_card_does_not_claim_exact_aspect_timing():
    card = build_birthday_card(
        recipient_name="Fiona",
        birth_date=date(1995, 9, 23),
        snapshot=_snapshot(False),
        poem="Words only reveal the wider possibilities waiting to be spoken.",
    )
    assert card.sun_calculation is None
    assert card.moon_calculation is None


def test_card_requires_generated_or_customer_supplied_poem():
    try:
        build_birthday_card(
            recipient_name="Fiona",
            birth_date=date(1995, 9, 23),
            snapshot=_snapshot(True),
            poem="",
        )
    except ValueError as exc:
        assert "poem" in str(exc).lower()
    else:
        raise AssertionError("An empty poem must never produce a canned birthday card.")
