"""Regression tests for Yearly must-surface event survival."""

from datetime import date

from synthesis import period_report


def _yearly_report():
    return period_report(
        sign="Libra",
        start=date(2026, 1, 1),
        end=date(2026, 12, 31),
        timezone_name="Australia/Sydney",
        period_name="2026",
    )


def _protected_identities(report):
    return {
        (
            str(event.get("event_date")),
            str(event.get("kind")),
            str(event.get("title")),
        )
        for event in report["yearly_protected_evidence"]
    }


def test_yearly_protected_eclipses_survive_strategic_compression():
    """Protected eclipses survive independently of nine-chapter compression."""
    report = _yearly_report()
    protected = _protected_identities(report)

    assert (
        "2026-08-13",
        "eclipse",
        "Total Solar Eclipse in Leo",
    ) in protected

    assert (
        "2026-08-28",
        "eclipse",
        "Partial Lunar Eclipse in Pisces",
    ) in protected

    assert len(report["strategic_chapters"]) == 9


def test_yearly_seasonal_anchors_survive_as_calculated_ingresses():
    """Registry seasonal anchors retain their underlying calculated events."""
    report = _yearly_report()
    protected = _protected_identities(report)

    expected = {
        ("2026-03-21", "ingress", "Sun enters Aries"),
        ("2026-06-22", "ingress", "Sun enters Cancer"),
        ("2026-09-23", "ingress", "Sun enters Libra"),
        ("2026-12-22", "ingress", "Sun enters Capricorn"),
    }

    assert expected <= protected
