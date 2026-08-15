from datetime import date

from monthly_sky_map import build_monthly_sky_snapshot, monthly_sky_map_png, monthly_sky_map_svg, snapshot_date_for_period
from monthly_experience_v1 import build_monthly_experience_html
from monthly_narrative_v1 import build_monthly_narrative
from synthesis import period_report


def _august_result(sign="Sagittarius"):
    return period_report(
        sign,
        date(2026, 8, 1),
        date(2026, 8, 31),
        "Australia/Sydney",
        "August 2026",
        transition_count=7,
    )


def test_monthly_sky_snapshot_uses_whole_sign_house_one():
    snapshot = build_monthly_sky_snapshot(_august_result("Sagittarius"))
    assert snapshot.sign == "Sagittarius"
    # Leo is Sagittarius whole-sign house 9; the August 2026 Sun is in Leo.
    assert snapshot.houses["Sun"] == 9
    assert snapshot.positions["Sun"].sign == "Leo"


def test_monthly_sky_map_has_no_natal_angles():
    snapshot = build_monthly_sky_snapshot(_august_result("Sagittarius"))
    svg = monthly_sky_map_svg(snapshot)
    assert "SAGITTARIUS SKY MAP" in svg
    assert "H1" in svg and "H9" in svg
    assert "ASC" not in svg
    assert ">MC<" not in svg


def test_free_preview_contains_sky_map_but_full_report_keeps_paid_natal_overlay_boundary():
    result = _august_result("Sagittarius")
    narrative = build_monthly_narrative(result, main_focus="General overview")
    preview_html = build_monthly_experience_html(narrative, result, show_print=False, preview=True)
    full_html = build_monthly_experience_html(narrative, result, show_print=False, preview=False)
    assert "Monthly sky snapshot" in preview_html
    assert "Geocentric tropical sky" in preview_html
    # Paid/full chronology does not gain a redundant generic sky wheel; its personal
    # natal recommendations remain the differentiator when a natal overlay is present.
    assert "Monthly sky snapshot" not in full_html


def test_snapshot_date_period_rule_is_bounded():
    # The helper always returns a date inside the requested month, regardless of now.
    chosen = snapshot_date_for_period(date(2030, 2, 1), date(2030, 2, 28), "Australia/Sydney")
    assert date(2030, 2, 1) <= chosen <= date(2030, 2, 28)


def test_free_preview_embeds_sky_wheel_as_image_data_uri():
    result = _august_result("Taurus")
    narrative = build_monthly_narrative(result, main_focus="General overview")
    preview_html = build_monthly_experience_html(narrative, result, show_print=False, preview=True)
    assert 'class="luna-sky-wheel-image"' in preview_html
    assert 'src="data:image/png;base64,' in preview_html
    sky_section = preview_html.split('Monthly sky snapshot', 1)[1].split('How August unfolds', 1)[0]
    assert '<svg' not in sky_section


def test_monthly_sky_map_png_is_valid_raster():
    import io
    from PIL import Image

    snapshot = build_monthly_sky_snapshot(_august_result("Taurus"))
    png = monthly_sky_map_png(snapshot, size=800)
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    image = Image.open(io.BytesIO(png))
    assert image.format == "PNG"
    assert image.size == (800, 800)
