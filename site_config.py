from __future__ import annotations

import os


def _environment_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


BRAND_NAME = "Luna Convergence"
BUILD_LABEL = "Luna Daily + Monthly Production Pass v2.9.2"

# Public deployments are customer-only by default. The Windows editorial
# launchers set LUNA_EDITOR_PREVIEW=1 so Yearly and inventory tools remain
# available for internal development without appearing on the live site.
EDITOR_PREVIEW_ENABLED = _environment_flag("LUNA_EDITOR_PREVIEW", False)
PUBLIC_YEARLY_ENABLED = _environment_flag("LUNA_PUBLIC_YEARLY", False)
MONTHLY_PREVIEW_BYPASS_ENABLED = _environment_flag(
    "LUNA_MONTHLY_PREVIEW_BYPASS",
    False,
)

TAGLINE = "The universe shifts. You’ve got this."
SUBTITLE = (
    "Daily and monthly astrology explained through planetary transitions, "
    "whole-sign houses, retrogrades and convergence points."
)

MONTHLY_PRICE = "A$4.95"
YEARLY_PRICE = "A$14.95"

DEFAULT_SIGN = "Sagittarius"
DEFAULT_TIMEZONE = "Australia/Sydney"

TIMEZONES = [
    "Australia/Sydney",
    "Australia/Melbourne",
    "Australia/Brisbane",
    "Australia/Perth",
    "Pacific/Auckland",
    "Europe/London",
    "America/New_York",
    "America/Los_Angeles",
    "UTC",
]

NAV_ITEMS = [
    "Home",
    "Daily Horoscope",
    "Reports",
    "House Guide",
    "Sample Report",
    "Solar Year",
    "How It Works",
]
