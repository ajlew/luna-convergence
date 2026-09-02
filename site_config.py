from __future__ import annotations

BRAND_NAME = "Luna Convergence"
BUILD_LABEL = "Luna v3.33 — Voice Composer Preview"
EDITOR_PREVIEW_ENABLED = False  # Public paid launch: no editorial/Stripe bypass.
TAGLINE = "The universe shifts. You’ve got this."
SUBTITLE = (
    "Daily, monthly and yearly astrology explained through planetary transitions, "
    "whole-sign houses, retrogrades and convergence points."
)

MONTHLY_PRICE = "A$3.30"
YEARLY_PRICE = "A$14.95"

# Public sign selectors start neutral.  A sign must come from the visitor,
# a verified birth date, or an explicit route/query value; the app must never
# silently build a reading for an arbitrary zodiac sign.
DEFAULT_SIGN = None
DEFAULT_TIMEZONE = "Australia/Sydney"

TIMEZONES = [
    "Australia/Sydney",
    "Australia/Melbourne",
    "Australia/Brisbane",
    "Australia/Perth",
    "Australia/Adelaide",
    "Australia/Hobart",
    "Australia/Darwin",
    "Pacific/Auckland",
    "Pacific/Port_Moresby",
    "Europe/London",
    "Europe/Dublin",
    "Europe/Paris",
    "Europe/Berlin",
    "Europe/Rome",
    "America/New_York",
    "America/Chicago",
    "America/Los_Angeles",
    "America/Toronto",
    "America/Vancouver",
    "America/Mexico_City",
    "America/Sao_Paulo",
    "America/Argentina/Buenos_Aires",
    "Africa/Johannesburg",
    "Asia/Singapore",
    "Asia/Tokyo",
    "Asia/Seoul",
    "Asia/Kolkata",
    "Asia/Dubai",
    "Pacific/Fiji",
    "Asia/Manila",
    "Asia/Jakarta",
    "Asia/Bangkok",
    "Asia/Kuala_Lumpur",
    "Asia/Hong_Kong",
    "Asia/Taipei",
    "Asia/Kathmandu",
    "Asia/Dhaka",
    "Asia/Karachi",
    "Africa/Cairo",
    "Asia/Amman",
    "Asia/Baghdad",
    "Asia/Beirut",
    "UTC",
]

NAV_ITEMS = [
    "Home",
    "Daily Horoscope",
    "Weekly View",
    "Reports",
    "12-Month Map",
    "House Guide",
    "Sample Report",
    "Solar Year",
    "How It Works",
]
