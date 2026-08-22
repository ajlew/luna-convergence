from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
import json
import secrets
from calendar import month_name
from pathlib import Path
from zoneinfo import ZoneInfo
from html import escape
import base64
from PIL import Image

import streamlit as st

from astrology_engine import SIGNS, HOUSE_NAMES
from customer_experience import (
    HOUSE_VOICE,
    free_daily_reading,
    prepared_order_email,
)
from synthesis import house_reference_matrix, house_aware_conclusion, period_report
from interpretation_library import HOUSE_STRATEGY
from daily_narrative_v3 import (
    build_daily_narrative,
    reading_comparison_text,
    render_daily_narrative_v3,
)
from monthly_narrative_v1 import build_monthly_narrative
from monthly_experience_v1 import render_monthly_experience
from monthly_report_pipeline import (
    build_production_monthly_report,
    render_production_monthly_report,
)
from yearly_experience_v1 import render_yearly_experience
from forecast_inventory import EDITORIAL_STATUSES, build_inventory, inventory_json
from ephemeris_admin import render_ephemeris_admin
from luna_voice import narrator_principle, voice_profile
from solar_cycle import (
    CITY_LOCATIONS,
    city_input_help,
    daily_solar_convergence,
    representative_city_name,
    resolve_location,
    solar_gate_label,
)
from natal_snapshot import (
    build_natal_snapshot,
    natal_wheel_svg,
    encode_natal_profile,
    natal_profile_summary,
)
from monthly_natal_overlay import build_monthly_natal_overlay
from concentration_theme import build_monthly_concentration_theme
from solar_year_wave import solar_year_wave_svg
from weekly_view import (
    all_video_copy,
    build_weekly_view,
    default_week_start,
    monday_for,
    week_label,
)
from timing_map import (
    build_timing_map,
    month_intensity,
)
from order_capture import (
    MONTHLY_FOCUS_CHOICES,
    QUESTION_MAX_CHARS,
    YEARLY_FOCUS_CHOICES,
    build_order_reference,
    default_month_label,
    default_year,
    month_choices,
    valid_email,
    year_choices,
)
from stripe_checkout import (
    StripeCheckoutError,
    checkout_amount,
    checkout_email,
    checkout_is_paid,
    checkout_metadata,
    create_checkout_session,
    resolve_price_id,
    retrieve_checkout_session,
)
from email_delivery import send_report_email
from report_pdf import build_report_pdf, report_filename
from site_config import (
    BRAND_NAME,
    BUILD_LABEL,
    EDITOR_PREVIEW_ENABLED,
    TAGLINE,
    SUBTITLE,
    MONTHLY_PRICE,
    YEARLY_PRICE,
    DEFAULT_SIGN,
    DEFAULT_TIMEZONE,
    TIMEZONES,
    NAV_ITEMS,
)


ASSET_DIR = Path(__file__).parent / "assets"
FAVICON_PATH = ASSET_DIR / "saturn_hex_favicon.png"
BRAND_ICON_PATH = ASSET_DIR / "saturn_hex_brand.png"
WEEKLY_BACKGROUND_PATH = ASSET_DIR / "luna_weekly_video_background_1080x1920.png"

st.set_page_config(
    page_title=f"{BRAND_NAME} | Strategic Horoscopes",
    page_icon=Image.open(FAVICON_PATH),
    layout="wide",
    initial_sidebar_state="collapsed",
)


def secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default
    return str(value or default)


MONTHLY_PAYMENT_URL = secret("STRIPE_MONTHLY_URL")
YEARLY_PAYMENT_URL = secret("STRIPE_YEARLY_URL")
STRIPE_SECRET_KEY = secret("STRIPE_SECRET_KEY")
STRIPE_MONTHLY_PRICE_ID = secret("STRIPE_MONTHLY_PRICE_ID")
STRIPE_YEARLY_PRICE_ID = secret("STRIPE_YEARLY_PRICE_ID")
RESEND_API_KEY = secret("RESEND_API_KEY")
RESEND_FROM = secret("RESEND_FROM")
SMTP_USER = secret("SMTP_USER")
SMTP_APP_PASSWORD = secret("SMTP_APP_PASSWORD")
SMTP_FROM = secret("SMTP_FROM")
REPORT_REQUEST_URL = secret("REPORT_REQUEST_URL")
NEWSLETTER_URL = secret("NEWSLETTER_URL")
CONTACT_EMAIL = secret("CONTACT_EMAIL", "your-email@example.com")
GA_MEASUREMENT_ID = secret("GA_MEASUREMENT_ID", "G-TE5HPKV94D")
GOOGLE_ADS_ID = secret("GOOGLE_ADS_ID", "AW-18379683881")
GOOGLE_ADS_PURCHASE_LABEL = secret("GOOGLE_ADS_PURCHASE_LABEL")
STATCOUNTER_PROJECT_ID = secret("STATCOUNTER_PROJECT_ID")
STATCOUNTER_SECURITY_CODE = secret("STATCOUNTER_SECURITY_CODE")
LUNA_YOUTUBE_CHANNEL_URL = secret("LUNA_YOUTUBE_CHANNEL_URL")
LUNA_YOUTUBE_FEATURED_VIDEO_URL = secret("LUNA_YOUTUBE_FEATURED_VIDEO_URL")
PUBLIC_SITE_URL = "https://luna-convergence.streamlit.app"
DAILY_PAGE_REF = None


def browser_timezone_name() -> str:
    """Return the visitor's browser timezone, with Luna's default as fallback."""
    try:
        timezone_name = str(st.context.timezone or "").strip()
        if timezone_name:
            ZoneInfo(timezone_name)  # Validate the IANA timezone name.
            return timezone_name
    except Exception:
        pass
    return DEFAULT_TIMEZONE


def browser_local_now() -> datetime:
    """Return the current real-world time converted to the visitor's timezone."""
    return datetime.now(timezone.utc).astimezone(ZoneInfo(browser_timezone_name()))


def browser_local_date() -> date:
    """Return today's calendar date for the visitor, not the Streamlit server."""
    return browser_local_now().date()


def timezone_select_index() -> int:
    """Select the browser timezone when Luna offers it, otherwise use the default."""
    timezone_name = browser_timezone_name()
    if timezone_name in TIMEZONES:
        return TIMEZONES.index(timezone_name)
    return TIMEZONES.index(DEFAULT_TIMEZONE)


def browser_time_caption() -> str:
    """Human-readable browser-local date and time for transparent date selection."""
    local_now = browser_local_now()
    return (
        f"Device timezone detected: {browser_timezone_name()} · "
        f"{local_now.strftime('%A, %d %B %Y · %I:%M %p')}"
    )


def install_css() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,400;6..96,500;6..96,600&family=IBM+Plex+Mono:wght@400;500;600&family=Josefin+Sans:wght@300;400;500;600;700&display=swap');

:root {
    --white: #ffffff;
    --black: #050505;
    --ink: #151515;
    --soft: #f5f5f2;
    --line: #d8d8d3;
    --muted: #696963;
}

*, *::before, *::after {
    box-sizing:border-box;
}

html,
body,
#root,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    width:100%;
    max-width:100%;
    overflow-x:hidden !important;
}

html, body, [class*="css"] {
    color: var(--ink);
    font-family: "Josefin Sans", "Avenir Next", "Century Gothic", Arial, sans-serif;
}

.stApp {
    min-height:100vh;
    min-height:100dvh;
    background: var(--white);
}

[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"],
[data-testid="column"] {
    min-width:0 !important;
    max-width:100%;
}

img, svg, canvas, video {
    max-width:100%;
    height:auto;
}

table {
    max-width:100%;
}

input, textarea, select {
    font-size:16px !important;
}

button, a, summary {
    touch-action:manipulation;
}

.block-container {
    width:100%;
    max-width:1280px;
    min-height:100vh;
    min-height:100dvh;
    padding-top:2.2rem;
    padding-bottom:calc(5rem + env(safe-area-inset-bottom, 0px));
    padding-left:max(clamp(1rem,4vw,4.5rem), env(safe-area-inset-left, 0px));
    padding-right:max(clamp(1rem,4vw,4.5rem), env(safe-area-inset-right, 0px));
}

header[data-testid="stHeader"] {
    display:none !important;
    height:0 !important;
}

#MainMenu,
footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
.stDeployButton {
    visibility:hidden !important;
    display:none !important;
}

h1, h2, h3, h4,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {
    color:var(--black) !important;
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, "Times New Roman", serif !important;
    font-optical-sizing:auto;
    font-weight:500 !important;
    letter-spacing:-.035em !important;
}

h1,
[data-testid="stMarkdownContainer"] h1 {
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, "Times New Roman", serif !important;
    font-size:clamp(3rem, 7vw, 7.1rem) !important;
    line-height:.94 !important;
    max-width: 1120px;
    margin-top: .5rem !important;
    margin-bottom: 1.4rem !important;
}

h2,
[data-testid="stMarkdownContainer"] h2 {
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, "Times New Roman", serif !important;
    font-size:clamp(2rem, 4vw, 4rem) !important;
    line-height:1.02 !important;
    margin-top: 2.6rem !important;
}

h3,
[data-testid="stMarkdownContainer"] h3 {
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, "Times New Roman", serif !important;
    font-size:clamp(1.35rem, 2vw, 2rem) !important;
    line-height:1.12 !important;
}

p, li {
    font-family: "Josefin Sans", "Avenir Next", "Century Gothic", Arial, sans-serif;
    font-size: 1.08rem;
    line-height: 1.62;
    font-weight: 400;
}

a {
    color: var(--black);
}

.brand-row {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:1rem;
    min-height:3rem;
    padding:.15rem 0 .9rem;
    background:#ffffff !important;
    position:relative;
    z-index:20;
}

.brand-row,
.brand-row div,
.brand-row span,
.brand-row img {
    color:#000000 !important;
    opacity:1 !important;
    filter:none !important;
    mix-blend-mode:normal !important;
    visibility:visible !important;
}

.brand-lockup {
    display:flex;
    align-items:center;
    gap:.75rem;
}

.brand-name {
    color:var(--black) !important;
    opacity:1 !important;
    font-family:"Josefin Sans", sans-serif;
    font-size:1.05rem;
    font-weight:600;
    letter-spacing:.17em;
    text-transform:uppercase;
    white-space:nowrap;
}

.brand-icon {
    width:2.35rem;
    height:2.35rem;
    display:block;
    opacity:1 !important;
    filter:none !important;
}

.brand-note {
    color:var(--black) !important;
    opacity:.68 !important;
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.69rem;
    letter-spacing:.04em;
    text-transform:uppercase;
}

.eyebrow,
.mono-label {
    color:var(--black);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-weight:500;
    letter-spacing:.055em;
    text-transform:uppercase;
    font-size:.73rem;
}

.editorial-title {
    margin:.45rem 0 1.35rem;
    color:#050505 !important;
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, "Times New Roman", serif !important;
    font-size:clamp(3rem, 7vw, 7.1rem);
    line-height:.94;
    font-weight:500;
    letter-spacing:-.045em;
}

.hero-subtitle {
    max-width:850px;
    color:var(--ink);
    font-size:clamp(1.14rem, 1.8vw, 1.45rem);
    line-height:1.5;
    font-weight:350;
}

.hero-rule {
    border-top:1px solid var(--black);
    margin:1.4rem 0 2rem;
}

.card {
    background:var(--white);
    border:1px solid var(--black);
    border-radius:0;
    padding:1.55rem;
    box-shadow:none;
    height:100%;
}

.card h3 {
    margin-top:.5rem;
}

.reading-card {
    background:var(--black);
    color:var(--white);
    border:1px solid var(--black);
    border-radius:0;
    padding:clamp(1.4rem, 3vw, 2.4rem);
    box-shadow:none;
    position:relative;
    overflow:hidden;
}

.reading-card::after {
    content:"";
    position:absolute;
    width:10rem;
    height:10rem;
    border:1px solid rgba(255,255,255,.36);
    transform:rotate(30deg);
    right:-4rem;
    bottom:-5rem;
}

.reading-card h3,
.reading-card p,
.reading-card strong {
    color:var(--white);
}

.reading-card .eyebrow {
    color:var(--white) !important;
}

.reading-card .muted-white {
    color:rgba(255,255,255,.76);
}

.daily-kicker {
    color:rgba(255,255,255,.78);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.68rem;
    letter-spacing:.04em;
    text-transform:uppercase;
}

.daily-headline {
    position:relative;
    z-index:2;
    color:var(--white) !important;
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, serif !important;
    font-size:clamp(2.6rem, 5.5vw, 5.6rem);
    line-height:.94;
    letter-spacing:-.045em;
    margin:.65rem 0 1rem;
    max-width:900px;
}

.daily-date {
    position:relative;
    z-index:2;
    color:rgba(255,255,255,.72);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.68rem;
    text-transform:uppercase;
}

.forecast-copy {
    max-width:860px;
    margin:2rem auto;
}

.forecast-copy p {
    font-family:"Josefin Sans", sans-serif;
    font-size:clamp(1.16rem, 1.7vw, 1.38rem);
    line-height:1.68;
    font-weight:350;
}

.relationship-card {
    border:1px solid var(--black);
    padding:1.35rem;
    margin:2rem 0;
    background:var(--soft);
}

.relationship-card h3 {
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, serif;
    font-size:2rem;
    line-height:1.05;
    margin:.4rem 0 .8rem;
}

.relationship-card p {
    font-family:"Josefin Sans", sans-serif;
    font-size:1.08rem;
    line-height:1.62;
    margin:0;
}

.best-move {
    border-top:1px solid var(--black);
    border-bottom:1px solid var(--black);
    padding:1.25rem 0;
    margin:2.1rem 0;
    display:grid;
    grid-template-columns:10rem 1fr;
    gap:1.2rem;
}

.best-move-label {
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.7rem;
    text-transform:uppercase;
}

.best-move-copy {
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, serif;
    font-size:1.55rem;
    line-height:1.25;
}

.question-list {
    display:grid;
    grid-template-columns:repeat(2, minmax(0,1fr));
    border-top:1px solid var(--black);
    border-left:1px solid var(--black);
}

.question-item {
    border-right:1px solid var(--black);
    border-bottom:1px solid var(--black);
    padding:1.2rem;
    min-height:8.5rem;
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, serif;
    font-size:1.33rem;
    line-height:1.25;
}

.area-strip {
    display:grid;
    grid-template-columns:repeat(3, minmax(0,1fr));
    border-top:1px solid var(--black);
    border-bottom:1px solid var(--black);
    margin:2.4rem 0;
}

.area-note {
    border-right:1px solid var(--black);
    padding:1.2rem;
}

.area-note:last-child {
    border-right:none;
}

.area-note p {
    font-size:1rem;
    line-height:1.5;
    margin-bottom:0;
}

.technical-line {
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.73rem;
    line-height:1.65;
}

@media (max-width: 700px) {
    .best-move {
        grid-template-columns:1fr;
        gap:.45rem;
    }
    .question-list {
        grid-template-columns:1fr;
    }
    .area-strip {
        grid-template-columns:1fr;
    }
    .area-note {
        border-right:none;
        border-bottom:1px solid var(--black);
    }
    .area-note:last-child {
        border-bottom:none;
    }
}

.price {
    font-family:"Josefin Sans", sans-serif;
    font-size:2.8rem;
    line-height:1;
    font-weight:500;
    margin:.6rem 0 1rem;
}

.pill {
    display:inline;
    padding:0;
    margin:0;
    border:0;
    background:transparent;
    color:var(--muted);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.67rem;
    font-weight:500;
    letter-spacing:.025em;
    text-transform:uppercase;
}

.pill + .pill::before {
    content:"·";
    display:inline-block;
    margin:0 .55rem;
    color:var(--muted);
    font-weight:400;
}

.trust-strip {
    display:grid;
    grid-template-columns:repeat(4, minmax(0,1fr));
    border-top:1px solid var(--black);
    border-bottom:1px solid var(--black);
    margin:2.4rem 0;
}

.trust-item {
    border-right:1px solid var(--black);
    background:var(--white);
    padding:1rem .85rem;
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.68rem;
    line-height:1.4;
    text-transform:uppercase;
    letter-spacing:.03em;
}

.trust-item:last-child {
    border-right:none;
}

.section-spacer {
    height:2.8rem;
}

.callout {
    border:1px solid var(--black);
    background:var(--soft);
    padding:1.2rem 1.35rem;
    border-radius:0;
}

.small-note {
    color:var(--muted);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.7rem;
    line-height:1.5;
}

.top-nav {
    display:flex;
    align-items:center;
    flex-wrap:wrap;
    gap:0;
    border-top:1px solid var(--black);
    border-bottom:1px solid var(--black);
    margin:.2rem 0 2.6rem;
}

.top-nav a {
    display:flex;
    align-items:center;
    gap:.48rem;
    min-height:2.75rem;
    padding:.15rem .82rem;
    color:var(--black) !important;
    text-decoration:none !important;
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.67rem;
    letter-spacing:.015em;
    text-transform:uppercase;
    white-space:nowrap;
}

.top-nav a:hover {
    background:var(--soft);
}

.mobile-nav {
    display:none;
    width:100%;
    margin:.15rem 0 1.2rem;
    border-top:1px solid var(--black);
    border-bottom:1px solid var(--black);
}
.mobile-nav summary {
    display:flex;
    align-items:center;
    justify-content:space-between;
    min-height:2.9rem;
    list-style:none;
    cursor:pointer;
    font-family:"IBM Plex Mono","Courier New",monospace;
    font-size:.68rem;
    letter-spacing:.03em;
    text-transform:uppercase;
}
.mobile-nav summary::-webkit-details-marker {
    display:none;
}
.mobile-nav summary::after {
    content:"+";
    font-size:1rem;
}
.mobile-nav[open] summary::after {
    content:"−";
}
.mobile-nav-grid {
    display:grid;
    grid-template-columns:1fr 1fr;
    padding:.45rem 0 .85rem;
    border-top:1px solid var(--line);
}
.mobile-nav-grid a {
    min-width:0;
    padding:.7rem .45rem .7rem 0;
    color:var(--black) !important;
    text-decoration:none !important;
    font-family:"IBM Plex Mono","Courier New",monospace;
    font-size:.66rem;
    line-height:1.35;
    text-transform:uppercase;
}
.mobile-nav-grid a.active {
    font-weight:600;
}

.nav-dot {
    width:.72rem;
    height:.72rem;
    border:1px solid var(--line);
    border-radius:50%;
    display:inline-block;
    background:var(--white);
}

.top-nav a.active .nav-dot {
    border-color:var(--black);
    box-shadow:inset 0 0 0 .23rem var(--black);
}

.solar-year-wave-wrap {
    max-width:760px;
    margin:.25rem auto .8rem;
    padding:.15rem 0 .25rem;
}

.solar-year-wave {
    width:100%;
    height:auto;
    display:block;
    overflow:visible;
}

.solar-year-wave-wrap.compact {
    margin:.05rem auto .35rem;
    padding:0;
    opacity:.82;
}

.daily-sign-picker-label {
    max-width:760px;
    margin:.45rem auto .35rem;
    color:var(--muted);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.66rem;
    letter-spacing:.045em;
    text-transform:uppercase;
}

.lean-daily {
    max-width:760px;
    margin:0 auto;
    padding:1.3rem 0 4.5rem;
}

.lean-daily-meta {
    display:flex;
    align-items:baseline;
    justify-content:space-between;
    gap:1rem;
    margin:1.4rem 0 2.8rem;
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.72rem;
    letter-spacing:.035em;
    text-transform:uppercase;
}

.lean-daily h1 {
    max-width:720px;
    margin:0 0 2.35rem !important;
    font-size:clamp(3.5rem, 8vw, 6.5rem) !important;
    line-height:.94 !important;
}

.lean-daily-story {
    max-width:680px;
    margin-bottom:3.25rem;
}

.lean-daily-story p {
    margin:0 0 1.35rem;
    font-size:clamp(1.08rem, 2vw, 1.24rem);
    line-height:1.72;
}

.lean-daily-move {
    max-width:680px;
    padding:1.55rem 0 1.35rem;
    border-top:1px solid var(--black);
    border-bottom:1px solid var(--line);
}

.lean-daily-label,
.lean-daily-empty {
  max-width: 700px;
  margin: 2.4rem auto 0;
  color: #6f6f6f;
  font-size: 0.82rem;
  letter-spacing: 0.02em;
}

.lean-daily-reset {
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.69rem;
    letter-spacing:.045em;
    text-transform:uppercase;
}

.lean-daily-move p {
    margin:.55rem 0 0;
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, serif;
    font-size:clamp(1.45rem, 3vw, 2.05rem);
    line-height:1.25;
}

.lean-daily-question {
    max-width:660px;
    margin:2.9rem 0 2.7rem;
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, serif;
    font-size:clamp(1.45rem, 3vw, 2.1rem);
    font-style:italic;
    line-height:1.3;
}

.lean-daily-reset {
    margin:0 0 2.8rem;
    color:var(--muted);
}

.lean-august-window {
    display:flex;
    align-items:baseline;
    gap:.75rem;
    margin:2rem 0 1.35rem;
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.68rem;
    letter-spacing:.035em;
    text-transform:uppercase;
}

.lean-august-window span {
    color:var(--muted);
}

.lean-august-window strong {
    font-weight:600;
}

.lean-monthly-link {
    display:inline-block;
    padding:.75rem 0 .35rem;
    border-bottom:1px solid var(--black);
    color:var(--black) !important;
    text-decoration:none !important;
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.76rem;
    letter-spacing:.025em;
    text-transform:uppercase;
}

.lean-monthly-link:hover {
    opacity:.62;
}

.lean-bookmark-note {
    max-width:680px;
    margin:1.35rem 0 0;
    color:var(--muted);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.66rem;
    line-height:1.55;
    letter-spacing:.02em;
}

.luna-video-slot {
    max-width:760px;
    margin:1rem auto 4rem;
    padding-top:1.6rem;
    border-top:1px solid var(--line);
}

.natal-shell {
    max-width:820px;
    margin:0 auto;
    padding:1.2rem 0 4rem;
}

.natal-intro {
    max-width:680px;
    margin:0 0 2.2rem;
    font-size:1.1rem;
    line-height:1.7;
}

.natal-birth-confirm {
    margin:-.3rem 0 1.1rem;
    padding:.75rem 0;
    border-top:1px solid var(--line);
    border-bottom:1px solid var(--line);
    color:var(--ink);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.68rem;
    line-height:1.6;
}

.natal-birth-confirm span {
    color:var(--muted);
}

.natal-theme {
    padding:1.5rem 0 1.6rem;
    border-top:1px solid var(--black);
}

.natal-theme h3 {
    margin:.3rem 0 .75rem !important;
}

.natal-evidence {
    color:var(--muted);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.66rem;
    letter-spacing:.025em;
    text-transform:uppercase;
}

.natal-chart-emphasis {
    margin:.35rem 0 1.65rem;
    padding:1rem 0 1.15rem;
    border-top:1px solid var(--black);
    border-bottom:1px solid var(--line);
}

.natal-chart-emphasis span {
    display:block;
    color:var(--muted);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.64rem;
    letter-spacing:.025em;
    text-transform:uppercase;
}

.natal-chart-emphasis strong {
    display:block;
    margin:.38rem 0 .45rem;
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, serif;
    font-size:clamp(1.55rem,3vw,2.2rem);
    font-weight:400;
    line-height:1.08;
}

.natal-chart-emphasis p {
    max-width:720px;
    margin:0;
    color:var(--ink);
    line-height:1.6;
}

.natal-signature-reading {
    padding:1.45rem 0 1.55rem;
    border-top:1px solid var(--line);
}

.natal-signature-reading h3 {
    margin:.28rem 0 .72rem !important;
}

.natal-signature-reading p {
    max-width:720px;
}

.natal-signature-meta {
    display:grid;
    grid-template-columns:repeat(2,minmax(0,1fr));
    gap:1rem;
    margin-top:.85rem;
    font-size:.84rem;
    line-height:1.55;
}

.natal-signature-meta span {
    display:block;
    margin-bottom:.2rem;
    color:var(--muted);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.62rem;
    letter-spacing:.025em;
    text-transform:uppercase;
}

.natal-signature-question {
    max-width:720px;
    margin:.9rem 0 0;
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, serif;
    font-size:1.08rem;
    line-height:1.45;
}

.natal-signature {
    display:grid;
    grid-template-columns:repeat(3,minmax(0,1fr));
    gap:1rem;
    margin:1.6rem 0 2rem;
}

.natal-signature > div {
    border-top:1px solid var(--line);
    padding-top:.8rem;
}

.natal-signature span {
    display:block;
    color:var(--muted);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.64rem;
    text-transform:uppercase;
    letter-spacing:.025em;
}

.natal-signature strong {
    display:block;
    margin-top:.35rem;
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, serif;
    font-size:1.6rem;
    font-weight:400;
}

.payment-link {
    display:flex;
    justify-content:center;
    align-items:center;
    width:100%;
    min-height:3.25rem;
    margin-top:.55rem;
    background:var(--black);
    color:var(--white) !important;
    border:1px solid var(--black);
    text-decoration:none !important;
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.76rem;
    font-weight:500;
    letter-spacing:.025em;
    text-transform:uppercase;
}

.payment-link:hover {
    opacity:.78;
}

.order-summary {
    display:grid;
    grid-template-columns:9.5rem 1fr;
    gap:.55rem 1rem;
    border-top:1px solid var(--black);
    border-bottom:1px solid var(--black);
    padding:1rem 0;
    margin:1rem 0;
}

.order-label {
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.68rem;
    text-transform:uppercase;
    color:var(--muted);
}

.order-value {
    font-family:"Josefin Sans", sans-serif;
    font-size:1rem;
    overflow-wrap:anywhere;
}

.delivery-notice {
    border:1px solid var(--black);
    background:var(--soft);
    padding:1rem 1.1rem;
    margin:1rem 0 1.25rem;
    font-family:"Josefin Sans", sans-serif;
    font-size:1rem;
    line-height:1.55;
}

.delivery-notice strong {
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.72rem;
    letter-spacing:.04em;
    text-transform:uppercase;
}

.checkout-note {
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.68rem;
    line-height:1.55;
    color:var(--muted);
}

@media (max-width: 700px) {
    .order-summary {
        grid-template-columns:1fr;
        gap:.2rem;
    }
}

.sign-grid {
    display:grid;
    grid-template-columns:repeat(3, minmax(0,1fr));
    gap:1rem;
}

.sign-card {
    display:block;
    border:1px solid var(--black);
    padding:1.2rem;
    color:var(--black) !important;
    text-decoration:none !important;
    min-height:10rem;
}

.sign-card:hover {
    background:var(--soft);
}

.sign-card-title {
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, serif;
    font-size:1.7rem;
    line-height:1.05;
    margin:.35rem 0 .75rem;
}

.sign-card-copy,
.date-line {
    font-family:"Josefin Sans", sans-serif;
    font-size:.98rem;
    line-height:1.5;
}

.date-list {
    border-top:1px solid var(--black);
}

.date-row {
    display:grid;
    grid-template-columns:8.5rem 1fr;
    gap:1rem;
    padding:1rem 0;
    border-bottom:1px solid var(--line);
}

.date-label {
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.69rem;
    text-transform:uppercase;
}

.related-signs {
    display:flex;
    flex-wrap:wrap;
    gap:.45rem;
    margin:1rem 0;
}

.related-signs a {
    border:1px solid var(--black);
    padding:.3rem .48rem;
    color:var(--black) !important;
    text-decoration:none !important;
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.61rem;
    text-transform:uppercase;
}

.monthly-other-signs-label {
    margin-top:1.35rem;
    font-size:.62rem;
}

.related-signs a:hover {
    background:var(--black);
    color:var(--white) !important;
}

@media (max-width: 900px) {
    .sign-grid {
        grid-template-columns:repeat(2, minmax(0,1fr));
    }
}

@media (max-width: 700px) {
    .top-nav a {
        padding:.1rem .55rem;
        font-size:.61rem;
    }
    .sign-grid {
        grid-template-columns:1fr;
    }
    .date-row {
        grid-template-columns:1fr;
        gap:.3rem;
    }
}

div[data-testid="stRadio"] {
    border-top:1px solid var(--black);
    border-bottom:1px solid var(--black);
    padding:.15rem 0;
}

div[data-testid="stRadio"] label {
    font-family:"IBM Plex Mono", "Courier New", monospace !important;
    font-size:.69rem !important;
    text-transform:uppercase;
    letter-spacing:.02em;
}

div[data-testid="stButton"] > button,
div[data-testid="stLinkButton"] > a,
button[kind="primary"],
button[kind="secondary"] {
    min-height:3.25rem;
    border-radius:0 !important;
    font-family:"IBM Plex Mono", "Courier New", monospace !important;
    font-size:.76rem !important;
    font-weight:500 !important;
    letter-spacing:.025em !important;
    text-transform:uppercase !important;
    box-shadow:none !important;
}

div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stLinkButton"] > a {
    background:var(--black) !important;
    color:var(--white) !important;
    border:1px solid var(--black) !important;
}

div[data-testid="stButton"] > button[kind="secondary"] {
    background:var(--white) !important;
    color:var(--black) !important;
    border:1px solid var(--black) !important;
}

div[data-testid="stButton"] > button:hover,
div[data-testid="stLinkButton"] > a:hover {
    opacity:.78;
}

div[data-baseweb="select"] > div,
div[data-testid="stDateInput"] input,
div[data-testid="stTextInput"] input {
    background:var(--white);
    border:1px solid var(--black) !important;
    border-radius:0 !important;
    min-height:3.15rem;
    font-family:"IBM Plex Mono", "Courier New", monospace;
}

label,
[data-testid="stWidgetLabel"] p {
    font-family:"IBM Plex Mono", "Courier New", monospace !important;
    font-size:.7rem !important;
    letter-spacing:.02em;
    text-transform:uppercase;
}

[data-testid="stForm"] {
    background:var(--white);
    border:1px solid var(--black);
    padding:1.35rem;
    border-radius:0;
}

[data-testid="stExpander"] {
    border:1px solid var(--black) !important;
    border-radius:0 !important;
}

[data-testid="stExpander"] summary {
    font-family:"IBM Plex Mono", "Courier New", monospace;
    text-transform:uppercase;
    font-size:.72rem;
}

[data-testid="stDataFrame"] {
    border:1px solid var(--black);
    border-radius:0;
    overflow:hidden;
}

table {
    width:100%;
    border-collapse:collapse;
    background:var(--white);
}

th {
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.68rem;
    text-transform:uppercase;
    font-weight:500;
}

th, td {
    border-bottom:1px solid var(--line);
    padding:.7rem .55rem !important;
}

hr {
    border:none;
    border-top:1px solid var(--black);
}

.stAlert {
    border-radius:0 !important;
    border:1px solid var(--black) !important;
    background:var(--soft) !important;
    color:var(--black) !important;
}

.weekly-view {
    width:100%;
    max-width:1120px;
    margin:0 auto;
    padding:.5rem 0 3.5rem;
}

.weekly-kicker,
.weekly-range,
.weekly-card-meta,
.weekly-evidence,
.weekly-move-label {
    font-family:"IBM Plex Mono", "Courier New", monospace;
    text-transform:uppercase;
    letter-spacing:.035em;
}

.weekly-kicker {
    font-size:.7rem;
    color:var(--muted);
    margin-top:.7rem;
}

.weekly-range {
    display:inline-block;
    margin:.85rem 0 1.2rem;
    padding:.38rem .55rem;
    border:1px solid var(--black);
    font-size:.68rem;
}

.weekly-view > h1 {
    max-width:900px;
    margin-bottom:1.1rem !important;
}

.weekly-intro {
    max-width:760px;
    margin:0 0 3rem;
    color:var(--muted);
    font-size:1rem;
}

.weekly-grid {
    display:grid;
    grid-template-columns:repeat(2,minmax(0,1fr));
    gap:0;
    border-top:1px solid var(--black);
    border-left:1px solid var(--black);
}

.weekly-card {
    min-width:0;
    padding:1.45rem 1.35rem 1.6rem;
    border-right:1px solid var(--black);
    border-bottom:1px solid var(--black);
    background:var(--white);
    break-inside:avoid;
    page-break-inside:avoid;
}

.weekly-card:last-child:nth-child(odd) {
    grid-column:1 / -1;
}

.weekly-card-meta {
    display:flex;
    justify-content:space-between;
    gap:1rem;
    padding-bottom:.75rem;
    border-bottom:1px solid var(--line);
    font-size:.67rem;
}

.weekly-evidence {
    margin:1.05rem 0 .75rem;
    color:var(--muted);
    font-size:.63rem;
    line-height:1.5;
}

.weekly-card h2 {
    min-height:2.3em;
    margin:.2rem 0 1rem !important;
    font-family:"IBM Plex Mono", "Courier New", monospace !important;
    font-size:clamp(1.35rem,2.3vw,2.15rem) !important;
    line-height:1.08 !important;
    letter-spacing:-.035em !important;
}

.weekly-card p {
    margin:.25rem 0;
    font-size:1rem;
    line-height:1.5;
}

.weekly-move {
    margin-top:1.3rem;
    padding-top:1rem;
    border-top:1px solid var(--black);
}

.weekly-move-label {
    margin-bottom:.35rem;
    font-size:.62rem;
    font-weight:600;
}

.weekly-move p {
    margin:0;
    font-weight:600;
}

.weekly-studio-controls {
    margin:1rem 0 2rem;
    padding:1.15rem;
    border:1px solid var(--black);
    background:var(--soft);
}

@media print {
    .brand-row,
    .top-nav,
    .mobile-nav,
    .solar-year-wave-wrap,
    .weekly-studio-controls,
    [data-testid="stDownloadButton"],
    [data-testid="stForm"],
    [data-testid="stExpander"],
    [data-testid="stSelectbox"],
    [data-testid="stCode"],
    .weekly-copy-heading,
    iframe {
        display:none !important;
    }
    .block-container {
        max-width:none;
        padding:.3in !important;
    }
    .weekly-grid {
        grid-template-columns:repeat(2,minmax(0,1fr));
    }
    .weekly-card {
        break-inside:avoid;
        page-break-inside:avoid;
    }
}

@media (max-width: 850px) {
    .trust-strip {
        grid-template-columns:1fr 1fr;
    }
    .trust-item:nth-child(2) {
        border-right:none;
    }
    .trust-item:nth-child(-n+2) {
        border-bottom:1px solid var(--black);
    }
}

@media (max-width: 700px) {
    .block-container {
        width:100%;
        max-width:100%;
        padding-left:max(1rem, env(safe-area-inset-left, 0px));
        padding-right:max(1rem, env(safe-area-inset-right, 0px));
        padding-top:.45rem;
        padding-bottom:calc(3rem + env(safe-area-inset-bottom, 0px));
    }
    .top-nav {
        display:none;
    }
    .mobile-nav {
        display:block;
    }
    [data-testid="stHorizontalBlock"] {
        flex-wrap:wrap !important;
        gap:.7rem !important;
    }
    [data-testid="column"] {
        width:100% !important;
        flex:1 1 100% !important;
    }
    h1 {
        font-size:3.45rem !important;
    }
    h2 {
        font-size:2.25rem !important;
    }
    p, li {
        font-size:1.02rem;
    }
    .brand-note {
        display:none;
    }
    .brand-name {
        font-size:.82rem;
        letter-spacing:.12em;
    }
    .brand-icon {
        width:1.95rem;
        height:1.95rem;
    }
    .solar-year-wave-wrap {
        margin:.05rem auto .55rem;
    }
    .lean-daily {
        padding:.35rem 0 3.75rem;
    }
    .lean-daily-meta {
        margin:1rem 0 2rem;
        align-items:flex-start;
        flex-direction:column;
        gap:.3rem;
    }
    .lean-daily h1 {
        font-size:clamp(3.15rem, 15vw, 4.75rem) !important;
        margin-bottom:1.9rem !important;
    }
    .lean-daily-story {
        margin-bottom:2.65rem;
    }
    .natal-signature {
        grid-template-columns:repeat(2,minmax(0,1fr));
    }
    .natal-signature-meta {
        grid-template-columns:1fr;
        gap:.55rem;
    }
    .lean-daily-question {
        margin:2.35rem 0 2.2rem;
    }
    .card, .reading-card {
        padding:1.15rem;
    }
    .trust-strip {
        grid-template-columns:1fr;
    }
    .trust-item {
        border-right:none !important;
        border-bottom:1px solid var(--black);
    }
    .trust-item:last-child {
        border-bottom:none;
    }
    .weekly-view {
        padding-top:.2rem;
    }
    .weekly-view > h1 {
        font-size:clamp(3rem,14vw,4.4rem) !important;
    }
    .weekly-intro {
        margin-bottom:2rem;
    }
    .weekly-grid {
        grid-template-columns:1fr;
    }
    .weekly-card h2 {
        min-height:0;
        font-size:1.75rem !important;
    }
}

.timing-shell {
    max-width:980px;
    margin:0 auto;
    padding:.5rem 0 4rem;
}
.timing-intro {
    max-width:760px;
    font-size:1.12rem;
    line-height:1.75;
    margin:0 0 2rem;
}
.timing-summary-grid {
    display:grid;
    grid-template-columns:repeat(3,minmax(0,1fr));
    border-top:1px solid var(--black);
    border-bottom:1px solid var(--black);
    margin:1.3rem 0 2rem;
}
.timing-summary-grid > div { padding:1.15rem 1rem; border-right:1px solid var(--black); }
.timing-summary-grid > div:last-child { border-right:none; }
.timing-summary-grid span, .timing-evidence, .timing-meta, .timing-month span, .timing-move-label {
    font-family:'IBM Plex Mono',monospace;
    text-transform:uppercase;
    letter-spacing:.08em;
}
.timing-summary-grid span { display:block; font-size:.69rem; color:var(--muted); margin-bottom:.4rem; }
.timing-summary-grid strong { font-family:'Josefin Sans',sans-serif; font-size:1.55rem; font-weight:500; }
.timing-strip { display:grid; grid-template-columns:repeat(13,minmax(0,1fr)); gap:5px; align-items:end; margin:.6rem 0 2.6rem; }
.timing-month { min-width:0; }
.timing-month span { display:block; font-size:.58rem; text-align:center; margin-bottom:.35rem; color:var(--muted); }
.timing-month i { display:block; min-height:4px; background:#111; border:1px solid #111; }
.timing-story { border-top:1px solid var(--black); padding:2rem 0 2.25rem; }
.timing-story:last-of-type { border-bottom:1px solid var(--black); }
.timing-meta { font-size:.7rem; color:var(--muted); margin-bottom:.65rem; }
.timing-story h2 { font-family:'Josefin Sans',sans-serif !important; font-size:clamp(2rem,5vw,3.25rem) !important; line-height:.98 !important; margin:.25rem 0 1rem !important; }
.timing-story p { max-width:800px; }
.timing-dates { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.7rem; margin:1.25rem 0; }
.timing-date-box { border:1px solid var(--black); padding:.8rem; }
.timing-date-box span { display:block; font-family:'IBM Plex Mono',monospace; text-transform:uppercase; letter-spacing:.07em; font-size:.62rem; color:var(--muted); margin-bottom:.2rem; }
.timing-date-box strong { font-family:'Josefin Sans',sans-serif; font-size:1.02rem; font-weight:500; }
.timing-scenarios { margin:1rem 0 1.25rem; padding-left:1.15rem; }
.timing-scenarios li { margin:.45rem 0; }
.timing-move { border-left:3px solid var(--black); padding:.75rem 0 .75rem 1rem; margin:1.15rem 0; }
.timing-move-label { font-size:.65rem; color:var(--muted); margin-bottom:.35rem; }
.timing-move strong { font-family:'Josefin Sans',sans-serif; font-size:1.25rem; font-weight:500; }
.timing-evidence { font-size:.72rem; line-height:1.65; }
.timing-test { border:1px solid var(--black); padding:1.25rem; margin:2.5rem 0 1rem; }
@media (max-width:700px) {
    .timing-summary-grid { grid-template-columns:1fr; }
    .timing-summary-grid > div { border-right:none; border-bottom:1px solid var(--black); }
    .timing-summary-grid > div:last-child { border-bottom:none; }
    .timing-strip { gap:2px; }
    .timing-month span { font-size:.48rem; }
    .timing-dates { grid-template-columns:1fr; }
}

</style>
        """,
        unsafe_allow_html=True,
    )


def brand_header() -> None:
    encoded_icon = base64.b64encode(BRAND_ICON_PATH.read_bytes()).decode("ascii")
    st.markdown(
        f"""
<div class="brand-row">
  <div class="brand-lockup">
    <img class="brand-icon" src="data:image/png;base64,{encoded_icon}" alt="Saturn hexagon mark">
    <div class="brand-name">{escape(BRAND_NAME)}</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def top_navigation(current_path: str) -> None:
    path = current_path or ""
    # The root, /daily-horoscope and the legacy Google Ads URL all render the
    # same Daily experience.  Monthly sign pages remain the only public
    # destination for This Month.
    if path in {"", "daily-horoscope", "august-2026-horoscopes"}:
        nav_path = ""
    elif path.startswith("august-2026-"):
        nav_path = "this-month"
    else:
        nav_path = path

    remembered_sign = (
        st.session_state.get("landing-daily-sign-v3195")
        or st.session_state.get("daily-sign")
        or DEFAULT_SIGN
    )
    if remembered_sign not in SIGNS:
        remembered_sign = DEFAULT_SIGN
    monthly_path = f"august-2026-{sign_slug(remembered_sign)}"

    # Public navigation is intentionally minimal. Routes used for checkout,
    # fulfilment, previews and administration still exist but stay out of sight.
    items = [
        ("", "Daily Horoscope"),
        ("weekly-view", "Weekly View"),
        (monthly_path, "This Month"),
        ("timing-map", "12-Month Map"),
        ("house-guide", "House Guide"),
        ("solar-year", "Solar Year"),
    ]

    desktop_links: list[str] = []
    mobile_links: list[str] = []
    current_label = "Daily Horoscope"

    for item_path, label in items:
        item_is_active = nav_path == item_path or (label == "This Month" and nav_path == "this-month")
        active = " active" if item_is_active else ""
        if item_is_active:
            current_label = label
        href = "/" if not item_path else f"/{item_path}"

        desktop_links.append(
            f'<a class="{active.strip()}" href="{href}">'
            f'<span class="nav-dot"></span>{escape(label)}</a>'
        )
        mobile_links.append(
            f'<a class="{active.strip()}" href="{href}">{escape(label)}</a>'
        )

    st.markdown(
        '<nav class="top-nav" aria-label="Primary navigation">'
        + "".join(desktop_links)
        + "</nav>"
        + '<details class="mobile-nav">'
        + f"<summary><span>Menu</span><strong>{escape(current_label)}</strong></summary>"
        + '<nav class="mobile-nav-grid" aria-label="Mobile navigation">'
        + "".join(mobile_links)
        + "</nav></details>",
        unsafe_allow_html=True,
    )

def set_page_metadata(title: str, description: str, path: str) -> None:
    canonical = PUBLIC_SITE_URL + (path if path.startswith("/") else f"/{path}")
    if path in ("", "/"):
        canonical = PUBLIC_SITE_URL + "/"
    st.html(
        f"""
<script>
(() => {{
  const title = {json.dumps(title)};
  const description = {json.dumps(description)};
  const canonical = {json.dumps(canonical)};
  document.title = title;

  let meta = document.head.querySelector('meta[name="description"]');
  if (!meta) {{
    meta = document.createElement('meta');
    meta.setAttribute('name', 'description');
    document.head.appendChild(meta);
  }}
  meta.setAttribute('content', description);

  let link = document.head.querySelector('link[rel="canonical"]');
  if (!link) {{
    link = document.createElement('link');
    link.setAttribute('rel', 'canonical');
    document.head.appendChild(link);
  }}
  link.setAttribute('href', canonical);

  const upsert = (property, value) => {{
    let node = document.head.querySelector(`meta[property="${{property}}"]`);
    if (!node) {{
      node = document.createElement('meta');
      node.setAttribute('property', property);
      document.head.appendChild(node);
    }}
    node.setAttribute('content', value);
  }};
  upsert('og:title', title);
  upsert('og:description', description);
  upsert('og:url', canonical);
  upsert('og:type', 'website');
}})();
</script>
        """,
        unsafe_allow_javascript=True,
    )


def install_google_analytics(page_title: str, page_path: str) -> None:
    if not GA_MEASUREMENT_ID.startswith("G-"):
        return

    session_key = f"_ga_page_view::{page_path}"
    send_page_view = not st.session_state.get(session_key, False)
    st.session_state[session_key] = True

    st.html(
        f"""
<script>
(() => {{
  const measurementId = {json.dumps(GA_MEASUREMENT_ID)};
  const googleAdsId = {json.dumps(GOOGLE_ADS_ID)};
  if (!window.dataLayer) window.dataLayer = [];
  if (!window.gtag) {{
    window.gtag = function() {{ window.dataLayer.push(arguments); }};
  }}
  if (!document.getElementById('luna-google-tag')) {{
    const tag = document.createElement('script');
    tag.id = 'luna-google-tag';
    tag.async = true;
    tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + measurementId;
    document.head.appendChild(tag);
    window.gtag('js', new Date());
  }}
  window.gtag('config', measurementId, {{
    send_page_view: false,
    page_path: {json.dumps(page_path)},
    page_title: {json.dumps(page_title)}
  }});
  if (googleAdsId && googleAdsId.startsWith('AW-')) {{
    window.gtag('config', googleAdsId);
  }}
  if ({str(send_page_view).lower()}) {{
    window.gtag('event', 'page_view', {{
      page_path: {json.dumps(page_path)},
      page_location: window.location.href,
      page_title: {json.dumps(page_title)}
    }});
  }}
}})();
</script>
        """,
        unsafe_allow_javascript=True,
    )


def install_statcounter() -> None:
    """Install the invisible Statcounter tracker once per visitor session."""
    project_id = STATCOUNTER_PROJECT_ID.strip()
    security_code = STATCOUNTER_SECURITY_CODE.strip()

    if not project_id.isdigit() or not security_code:
        return
    if st.session_state.get("_statcounter_loaded", False):
        return

    st.html(
        f"""
<script>
(() => {{
  globalThis.sc_project = {int(project_id)};
  globalThis.sc_invisible = 1;
  globalThis.sc_security = {json.dumps(security_code)};
  globalThis.sc_https = 1;

  if (!document.getElementById('luna-statcounter-script')) {{
    const script = document.createElement('script');
    script.id = 'luna-statcounter-script';
    script.async = true;
    script.src = 'https://secure.statcounter.com/counter/counter.js';
    document.head.appendChild(script);
  }}
}})();
</script>
        """,
        unsafe_allow_javascript=True,
    )
    st.session_state["_statcounter_loaded"] = True


def track_event(event_name: str, parameters: dict | None = None) -> None:
    if not GA_MEASUREMENT_ID.startswith("G-"):
        return
    st.html(
        f"""
<script>
if (window.gtag) {{
  window.gtag('event', {json.dumps(event_name)}, {json.dumps(parameters or {})});
}}
</script>
        """,
        unsafe_allow_javascript=True,
    )


def payment_button(
    label: str,
    url: str,
    key: str,
    event_name: str,
    event_parameters: dict | None = None,
) -> None:
    if url:
        safe_url = escape(url, quote=True)
        safe_label = escape(label)
        parameters = {
            "event_category": "conversion",
            "link_url": url,
            "value": 1,
            **(event_parameters or {}),
        }
        onclick = (
            "if(window.gtag){window.gtag("
            + json.dumps("event")
            + ","
            + json.dumps(event_name)
            + ","
            + json.dumps(parameters)
            + ");}"
        )
        st.html(
            f"""
<a class="payment-link"
   href="{safe_url}"
   target="_blank"
   rel="noopener noreferrer"
   onclick='{escape(onclick, quote=True)}'>
   {safe_label}
</a>
            """,
            unsafe_allow_javascript=True,
        )
    else:
        st.button(
            f"{label} — link not connected",
            key=key,
            disabled=True,
            use_container_width=True,
        )


def _order_token(context: str, product_code: str) -> str:
    key = f"order-token::{context}::{product_code}"
    if key not in st.session_state:
        st.session_state[key] = secrets.token_hex(4).upper()
    return str(st.session_state[key])


def _order_summary(
    report_name: str,
    sign: str,
    period: str,
    timezone_name: str,
    nearest_city: str,
    location_basis: str,
    delivery_email: str,
    main_focus: str,
    personal_question: str,
    reference: str,
    natal_summary: str = "",
    natal_precision: str = "",
) -> None:
    question_value = personal_question or "No optional question supplied"
    natal_html = ""
    if natal_summary:
        natal_html = (
            f'<div class="order-label">Natal basis</div><div class="order-value">{escape(natal_summary)}</div>'
            f'<div class="order-label">Birth-time precision</div><div class="order-value">{escape(natal_precision)}</div>'
        )
    st.markdown(
        f"""
<div class="order-summary">
  <div class="order-label">Report</div>
  <div class="order-value">{escape(report_name)}</div>
  <div class="order-label">Star sign</div>
  <div class="order-value">{escape(sign)}</div>
  <div class="order-label">Period</div>
  <div class="order-value">{escape(period)}</div>
  <div class="order-label">Timezone</div>
  <div class="order-value">{escape(timezone_name)}</div>
  <div class="order-label">Nearest city</div>
  <div class="order-value">{escape(nearest_city)} ({escape(location_basis)})</div>
  <div class="order-label">Main focus</div>
  <div class="order-value">{escape(main_focus)}</div>
  {natal_html}
  <div class="order-label">Personal question</div>
  <div class="order-value">{escape(question_value)}</div>
  <div class="order-label">Delivery email</div>
  <div class="order-value">{escape(delivery_email)}</div>
  <div class="order-label">Delivery</div>
  <div class="order-value">Instant access after payment + immediate email link + monthly PDF download</div>
  <div class="order-label">Order reference</div>
  <div class="order-value">{escape(reference)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


@lru_cache(maxsize=4)
def _stripe_price_id(product_code: str) -> str:
    code = str(product_code or "").upper()
    if code == "MONTHLY":
        return resolve_price_id(
            STRIPE_SECRET_KEY,
            explicit_price_id=STRIPE_MONTHLY_PRICE_ID,
            payment_link_url=MONTHLY_PAYMENT_URL,
        )
    if code in {"YEAR", "YEARLY"}:
        return resolve_price_id(
            STRIPE_SECRET_KEY,
            explicit_price_id=STRIPE_YEARLY_PRICE_ID,
            payment_link_url=YEARLY_PAYMENT_URL,
        )
    return ""


def _create_instant_checkout(order: dict, product_code: str) -> str:
    """Create a fresh Stripe Checkout Session carrying exact fulfilment metadata."""
    if not STRIPE_SECRET_KEY.startswith("sk_"):
        raise StripeCheckoutError(
            "Instant checkout needs STRIPE_SECRET_KEY in Streamlit Secrets."
        )
    price_id = _stripe_price_id(product_code)
    if not price_id:
        raise StripeCheckoutError(
            "Luna could not resolve the Stripe Price ID. Add STRIPE_MONTHLY_PRICE_ID "
            "or STRIPE_YEARLY_PRICE_ID to Streamlit Secrets."
        )
    order = dict(order)
    order["product_code"] = product_code
    session = create_checkout_session(
        STRIPE_SECRET_KEY,
        price_id=price_id,
        order=order,
        public_site_url=PUBLIC_SITE_URL,
    )
    url = str(session.get("url") or "")
    if not url.startswith("https://"):
        raise StripeCheckoutError("Stripe did not return a secure Checkout URL.")
    return url


def _send_purchase_events(session: dict) -> None:
    """Record the paid order in GA4 and optional Google Ads conversion tracking."""
    session_id = str(session.get("id") or "")
    state_key = f"purchase-events::{session_id}"
    if not session_id or st.session_state.get(state_key):
        return
    amount, currency = checkout_amount(session)
    metadata = checkout_metadata(session)
    track_event(
        "purchase",
        {
            "transaction_id": session_id,
            "value": amount,
            "currency": currency,
            "items": [
                {
                    "item_name": metadata.get("report_name", "Luna report"),
                    "item_category": metadata.get("product_code", "REPORT"),
                    "item_variant": metadata.get("sign", ""),
                    "price": amount,
                    "quantity": 1,
                }
            ],
        },
    )
    if GOOGLE_ADS_PURCHASE_LABEL and GOOGLE_ADS_ID.startswith("AW-"):
        send_to = f"{GOOGLE_ADS_ID}/{GOOGLE_ADS_PURCHASE_LABEL}"
        st.html(
            f"""
<script>
if (window.gtag) {{
  window.gtag('event', 'conversion', {{
    'send_to': {json.dumps(send_to)},
    'value': {amount},
    'currency': {json.dumps(currency)},
    'transaction_id': {json.dumps(session_id)}
  }});
}}
</script>
            """,
            unsafe_allow_javascript=True,
        )
    st.session_state[state_key] = True


def _email_paid_report(
    session: dict,
    *,
    attachment_bytes: bytes | None = None,
    attachment_filename: str = "",
) -> None:
    session_id = str(session.get("id") or "")
    state_key = f"fulfilment-email::{session_id}"
    if not session_id or st.session_state.get(state_key):
        return
    metadata = checkout_metadata(session)
    recipient = checkout_email(session)
    report_url = f"{PUBLIC_SITE_URL}/payment-success?session_id={session_id}"
    result = send_report_email(
        to_email=recipient,
        report_name=metadata.get("report_name", "Luna report"),
        sign=metadata.get("sign", "Your sign"),
        period=metadata.get("period", metadata.get("period_code", "")),
        report_url=report_url,
        order_reference=metadata.get(
            "order_reference", str(session.get("client_reference_id") or "")
        ),
        idempotency_key=f"luna-fulfil-{session_id}",
        resend_api_key=RESEND_API_KEY,
        resend_from=RESEND_FROM,
        smtp_user=SMTP_USER,
        smtp_app_password=SMTP_APP_PASSWORD,
        smtp_from=SMTP_FROM,
        attachment_bytes=attachment_bytes,
        attachment_filename=attachment_filename,
    )
    st.session_state[state_key] = result.sent
    if result.sent:
        if attachment_bytes:
            st.success(
                f"Your personalised PDF has been emailed to {recipient}. "
                "A link to reopen this paid report is included too."
            )
        else:
            st.success(f"A link to reopen this paid report has been emailed to {recipient}.")
    else:
        st.info(
            "Your report is available below now. Automatic email is not yet connected "
            "on this deployment, so keep this page open or download the report."
        )


def payment_success_page() -> None:
    set_page_metadata(
        "Your Luna Report Is Ready | Luna Convergence",
        "Secure paid-report fulfilment for Luna Convergence.",
        "/payment-success",
    )
    st.markdown('<div class="eyebrow">Payment confirmed</div>', unsafe_allow_html=True)
    st.markdown("# Your Luna report is ready")

    session_id = str(st.query_params.get("session_id", "")).strip()
    if not session_id:
        st.error("This private report link is missing its Stripe session reference.")
        return
    try:
        session = retrieve_checkout_session(STRIPE_SECRET_KEY, session_id)
    except Exception as exc:
        st.error("Luna could not verify this payment with Stripe.")
        st.caption(str(exc))
        return
    if not checkout_is_paid(session):
        st.warning("Stripe has not marked this Checkout Session as paid yet.")
        return

    metadata = checkout_metadata(session)
    product_code = metadata.get("product_code", "").upper()
    sign = metadata.get("sign", "")
    period_code = metadata.get("period_code", "")
    timezone_name = metadata.get("timezone", DEFAULT_TIMEZONE)
    nearest_city = metadata.get("nearest_city", "")
    main_focus = metadata.get("main_focus", "General overview")
    personal_question = metadata.get("personal_question", "")
    natal_profile_value = metadata.get("natal_profile", "")
    natal_summary_value = metadata.get("natal_summary", "")
    natal_precision_value = metadata.get("natal_precision", "")
    order_reference = metadata.get(
        "order_reference", str(session.get("client_reference_id") or "")
    )

    st.markdown(
        f"**{escape(sign)} · {escape(metadata.get('period', period_code))}**  "
        f"  \nOrder reference: `{escape(order_reference)}`"
    )
    _send_purchase_events(session)
    st.caption(
        "This is a private paid-report link. Keep the email or bookmark this page; "
        "do not share the link."
    )

    try:
        if product_code == "MONTHLY":
            year_text, month_text = period_code.split("-", 1)
            narrative, result = build_production_monthly_report(
                sign=sign,
                year=int(year_text),
                month=int(month_text),
                timezone_name=timezone_name,
                nearest_city=nearest_city,
                main_focus=main_focus,
                personal_question=personal_question,
            )
            if natal_profile_value:
                result["natal_overlay"] = build_monthly_natal_overlay(natal_profile_value, result)
                result["natal_summary"] = natal_summary_value
                result["natal_precision"] = natal_precision_value
            pdf_bytes = build_report_pdf(
                result,
                main_focus=main_focus,
                personal_question=personal_question,
                order_reference=order_reference,
            )
            pdf_name = report_filename(result)
            st.download_button(
                "Download your personalised PDF",
                data=pdf_bytes,
                file_name=pdf_name,
                mime="application/pdf",
                use_container_width=True,
                key=f"paid-pdf-{session_id}",
            )
            _email_paid_report(
                session,
                attachment_bytes=pdf_bytes,
                attachment_filename=pdf_name,
            )
            render_production_monthly_report(
                narrative,
                result,
                show_print=True,
                order_reference=order_reference,
            )
        elif product_code in {"YEAR", "YEARLY"}:
            year = int(period_code)
            result = period_report(
                sign,
                date(year, 1, 1),
                date(year, 12, 31),
                timezone_name,
                str(year),
                transition_count=9,
                nearest_city=nearest_city,
                main_focus=main_focus,
            )
            pdf_bytes = build_report_pdf(
                result,
                main_focus=main_focus,
                personal_question=personal_question,
                order_reference=order_reference,
            )
            pdf_name = report_filename(result)
            st.download_button(
                "Download your personalised PDF",
                data=pdf_bytes,
                file_name=pdf_name,
                mime="application/pdf",
                use_container_width=True,
                key=f"paid-pdf-{session_id}",
            )
            _email_paid_report(
                session,
                attachment_bytes=pdf_bytes,
                attachment_filename=pdf_name,
            )
            render_yearly_experience(
                result,
                show_print=True,
                order_reference=order_reference,
            )
        else:
            st.error("The paid order does not contain a recognised Luna report type.")
    except Exception as exc:
        st.error(
            "Payment is confirmed, but Luna could not generate the report on this run. "
            "Use the order reference above for support."
        )
        st.exception(exc)



def _monthly_natal_checkout_fields(key_context: str) -> dict:
    """Render the paid Monthly natal inputs using the same precision rules as the free snapshot."""
    prefill = dict(st.session_state.get("luna_natal_checkout_prefill") or {})
    try:
        prefill_date = date.fromisoformat(str(prefill.get("birth_date") or ""))
    except Exception:
        prefill_date = None
    prefill_time_text = str(prefill.get("birth_time") or "12:00")
    try:
        prefill_time = datetime.strptime(prefill_time_text, "%H:%M").time()
    except Exception:
        prefill_time = datetime.strptime("12:00", "%H:%M").time()

    st.markdown("### Personalise with your natal chart")
    st.caption(
        "The paid Monthly uses your natal geometry as a second layer over the sign forecast. "
        "If you do not know the exact birth time, leave it unchecked; Luna will not invent the Ascendant or houses."
    )

    birth_date_value = st.date_input(
        "Birth date",
        value=prefill_date,
        min_value=date(1900, 1, 1),
        max_value=browser_local_date(),
        key=f"{key_context}-monthly-natal-birth-date",
    )
    time_known_value = st.checkbox(
        "I know my birth time exactly",
        value=bool(prefill.get("time_known", False)),
        key=f"{key_context}-monthly-natal-time-known",
    )

    values = {
        "birth_date": birth_date_value,
        "time_known": time_known_value,
        "birth_time": None,
        "time_basis": "Local time at birthplace",
        "city_choice": "",
        "manual_city": "",
        "manual_country": "",
        "manual_latitude": None,
        "manual_longitude": None,
        "manual_timezone": "UTC",
        "unlisted_timezone": "UTC",
    }

    if not time_known_value:
        st.caption("Birth time unknown: Luna will use the reliable planetary geometry and omit Ascendant, Midheaven and houses.")
        return values

    values["birth_time"] = st.time_input(
        "Birth time",
        value=prefill_time,
        key=f"{key_context}-monthly-natal-birth-time",
        help="Normally enter the local clock time at the place of birth. If your source explicitly gives Universal Time, choose UTC below.",
    )
    basis_options = ["Local time at birthplace", "Universal Time (UTC)"]
    prefill_basis = str(prefill.get("time_basis") or basis_options[0])
    values["time_basis"] = st.selectbox(
        "Time basis",
        basis_options,
        index=basis_options.index(prefill_basis) if prefill_basis in basis_options else 0,
        key=f"{key_context}-monthly-natal-time-basis",
    )

    city_options = sorted(CITY_LOCATIONS) + [
        "Other city — enter manually",
        "Not listed — planetary snapshot only",
    ]
    prefill_choice = str(prefill.get("city_choice") or "")
    if prefill_choice not in city_options and prefill.get("location_name"):
        # A previous manual location should reopen the manual entry path.
        prefill_choice = "Other city — enter manually"
    values["city_choice"] = st.selectbox(
        "Birth city",
        city_options,
        index=city_options.index(prefill_choice) if prefill_choice in city_options else None,
        placeholder="Choose your birth city",
        key=f"{key_context}-monthly-natal-city",
        help="Use Other city if the place is not listed. Exact coordinates keep the Ascendant and houses precise.",
    )

    if values["city_choice"] == "Other city — enter manually":
        st.caption("Enter the birthplace directly. These raw birth details are used only to calculate the natal geometry in this app session.")
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            values["manual_city"] = st.text_input(
                "City / town",
                value=str(prefill.get("manual_city") or prefill.get("location_name") or "").split(",", 1)[0],
                key=f"{key_context}-monthly-natal-manual-city",
            )
            values["manual_latitude"] = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=float(prefill.get("latitude") or 0.0),
                step=0.0001,
                format="%.4f",
                key=f"{key_context}-monthly-natal-manual-lat",
            )
        with c2:
            values["manual_country"] = st.text_input(
                "Country",
                value=str(prefill.get("manual_country") or ""),
                key=f"{key_context}-monthly-natal-manual-country",
            )
            values["manual_longitude"] = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=float(prefill.get("longitude") or 0.0),
                step=0.0001,
                format="%.4f",
                key=f"{key_context}-monthly-natal-manual-lon",
            )
        if values["time_basis"] == "Local time at birthplace":
            values["manual_timezone"] = st.text_input(
                "Birth timezone · IANA name",
                value=str(prefill.get("timezone_name") or browser_timezone_name()),
                key=f"{key_context}-monthly-natal-manual-timezone",
                help="Examples: Pacific/Port_Moresby, Australia/Sydney, Europe/London, America/New_York.",
            )
        else:
            values["manual_timezone"] = "UTC"
            st.caption("Universal Time selected: Luna uses the entered time directly as UTC while retaining the birth coordinates for Ascendant and houses.")
    elif values["city_choice"] == "Not listed — planetary snapshot only":
        if values["time_basis"] == "Local time at birthplace":
            prefill_tz = str(prefill.get("timezone_name") or DEFAULT_TIMEZONE)
            values["unlisted_timezone"] = st.selectbox(
                "Birth timezone",
                TIMEZONES,
                index=TIMEZONES.index(prefill_tz) if prefill_tz in TIMEZONES else timezone_select_index(),
                key=f"{key_context}-monthly-natal-unlisted-timezone",
                help="This places the planets at the correct moment, but without coordinates Luna will not calculate the Ascendant or houses.",
            )
        else:
            values["unlisted_timezone"] = "UTC"

    return values


def _build_monthly_checkout_natal(values: dict):
    """Validate paid Monthly natal inputs and return a derived snapshot plus precision label."""
    birth_date_value = values.get("birth_date")
    if birth_date_value is None:
        raise ValueError("Choose your birth date.")
    time_known = bool(values.get("time_known"))
    if not time_known:
        snapshot = build_natal_snapshot(
            birth_date=birth_date_value,
            birth_time_known=False,
            timezone_name="UTC",
        )
        return snapshot, "Birth time unknown · angles and houses omitted"

    birth_time_value = values.get("birth_time")
    if birth_time_value is None:
        raise ValueError("Enter the exact birth time or untick 'I know my birth time exactly'.")

    city_choice = str(values.get("city_choice") or "")
    if not city_choice:
        raise ValueError("Choose the birth city, enter another city, or choose planetary snapshot only.")

    latitude = longitude = None
    location_name = None
    time_basis = str(values.get("time_basis") or "Local time at birthplace")

    if city_choice in CITY_LOCATIONS:
        location = CITY_LOCATIONS[city_choice]
        timezone_name = "UTC" if time_basis == "Universal Time (UTC)" else location.timezone
        latitude = location.latitude
        longitude = location.longitude
        location_name = f"{location.name}, {location.country}"
    elif city_choice == "Other city — enter manually":
        manual_city = str(values.get("manual_city") or "").strip()
        if not manual_city:
            raise ValueError("Enter the birth city or town name.")
        timezone_name = "UTC" if time_basis == "Universal Time (UTC)" else str(values.get("manual_timezone") or "").strip()
        if time_basis == "Local time at birthplace":
            try:
                ZoneInfo(timezone_name)
            except Exception as exc:
                raise ValueError("That birth timezone is not recognised. Use an IANA name such as Pacific/Port_Moresby or Australia/Sydney.") from exc
        latitude = float(values.get("manual_latitude") or 0.0)
        longitude = float(values.get("manual_longitude") or 0.0)
        location_name = manual_city
        manual_country = str(values.get("manual_country") or "").strip()
        if manual_country:
            location_name += f", {manual_country}"
    else:
        timezone_name = "UTC" if time_basis == "Universal Time (UTC)" else str(values.get("unlisted_timezone") or DEFAULT_TIMEZONE)

    snapshot = build_natal_snapshot(
        birth_date=birth_date_value,
        birth_time_known=True,
        birth_time=birth_time_value,
        timezone_name=timezone_name,
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
    )
    if snapshot.ascendant:
        precision = "Exact birth time supplied · Ascendant and houses calculated"
    else:
        precision = "Exact birth time supplied · birthplace coordinates unavailable, so angles and houses omitted"
    return snapshot, precision

def report_cta(
    context: str = "general",
    prefill_sign: str | None = None,
    prefill_month: str | None = None,
    prefill_year: int | None = None,
    prefill_city: str | None = None,
) -> None:
    key_context = "".join(
        character if character.isalnum() else "-"
        for character in context.lower()
    ).strip("-") or "general"

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    monthly_tab, yearly_tab = st.tabs(
        [
            f"Monthly report — {MONTHLY_PRICE}",
            f"Year-ahead report — {YEARLY_PRICE}",
        ]
    )

    with monthly_tab:
        pairs = month_choices()
        month_labels = [label for label, _ in pairs]
        month_codes = dict(pairs)
        chosen_default_month = (
            prefill_month
            if prefill_month in month_labels
            else default_month_label()
        )
        chosen_default_sign = (
            prefill_sign if prefill_sign in SIGNS else DEFAULT_SIGN
        )

        with st.container(border=True):
            st.markdown("### Choose your monthly report")
            m1, m2 = st.columns(2)
            with m1:
                delivery_email = st.text_input(
                    "Delivery email",
                    key=f"{key_context}-monthly-email",
                    placeholder="name@example.com",
                )
                sign = st.selectbox(
                    "Your star sign",
                    SIGNS,
                    index=SIGNS.index(chosen_default_sign),
                    key=f"{key_context}-monthly-sign",
                    help="Use your Sun sign unless you know and prefer your rising sign.",
                )
            with m2:
                month_label = st.selectbox(
                    "Report month",
                    month_labels,
                    index=month_labels.index(chosen_default_month),
                    key=f"{key_context}-monthly-period",
                )
                timezone_name = st.selectbox(
                    "Timezone",
                    TIMEZONES,
                    index=timezone_select_index(),
                    key=f"{key_context}-monthly-timezone",
                )
            nearest_city = st.text_input(
                "Nearest city for local light",
                value=prefill_city or "",
                key=f"{key_context}-monthly-city",
                placeholder=representative_city_name(timezone_name),
                help=city_input_help(timezone_name),
            )
            main_focus = st.selectbox(
                "Main focus",
                MONTHLY_FOCUS_CHOICES,
                key=f"{key_context}-monthly-focus",
                help="This guides which themes receive extra emphasis in the personalised PDF.",
            )
            personal_question = st.text_area(
                "Optional personal question",
                key=f"{key_context}-monthly-question",
                max_chars=QUESTION_MAX_CHARS,
                placeholder="What would you most like clarity about this month?",
                help=f"Optional. Maximum {QUESTION_MAX_CHARS} characters. It is stored with your secure Stripe checkout so Luna can personalise the report after payment.",
            )
            natal_values = _monthly_natal_checkout_fields(key_context)
            st.caption(
                "Instant delivery: after Stripe confirms payment, your report opens immediately and Luna emails your private return link. "
                "Raw birth details are used to calculate the natal chart in this session; Stripe receives only the derived natal geometry needed for fulfilment."
            )
            submitted = st.button(
                f"Prepare monthly checkout — {MONTHLY_PRICE}",
                type="primary",
                use_container_width=True,
                key=f"{key_context}-monthly-submit",
            )

        state_key = f"prepared-order::{key_context}::monthly"
        if submitted:
            if not valid_email(delivery_email):
                st.error("Enter a valid delivery email before continuing to payment.")
                st.session_state.pop(state_key, None)
            else:
                try:
                    natal_snapshot, natal_precision = _build_monthly_checkout_natal(natal_values)
                except Exception as exc:
                    st.error(f"Natal details need attention: {exc}")
                    st.session_state.pop(state_key, None)
                else:
                    period_code = month_codes[month_label]
                    reference = build_order_reference(
                        "MONTHLY",
                        sign,
                        period_code,
                        timezone_name,
                        _order_token(key_context, "MONTHLY"),
                        main_focus=main_focus,
                        personal_question=personal_question,
                        nearest_city=nearest_city,
                    )
                    location, location_basis = resolve_location(
                        nearest_city,
                        timezone_name,
                    )
                    order = {
                        "product_code": "MONTHLY",
                        "report_name": "Monthly Strategic Report",
                        "email": delivery_email.strip(),
                        "sign": sign,
                        "period": month_label,
                        "period_code": period_code,
                        "timezone": timezone_name,
                        "nearest_city": location.name,
                        "location_basis": location_basis,
                        "main_focus": main_focus,
                        "personal_question": personal_question.strip(),
                        "reference": reference,
                        "natal_profile": encode_natal_profile(natal_snapshot),
                        "natal_summary": natal_profile_summary(natal_snapshot),
                        "natal_precision": natal_precision,
                    }
                    try:
                        order["checkout_url"] = _create_instant_checkout(order, "MONTHLY")
                    except Exception as exc:
                        st.error(f"Secure checkout is not ready: {exc}")
                        st.session_state.pop(state_key, None)
                    else:
                        st.session_state[state_key] = order
                        track_event(
                            "monthly_order_prepared",
                            {
                                "zodiac_sign": sign,
                                "report_period": period_code,
                                "timezone": timezone_name,
                                "main_focus": main_focus,
                                "natal_time_known": bool(natal_values.get("time_known")),
                            },
                        )

        order = st.session_state.get(state_key)
        if order:
            _order_summary(
                order["report_name"],
                order["sign"],
                order["period"],
                order["timezone"],
                order["nearest_city"],
                order["location_basis"],
                order["email"],
                order["main_focus"],
                order["personal_question"],
                order["reference"],
                order.get("natal_summary", ""),
                order.get("natal_precision", ""),
            )
            payment_button(
                f"Continue to secure payment — {MONTHLY_PRICE}",
                order["checkout_url"],
                f"{key_context}-monthly-payment-disabled",
                "monthly_report_click",
                {
                    "zodiac_sign": order["sign"],
                    "report_period": order["period_code"],
                    "order_reference": order["reference"],
                },
            )
            st.markdown(
                '<div class="checkout-note">'
                "Stripe opens in a new tab. After payment, Stripe returns you to Luna's private "
                "report page. The complete report opens immediately and Luna emails the same "
                "private return link straight away."
                "</div>",
                unsafe_allow_html=True,
            )

    with yearly_tab:
        years = year_choices()
        chosen_default_year = (
            prefill_year if prefill_year in years else default_year()
        )
        chosen_default_sign = (
            prefill_sign if prefill_sign in SIGNS else DEFAULT_SIGN
        )

        with st.form(f"{key_context}-yearly-checkout"):
            st.markdown("### Choose your year-ahead report")
            y1, y2 = st.columns(2)
            with y1:
                delivery_email = st.text_input(
                    "Delivery email",
                    key=f"{key_context}-yearly-email",
                    placeholder="name@example.com",
                )
                sign = st.selectbox(
                    "Your star sign",
                    SIGNS,
                    index=SIGNS.index(chosen_default_sign),
                    key=f"{key_context}-yearly-sign",
                    help="Use your Sun sign unless you know and prefer your rising sign.",
                )
            with y2:
                selected_year = st.selectbox(
                    "Calendar year",
                    years,
                    index=years.index(chosen_default_year),
                    key=f"{key_context}-yearly-period",
                )
                timezone_name = st.selectbox(
                    "Timezone",
                    TIMEZONES,
                    index=timezone_select_index(),
                    key=f"{key_context}-yearly-timezone",
                )
            nearest_city = st.text_input(
                "Nearest city for local light",
                value=prefill_city or "",
                key=f"{key_context}-yearly-city",
                placeholder=representative_city_name(timezone_name),
                help=city_input_help(timezone_name),
            )
            main_focus = st.selectbox(
                "Main priority for the year",
                YEARLY_FOCUS_CHOICES,
                key=f"{key_context}-yearly-focus",
                help="This guides which themes receive extra emphasis in the personalised PDF.",
            )
            personal_question = st.text_area(
                "Optional decision or transition",
                key=f"{key_context}-yearly-question",
                max_chars=QUESTION_MAX_CHARS,
                placeholder="Is there a major decision, relationship or transition to consider?",
                help=f"Optional. Maximum {QUESTION_MAX_CHARS} characters. It is stored with your secure Stripe checkout so Luna can personalise the report after payment.",
            )
            st.caption(
                "Instant delivery: after Stripe confirms payment, your report opens immediately and Luna emails your private return link."
            )
            submitted = st.form_submit_button(
                f"Prepare year-ahead checkout — {YEARLY_PRICE}",
                type="primary",
                use_container_width=True,
            )

        state_key = f"prepared-order::{key_context}::yearly"
        if submitted:
            if not valid_email(delivery_email):
                st.error("Enter a valid delivery email before continuing to payment.")
                st.session_state.pop(state_key, None)
            else:
                period_code = str(selected_year)
                reference = build_order_reference(
                    "YEAR",
                    sign,
                    period_code,
                    timezone_name,
                    _order_token(key_context, "YEAR"),
                    main_focus=main_focus,
                    personal_question=personal_question,
                    nearest_city=nearest_city,
                )
                location, location_basis = resolve_location(
                    nearest_city,
                    timezone_name,
                )
                order = {
                    "product_code": "YEAR",
                    "report_name": "Year-Ahead Strategic Report",
                    "email": delivery_email.strip(),
                    "sign": sign,
                    "period": f"Calendar year {selected_year}",
                    "period_code": period_code,
                    "timezone": timezone_name,
                    "nearest_city": location.name,
                    "location_basis": location_basis,
                    "main_focus": main_focus,
                    "personal_question": personal_question.strip(),
                    "reference": reference,
                }
                try:
                    order["checkout_url"] = _create_instant_checkout(order, "YEAR")
                except Exception as exc:
                    st.error(f"Secure checkout is not ready: {exc}")
                    st.session_state.pop(state_key, None)
                else:
                    st.session_state[state_key] = order
                    track_event(
                        "yearly_order_prepared",
                        {
                            "zodiac_sign": sign,
                            "report_period": period_code,
                            "timezone": timezone_name,
                            "main_focus": main_focus,
                        },
                    )

        order = st.session_state.get(state_key)
        if order:
            _order_summary(
                order["report_name"],
                order["sign"],
                order["period"],
                order["timezone"],
                order["nearest_city"],
                order["location_basis"],
                order["email"],
                order["main_focus"],
                order["personal_question"],
                order["reference"],
            )
            payment_button(
                f"Continue to secure payment — {YEARLY_PRICE}",
                order["checkout_url"],
                f"{key_context}-yearly-payment-disabled",
                "yearly_report_click",
                {
                    "zodiac_sign": order["sign"],
                    "report_period": order["period_code"],
                    "order_reference": order["reference"],
                },
            )
            st.markdown(
                '<div class="checkout-note">'
                "Stripe opens in a new tab. After payment, Stripe returns you to Luna's private "
                "report page and Luna emails the same private return link straight away."
                "</div>",
                unsafe_allow_html=True,
            )


def daily_controls(prefix: str = "daily") -> tuple[str, date, str, str]:
    first_row = st.columns(2, gap="medium")
    with first_row[0]:
        sign = st.selectbox(
            "Your zodiac sign",
            SIGNS,
            index=SIGNS.index(DEFAULT_SIGN),
            key=f"{prefix}-sign",
        )
    with first_row[1]:
        reading_date = st.date_input(
            "Date",
            value=browser_local_date(),
            min_value=date(1900, 1, 1),
            max_value=date(2100, 12, 31),
            key=f"{prefix}-date",
        )

    second_row = st.columns(2, gap="medium")
    with second_row[0]:
        timezone_name = st.selectbox(
            "Timezone",
            TIMEZONES,
            index=timezone_select_index(),
            key=f"{prefix}-timezone",
        )
    with second_row[1]:
        nearest_city = st.text_input(
            "Nearest city for local light",
            key=f"{prefix}-city",
            placeholder=representative_city_name(timezone_name),
            help=city_input_help(timezone_name),
        )

    st.caption(browser_time_caption())

    return sign, reading_date, timezone_name, nearest_city


@st.cache_data(show_spinner=False, ttl=86400)
def _previous_daily_texts(
    sign: str,
    reading_date_iso: str,
    timezone_name: str,
    days: int = 4,
) -> list[str]:
    reading_date = date.fromisoformat(reading_date_iso)
    texts: list[str] = []
    for offset in range(1, days + 1):
        prior = free_daily_reading(
            sign,
            reading_date - timedelta(days=offset),
            timezone_name,
        )
        texts.append(reading_comparison_text(prior))
    return texts


@st.cache_data(show_spinner=False, ttl=86400)
def _daily_solar_snapshot(
    sign: str,
    reading_date_iso: str,
    timezone_name: str,
    nearest_city: str,
) -> dict:
    return daily_solar_convergence(
        sign,
        date.fromisoformat(reading_date_iso),
        timezone_name,
        nearest_city=nearest_city,
    ).to_dict()


def render_free_reading(
    sign: str,
    reading_date: date,
    timezone_name: str,
    nearest_city: str = "",
) -> None:
    cache_key = (sign, reading_date.isoformat(), timezone_name)
    if st.session_state.get("daily_cache_key") != cache_key:
        with st.spinner("Reading the planetary pattern and active houses..."):
            st.session_state.daily_reading = free_daily_reading(
                sign,
                reading_date,
                timezone_name,
            )
            st.session_state.daily_cache_key = cache_key

    reading = st.session_state.daily_reading
    previous_texts = _previous_daily_texts(
        sign,
        reading_date.isoformat(),
        timezone_name,
    )
    narrative = build_daily_narrative(
        reading,
        sign=sign,
        reading_date=reading_date,
        timezone_name=timezone_name,
        house_voice=HOUSE_VOICE,
        previous_texts=previous_texts,
    )
    solar = _daily_solar_snapshot(
        sign,
        reading_date.isoformat(),
        timezone_name,
        nearest_city,
    )
    render_daily_narrative_v3(narrative, solar=solar)


def _daily_date_label(reading_date: date) -> str:
    return reading_date.strftime("%A, %d %B").replace(", 0", ", ")


def _daily_narrative_for_landing(
    sign: str,
    reading_date: date,
    timezone_name: str,
):
    """Build the lean Daily directly for the currently selected sign.

    The landing page deliberately does not cache the narrative in session_state.
    A zodiac-sign change must always rebuild the house map and narrative on the
    same rerun so one sign can never inherit another sign's Daily copy.
    """
    reading = free_daily_reading(sign, reading_date, timezone_name)
    previous_texts = _previous_daily_texts(
        sign,
        reading_date.isoformat(),
        timezone_name,
    )
    return build_daily_narrative(
        reading,
        sign=sign,
        reading_date=reading_date,
        timezone_name=timezone_name,
        house_voice=HOUSE_VOICE,
        previous_texts=previous_texts,
    )


def _query_daily_sign() -> str | None:
    try:
        raw = str(st.query_params.get("sign", "") or "").strip().lower()
    except Exception:
        raw = ""
    if not raw:
        return None
    for item in SIGNS:
        if sign_slug(item) == raw:
            return item
    return None


def _remember_daily_sign_in_url(sign: str) -> None:
    try:
        st.query_params["sign"] = sign_slug(sign)
    except Exception:
        pass


def _render_optional_luna_video() -> None:
    if not LUNA_YOUTUBE_FEATURED_VIDEO_URL:
        return
    st.markdown('<section class="luna-video-slot">', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Luna short</div>', unsafe_allow_html=True)
    playable_url = _youtube_playable_url(LUNA_YOUTUBE_FEATURED_VIDEO_URL)
    st.video(playable_url)
    if LUNA_YOUTUBE_CHANNEL_URL:
        st.markdown(
            f'<a class="lean-monthly-link" href="{escape(LUNA_YOUTUBE_CHANNEL_URL)}" target="_blank" rel="noopener">Luna on YouTube →</a>',
            unsafe_allow_html=True,
        )
    st.markdown('</section>', unsafe_allow_html=True)


def _render_lean_daily(path: str) -> None:
    set_page_metadata(
        "Daily Horoscope | Luna Convergence",
        "Read today's Luna Convergence horoscope for your zodiac sign, with one clear interpretation and one practical move.",
        path,
    )

    saved_sign = st.session_state.get("landing-daily-sign-v3195") or _query_daily_sign()
    saved_index = SIGNS.index(saved_sign) if saved_sign in SIGNS else None
    st.markdown(
        '<div class="daily-sign-picker-label">Choose your star sign</div>',
        unsafe_allow_html=True,
    )
    sign = st.selectbox(
        "Your zodiac sign",
        SIGNS,
        index=saved_index,
        placeholder="Select a sign",
        key="landing-daily-sign-v3195",
        label_visibility="collapsed",
        persist_state="session",
    )

    # A neutral first state is deliberate: Luna must never imply that a new
    # visitor is Sagittarius.  It also turns the first sign choice into a real
    # engagement signal instead of firing analytics automatically on page load.
    if sign is None:
        st.markdown(
            '<div class="lean-daily-empty">Choose your star sign to open today\'s horoscope.</div>',
            unsafe_allow_html=True,
        )
        return

    st.session_state["daily-sign"] = sign
    _remember_daily_sign_in_url(sign)

    last_sign = st.session_state.get("tracked_landing_daily_sign")
    if last_sign != sign:
        track_event(
            "daily_reading_generated",
            {"zodiac_sign": sign, "source": "daily_landing"},
        )
        st.session_state["tracked_landing_daily_sign"] = sign

    reading_date = browser_local_date()
    timezone_name = browser_timezone_name()
    narrative = _daily_narrative_for_landing(sign, reading_date, timezone_name)

    story = tuple(narrative.today_story[:2])
    story_html = "".join(
        f"<p>{escape(paragraph)}</p>" for paragraph in story if paragraph
    )
    question = narrative.reflection_questions[0] if narrative.reflection_questions else ""
    monthly_href = f"/august-2026-{sign_slug(sign)}"

    st.markdown(
        f"""
<section class="lean-daily" aria-label="Today's horoscope">
  <div class="lean-daily-meta">
    <strong>{escape(sign)}</strong>
    <span>{escape(_daily_date_label(reading_date))}</span>
  </div>
  <h1>{escape(narrative.hook_headline)}</h1>
  <div class="lean-daily-story">{story_html}</div>
  <div class="lean-daily-move">
    <div class="lean-daily-label">Your move</div>
    <p>{escape(narrative.action_today)}</p>
  </div>
  {f'<div class="lean-daily-question">{escape(question)}</div>' if question else ''}
  <div class="lean-daily-reset">Focus Reset</div>
  <a class="lean-monthly-link" href="{monthly_href}">See your August forecast →</a>
  <div class="lean-bookmark-note">Bookmark this page in your browser and Luna will reopen on {escape(sign)}.</div>
</section>
        """,
        unsafe_allow_html=True,
    )
    _render_optional_luna_video()


def _render_site_solar_wave(path: str) -> None:
    """Keep the solar clock present across the customer experience without clutter.

    Daily and Solar Year retain the fully labelled clock. Other customer pages
    use a 72px masthead version: same astronomical curve/current Sun, but no
    repeated tropic or gate labels. Operational/admin/payment pages stay clear.
    """
    clean = str(path or "").strip("/")
    if clean in {"ephemeris-admin", "editorial-preview", "payment-success"}:
        return
    full = clean in {"", "daily-horoscope", "august-2026-horoscopes", "solar-year"}
    if full:
        wave_html = solar_year_wave_svg(browser_local_now(), browser_timezone_name())
    else:
        wave_html = solar_year_wave_svg(
            browser_local_now(),
            browser_timezone_name(),
            compact=True,
        )
    st.markdown(wave_html, unsafe_allow_html=True)


def home_page() -> None:
    _render_lean_daily("/")


def daily_page() -> None:
    # Keep the established /daily-horoscope URL alive for bookmarks and links,
    # while showing the same stripped-back Daily experience as the homepage.
    _render_lean_daily("/daily-horoscope")


def _weekly_cards_html(days) -> str:
    cards: list[str] = []
    for item in days:
        cards.append(
            f"""
<article class="weekly-card">
  <div class="weekly-card-meta">
    <strong>{escape(item.weekday)}</strong>
    <span>{escape(item.date_label)}</span>
  </div>
  <div class="weekly-evidence">{escape(item.evidence)}</div>
  <h2>{escape(item.headline)}</h2>
  <p>{escape(item.line_one)}</p>
  <p>{escape(item.line_two)}</p>
  <div class="weekly-move">
    <div class="weekly-move-label">Your move</div>
    <p>{escape(item.action)}</p>
  </div>
</article>
            """
        )
    return "".join(cards)


def _render_weekly_cards(days, monday: date, *, studio: bool = False) -> None:
    studio_class = " weekly-studio" if studio else ""
    if studio:
        heading = (
            '<div class="weekly-kicker">Seven-day production preview</div>'
            f'<div class="weekly-range">{escape(week_label(monday))}</div>'
        )
    else:
        heading = (
            '<div class="weekly-kicker">Week ahead · Monday to Sunday</div>'
            f'<div class="weekly-range">{escape(week_label(monday))}</div>'
            '<h1>Seven days. One changing sky.</h1>'
            '<p class="weekly-intro">The shared planetary weather before it moves through your star sign. Each day gives you the evidence, the human pressure point and one clean move.</p>'
        )
    st.markdown(
        f"""
<section class="weekly-view{studio_class}" aria-label="Luna weekly astrology view">
  {heading}
  <div class="weekly-grid">{_weekly_cards_html(days)}</div>
</section>
        """,
        unsafe_allow_html=True,
    )


def _weekly_sign_summary(sign: str, monday: date, timezone_name: str) -> dict:
    """Translate the shared Monday-Sunday sky into a compact sign-specific layer."""
    sunday = monday + timedelta(days=6)
    data = period_report(
        sign,
        monday,
        sunday,
        timezone_name,
        week_label(monday),
        transition_count=7,
    )
    dominant = data.get("dominant_houses", [])[:3]
    house_numbers = [int(item.get("house", 1)) for item in dominant if item.get("house")]
    if not house_numbers:
        house_numbers = [1]
    areas = [HOUSE_NAMES.get(h, f"House {h}") for h in house_numbers[:2]]
    transitions = data.get("major_transitions", [])
    first = transitions[0] if transitions else None
    primary = house_numbers[0]
    strategy = HOUSE_STRATEGY.get(primary, {})
    action = strategy.get("action", "keep the facts visible before committing")
    risk = strategy.get("risk", "moving before the pattern is clear")
    headline = f"{areas[0]} comes into focus"
    interpretation = (
        f"This week's shared sky concentrates most strongly around {', '.join(a.lower() for a in areas)}. "
        f"The useful response is to {action}; the main risk is {risk}."
    )
    if first:
        first_title = first.get("title") or "The week's leading shift"
        interpretation = f"{first_title} sets the first pressure point. " + interpretation
    return {
        "sign": sign,
        "headline": headline,
        "areas": areas,
        "interpretation": interpretation,
        "move": action.rstrip("."),
    }



def _weekly_social_area(summary: dict) -> str:
    """Compress calculated weekly life areas into a phone-readable social-card label."""
    raw = " · ".join(str(x) for x in summary.get("areas", []) if x)
    replacements = (
        ("income, possessions and self-worth", "MONEY · VALUE · SELF-WORTH"),
        ("rest, hidden matters, closure and psychological patterns", "REST · CLOSURE · INNER LIFE"),
        ("identity, body and self-direction", "IDENTITY · DIRECTION"),
        ("money, possessions and self-worth", "MONEY · VALUE · SELF-WORTH"),
        ("communication, learning and local movement", "COMMUNICATION · LEARNING"),
        ("home, family and foundations", "HOME · FAMILY"),
        ("creativity, romance and pleasure", "CREATIVITY · ROMANCE"),
        ("work, health and daily systems", "WORK · ROUTINE"),
        ("partnerships, agreements and open rivals", "RELATIONSHIPS · AGREEMENTS"),
        ("shared money, intimacy and deep change", "SHARED MONEY · CHANGE"),
        ("travel, belief and higher learning", "TRAVEL · BELIEF · LEARNING"),
        ("career, reputation and public direction", "CAREER · DIRECTION"),
        ("friends, networks and future aims", "NETWORKS · FUTURE"),
    )
    value = raw.lower()
    for long_form, short_form in replacements:
        if long_form in value:
            return short_form
    first = str((summary.get("areas") or ["YOUR PRIORITIES"])[0])
    first = first.replace(" and ", " · ").replace(",", " ·")
    return " ".join(first.upper().split()[:5]).rstrip(" ·,")


def _weekly_social_move(summary: dict) -> str:
    """Compress the calculated strongest move without changing its meaning."""
    move = str(summary.get("move") or "Keep the facts visible before committing").strip().rstrip(".")
    low = move.lower()
    rules = (
        ("measure cash, margin and recurring cost separately", "MEASURE THE REAL COST"),
        ("keep the facts visible before committing", "VERIFY BEFORE COMMITTING"),
        ("remove the false assumption", "REMOVE THE FALSE ASSUMPTION"),
        ("change the method before adding effort", "CHANGE THE METHOD FIRST"),
        ("choose what deserves amplification", "AMPLIFY WHAT MATTERS"),
        ("state both prices", "NAME THE REAL COST"),
        ("do the necessary thing", "DO WHAT IS NECESSARY"),
    )
    for needle, short in rules:
        if needle in low:
            return short
    words = move.upper().split()
    return " ".join(words if len(words) <= 6 else words[:6]).rstrip(",;:")


def _weekly_social_card_copy(summary: dict, monday: date) -> str:
    """Canva-ready 1080x1920 copy for a four-second sign card."""
    sunday = monday + timedelta(days=6)
    date_line = f"{monday.strftime('%d %b').lstrip('0')}–{sunday.strftime('%d %b').lstrip('0')}".upper()
    return (
        f"THE WEEK AHEAD · {date_line}\n\n"
        f"{str(summary.get('sign', '')).upper()}\n\n"
        "WHERE IT LANDS\n"
        f"{_weekly_social_area(summary)}\n\n"
        "YOUR MOVE\n"
        f"{_weekly_social_move(summary)}.\n\n"
        "LUNA CONVERGENCE"
    )


def _render_weekly_sign_layer(sign: str, monday: date, timezone_name: str) -> None:
    summary = _weekly_sign_summary(sign, monday, timezone_name)
    st.markdown(f"## {escape(sign)} · The Week Ahead")
    st.markdown(f"### {escape(summary['headline'])}")
    st.markdown("**WHERE IT LANDS**")
    st.markdown(" · ".join(summary["areas"]))
    st.markdown(summary["interpretation"])
    st.markdown("**YOUR STRONGEST MOVE**")
    st.markdown(f"**{summary['move'].capitalize()}.**")




def _weekly_choice_options(anchor: date, weeks_back: int = 4, weeks_forward: int = 12):
    """Return ready-to-pick Monday starts around the current week."""
    current_monday = default_week_start(anchor)
    starts = [current_monday + timedelta(weeks=offset) for offset in range(-weeks_back, weeks_forward + 1)]
    return starts


def _weekly_choice_label(monday: date, current_monday: date) -> str:
    sunday = monday + timedelta(days=6)
    if monday == current_monday:
        prefix = "This week · "
    elif monday == current_monday + timedelta(weeks=1):
        prefix = "Next week · "
    elif monday == current_monday - timedelta(weeks=1):
        prefix = "Last week · "
    else:
        prefix = ""
    return f"{prefix}{monday.strftime('%d %b').lstrip('0')} – {sunday.strftime('%d %b %Y').lstrip('0')}"


def _youtube_playable_url(url: str) -> str:
    """Normalize YouTube Shorts/share links to the standard watch URL for desktop embeds."""
    value = str(url or "").strip()
    if not value:
        return ""
    if "youtube.com/shorts/" in value:
        video_id = value.split("youtube.com/shorts/", 1)[1].split("?", 1)[0].split("/", 1)[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
    if "youtu.be/" in value:
        video_id = value.split("youtu.be/", 1)[1].split("?", 1)[0].split("/", 1)[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
    return value

def weekly_page() -> None:
    set_page_metadata(
        "Weekly Astrology View | Luna Convergence",
        "One changing sky, translated for your star sign, with the week's evidence and practical moves.",
        "/weekly-view",
    )
    today = browser_local_date()
    current_monday = default_week_start(today)
    week_options = _weekly_choice_options(today)
    monday = st.selectbox(
        "Choose week",
        week_options,
        index=week_options.index(current_monday),
        format_func=lambda value: _weekly_choice_label(value, current_monday),
        key="weekly-view-week-v332",
    )
    timezone_name = browser_timezone_name()
    try:
        days = build_weekly_view(monday, timezone_name)
    except Exception as exc:
        st.error("Luna could not calculate this week's planetary pattern.")
        if EDITOR_PREVIEW_ENABLED:
            st.exception(exc)
        return

    st.markdown('<div class="weekly-kicker">Week ahead · Monday to Sunday</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="weekly-range">{escape(week_label(monday))}</div>', unsafe_allow_html=True)
    st.markdown("# One changing sky.")
    st.markdown("The planets make one shared pattern. **Where that pattern lands depends on your sign.**")
    sign = st.selectbox("Where does it land for you?", SIGNS, key="weekly-sign-v331")
    try:
        _render_weekly_sign_layer(sign, monday, timezone_name)
    except Exception as exc:
        st.warning("Luna could not build the sign-specific weekly layer, so the shared seven-day sky is shown below.")
        if EDITOR_PREVIEW_ENABLED:
            st.exception(exc)
    st.markdown("## The shared sky · Seven days")
    _render_weekly_cards(days, monday, studio=True)
    st.markdown('<a class="lean-monthly-link" href="/daily-horoscope">Open your sign-specific Daily Horoscope →</a>', unsafe_allow_html=True)


def weekly_studio_page() -> None:
    """Hidden owner workspace for the shared weekly sky and 12 sign translations."""
    set_page_metadata(
        "Weekly Video Studio | Luna Convergence",
        "Private Luna production workspace for one weekly sky, twelve sign cards and Monday-to-Sunday source material.",
        "/weekly-studio",
    )
    st.markdown('<div class="eyebrow">Owner production workspace</div>', unsafe_allow_html=True)
    st.markdown("# Weekly video studio")

    with st.expander("How to use this studio", expanded=True):
        st.markdown("""
1. **Choose any date** in the week you want. Luna automatically snaps it back to Monday.
2. Confirm the **timezone**. This controls the calculated weekly sky.
3. Use **One Changing Sky** as the opening frame of the weekly video.
4. Use the **1080 × 1920 SOCIAL CARD COPY** inside each sign. Luna automatically compresses the calculated *Where it lands* and *Your move* into four-second, phone-readable wording.
5. Keep the longer interpretation on the website; do not squeeze it onto the social card.
6. Use the existing **Monday-Sunday cards** for the seven separate Daily clips and as the evidence behind the weekly synthesis.
7. Export social/video artwork at **1080 × 1920 (9:16)**.

**Production rule:** calculate the sky once; translate it twelve ways. Do not manually invent twelve different skies.
        """)

    with st.form("weekly-studio-controls-v332", clear_on_submit=False):
        controls = st.columns(2, gap="medium")
        current_monday = default_week_start(browser_local_date())
        week_options = _weekly_choice_options(browser_local_date())
        with controls[0]:
            selected_monday = st.selectbox(
                "Choose week",
                week_options,
                index=week_options.index(current_monday),
                format_func=lambda value: _weekly_choice_label(value, current_monday),
                key="weekly-studio-week-v332",
            )
        with controls[1]:
            timezone_name = st.selectbox("Timezone", TIMEZONES, index=timezone_select_index(), key="weekly-studio-timezone-v332")
        st.form_submit_button("Build weekly sky + 12 signs", type="primary", use_container_width=True)

    monday = selected_monday
    days = build_weekly_view(monday, timezone_name)
    st.caption(f"Production week: Monday {monday.strftime('%d %B %Y').lstrip('0')} · {timezone_name}")

    st.markdown("## 12 sign translations")
    sign_summaries = []
    for sign in SIGNS:
        try:
            sign_summaries.append(_weekly_sign_summary(sign, monday, timezone_name))
        except Exception as exc:
            if EDITOR_PREVIEW_ENABLED:
                st.warning(f"{sign}: sign translation unavailable: {exc}")

    for item in sign_summaries:
        with st.expander(item["sign"], expanded=False):
            st.markdown(f"### {item['headline']}")
            st.markdown("**WHERE IT LANDS**  ")
            st.markdown(" · ".join(item["areas"]))
            st.markdown(item["interpretation"])
            st.markdown("**YOUR MOVE**  ")
            st.markdown(f"**{item['move'].capitalize()}.**")
            st.markdown("**1080 × 1920 SOCIAL CARD COPY**")
            social_copy = _weekly_social_card_copy(item, monday)
            st.code(social_copy, language=None, wrap_lines=True)

    all_sign_copy = "\n\n---\n\n".join(
        _weekly_social_card_copy(i, monday) for i in sign_summaries
    )
    st.download_button("Download all 12 sign cards copy", data=all_sign_copy, file_name=f"luna_week_{monday.isoformat()}_12_signs.txt", mime="text/plain", use_container_width=True)

    st.markdown("## Monday-Sunday source cards")
    _render_weekly_cards(days, monday, studio=True)
    combined_copy = all_video_copy(days)
    st.download_button("Download all seven daily scripts", data=combined_copy, file_name=f"luna_week_{monday.isoformat()}_daily_canva_copy.txt", mime="text/plain", use_container_width=True)
    if WEEKLY_BACKGROUND_PATH.exists():
        st.download_button("Download 1080 × 1920 background", data=WEEKLY_BACKGROUND_PATH.read_bytes(), file_name="luna_weekly_video_background_1080x1920.png", mime="image/png", use_container_width=True)



# ---------------------------------------------------------------------------
# Historical context layer
# ---------------------------------------------------------------------------
# Luna uses these scores internally only. Readers see plain-English precedent,
# not percentages.  The comparison is structural: houses + major transition
# labels.  It does not claim that the same real-world event must repeat.

def _history_tokens(value: str) -> set[str]:
    stop = {
        "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
        "enters", "entry", "moves", "move", "turns", "direct", "retrograde",
    }
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in str(value or ""))
    return {word for word in cleaned.split() if len(word) > 2 and word not in stop}


def _monthly_structure_signature(result: dict) -> dict:
    houses = [
        int(item.get("house"))
        for item in (result.get("dominant_houses") or [])[:4]
        if item.get("house")
    ]
    titles = [str(item.get("title") or "") for item in (result.get("major_transitions") or [])[:8]]
    tokens = set()
    for title in titles:
        tokens |= _history_tokens(title)
    return {"houses": houses, "tokens": tokens, "titles": titles}


def _set_similarity(left: set, right: set) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _monthly_similarity(current: dict, past: dict) -> float:
    a = _monthly_structure_signature(current)
    b = _monthly_structure_signature(past)
    house_a, house_b = set(a["houses"]), set(b["houses"])
    house_score = _set_similarity(house_a, house_b)
    token_score = _set_similarity(a["tokens"], b["tokens"])
    top_house = 1.0 if a["houses"] and b["houses"] and a["houses"][0] == b["houses"][0] else 0.0
    return (0.58 * house_score) + (0.32 * token_score) + (0.10 * top_house)


@st.cache_data(show_spinner=False, ttl=60 * 60 * 12)
def _monthly_history_matches(sign: str, year: int, month: int, timezone_name: str, lookback_years: int = 18) -> list[dict]:
    """Find the closest same-month sign-level sky structures in prior years."""
    if month == 12:
        current_end = date(year, 12, 31)
    else:
        current_end = date(year, month + 1, 1) - timedelta(days=1)
    current = period_report(
        sign,
        date(year, month, 1),
        current_end,
        timezone_name,
        f"{month_name[month]} {year}",
        transition_count=9,
    )
    current_sig = _monthly_structure_signature(current)
    matches = []
    for past_year in range(year - 1, max(1949, year - lookback_years) - 1, -1):
        try:
            if month == 12:
                past_end = date(past_year, 12, 31)
            else:
                past_end = date(past_year, month + 1, 1) - timedelta(days=1)
            past = period_report(
                sign,
                date(past_year, month, 1),
                past_end,
                timezone_name,
                f"{month_name[month]} {past_year}",
                transition_count=9,
            )
            score = _monthly_similarity(current, past)
            past_sig = _monthly_structure_signature(past)
            shared_houses = [h for h in current_sig["houses"] if h in set(past_sig["houses"])]
            current_only = [h for h in current_sig["houses"] if h not in set(past_sig["houses"])]
            past_only = [h for h in past_sig["houses"] if h not in set(current_sig["houses"])]
            matches.append({
                "year": past_year,
                "score": score,
                "shared_houses": shared_houses,
                "current_only": current_only,
                "past_only": past_only,
                "past_first_title": (past_sig["titles"][0] if past_sig["titles"] else ""),
            })
        except Exception:
            continue
    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches[:3]


def _house_short(house: int) -> str:
    name = str(HOUSE_NAMES.get(house, f"House {house}"))
    # Keep historical comparison conversational rather than technical.
    return name.lower()


def _render_monthly_history(
    sign: str,
    year: int,
    month: int,
    timezone_name: str,
    birth_date_value: date | None = None,
) -> None:
    """Reader-facing precedent: age + shared theme + a concrete then/now contrast."""
    try:
        matches = _monthly_history_matches(sign, int(year), int(month), timezone_name)
    except Exception:
        return
    if not matches:
        return

    st.markdown("### Have you been somewhere like this before?")
    st.markdown(
        "Luna looks backward for earlier months with a similar **sky structure**. "
        "The point is not to say that the same event repeats. It is to give the present month a reference point."
    )

    for index, item in enumerate(matches, start=1):
        past_year = int(item["year"])
        past_label = f"{month_name[int(month)]} {past_year}"
        shared = item.get("shared_houses") or []
        now_only = item.get("current_only") or []
        then_only = item.get("past_only") or []

        age_line = ""
        if birth_date_value:
            reference_date = date(past_year, int(month), 15)
            if reference_date >= birth_date_value:
                age = reference_date.year - birth_date_value.year - (
                    (reference_date.month, reference_date.day) < (birth_date_value.month, birth_date_value.day)
                )
                age_line = f"You were about **{age}**."

        heading = "Think back" if index == 1 else "Another echo"
        st.markdown(f"### {heading} · {past_label}")
        if age_line:
            st.markdown(age_line)

        if shared:
            shared_text = " and ".join(_house_short(h) for h in shared[:2])
            st.markdown(
                f"**What rhymes:** both periods put unusual weight on **{shared_text}**. "
                "That is the part worth remembering."
            )
        else:
            st.markdown(
                "**What rhymes:** the sequence of planetary changes is unusually close, "
                "even though the emphasis does not land in exactly the same life areas."
            )

        if now_only and then_only:
            st.markdown(
                f"**What changes the meaning now:** the present month adds **{_house_short(now_only[0])}**, "
                f"while {past_label} leaned more toward **{_house_short(then_only[0])}**."
            )
        elif now_only:
            st.markdown(
                f"**What changes the meaning now:** this month adds **{_house_short(now_only[0])}** "
                "to a pattern that was simpler before."
            )
        elif then_only:
            st.markdown(
                f"**What changes the meaning now:** {past_label} carried more **{_house_short(then_only[0])}**; "
                "that extra weight is not as dominant now."
            )
        else:
            st.markdown(
                "**What changes the meaning now:** the same broad structure returns with a different supporting cast. "
                "Treat it as an echo, not a replay."
            )

        st.caption(
            "Memory prompt: what was changing around love, work, money, home or direction? "
            "You supply the memory; Luna supplies the astronomical reference."
        )

    with st.expander("How Luna chose these dates"):
        st.markdown(
            "Luna compares the month's dominant whole-sign houses and major planetary transition labels with earlier "
            "months for the same sign, ranks the closest structures internally, and shows only the clearest precedents. "
            "The hidden similarity score is a retrieval tool — not a probability that an event will happen."
        )


_TRANSIT_RECURRENCE_YEARS = {
    "Jupiter": 11.86,
    "Saturn": 29.46,
    "Uranus": 84.01,
    "Neptune": 164.8,
    "Pluto": 248.0,
}


def _previous_transit_echo_date(story) -> date | None:
    """Estimate the previous recurrence of the same slow-planet transit family."""
    if not getattr(story, "hits", None):
        return None
    years = _TRANSIT_RECURRENCE_YEARS.get(str(getattr(story, "transit_planet", "")))
    if not years:
        return None
    aspect = str(getattr(story, "aspect", "")).lower()
    # Squares/trines/sextiles occur at two geometrically equivalent points per orbit.
    factor = 0.5 if any(word in aspect for word in ("square", "trine", "sextile")) else 1.0
    days = int(round(years * factor * 365.2425))
    return story.hits[0].exact_date - timedelta(days=days)


def _transit_human_theme(story) -> str:
    planet = str(getattr(story, "transit_planet", ""))
    target = str(getattr(story, "natal_target", ""))
    house = getattr(story, "natal_house", None)
    planet_theme = {
        "Saturn": "responsibility, limits and what has to become sustainable",
        "Uranus": "freedom, disruption and the cost of staying unchanged",
        "Jupiter": "growth, visibility and the opening that becomes available",
        "Neptune": "uncertainty, ideals and what needs clearer boundaries",
        "Pluto": "power, control and what can no longer remain superficial",
    }.get(planet, "change and timing")
    house_text = f" in natal house {house}" if house else ""
    return f"{planet_theme}{house_text}, working through your natal {target}"


def _render_transit_history(story, birth_date_value: date | None = None) -> None:
    """Human precedent: age, remembered life theme, and what makes the current transit distinct."""
    earlier = _previous_transit_echo_date(story)
    if earlier is None:
        return

    st.markdown("### Have you been here before?")
    theme = _transit_human_theme(story)

    if birth_date_value and earlier >= birth_date_value:
        age = earlier.year - birth_date_value.year - (
            (earlier.month, earlier.day) < (birth_date_value.month, birth_date_value.day)
        )
        st.markdown(f"**Think back to {_timing_date_label(earlier)}. You were about {age}.**")
        st.markdown(
            f"The same broad **{story.transit_planet}–{story.natal_target} transit family** was returning then. "
            f"The recurring question is less about a literal event and more about **{theme}**."
        )
        st.markdown(
            "**What do you remember?** Was that period more about home, work, money, relationships, independence, "
            "responsibility or a change in direction?"
        )
    else:
        st.markdown(f"**Before your time · around {_timing_date_label(earlier)}**")
        st.markdown(
            f"You may not have lived through this earlier cycle, but the sky did. "
            f"It gives the present **{story.transit_planet}–{story.natal_target}** contact a longer context: **{theme}**."
        )

    polarity = str(getattr(story, "polarity", "")).lower()
    if "opportun" in polarity:
        difference = (
            "This time the current report ranks the transit as an **opening**. "
            "The useful question is not whether the old story repeats, but whether you can use the room that exists now."
        )
    elif "pressure" in polarity:
        difference = (
            "This time the current report ranks the transit as a **test or constraint**. "
            "The useful comparison is what you tolerated then versus what now needs a clearer limit, term or decision."
        )
    else:
        difference = (
            "This time the exact dates, supporting transits and your present life stage alter the meaning. "
            "The earlier cycle is a reference point, not a script."
        )
    st.markdown(f"**What is different now:** {difference}")
    st.caption(
        "Luna keeps the recurrence calculation behind the scenes. The reader-facing question is simpler: "
        "what feels familiar, and what is materially different this time?"
    )


def render_monthly_preview_workspace() -> None:
    """Owner-only Monthly editorial workspace. Public customers use the unified free Monthly page."""
    local_today = browser_local_date()
    default_year_value = min(max(local_today.year, 1950), 2100)
    default_month_value = local_today.month

    st.caption(browser_time_caption())

    with st.form("monthly-preview-form", clear_on_submit=False):
        first_row = st.columns(3, gap="medium")
        with first_row[0]:
            sign = st.selectbox(
                "Star sign",
                SIGNS,
                index=SIGNS.index(DEFAULT_SIGN),
                key="monthly-preview-sign",
            )
        with first_row[1]:
            forecast_year = st.number_input(
                "Year",
                min_value=1950,
                max_value=2100,
                value=default_year_value,
                step=1,
                key="monthly-preview-year",
            )
        with first_row[2]:
            selected_month = st.selectbox(
                "Month",
                list(range(1, 13)),
                index=default_month_value - 1,
                format_func=lambda value: month_name[value],
                key="monthly-preview-month",
            )

        second_row = st.columns(2, gap="medium")
        with second_row[0]:
            timezone_name = st.selectbox(
                "Timezone",
                TIMEZONES,
                index=timezone_select_index(),
                key="monthly-preview-timezone",
            )
        with second_row[1]:
            nearest_city = st.text_input(
                "Nearest city",
                value=representative_city_name(timezone_name),
                help=city_input_help(timezone_name),
                key="monthly-preview-city",
            )

        main_focus = st.selectbox(
            "Main focus",
            MONTHLY_FOCUS_CHOICES,
            key="monthly-preview-focus",
        )

        submitted = st.form_submit_button(
            "Generate full monthly preview",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        year = int(forecast_year)
        month = int(selected_month)

        try:
            with st.spinner(
                f"Building {sign} — {month_name[month]} {year}..."
            ):
                narrative, result = build_production_monthly_report(
                    sign=sign,
                    year=year,
                    month=month,
                    timezone_name=timezone_name,
                    nearest_city=nearest_city,
                    main_focus=main_focus,
                )
        except Exception as exc:
            st.error("Luna could not generate this monthly preview.")
            st.exception(exc)
            return

        st.session_state["monthly-preview-result"] = result
        st.session_state["monthly-preview-narrative"] = narrative
        st.session_state["monthly-preview-focus-value"] = main_focus
        st.session_state["monthly-preview-history-context"] = {
            "sign": sign, "year": year, "month": month, "timezone_name": timezone_name
        }
        st.rerun()

    result = st.session_state.get("monthly-preview-result")
    if not result:
        st.info(
            "Choose a sign and month, then generate the preview. "
            "The complete customer-style monthly report will appear below."
        )
        return

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.caption(
        f"{result.get('sign')} / {result.get('label')} · "
        "full editorial preview · no checkout"
    )

    narrative = st.session_state.get("monthly-preview-narrative")
    if narrative is None:
        narrative = build_monthly_narrative(
            result,
            main_focus=st.session_state.get(
                "monthly-preview-focus-value",
                "General overview",
            ),
        )
    render_production_monthly_report(
        narrative,
        result,
        show_print=True,
    )
    history_context = st.session_state.get("monthly-preview-history-context") or {}
    if history_context:
        _render_monthly_history(
            history_context.get("sign", result.get("sign", DEFAULT_SIGN)),
            int(history_context.get("year", local_today.year)),
            int(history_context.get("month", local_today.month)),
            str(history_context.get("timezone_name") or browser_timezone_name()),
        )


def monthly_preview_page() -> None:
    """Unlisted owner/editor route for viewing complete monthly reports."""
    set_page_metadata(
        "Monthly Preview | Luna Convergence",
        "Unlisted editorial workspace for generating complete Luna monthly reports without checkout.",
        "/monthly-preview",
    )
    st.markdown(
        '<div class="eyebrow">Unlisted editorial workspace</div>',
        unsafe_allow_html=True,
    )
    st.markdown("# Monthly preview")
    st.markdown(
        "Generate any Luna monthly report here without entering Stripe. "
        "This route is intentionally excluded from the normal navigation."
    )
    st.warning(
        "Editorial testing only. This page renders the complete monthly product, "
        "including the browser print/save controls."
    )
    render_monthly_preview_workspace()


def render_report_generator_workspace() -> None:
    report_type = st.radio(
        "Report type",
        ["Monthly", "Year ahead"],
        horizontal=True,
        key="report-generator-type",
    )

    with st.form("report-generator-form", clear_on_submit=False):
        first_row = st.columns(3, gap="medium")
        with first_row[0]:
            sign = st.selectbox(
                "Star sign",
                SIGNS,
                index=SIGNS.index(DEFAULT_SIGN),
                key="report-generator-sign",
            )
        with first_row[1]:
            forecast_year = st.number_input(
                "Year",
                min_value=1950,
                max_value=2100,
                value=2026 if report_type == "Monthly" else 2027,
                step=1,
                key=f"report-generator-year-{report_type}",
            )
        with first_row[2]:
            selected_month = st.selectbox(
                "Month",
                list(range(1, 13)),
                index=7,
                format_func=lambda value: month_name[value],
                disabled=report_type != "Monthly",
                key="report-generator-month",
            )

        second_row = st.columns(2, gap="medium")
        with second_row[0]:
            timezone_name = st.selectbox(
                "Timezone",
                TIMEZONES,
                index=timezone_select_index(),
                key="report-generator-timezone",
            )
        with second_row[1]:
            nearest_city = st.text_input(
                "Nearest city",
                value=representative_city_name(timezone_name),
                help=city_input_help(timezone_name),
                key="report-generator-city",
            )

        focus_choices = (
            MONTHLY_FOCUS_CHOICES
            if report_type == "Monthly"
            else YEARLY_FOCUS_CHOICES
        )
        main_focus = st.selectbox(
            "Main focus",
            focus_choices,
            key=f"report-generator-focus-{report_type}",
        )

        submitted = st.form_submit_button(
            "Generate customer report",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        year = int(forecast_year)
        if report_type == "Monthly":
            start_date = date(year, selected_month, 1)
            if selected_month == 12:
                end_date = date(year, 12, 31)
            else:
                end_date = (
                    date(year, selected_month + 1, 1)
                    - timedelta(days=1)
                )
            result = period_report(
                sign,
                start_date,
                end_date,
                timezone_name,
                f"{month_name[selected_month]} {year}",
                transition_count=9,
                nearest_city=nearest_city,
                main_focus=main_focus,
            )
        else:
            result = period_report(
                sign,
                date(year, 1, 1),
                date(year, 12, 31),
                timezone_name,
                str(year),
                transition_count=9,
                nearest_city=nearest_city,
                main_focus=main_focus,
            )

        st.session_state["report-generator-result"] = result
        st.session_state["report-generator-focus"] = main_focus
        st.rerun()

    result = st.session_state.get("report-generator-result")
    if not result:
        return

    st.caption(
        f"{result.get('sign')} / {result.get('label')} • "
        f"{BUILD_LABEL} • Checkout bypassed"
    )

    if result.get("period") == "monthly":
        narrative = build_monthly_narrative(
            result,
            main_focus=st.session_state.get(
                "report-generator-focus",
                "General overview",
            ),
        )
        render_monthly_experience(
            narrative,
            result,
            show_print=True,
            preview=False,
        )
    elif result.get("period") == "yearly":
        render_yearly_experience(
            result,
            show_print=True,
        )


def forecast_library_page() -> None:
    if not EDITOR_PREVIEW_ENABLED:
        st.error("Forecast library is disabled.")
        return

    set_page_metadata(
        "Forecast Library | Luna Convergence",
        "Precompute, review and download daily, monthly and yearly Luna forecast inventory.",
        "/forecast-library",
    )
    st.markdown('<div class="eyebrow">Editorial production</div>', unsafe_allow_html=True)
    st.markdown("# Build the forecast inventory")
    st.markdown(
        "Precompute the common astronomical structure and Luna narrative, then "
        "apply city, focus and customer-question personalisation at delivery."
    )

    voice_cols = st.columns(3, gap="medium")
    for column, product in zip(voice_cols, ("daily", "monthly", "yearly")):
        profile = voice_profile(product)
        with column:
            st.markdown(f"### {product.title()}")
            st.caption(profile.narrator_role)
            st.write(profile.purpose)
            st.markdown(f"**Pace:** {profile.pace}")
    st.caption(narrator_principle())
    st.page_link(
        EPHEMERIS_ADMIN_REF,
        label="Manage ephemeris years / run historical test",
        use_container_width=True,
    )

    report_type = st.radio(
        "Inventory type",
        ["daily", "monthly", "yearly"],
        horizontal=True,
        format_func=str.title,
        key="inventory-report-type",
    )

    with st.form("forecast-inventory-form", clear_on_submit=False):
        top = st.columns(3, gap="medium")
        with top[0]:
            year = int(st.number_input("Year", min_value=1950, max_value=2100, value=2027, step=1))
        with top[1]:
            timezone_name = st.selectbox(
                "Timezone basis",
                TIMEZONES,
                index=timezone_select_index(),
            )
        with top[2]:
            city = st.text_input(
                "Representative city",
                value=representative_city_name(timezone_name),
                help="Used for the local-light layer. Customer delivery can apply a different city.",
            )

        signs = st.multiselect(
            "Signs",
            SIGNS,
            default=[DEFAULT_SIGN],
            help="Choose one sign for editorial refinement or several for batch production.",
        )
        status = st.selectbox(
            "Editorial status",
            EDITORIAL_STATUSES,
            index=EDITORIAL_STATUSES.index("calculated"),
        )

        months: list[int] = []
        start_date = None
        end_date = None
        if report_type == "daily":
            dates = st.columns(2, gap="medium")
            with dates[0]:
                start_date = st.date_input("Start date", value=date(year, 1, 1))
            with dates[1]:
                end_date = st.date_input("End date", value=date(year, 1, 7))
            main_focus = "Daily overview"
            estimate = len(signs) * (((end_date - start_date).days + 1) if end_date >= start_date else 0)
        elif report_type == "monthly":
            months = st.multiselect(
                "Months",
                list(range(1, 13)),
                default=[1],
                format_func=lambda value: month_name[value],
            )
            main_focus = st.selectbox("Core focus", MONTHLY_FOCUS_CHOICES)
            estimate = len(signs) * len(months)
        else:
            main_focus = st.selectbox("Core focus", YEARLY_FOCUS_CHOICES)
            estimate = len(signs)

        st.caption(f"Estimated records: {estimate}")
        submitted = st.form_submit_button(
            "Generate inventory",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not signs:
            st.error("Choose at least one sign.")
            return
        try:
            with st.spinner("Calculating the forecast inventory..."):
                records = build_inventory(
                    report_type,
                    signs,
                    year=year,
                    timezone_name=timezone_name,
                    city=city,
                    months=months,
                    start_date=start_date,
                    end_date=end_date,
                    main_focus=main_focus,
                    status=status,
                )
                document = inventory_json(records)
            st.session_state["forecast-inventory-json"] = document
            st.session_state["forecast-inventory-count"] = len(records)
            st.session_state["forecast-inventory-name"] = (
                f"luna_{report_type}_inventory_{year}.json"
            )
        except Exception as exc:
            st.exception(exc)
            return

    document = st.session_state.get("forecast-inventory-json")
    if document:
        count = int(st.session_state.get("forecast-inventory-count", 0))
        st.success(f"Generated {count} forecast record{'s' if count != 1 else ''}.")
        st.download_button(
            "Download forecast inventory",
            data=document,
            file_name=st.session_state.get("forecast-inventory-name", "luna_forecast_inventory.json"),
            mime="application/json",
            use_container_width=True,
        )
        with st.expander("Inventory preview", expanded=False):
            preview = json.loads(document)
            st.json({
                "inventory_version": preview.get("inventory_version"),
                "record_count": preview.get("record_count"),
                "first_record": (preview.get("records") or [{}])[0],
            })


def ephemeris_admin_page() -> None:
    set_page_metadata(
        "Ephemeris Admin | Luna Convergence",
        "Register durable yearly ephemeris references and run historical Luna stress tests.",
        "/ephemeris-admin",
    )
    render_ephemeris_admin(
        editor_preview_enabled=EDITOR_PREVIEW_ENABLED,
        default_sign=DEFAULT_SIGN,
        default_timezone=DEFAULT_TIMEZONE,
        timezones=TIMEZONES,
    )


def editorial_preview_page() -> None:
    if not EDITOR_PREVIEW_ENABLED:
        st.error("Editorial preview is disabled.")
        return

    set_page_metadata(
        "Editorial Preview | Luna Convergence",
        "Generate and print complete Luna monthly and year-ahead reports without checkout while the product is being edited.",
        "/editorial-preview",
    )
    st.markdown(
        '<div class="eyebrow">Temporary editorial workspace</div>',
        unsafe_allow_html=True,
    )
    st.markdown("# Preview before payment")
    st.warning(
        f"{BUILD_LABEL} is running with Stripe bypassed. "
        "Set EDITOR_PREVIEW_ENABLED to False before the paid public launch."
    )
    render_report_generator_workspace()


def reports_page() -> None:
    set_page_metadata(
        "Monthly and Year-Ahead Astrology Reports | Luna Convergence",
        "Order a monthly strategic astrology report or a detailed year-ahead forecast delivered electronically.",
        "/reports",
    )

    # Private monthly preview fallback. This deliberately uses the existing
    # /reports route so the preview remains reachable even if a deployment
    # has trouble recognising the separate /monthly-preview route.
    preview_mode = str(st.query_params.get("preview", "")).strip().lower()
    if preview_mode in {"monthly", "month", "monthly-report"}:
        st.markdown(
            '<div class="eyebrow">Private monthly preview</div>',
            unsafe_allow_html=True,
        )
        st.markdown("# Generate a complete monthly report")
        st.caption(
            "Preview workspace — no Stripe checkout. Choose the sign, month, "
            "year and location settings, then generate the full Luna monthly."
        )
        render_monthly_preview_workspace()
        return
    if EDITOR_PREVIEW_ENABLED:
        st.markdown(
            '<div class="eyebrow">Monthly and year-ahead reports</div>',
            unsafe_allow_html=True,
        )
        st.markdown("# Generate the complete report")
        st.markdown(
            "Use the same Luna customer interface locally or on the website. "
            "Choose the period, generate the reading and print it directly from "
            "the page. Stripe is temporarily bypassed while editing."
        )
        render_report_generator_workspace()
        return

    st.markdown('<div class="eyebrow">Paid reports</div>', unsafe_allow_html=True)
    st.markdown("# Choose the depth you need")
    st.markdown(
        "Choose your star sign and report period before entering Stripe. "
        "After payment, Luna verifies the Stripe session and generates the complete report immediately."
    )
    if EDITOR_PREVIEW_ENABLED:
        st.warning(
            f"Editorial preview is enabled for {BUILD_LABEL}. "
            "Stripe is bypassed while Luna is being edited."
        )
        st.page_link(
            EDITORIAL_PREVIEW_REF,
            label="Open the full printable editorial preview",
            use_container_width=True,
        )
    report_cta(context="reports")

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("## How ordering works")
    c1, c2, c3 = st.columns(3, gap="large")
    steps = [
        (
            "1. Choose",
            "Select the report, sign, period, timezone, main focus, optional question and delivery email.",
        ),
        (
            "2. Pay",
            "Continue to the secure Stripe checkout carrying your Luna order reference.",
        ),
        (
            "3. Receive",
            "Stripe returns you to Luna immediately. Read the full report online, download the monthly PDF and use the emailed private return link.",
        ),
    ]
    for column, (title, body) in zip((c1, c2, c3), steps):
        with column:
            st.markdown(
                f'<div class="card"><h3>{escape(title)}</h3><p>{escape(body)}</p></div>',
                unsafe_allow_html=True,
            )

    with st.expander("Already paid without selecting a star sign or report period?"):
        st.markdown(
            "Use this recovery form for an earlier payment. It prepares an email "
            "with the missing fulfilment information and your payment reference."
        )
        with st.form("report-order-details"):
            product = st.selectbox(
                "Report ordered",
                [
                    f"Monthly Strategic Report — {MONTHLY_PRICE}",
                    f"Year-Ahead Strategic Report — {YEARLY_PRICE}",
                ],
            )
            c1, c2 = st.columns(2)
            with c1:
                customer_name = st.text_input("Name")
                customer_email = st.text_input("Email")
                sign = st.selectbox(
                    "Star sign",
                    SIGNS,
                    index=SIGNS.index(DEFAULT_SIGN),
                )
            with c2:
                requested_period = st.text_input(
                    "Requested month or calendar year",
                    placeholder="Example: August 2026 or 2027",
                )
                timezone_name = st.selectbox(
                    "Timezone",
                    TIMEZONES,
                    index=timezone_select_index(),
                )
                payment_reference = st.text_input(
                    "Stripe payment reference or receipt number",
                    placeholder="Add the reference shown in Stripe or your receipt",
                )
            nearest_city = st.text_input(
                "Nearest city for local light",
                placeholder=representative_city_name(timezone_name),
                help=city_input_help(timezone_name),
                key="recovery-nearest-city",
            )
            recovery_focus_options = list(
                dict.fromkeys(MONTHLY_FOCUS_CHOICES + YEARLY_FOCUS_CHOICES)
            )
            main_focus = st.selectbox(
                "Main focus",
                recovery_focus_options,
                key="recovery-main-focus",
            )
            personal_question = st.text_area(
                "Optional personal question",
                max_chars=QUESTION_MAX_CHARS,
                key="recovery-personal-question",
            )
            submitted = st.form_submit_button(
                "Prepare recovery email",
                type="primary",
            )

        if submitted:
            if not customer_name or not valid_email(customer_email) or not requested_period:
                st.error("Enter your name, a valid email and the requested month or year.")
            elif CONTACT_EMAIL == "your-email@example.com":
                st.warning(
                    "The site owner must add CONTACT_EMAIL to Streamlit secrets before public launch."
                )
            else:
                mailto = prepared_order_email(
                    CONTACT_EMAIL,
                    product,
                    customer_name,
                    customer_email,
                    sign,
                    requested_period,
                    timezone_name,
                    payment_reference,
                    main_focus=main_focus,
                    personal_question=personal_question,
                    nearest_city=nearest_city,
                )
                st.link_button(
                    "Open the prepared recovery email",
                    mailto,
                    use_container_width=True,
                )

        if REPORT_REQUEST_URL:
            st.link_button(
                "Use the online order-details form instead",
                REPORT_REQUEST_URL,
            )

def houses_page() -> None:
    set_page_metadata(
        "The 12 Astrological Houses | Luna Convergence",
        "Learn what the twelve astrological houses mean for identity, income, communication, home, work, relationships, career and long-term goals.",
        "/house-guide",
    )
    st.markdown('<div class="eyebrow">House guide</div>', unsafe_allow_html=True)
    st.markdown("# The twelve areas of life")
    st.markdown(
        "**Planets** describe what force is operating. **Signs** describe how it behaves. "
        "**Houses** describe where in life it operates."
    )
    sign = st.selectbox(
        "Show the whole-sign house map for",
        SIGNS,
        index=SIGNS.index(DEFAULT_SIGN),
        key="house-guide-sign",
    )
    st.markdown(house_reference_matrix(sign))

    st.markdown("## Build, protect, review and consolidate")
    st.markdown(
        """
- **Build around a house:** invest in the constructive potential of that life area.
- **Protect against a house:** add safeguards where pressure or volatility is concentrated.
- **Review a house:** correct the area before expanding it during a retrograde cycle.
- **Consolidate a house:** make gains repeatable, measurable and durable.
        """
    )

    st.markdown("## Use this sign for a report")
    st.markdown(
        "The twelve-house map is fixed by the selected sign, so it does **not** need "
        "a month selector. The purchase panel below asks for a month or calendar year "
        "because that determines which planetary movements are analysed."
    )
    report_cta(
        context="house-guide",
        prefill_sign=sign,
    )


def sample_page() -> None:
    set_page_metadata(
        "Sagittarius 2026 Astrology Report Sample | Luna Convergence",
        "Read a sample Luna Convergence year-ahead astrology report showing houses, transitions, convergence points and practical conclusions.",
        "/sample-report",
    )
    st.markdown('<div class="eyebrow">Example report</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="editorial-title">Sagittarius 2026 —<br>sample</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "This excerpt shows the depth and structure of a year-ahead report without publishing every paid section."
    )

    st.markdown(
        """
<div class="card">
  <div class="eyebrow">Core theme</div>
  <h3>Expansion becomes useful only when the foundations can carry it</h3>
  <p>The year connects creative enterprise, partnerships, communication and international reach.
  The main question is not whether opportunity exists, but whether money, contracts and operations
  can support the scale of the opening.</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## Example major transition")
    st.markdown(
        """
### Jupiter enters the ninth house

The ninth house governs **travel, publishing, higher education, law and foreign markets**.  
The opportunity is to take one proven idea into a larger territory. The risk is expanding before
shipping, pricing, content or legal systems are ready.

**Strategic response:** prove the offer in one market, document the process, then increase reach.
        """
    )

    st.markdown("## Example convergence point")
    st.markdown(
        """
### Expansion versus control

Several events connect houses 3, 5, 7 and 9: communication, creativity, contracts and foreign reach.
The interaction matters more than any single aspect. A partnership or media opportunity can accelerate
growth, but unclear ownership, payment or messaging can turn the same opening into a power struggle.

**Sequence:** clarify the agreement, test the channel, measure the result and only then scale.
        """
    )

    st.markdown("## Example two-sentence conclusion")
    st.info(
        "House 9 governs travel, publishing, higher education, law and foreign markets, "
        "so the best strategy for Sagittarius is to take one proven idea into a larger territory. "
        "House 2 governs personal income, pricing, possessions and self-worth, so short-term pressure "
        "in this area—especially confusing turnover, credit or possessions with financial strength—"
        "should not derail the larger transition."
    )

    report_cta(
        context="sample",
        prefill_sign=DEFAULT_SIGN,
        prefill_year=2026,
    )


def method_page() -> None:
    set_page_metadata(
        "How Luna Convergence Astrology Works",
        "See how Luna Convergence combines Swiss Ephemeris calculations, whole-sign houses, retrogrades, eclipses and convergence-point interpretation.",
        "/how-it-works",
    )
    st.markdown('<div class="eyebrow">Method and transparency</div>', unsafe_allow_html=True)
    st.markdown("# How the forecast is built")
    st.markdown(
        """
1. **Swiss Ephemeris** calculates tropical geocentric planetary positions.
2. The selected sign becomes **house 1** under the whole-sign method.
3. The engine detects aspects, sign changes, stations, lunations and eclipses.
4. Retrogrades are reconstructed as pre-shadow, retrograde, direct and post-shadow phases.
5. Important events are grouped into **convergence points**.
6. The interpretation library converts the facts into opportunity, risk and strategic action.
7. An optional local language model can improve prose without changing the calculated facts.
        """
    )

    st.markdown("## Explainable Astrology")
    st.markdown(
        "Luna Convergence presents the human story first, then answers three questions: "
        "**what changed today, why it differs from yesterday, and what evidence supports it**. "
        "The public Sky Snapshot stays readable; full positions, houses and orbs remain optional."
    )

    st.markdown("## What this is—and is not")
    st.markdown(
        """
This is a general Sun-sign or rising-sign forecast. It is not a personal natal chart.
A personal version would require a birth date, exact birth time and birthplace.

Astrology is presented as a symbolic interpretive framework. It is not scientifically established
as causal prediction and should not replace financial, medical, legal or other professional advice.
        """
    )

    st.markdown("## Privacy during the MVP")
    st.markdown(
        "The public daily reading requires no account. Paid orders use Stripe-verified instant fulfilment, "
        "and Luna only uses the minimum details required to generate and deliver the purchased report."
    )


SEO_YEAR = 2026
SEO_MONTH = 8
SEO_MONTH_NAME = "August"


@lru_cache(maxsize=32)
def monthly_seo_data(sign: str) -> dict:
    result = period_report(
        sign,
        date(SEO_YEAR, SEO_MONTH, 1),
        date(SEO_YEAR, SEO_MONTH, 31),
        DEFAULT_TIMEZONE,
        f"{SEO_MONTH_NAME} {SEO_YEAR}",
        transition_count=7,
    )
    result["concentration_theme"] = build_monthly_concentration_theme(result)
    return result


def sign_slug(sign: str) -> str:
    return sign.lower().replace(" ", "-")


def focus_paragraph(data: dict, target_houses: set[int], label: str) -> str:
    transitions = [
        event
        for event in data["major_transitions"]
        if set(event.get("houses", [])) & target_houses
    ]
    primary = data["dominant_houses"][0]["house"]
    if transitions:
        event = transitions[0]
        relevant = next(
            house for house in event["houses"] if house in target_houses
        )
        return (
            f"**{event['title']}** activates house {relevant}, "
            f"which governs **{HOUSE_NAMES[relevant]}**. "
            f"The constructive use of this period is to "
            f"{HOUSE_STRATEGY[relevant]['action']}; the risk is "
            f"{HOUSE_STRATEGY[relevant]['risk']}."
        )
    return (
        f"No single major transition completely dominates {label}. "
        f"Use the month's leading house {primary}—"
        f"**{HOUSE_NAMES[primary]}**—as the organising principle: "
        f"{HOUSE_STRATEGY[primary]['action']}."
    )


def monthly_index_page() -> None:
    """Legacy August ad URL: render the Daily only.

    Google Ads and old bookmarks may still point to /august-2026-horoscopes.
    That URL must not expose the old monthly library, twelve-card grid or
    checkout.  It now renders the exact same lean Daily experience as /.
    """
    _render_lean_daily("/august-2026-horoscopes")


AUGUST_2026_PREVIEW_HOOKS = {
    "Aries": "Make room for pleasure without promising more than August can hold",
    "Taurus": "Home sets the terms for the future you are building",
    "Gemini": "The right conversation can change the direction of your work",
    "Cancer": "Money gets clearer when the bigger plan has a real price",
    "Leo": "Choose the version of yourself that can carry the next commitment",
    "Virgo": "Protect the quiet; relationships reveal what should stay",
    "Libra": "Your future circle is changing; keep the plans that support real life",
    "Scorpio": "Visibility rises; make sure the work can carry the attention",
    "Sagittarius": "The wider road is opening, but home still sets the terms",
    "Capricorn": "Shared money needs cleaner terms before the next decision",
    "Aquarius": "Relationships get clearer when values and expectations are named",
    "Pisces": "Your routines decide how much of the new direction you can sustain",
}


def _august_preview_narrative(narrative):
    """Give each public August sign page its own concise editorial lead.

    The paid narrative and its evidence remain untouched.  This replacement is
    only for the free August 2026 sign preview, where repeating the same
    'pressure builds' sentence across signs makes the product feel templated.
    """
    from dataclasses import replace

    hook = AUGUST_2026_PREVIEW_HOOKS.get(narrative.sign)
    if not hook:
        return narrative
    return replace(narrative, hook_headline=hook)



def _free_monthly_profile(sign: str) -> tuple[object | None, date | None, str, str, bool]:
    st.markdown(
        """
        <style id="monthly-profile-uniform-css">
        div[data-testid="stForm"]{
            border:1px solid rgba(0,0,0,.45);
            border-radius:0;
            padding:1rem 1rem .8rem 1rem;
        }
        div[data-testid="stForm"] label{
            font-family:"IBM Plex Mono",monospace;
            font-size:.68rem;
            letter-spacing:.05em;
            text-transform:uppercase;
        }
        div[data-testid="stForm"] button{
            border-radius:0 !important;
            text-transform:uppercase;
            letter-spacing:.06em;
            font-family:"Josefin Sans",Arial,sans-serif;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="eyebrow">FREE · PERSONAL MONTH</div>', unsafe_allow_html=True)
    st.markdown("## Your August")
    st.markdown(
        "Add the birth details you know. Luna uses them to anchor the sky map, show your age at earlier echoes, "
        "and add natal geometry only where the data supports it."
    )

    with st.form(f"free-monthly-profile-{sign_slug(sign)}", clear_on_submit=False):
        birth_date_value = st.date_input(
            "Birth date",
            value=st.session_state.get(f"free-monthly-birth-date-{sign_slug(sign)}"),
            min_value=date(1900, 1, 1),
            max_value=browser_local_date(),
            key=f"free-monthly-birth-date-input-{sign_slug(sign)}",
        )
        time_known = st.checkbox(
            "I know my birth time exactly",
            value=bool(st.session_state.get(f"free-monthly-time-known-{sign_slug(sign)}", False)),
            key=f"free-monthly-time-known-input-{sign_slug(sign)}",
        )

        birth_time_value = None
        birth_city = None
        birth_timezone = "UTC"

        if time_known:
            birth_time_value = st.time_input(
                "Birth time",
                value=datetime.strptime("12:00", "%H:%M").time(),
                key=f"free-monthly-birth-time-{sign_slug(sign)}",
            )
            city_options = sorted(CITY_LOCATIONS) + ["Not listed — planetary geometry only"]
            birth_city = st.selectbox(
                "Birthplace",
                city_options,
                index=None,
                placeholder="Choose your birth city",
                key=f"free-monthly-birth-city-{sign_slug(sign)}",
            )
            if birth_city and birth_city != "Not listed — planetary geometry only":
                birth_timezone = CITY_LOCATIONS[birth_city].timezone
            else:
                birth_timezone = st.selectbox(
                    "Birth timezone",
                    TIMEZONES,
                    index=timezone_select_index(),
                    key=f"free-monthly-birth-tz-{sign_slug(sign)}",
                )
        else:
            st.caption(
                "Birth time unknown: Luna can still use your birth date for age/history context, "
                "but will not invent an Ascendant, Midheaven or timed houses."
            )

        current_cols = st.columns(2, gap="medium")
        with current_cols[0]:
            current_timezone = st.selectbox(
                "Where are you now? · timezone",
                TIMEZONES,
                index=timezone_select_index(),
                key=f"free-monthly-current-tz-{sign_slug(sign)}",
            )
        with current_cols[1]:
            current_city = st.text_input(
                "Current city",
                value=representative_city_name(browser_timezone_name()),
                key=f"free-monthly-current-city-{sign_slug(sign)}",
            )

        submitted = st.form_submit_button("Show my free month", type="primary", use_container_width=True)

    ready_key = f"free-monthly-ready-{sign_slug(sign)}"
    if submitted:
        st.session_state[ready_key] = True
        st.session_state[f"free-monthly-birth-date-{sign_slug(sign)}"] = birth_date_value
        st.session_state[f"free-monthly-time-known-{sign_slug(sign)}"] = time_known

    if not st.session_state.get(ready_key):
        return None, None, browser_timezone_name(), representative_city_name(browser_timezone_name()), False

    snapshot = None
    if birth_date_value:
        try:
            if time_known and birth_time_value:
                if birth_city and birth_city in CITY_LOCATIONS:
                    location = CITY_LOCATIONS[birth_city]
                    snapshot = build_natal_snapshot(
                        birth_date=birth_date_value,
                        birth_time=birth_time_value,
                        birth_time_known=True,
                        latitude=location.latitude,
                        longitude=location.longitude,
                        timezone_name=location.timezone,
                        location_name=f"{location.name}, {location.country}",
                    )
                else:
                    snapshot = build_natal_snapshot(
                        birth_date=birth_date_value,
                        birth_time=birth_time_value,
                        birth_time_known=True,
                        timezone_name=birth_timezone,
                    )
            else:
                snapshot = build_natal_snapshot(
                    birth_date=birth_date_value,
                    birth_time_known=False,
                    timezone_name="UTC",
                )
        except Exception as exc:
            st.warning(f"Luna could not add the natal layer: {exc}")

    return snapshot, birth_date_value, current_timezone, current_city, True



_MONTHLY_READER_LABELS = {
    1: "identity + direction",
    2: "money + self-worth",
    3: "communication + movement",
    4: "home + family",
    5: "love + creativity",
    6: "work + routine",
    7: "relationships + agreements",
    8: "shared money + obligations",
    9: "the wider world",
    10: "career + public direction",
    11: "networks + future plans",
    12: "rest + closure",
}


def _monthly_reader_house_label(house_number) -> str:
    try:
        return _MONTHLY_READER_LABELS.get(int(house_number), _house_short(house_number))
    except Exception:
        return _house_short(house_number)


def _render_monthly_past_echo_strip(
    sign: str,
    year: int,
    month: int,
    timezone_name: str,
    birth_date_value: date | None = None,
) -> None:
    """Monthly precedent rendered in the same full-width editorial rhythm as Personal Transits."""
    try:
        matches = _monthly_history_matches(sign, int(year), int(month), timezone_name)
    except Exception:
        return
    if not matches:
        return

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">PAST CONTEXT</div>', unsafe_allow_html=True)
    st.markdown("## Have you been somewhere like this before?")
    st.markdown(
        "Before reading the month forward, Luna checks the closest earlier sky patterns. "
        "They are reference points, not claims that the same life event must repeat."
    )

    for index, item in enumerate(matches[:3], start=1):
        past_year = int(item["year"])
        past_label = f"{month_name[int(month)]} {past_year}"
        shared = item.get("shared_houses") or []
        now_only = item.get("current_only") or []
        then_only = item.get("past_only") or []

        st.markdown("---")

        age_text = ""
        if birth_date_value:
            ref_date = date(past_year, int(month), 15)
            if ref_date >= birth_date_value:
                age = ref_date.year - birth_date_value.year - (
                    (ref_date.month, ref_date.day) < (birth_date_value.month, birth_date_value.day)
                )
                age_text = f" · YOU WERE ABOUT {age}"

        st.markdown(
            f'<div class="eyebrow">PAST ECHO · {escape(past_label.upper())}{escape(age_text)}</div>',
            unsafe_allow_html=True,
        )

        if shared:
            shared_text = " + ".join(_monthly_reader_house_label(h) for h in shared[:2])
        else:
            shared_text = "a similar planetary sequence"

        st.markdown(f"### {shared_text.title()}")

        if now_only and then_only:
            now_text = _monthly_reader_house_label(now_only[0])
            then_text = _monthly_reader_house_label(then_only[0])
            st.markdown(
                f"**What rhymes:** the earlier month carried the same underlying emphasis around **{shared_text}**."
            )
            st.markdown(
                f"**What is different now:** **{now_text}** has joined the story, while {past_label} "
                f"leaned more toward **{then_text}**."
            )
        elif now_only:
            now_text = _monthly_reader_house_label(now_only[0])
            st.markdown(
                f"**What rhymes:** the earlier month carried the same underlying emphasis around **{shared_text}**."
            )
            st.markdown(
                f"**What is different now:** this month adds **{now_text}**, changing how the old pattern can express itself."
            )
        elif then_only:
            then_text = _monthly_reader_house_label(then_only[0])
            st.markdown(
                f"**What rhymes:** the earlier month carried the same underlying emphasis around **{shared_text}**."
            )
            st.markdown(
                f"**What is different now:** {past_label} carried more **{then_text}** than the present month does."
            )
        else:
            st.markdown(
                f"**What rhymes:** both months share **{shared_text}**."
            )
            st.markdown(
                "**What is different now:** the supporting planets and exact sequence have changed, so treat this as an echo rather than a replay."
            )

        if birth_date_value and ref_date >= birth_date_value:
            st.markdown(
                "**What do you remember?** Was that period more about love, work, money, home, independence, "
                "responsibility or a change in direction?"
            )
        else:
            st.markdown(
                "**Before your time:** the earlier sky still gives this month a longer cycle context."
            )

    with st.expander("Why Luna sees these dates"):
        st.markdown(
            "Luna compares the month's dominant whole-sign houses and major planetary transition labels with earlier "
            "months for the same sign. The similarity score stays internal. What the reader sees is the useful part: "
            "what rhymes, what changed, and what that difference may mean."
        )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)


def _render_monthly_personal_sky(snapshot) -> None:
    if snapshot is None:
        return
    st.markdown("### Your starting sky")
    if bool(getattr(snapshot, "birth_time_known", False)):
        st.markdown(
            "Your birth details set the starting geometry. The ecliptic above is the shared moving sky; "
            "this wheel is the reference point Luna compares it with."
        )
    else:
        st.markdown(
            "Birth time is unknown, so Luna uses the reliable planetary geometry only. "
            "Ascendant, Midheaven and timed houses are deliberately omitted."
        )
    try:
        st.markdown(natal_wheel_svg(snapshot, size=720), unsafe_allow_html=True)
    except Exception:
        pass



def _render_monthly_flowing_report(narrative, result) -> None:
    """
    Render the existing production Monthly with a flatter hierarchy:
    one major hero headline, then small section labels and contextual subheads.
    This preserves the production calculations/content while changing how
    Streamlit presents the headings.
    """
    original_markdown = st.markdown

    def flowing_markdown(body, *args, **kwargs):
        if isinstance(body, str):
            stripped = body.strip()

            # "How August unfolds" is a section label, not another major headline.
            body = re.sub(
                r"(?im)^##\s+How\s+([A-Za-z]+)\s+unfolds\s*$",
                r'<div class="monthly-flow-label">HOW \1 UNFOLDS</div>',
                body,
            )
            body = re.sub(
                r"(?im)^#\s+How\s+([A-Za-z]+)\s+unfolds\s*$",
                r'<div class="monthly-flow-label">HOW \1 UNFOLDS</div>',
                body,
            )

            # "Luna's read" becomes a quiet contextual label.
            body = re.sub(
                r"(?im)^\s*Luna['’]s\s+read\s*$",
                r'<div class="monthly-flow-label">SUPPORTING SIGNAL</div>',
                body,
            )
            body = re.sub(
                r"(?im)^#{1,4}\s+Luna['’]s\s+read\s*$",
                r'<div class="monthly-flow-label">SUPPORTING SIGNAL</div>',
                body,
            )

            # The large 18–21 Aug signal is another dated subhead, not a second headline.
            body = re.sub(
                r"(?im)^##\s+Around\s+([0-9]{1,2})-([0-9]{1,2})\s+([A-Za-z]+)\s+([0-9]{4}),\s*(.+)$",
                r'<div class="monthly-flow-date">\1–\2 \3 \4</div>\n### \5',
                body,
            )
            body = re.sub(
                r"(?im)^#\s+Around\s+([0-9]{1,2})-([0-9]{1,2})\s+([A-Za-z]+)\s+([0-9]{4}),\s*(.+)$",
                r'<div class="monthly-flow-date">\1–\2 \3 \4</div>\n### \5',
                body,
            )

            # Dated story headlines should read like transit subheads, not new page titles.
            body = re.sub(
                r"(?im)^###\s+(The wider road .+)$",
                r'#### \1',
                body,
            )

            # "Where the story lands" and "Your move" are structural labels.
            body = re.sub(
                r"(?im)^#{1,4}\s+Where the story lands\s*$",
                r'<div class="monthly-flow-label">WHERE IT LANDS</div>',
                body,
            )
            body = re.sub(
                r"(?im)^#{1,4}\s+Your move\s*$",
                r'<div class="monthly-flow-label">YOUR MOVE</div>',
                body,
            )

            # Make sure injected HTML can render.
            if "monthly-flow-" in body and "unsafe_allow_html" not in kwargs:
                kwargs["unsafe_allow_html"] = True

        return original_markdown(body, *args, **kwargs)

    # CSS applies only to the visual classes injected above; the black hero remains untouched.
    original_markdown(
        """
        <style>
        .monthly-flow-label{
            margin:1.9rem 0 .45rem 0;
            padding-top:.65rem;
            border-top:1px solid rgba(0,0,0,.40);
            font-family:"IBM Plex Mono",monospace;
            font-size:.66rem;
            line-height:1.2;
            letter-spacing:.08em;
            text-transform:uppercase;
        }
        .monthly-flow-date{
            margin:1.15rem 0 .15rem 0;
            font-family:"IBM Plex Mono",monospace;
            font-size:.70rem;
            line-height:1.2;
            letter-spacing:.06em;
            text-transform:uppercase;
        }
        /* Keep post-hero headings subordinate to the single editorial headline. */
        .stMainBlockContainer h2{
            font-size:clamp(1.65rem,3.1vw,2.35rem);
            line-height:1.05;
            margin-top:1.6rem;
            margin-bottom:.55rem;
        }
        .stMainBlockContainer h3{
            font-size:clamp(1.32rem,2.35vw,1.82rem);
            line-height:1.08;
            margin-top:.65rem;
            margin-bottom:.45rem;
        }
        .stMainBlockContainer h4{
            font-size:clamp(1.05rem,1.8vw,1.35rem);
            line-height:1.12;
            margin-top:.4rem;
            margin-bottom:.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown = flowing_markdown
    try:
        render_production_monthly_report(narrative, result, show_print=True)
    finally:
        st.markdown = original_markdown


def monthly_sign_page(sign: str) -> None:
    """Unified free Monthly: birth context first, one editorial report, one history section."""
    title = f"{sign} August 2026 Horoscope | Luna Convergence"
    description = (
        f"Free {sign} August 2026 horoscope with key dates, love/work/money context, "
        "historical echoes and optional natal context."
    )
    path = f"/august-2026-{sign_slug(sign)}"
    set_page_metadata(title, description, path)

    snapshot, birth_date_value, timezone_name, nearest_city, ready = _free_monthly_profile(sign)
    if not ready:
        st.info("Enter the details you know. Luna will not invent missing birth-time precision.")
        return

    try:
        with st.spinner(f"Building your free {SEO_MONTH_NAME} {SEO_YEAR}…"):
            narrative, result = build_production_monthly_report(
                sign=sign,
                year=SEO_YEAR,
                month=SEO_MONTH,
                timezone_name=timezone_name,
                nearest_city=nearest_city,
                main_focus="General overview",
            )
            if snapshot is not None:
                try:
                    result["natal_overlay"] = build_monthly_natal_overlay(snapshot, result)
                    result["natal_summary"] = natal_profile_summary(snapshot)
                except Exception:
                    pass
    except Exception as exc:
        st.error("Luna could not build this Monthly.")
        if EDITOR_PREVIEW_ENABLED:
            st.exception(exc)
        return

    st.markdown('<div class="eyebrow">THE SKY</div>', unsafe_allow_html=True)
    st.markdown("### One moving sky. One personal reference point.")
    _render_monthly_personal_sky(snapshot)

    _render_monthly_past_echo_strip(
        sign,
        SEO_YEAR,
        SEO_MONTH,
        timezone_name,
        birth_date_value=birth_date_value,
    )

    _render_monthly_flowing_report(narrative, result)


    st.markdown("## Something specific on your mind?")
    st.markdown(
        "Daily, Weekly and Monthly are free. Luna's paid layer is for a **specific question or personal timing across time**."
    )
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown("**Ask Luna · planned launch price A$1.95**<br>One focused question about work, relationships, money or timing.", unsafe_allow_html=True)
    with c2:
        st.markdown("**Personal Transits**<br>See when your strongest natal activations build, peak, change and release.", unsafe_allow_html=True)

    st.markdown(
        '<div class="eyebrow monthly-other-signs-label" style="margin-top:2rem">Read another August 2026 sign</div>',
        unsafe_allow_html=True,
    )
    links = [f'<a href="/august-2026-{sign_slug(item)}">{escape(item)}</a>' for item in SIGNS]
    st.markdown('<div class="related-signs">' + "".join(links) + "</div>", unsafe_allow_html=True)


def make_monthly_page(sign: str):
    def page() -> None:
        monthly_sign_page(sign)

    page.__name__ = f"{sign_slug(sign).replace('-', '_')}_august_2026"
    return page


def natal_snapshot_page() -> None:
    set_page_metadata(
        "Free Natal Snapshot | Luna Convergence",
        "Create a free Luna natal snapshot from your birth date, time and location. Story first, chart evidence available.",
        "/natal-snapshot",
    )
    st.markdown('<section class="natal-shell">', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Free · natal snapshot</div>', unsafe_allow_html=True)
    st.markdown('<div class="editorial-title">What keeps<br>repeating?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="natal-intro">Luna reads the natal chart as a persistent pattern, not a verdict. '
        'Give the birth time only if you know it. If the time or location is uncertain, Luna leaves the Ascendant and houses out rather than inventing precision.</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        birth_date = st.date_input(
            "Birth date",
            value=None,
            min_value=date(1900, 1, 1),
            max_value=browser_local_date(),
            key="natal-birth-date-v323",
        )
        time_known = st.checkbox(
            "I know my birth time exactly",
            value=False,
            key="natal-time-known-v323",
        )
        birth_time_value = None
        city_choice = None
        timezone_name = "UTC"
        manual_city_name = ""
        manual_country = ""
        manual_latitude = None
        manual_longitude = None
        manual_timezone = "UTC"
        time_basis = "Local time at birthplace"

        if time_known:
            birth_time_value = st.time_input(
                "Birth time",
                value=datetime.strptime("12:00", "%H:%M").time(),
                key="natal-birth-time-v323",
                help="Normally enter the local clock time at the place of birth. If your source explicitly gives Universal Time, choose UTC below.",
            )
            time_basis = st.selectbox(
                "Time basis",
                ["Local time at birthplace", "Universal Time (UTC)"],
                index=0,
                key="natal-time-basis-v323",
                help="Most birth certificates use local time. Some astrology records state UT/UTC directly.",
            )
            city_options = sorted(CITY_LOCATIONS) + [
                "Other city — enter manually",
                "Not listed — planetary snapshot only",
            ]
            city_choice = st.selectbox(
                "Birth city",
                city_options,
                index=None,
                placeholder="Choose your birth city",
                key="natal-city-v323",
                help=(
                    "Luna now includes a wider international city list, including Alotau, Papua New Guinea. "
                    "If your city is still missing, choose Other city and enter coordinates and an IANA timezone."
                ),
            )

            if city_choice == "Other city — enter manually":
                st.caption("City not listed? Enter it directly. Coordinates keep the Ascendant and houses precise without sending your birth place to an external geocoding service.")
                manual_cols = st.columns(2, gap="medium")
                with manual_cols[0]:
                    manual_city_name = st.text_input("City / town", key="natal-manual-city-v323")
                    manual_latitude = st.number_input(
                        "Latitude",
                        min_value=-90.0,
                        max_value=90.0,
                        value=0.0,
                        step=0.0001,
                        format="%.4f",
                        key="natal-manual-lat-v323",
                    )
                with manual_cols[1]:
                    manual_country = st.text_input("Country", key="natal-manual-country-v323")
                    manual_longitude = st.number_input(
                        "Longitude",
                        min_value=-180.0,
                        max_value=180.0,
                        value=0.0,
                        step=0.0001,
                        format="%.4f",
                        key="natal-manual-lon-v323",
                    )
                if time_basis == "Local time at birthplace":
                    manual_timezone = st.text_input(
                        "Birth timezone · IANA name",
                        value=browser_timezone_name(),
                        key="natal-manual-timezone-v323",
                        help="Examples: Pacific/Port_Moresby, Australia/Sydney, Europe/London, America/New_York.",
                    )
                else:
                    manual_timezone = "UTC"
                    st.caption("Universal Time selected: Luna uses the entered time directly as UTC while retaining the birth coordinates for Ascendant and houses.")
            elif city_choice == "Not listed — planetary snapshot only":
                if time_basis == "Local time at birthplace":
                    timezone_name = st.selectbox(
                        "Birth timezone",
                        TIMEZONES,
                        index=timezone_select_index(),
                        key="natal-unlisted-timezone-v323",
                        help="This places the planets at the correct moment, but without coordinates Luna will not calculate the Ascendant or houses.",
                    )
                else:
                    timezone_name = "UTC"

        submitted = st.button("Create my free snapshot", use_container_width=True, key="natal-submit-v323")

    if not submitted:
        st.markdown(
            '<div class="lean-bookmark-note">Birth details stay out of the page URL. This free snapshot is calculated in the current app session and is not sent to Stripe.</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</section>', unsafe_allow_html=True)
        return

    if birth_date is None:
        st.error("Choose your birth date before creating the snapshot.")
        st.markdown('</section>', unsafe_allow_html=True)
        return

    latitude = longitude = None
    location_name = None
    if time_known:
        if city_choice in CITY_LOCATIONS:
            location = CITY_LOCATIONS[city_choice]
            timezone_name = "UTC" if time_basis == "Universal Time (UTC)" else location.timezone
            latitude = location.latitude
            longitude = location.longitude
            location_name = f"{location.name}, {location.country}"
        elif city_choice == "Other city — enter manually":
            if time_basis == "Local time at birthplace":
                try:
                    ZoneInfo(str(manual_timezone).strip())
                except Exception:
                    st.error("That timezone name is not recognised. Use an IANA name such as Pacific/Port_Moresby or Australia/Sydney.")
                    st.markdown('</section>', unsafe_allow_html=True)
                    return
            else:
                manual_timezone = "UTC"
            if not str(manual_city_name).strip():
                st.error("Enter the birth city or town name.")
                st.markdown('</section>', unsafe_allow_html=True)
                return
            timezone_name = str(manual_timezone).strip()
            latitude = float(manual_latitude)
            longitude = float(manual_longitude)
            location_name = str(manual_city_name).strip()
            if str(manual_country).strip():
                location_name += f", {str(manual_country).strip()}"
        elif city_choice != "Not listed — planetary snapshot only":
            st.error("Choose a birth city, use Other city, or choose planetary snapshot only.")
            st.markdown('</section>', unsafe_allow_html=True)
            return

    snapshot = build_natal_snapshot(
        birth_date=birth_date,
        birth_time_known=time_known,
        birth_time=birth_time_value,
        timezone_name=timezone_name,
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
    )

    # Reuse the same birth inputs if this customer later opens the paid Monthly
    # checkout during the same app session. These details stay in Streamlit
    # session state only; raw birth data is never copied into the page URL,
    # analytics payloads or Stripe metadata.
    st.session_state["luna_natal_checkout_prefill"] = {
        "birth_date": birth_date.isoformat(),
        "time_known": bool(time_known),
        "birth_time": birth_time_value.strftime("%H:%M") if birth_time_value else "",
        "time_basis": time_basis,
        "city_choice": city_choice or "",
        "location_name": location_name or "",
        "timezone_name": timezone_name,
        "latitude": latitude,
        "longitude": longitude,
        "manual_city": manual_city_name,
        "manual_country": manual_country,
    }

    track_event("free_natal_snapshot_generated", {"birth_time_known": bool(time_known)})

    by_planet = {item.planet: item for item in snapshot.positions}
    moon_value = by_planet["Moon"].sign
    if not time_known and len(snapshot.moon_uncertain) > 1:
        moon_value = " / ".join(snapshot.moon_uncertain)

    st.markdown("## Your natal signature")
    signature_items = [
        ("Sun", by_planet["Sun"].sign),
        ("Moon", moon_value),
        ("Rising", snapshot.ascendant.sign if snapshot.ascendant else "Not calculated"),
        ("Dominant element", snapshot.dominant_element),
        ("Dominant mode", snapshot.dominant_modality),
        ("Midheaven", snapshot.midheaven.sign if snapshot.midheaven else "Not calculated"),
    ]
    signature_html = "".join(
        f'<div><span>{escape(label)}</span><strong>{escape(value)}</strong></div>'
        for label, value in signature_items
    )
    st.markdown(f'<div class="natal-signature">{signature_html}</div>', unsafe_allow_html=True)

    birth_bits = [birth_date.strftime("%d %B %Y")]
    if time_known and birth_time_value is not None:
        birth_bits.append(birth_time_value.strftime("%H:%M"))
        birth_bits.append("UTC" if time_basis == "Universal Time (UTC)" else "local time")
        birth_bits.append(location_name or "Location not supplied")
        birth_bits.append(timezone_name)
        birth_precision = "Exact birth time supplied"
    else:
        birth_bits.append("Birth time unknown")
        birth_precision = "Angles and houses intentionally omitted"
    st.markdown(
        f'<div class="natal-birth-confirm"><strong>Birth data</strong> · {escape(" · ".join(birth_bits))}<br><span>{escape(birth_precision)}</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown(natal_wheel_svg(snapshot, size=760), unsafe_allow_html=True)

    if not time_known:
        if len(snapshot.moon_uncertain) > 1:
            st.info(
                "Birth time is unknown, and the Moon changed sign during this date. "
                f"Luna will not choose between {' / '.join(snapshot.moon_uncertain)} without a time."
            )
        else:
            st.caption(
                "Birth time unknown: planetary positions are shown as a date-only snapshot. "
                "Ascendant, Midheaven and houses are intentionally omitted."
            )
    elif snapshot.ascendant is None:
        st.caption(
            "Exact time supplied, but the birth location was not available. "
            "Planetary positions use the selected timezone; Ascendant and houses are intentionally omitted."
        )
    else:
        st.caption("Tropical geocentric positions · Whole-sign houses · Swiss Ephemeris")

    concentration = dict(snapshot.concentration_theme or {})
    if concentration:
        clusters = list(concentration.get("clusters") or [])
        cluster_names = " + ".join(str(item.get("sign")) for item in clusters if item.get("sign"))
        headline = f"{cluster_names} carry unusual weight" if cluster_names else "Several parts of the chart share one climate"
        st.markdown(
            f'''<div class="natal-chart-emphasis">
  <span>Chart emphasis · the forest</span>
  <strong>{escape(headline)}</strong>
  <p>{escape(str(concentration.get("summary") or ""))}</p>
</div>''',
            unsafe_allow_html=True,
        )

    if snapshot.signatures:
        st.markdown("## Your strongest signatures")
        st.caption(
            "These are the combinations Luna gives the greatest behavioural weight. "
            "The chart evidence is shown once; each signature translates it into lived behaviour, strength and watch-point."
        )
        for signature in snapshot.signatures:
            question_html = (
                f'<div class="natal-signature-question">{escape(signature.question)}</div>'
                if signature.question else ""
            )
            st.markdown(
                f'''<div class="natal-signature-reading">
  <div class="natal-evidence">{escape(signature.evidence)}</div>
  <h3>{escape(signature.title)}</h3>
  <p>{escape(signature.text)}</p>
  <div class="natal-signature-meta">
    <div><span>Strength</span>{escape(signature.strength)}</div>
    <div><span>Watch</span>{escape(signature.watch)}</div>
  </div>
  {question_html}
</div>''',
                unsafe_allow_html=True,
            )

    with st.expander("Chart evidence"):
        rows = []
        for item in snapshot.positions:
            rows.append(
                {
                    "Point": item.planet,
                    "Position": item.label(),
                    "House": item.house if item.house is not None else "—",
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.markdown("**Strongest aspects**")
        for aspect in snapshot.aspects[:10]:
            st.markdown(f"- {aspect.label()}")

    st.markdown(
        "**Next layer:** compare these persistent natal patterns with the next 12 months — "
        "showing which pattern is active, when it peaks and when the conditions change."
    )
    st.markdown(
        '<a class="lean-monthly-link" href="/timing-map">Build your 12-Month Timing Map →</a>',
        unsafe_allow_html=True,
    )
    st.markdown('</section>', unsafe_allow_html=True)

def _timing_date_label(value: date) -> str:
    return value.strftime("%d %b %Y").lstrip("0")


def _timing_range_label(start: date, end: date) -> str:
    if start == end:
        return _timing_date_label(start)
    if start.year == end.year and start.month == end.month:
        return f"{start.day}–{end.day} {start.strftime('%b %Y')}"
    return f"{_timing_date_label(start)} – {_timing_date_label(end)}"


def _timing_strip_html(report) -> str:
    cells = []
    for label, value in month_intensity(report):
        height = 6 + int(round(38 * float(value)))
        opacity = 0.18 + 0.82 * float(value)
        cells.append(
            f'<div class="timing-month"><span>{escape(label)}</span>'
            f'<i style="height:{height}px;opacity:{opacity:.2f}"></i></div>'
        )
    return '<div class="timing-strip" aria-label="Transit intensity by month">' + "".join(cells) + '</div>'


def _timing_birth_snapshot():
    """Collect birth inputs for the Timing Map without changing existing natal/checkout flows."""
    prefill = dict(st.session_state.get("luna_natal_checkout_prefill") or {})
    prefill_date = None
    try:
        if prefill.get("birth_date"):
            prefill_date = date.fromisoformat(str(prefill["birth_date"]))
    except Exception:
        prefill_date = None

    birth_date = st.date_input(
        "Birth date",
        value=prefill_date,
        min_value=date(1900, 1, 1),
        max_value=browser_local_date(),
        key="timing-birth-date-v330",
    )
    time_known = st.checkbox(
        "I know my birth time exactly",
        value=bool(prefill.get("time_known", False)),
        key="timing-time-known-v330",
    )

    birth_time_value = None
    city_choice = None
    timezone_name = "UTC"
    manual_city_name = ""
    manual_country = ""
    manual_latitude = None
    manual_longitude = None
    manual_timezone = "UTC"
    time_basis = str(prefill.get("time_basis") or "Local time at birthplace")

    if time_known:
        try:
            default_time = datetime.strptime(str(prefill.get("birth_time") or "12:00"), "%H:%M").time()
        except ValueError:
            default_time = datetime.strptime("12:00", "%H:%M").time()
        birth_time_value = st.time_input(
            "Birth time",
            value=default_time,
            key="timing-birth-time-v330",
        )
        time_basis = st.selectbox(
            "Time basis",
            ["Local time at birthplace", "Universal Time (UTC)"],
            index=0 if time_basis != "Universal Time (UTC)" else 1,
            key="timing-time-basis-v330",
        )
        city_options = sorted(CITY_LOCATIONS) + [
            "Other city — enter manually",
            "Not listed — planetary timing only",
        ]
        previous_city = str(prefill.get("city_choice") or "")
        default_index = city_options.index(previous_city) if previous_city in city_options else None
        city_choice = st.selectbox(
            "Birth city",
            city_options,
            index=default_index,
            placeholder="Choose your birth city",
            key="timing-city-v330",
        )

        if city_choice == "Other city — enter manually":
            c1, c2 = st.columns(2, gap="medium")
            with c1:
                manual_city_name = st.text_input(
                    "City / town", value=str(prefill.get("manual_city") or ""), key="timing-manual-city-v330"
                )
                manual_latitude = st.number_input(
                    "Latitude", min_value=-90.0, max_value=90.0,
                    value=float(prefill.get("latitude") or 0.0), step=0.0001, format="%.4f",
                    key="timing-manual-lat-v330",
                )
            with c2:
                manual_country = st.text_input(
                    "Country", value=str(prefill.get("manual_country") or ""), key="timing-manual-country-v330"
                )
                manual_longitude = st.number_input(
                    "Longitude", min_value=-180.0, max_value=180.0,
                    value=float(prefill.get("longitude") or 0.0), step=0.0001, format="%.4f",
                    key="timing-manual-lon-v330",
                )
            if time_basis == "Local time at birthplace":
                manual_timezone = st.text_input(
                    "Birth timezone · IANA name",
                    value=str(prefill.get("timezone_name") or browser_timezone_name()),
                    key="timing-manual-timezone-v330",
                )
            else:
                manual_timezone = "UTC"
        elif city_choice == "Not listed — planetary timing only":
            if time_basis == "Local time at birthplace":
                default_tz = str(prefill.get("timezone_name") or browser_timezone_name())
                tz_index = TIMEZONES.index(default_tz) if default_tz in TIMEZONES else timezone_select_index()
                timezone_name = st.selectbox(
                    "Birth timezone", TIMEZONES, index=tz_index, key="timing-unlisted-timezone-v330"
                )
            else:
                timezone_name = "UTC"

    if birth_date is None:
        return None, "Choose your birth date before creating the map.", None

    latitude = longitude = None
    location_name = None
    if time_known:
        if city_choice in CITY_LOCATIONS:
            location = CITY_LOCATIONS[city_choice]
            timezone_name = "UTC" if time_basis == "Universal Time (UTC)" else location.timezone
            latitude = location.latitude
            longitude = location.longitude
            location_name = f"{location.name}, {location.country}"
        elif city_choice == "Other city — enter manually":
            if not str(manual_city_name).strip():
                return None, "Enter the birth city or town name.", None
            if time_basis == "Local time at birthplace":
                try:
                    ZoneInfo(str(manual_timezone).strip())
                except Exception:
                    return None, "That timezone name is not recognised. Use an IANA name such as Australia/Sydney.", None
            else:
                manual_timezone = "UTC"
            timezone_name = str(manual_timezone).strip()
            latitude = float(manual_latitude)
            longitude = float(manual_longitude)
            location_name = str(manual_city_name).strip()
            if str(manual_country).strip():
                location_name += f", {str(manual_country).strip()}"
        elif city_choice != "Not listed — planetary timing only":
            return None, "Choose a birth city, use Other city, or choose planetary timing only.", None

    snapshot = build_natal_snapshot(
        birth_date=birth_date,
        birth_time_known=time_known,
        birth_time=birth_time_value,
        timezone_name=timezone_name,
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
    )
    prefill_out = {
        "birth_date": birth_date.isoformat(),
        "time_known": bool(time_known),
        "birth_time": birth_time_value.strftime("%H:%M") if birth_time_value else "",
        "time_basis": time_basis,
        "city_choice": city_choice or "",
        "location_name": location_name or "",
        "timezone_name": timezone_name,
        "latitude": latitude,
        "longitude": longitude,
        "manual_city": manual_city_name,
        "manual_country": manual_country,
    }
    return snapshot, "", prefill_out



def _timing_signal_type(story) -> str:
    """Translate a transit story into a neutral human signal type."""
    planet = str(getattr(story, "transit_planet", ""))
    polarity = str(getattr(story, "polarity", "")).lower()
    aspect = str(getattr(story, "aspect", "")).lower()

    if planet == "Uranus":
        return "CHANGE"
    if planet == "Pluto":
        return "POWER SHIFT"
    if planet == "Neptune":
        return "CLARITY TEST"
    if planet == "Jupiter":
        return "OPENING" if "opportun" in polarity else "EXPANSION"
    if planet == "Saturn":
        return "DECISION" if any(x in aspect for x in ("square", "opposition")) else "STRUCTURE"
    if "opportun" in polarity:
        return "SUPPORT"
    if "pressure" in polarity:
        return "FRICTION"
    return "MIXED"


def _timing_signal_strip(report) -> str:
    """Show what kind of transit signal dominates each month, separate from intensity."""
    labels = []
    for month_index in range(12):
        month_start = (report.start_date.replace(day=1) + timedelta(days=32 * month_index)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        candidates = []
        for story in report.stories:
            if any(period.start_date <= month_end and period.end_date >= month_start for period in story.periods):
                candidates.append(story)

        if candidates:
            midpoint = month_start + timedelta(days=max(0, (month_end - month_start).days // 2))
            def distance(story):
                if not story.hits:
                    return 9999
                return min(abs((hit.exact_date - midpoint).days) for hit in story.hits)
            dominant = sorted(candidates, key=distance)[0]
            signal = _timing_signal_type(dominant)
        else:
            signal = "QUIET"

        labels.append(
            f'<div style="min-width:0;text-align:center">'
            f'<span style="font:500 9px IBM Plex Mono,monospace;letter-spacing:.05em">'
            f'{escape(month_start.strftime("%b").upper())}</span><br>'
            f'<strong style="font:500 9px Josefin Sans,sans-serif">{escape(signal)}</strong></div>'
        )
    return (
        '<div style="display:grid;grid-template-columns:repeat(12,1fr);gap:4px;'
        'margin:.35rem 0 1.2rem">' + "".join(labels) + "</div>"
    )


def _timing_year_story(report) -> list[str]:
    """Connect the strongest calculated stories into a short deterministic annual arc."""
    if not report.stories:
        return []
    ordered = sorted(
        report.stories,
        key=lambda story: story.hits[0].exact_date if getattr(story, "hits", None) else report.end_date,
    )
    selected = ordered[:4]
    lines = []
    for index, story in enumerate(selected):
        signal = _timing_signal_type(story).lower()
        headline = str(getattr(story, "headline", "")).rstrip(".")
        if index == 0:
            lines.append(f"The year opens with **{signal}**: **{headline}**.")
        elif index == len(selected) - 1:
            lines.append(f"By the later phase, the question becomes **{headline.lower()}**.")
        else:
            lines.append(f"That develops into **{signal}**: **{headline}**.")
    return lines


def timing_map_page() -> None:
    set_page_metadata(
        "Personal Transits | Luna Convergence",
        "A personalised 12-month transit map showing when major natal activations strengthen, peak, change and release.",
        "/timing-map",
    )
    st.markdown('<section class="timing-shell">', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Pilot · personal transits</div>', unsafe_allow_html=True)
    st.markdown('<div class="editorial-title">Your 12-Month<br>Personal Transits</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="timing-intro">This is not another Sun-sign year. Luna compares your natal geometry with Jupiter, Saturn, Uranus, Neptune and Pluto across the next 365 days, ranks the strongest contacts and shows the strongest periods first. The calculation stays one click underneath.</div>',
        unsafe_allow_html=True,
    )
    st.caption("Tropical geocentric astrology · day-level timing · symbolic interpretation, not a prediction or professional advice.")

    start_date = st.date_input(
        "Start the 12 months on",
        value=browser_local_date(),
        min_value=date(1950, 1, 1),
        max_value=date(2100, 12, 31),
        key="timing-start-date-v330",
        help="The pilot defaults to today in your browser timezone. You can test another 12-month window.",
    )

    with st.container(border=True):
        st.markdown("### Tell Luna when you were born")
        st.caption("If the birth time is unknown, Luna leaves Ascendant, Midheaven and houses out rather than inventing precision.")
        snapshot, validation_message, prefill_out = _timing_birth_snapshot()
        generate = st.button("Build my 12-month map", type="primary", use_container_width=True, key="timing-generate-v330")

    if generate:
        if snapshot is None:
            st.error(validation_message or "Complete the birth details first.")
        else:
            st.session_state["luna_natal_checkout_prefill"] = prefill_out or {}
            with st.spinner("Luna is ranking the strongest 12-month contacts…"):
                report = build_timing_map(
                    snapshot,
                    start_date=start_date,
                    timezone_name=browser_timezone_name(),
                    max_stories=10,
                )
            st.session_state["timing-map-report-v330"] = report
            st.session_state["timing-map-summary-v330"] = natal_profile_summary(snapshot)
            st.session_state["timing-map-time-known-v330"] = bool(snapshot.birth_time_known)
            st.session_state["timing-map-birth-date-v334"] = getattr(snapshot, "birth_date", None) or (prefill_out or {}).get("birth_date")
            track_event(
                "timing_map_generated",
                {
                    "birth_time_known": bool(snapshot.birth_time_known),
                    "stories": len(report.stories),
                    "turning_points": report.turning_points,
                },
            )

    report = st.session_state.get("timing-map-report-v330")
    if report is None:
        st.markdown(
            '<div class="lean-bookmark-note">Birth details stay out of the page URL and analytics. This pilot calculates the natal geometry in the current app session.</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</section>', unsafe_allow_html=True)
        return

    profile_summary = str(st.session_state.get("timing-map-summary-v330") or "Personal natal profile")
    st.markdown("## The year at a glance")
    st.caption(f"{profile_summary} · {_timing_date_label(report.start_date)} → {_timing_date_label(report.end_date)}")
    st.markdown(
        f'''<div class="timing-summary-grid">
  <div><span>Major games</span><strong>{report.major_games}</strong></div>
  <div><span>Turning points</span><strong>{report.turning_points}</strong></div>
  <div><span>Rule changes</span><strong>{report.rule_changes}</strong></div>
</div>''',
        unsafe_allow_html=True,
    )
    st.markdown("**Transit intensity**")
    st.markdown(_timing_strip_html(report), unsafe_allow_html=True)
    st.caption(
        "Intensity answers only one question: **how much significant transit activity is clustering here?** "
        "It does not mean trouble. A high month can be an opening, a decision, a change, support, friction or a mixed period."
    )
    st.markdown("**What kind of period is it?**")
    st.markdown(_timing_signal_strip(report), unsafe_allow_html=True)

    year_story = _timing_year_story(report)
    if year_story:
        st.markdown("## The story of your year")
        st.markdown("These are not unrelated events. Luna reads the strongest calculated contacts as a sequence:")
        for line in year_story:
            st.markdown(line)
        st.caption(
            "The sequence is deterministic: Luna orders the strongest calculated transit stories by date, "
            "then translates their dominant function into a readable arc."
        )

    if not report.stories:
        st.info("No major exact contacts passed the pilot threshold in this 12-month window. Try a different start date.")
    else:
        for number, story in enumerate(report.stories, start=1):
            periods_label = " · ".join(_timing_range_label(item.start_date, item.end_date) for item in story.periods)
            date_boxes = []
            hit_labels = ["Peak", "Returns", "Final pass"]
            for hit_index, hit in enumerate(story.hits[:3]):
                label = hit_labels[min(hit_index, 2)] if len(story.hits) > 1 else "Exact"
                suffix = " · retrograde" if hit.retrograde else ""
                date_boxes.append(
                    f'<div class="timing-date-box"><span>{escape(label)}</span>'
                    f'<strong>{escape(_timing_date_label(hit.exact_date) + suffix)}</strong></div>'
                )
            scenario_html = "".join(f"<li>{escape(line)}</li>" for line in story.scenarios)
            st.markdown(
                f'''<article class="timing-story">
  <div class="timing-meta">{number:02d} / {escape(_timing_signal_type(story))} · {escape(story.polarity)} · active {escape(periods_label)}</div>
  <h2>{escape(story.headline)}</h2>
  <p>{escape(story.summary)}</p>
  <div class="timing-dates">{"".join(date_boxes)}</div>
  <ul class="timing-scenarios">{scenario_html}</ul>
  <div class="timing-move"><div class="timing-move-label">Your move</div><strong>{escape(story.move)}</strong></div>
  <p><strong>Watch:</strong> {escape(story.watch)}</p>
</article>''',
                unsafe_allow_html=True,
            )
            birth_date_for_history = st.session_state.get("timing-map-birth-date-v334")
            if isinstance(birth_date_for_history, str):
                try:
                    birth_date_for_history = date.fromisoformat(birth_date_for_history)
                except Exception:
                    birth_date_for_history = None
            _render_transit_history(story, birth_date_for_history)

            with st.expander("Why Luna sees this"):
                st.markdown(
                    f"**Transit {story.transit_planet} {story.aspect} natal {story.natal_target}**"
                    + (f" · natal house {story.natal_house}" if story.natal_house else "")
                )
                for pass_number, hit in enumerate(story.hits, start=1):
                    motion = "retrograde" if hit.retrograde else "direct"
                    st.markdown(
                        f"- Pass {pass_number}: **{_timing_date_label(hit.exact_date)}** · {motion} · daily minimum orb {hit.orb:.2f}°"
                    )
                st.caption(
                    "Luna scans the selected 365-day window with Swiss Ephemeris positions, detects exact natal contacts, groups repeated direct/retrograde passes, then ranks the result by transit planet, natal target, aspect and angular/house emphasis."
                )

    st.markdown(
        "<div class=\"timing-test\"><strong>Personal Transits · pilot</strong><br>This is Luna's paid-value layer: personal timing, major peaks, historical context and the difference between then and now. Pricing is still being tested; no payment is collected in this pilot.</div>",
        unsafe_allow_html=True,
    )
    vote_cols = st.columns(3, gap="small")
    choices = [("Yes", "yes"), ("Maybe", "maybe"), ("No", "no")]
    for column, (label, value) in zip(vote_cols, choices):
        with column:
            if st.button(label, use_container_width=True, key=f"timing-price-{value}-v330"):
                st.session_state["timing-map-vote-v330"] = value
                track_event(
                    "timing_map_price_test",
                    {
                        "response": value,
                        "price_aud": 7.95,
                        "birth_time_known": bool(st.session_state.get("timing-map-time-known-v330", False)),
                    },
                )
    if st.session_state.get("timing-map-vote-v330"):
        st.success("Recorded. This pilot records only the response and product context — not your birth details.")

    st.markdown('</section>', unsafe_allow_html=True)

def solar_year_page() -> None:
    set_page_metadata(
        "The Solar Year | Luna Convergence",
        "Explore the twelve tropical solar phases, four equinox and solstice gates, local daylight movement and the activated whole-sign house.",
        "/solar-year",
    )
    st.markdown('<div class="eyebrow">Explainable astrology / solar structure</div>', unsafe_allow_html=True)
    st.markdown('<a class="lean-monthly-link" href="/natal-snapshot">Create your free Natal Snapshot →</a>', unsafe_allow_html=True)
    st.markdown('<div class="editorial-title">The Solar<br>Convergence</div>', unsafe_allow_html=True)
    st.markdown(
        "**The Sun is Luna's primary natural clock.** The Aries Gate at the March Equinox is the head of the "
        "universal Aries-to-Pisces solar-zodiacal cycle. Your location does not reverse that sequence; it tells Luna "
        "what the Sun is physically doing where you stand — whether local daylight is increasing, decreasing or near a turning point."
    )

    st.markdown("## The Luna Solar Clock")
    st.markdown(
        """
| Solar quarter | Signs | Process | Strategic use |
|---|---|---|---|
| Emergence | Aries, Taurus, Gemini | Initiate -> stabilise -> communicate | Begin and make the direction viable |
| Expression | Cancer, Leo, Virgo | Protect -> create -> refine | Develop and bring the result into view |
| Rebalancing | Libra, Scorpio, Sagittarius | Relate -> transform -> understand | Test the result through reciprocity and truth |
| Gestation | Capricorn, Aquarius, Pisces | Structure -> renew -> release | Consolidate, redesign and clear the cycle |
        """
    )

    st.markdown("## The four solar gates")
    st.markdown(
        """
| Gate | Tropical ingress | Strategic question |
|---|---|---|
| Aries Gate · March Equinox | Sun enters Aries | What must begin? |
| Cancer Gate · June Solstice | Sun enters Cancer | What must be protected and sustained? |
| Libra Gate · September Equinox | Sun enters Libra | What must be corrected or reciprocated? |
| Capricorn Gate · December Solstice | Sun enters Capricorn | What must survive the next cycle? |
        """
    )

    st.markdown("## Calculate your current Solar Convergence")
    c1, c2, c3 = st.columns(3)
    with c1:
        sign = st.selectbox(
            "Star sign",
            SIGNS,
            index=SIGNS.index(DEFAULT_SIGN),
            key="solar-year-sign",
        )
    with c2:
        selected_date = st.date_input(
            "Date",
            value=browser_local_date(),
            min_value=date(1900, 1, 1),
            max_value=date(2100, 12, 31),
            key="solar-year-date",
        )
    with c3:
        timezone_name = st.selectbox(
            "Timezone",
            TIMEZONES,
            index=timezone_select_index(),
            key="solar-year-timezone",
        )
    nearest_city = st.text_input(
        "Nearest city for local light",
        key="solar-year-city",
        placeholder=representative_city_name(timezone_name),
        help=city_input_help(timezone_name),
    )
    st.caption(browser_time_caption())

    solar = daily_solar_convergence(
        sign,
        selected_date,
        timezone_name,
        nearest_city=nearest_city,
    )
    st.markdown(
        f"""
<div class="card">
  <div class="eyebrow">First principle · Solar Clock</div>
  <h3>The Sun is Luna's primary natural clock.</h3>
  <p><strong>Your Sun:</strong> {escape(sign)}</p>
  <p><strong>Current Sun:</strong> {escape(solar.solar_sign)} · {escape(solar.solar_quarter)} / {escape(solar.solar_process)}</p>
  <p><strong>Local light:</strong> {escape(solar.light_direction)} from {escape(solar.city)}</p>
  <p><strong>Next gate:</strong> {escape(solar_gate_label(solar.next_solar_gate))} in {solar.days_to_next_gate} days</p>
  <p><strong>Activated life area:</strong> {escape(solar.activated_house_name)}</p>
  <p><strong>Reference frame:</strong> Local light changes with location; the Aries-to-Pisces solar sequence does not.</p>
  <p><strong>Meaning:</strong> {escape(solar.focus_meaning)}</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## Historical symbolism and factual boundary")
    st.markdown(
        "Many cultures organised calendars, symbols and stories around the Sun, its annual decline and return of light. "
        "Luna uses the astronomical structure - twelve solar phases, four gates and location-aware local light - without claiming "
        "that culturally distinct religions are secretly identical or that symbolic resemblance proves direct historical copying."
    )


def privacy_page() -> None:
    set_page_metadata(
        "Privacy and Analytics | Luna Convergence",
        "How Luna Convergence uses Google Analytics, Statcounter, Stripe and customer information for digital astrology reports.",
        "/privacy",
    )
    st.markdown('<div class="eyebrow">Privacy</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="editorial-title">Privacy and<br>analytics</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
Luna Convergence uses **Google Analytics 4** and **Statcounter** to understand
website visits, page use, free-reading generation and clicks leading to Stripe
checkout. These analytics services may process device, browser, approximate
location and usage information according to their own privacy terms.

Payments are processed by **Stripe**. Luna Convergence does not receive or
store complete card details. Stripe supplies the payment status, customer
email and any checkout information the customer submits.

Paid reports use automated fulfilment after Stripe confirms payment. Information such as
email, zodiac sign, requested period, timezone, optional nearest city, selected focus and
optional question is stored in Stripe Checkout metadata and used only to generate, deliver
and support the purchased report. A city is used to
estimate latitude, hemisphere and daylight; a street address is not requested.

The free Natal Snapshot and the 12-Month Timing Map pilot use birth details in the current app session to calculate the result.
Birth details are not placed in the page URL or analytics events by either feature. The Timing Map price test records only the
response, pilot price and whether an exact birth time was available; it does not record the birth date, time or place.
For paid Monthly personalisation, the same birth inputs are used in-session to calculate a compact
derived natal profile. Stripe receives that derived geometry and a Sun/Moon/Rising summary for
fulfilment; it does **not** receive the raw birth date, birth time or birthplace.

To request correction or deletion of order information, use the contact
email displayed during checkout or in the report-delivery message.
        """
    )
    st.markdown("## Analytics events used")
    st.markdown(
        """
- page views;
- free daily reading generation;
- free natal snapshot generation (without birth details in the event payload);
- 12-month timing-map generation and pilot price-test response (without birth details);
- monthly report checkout clicks;
- year-ahead report checkout clicks;
- confirmed paid-report purchases.
        """
    )


def footer() -> None:
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.divider()
    st.markdown(
        f"""
<div class="small-note">
<strong>{escape(BRAND_NAME)}</strong> — astrology is a symbolic interpretive framework and is not a substitute for professional advice.
{"<br><strong>Preview build:</strong> " + escape(BUILD_LABEL) if EDITOR_PREVIEW_ENABLED else ""}
<br><a href="/privacy">Privacy</a> · <a href="/natal-snapshot">Free Natal Snapshot</a> · <a href="/timing-map">12-Month Timing Map</a>{f' · <a href="{escape(LUNA_YOUTUBE_CHANNEL_URL)}" target="_blank" rel="noopener">YouTube</a>' if LUNA_YOUTUBE_CHANNEL_URL else ''}
</div>
        """,
        unsafe_allow_html=True,
    )


install_css()

HOME_PAGE_REF = st.Page(
    home_page,
    title="Home",
    default=True,
)
DAILY_PAGE_REF = st.Page(
    daily_page,
    title="Daily Horoscope",
    url_path="daily-horoscope",
)
WEEKLY_PAGE_REF = st.Page(
    weekly_page,
    title="Weekly View",
    url_path="weekly-view",
)
WEEKLY_STUDIO_REF = st.Page(
    weekly_studio_page,
    title="Weekly Video Studio",
    url_path="weekly-studio",
    visibility="hidden",
)
MONTHLY_INDEX_REF = st.Page(
    monthly_index_page,
    title="August 2026 Horoscopes",
    url_path="august-2026-horoscopes",
)
MONTHLY_PREVIEW_REF = st.Page(
    monthly_preview_page,
    title="Monthly Preview",
    url_path="monthly-preview",
    visibility="hidden",
)
EDITORIAL_PREVIEW_REF = st.Page(
    editorial_preview_page,
    title="Editorial Preview",
    url_path="editorial-preview",
    visibility="hidden",
)
FORECAST_LIBRARY_REF = st.Page(
    forecast_library_page,
    title="Forecast Library",
    url_path="forecast-library",
    visibility="hidden",
)
EPHEMERIS_ADMIN_REF = st.Page(
    ephemeris_admin_page,
    title="Ephemeris Admin",
    url_path="ephemeris-admin",
    visibility="hidden",
)
REPORTS_PAGE_REF = st.Page(
    reports_page,
    title="Reports",
    url_path="reports",
)
HOUSES_PAGE_REF = st.Page(
    houses_page,
    title="House Guide",
    url_path="house-guide",
)
SAMPLE_PAGE_REF = st.Page(
    sample_page,
    title="Sample Report",
    url_path="sample-report",
)
SOLAR_YEAR_PAGE_REF = st.Page(
    solar_year_page,
    title="Solar Year",
    url_path="solar-year",
)
NATAL_SNAPSHOT_REF = st.Page(
    natal_snapshot_page,
    title="Free Natal Snapshot",
    url_path="natal-snapshot",
    visibility="hidden",
)
TIMING_MAP_REF = st.Page(
    timing_map_page,
    title="12-Month Timing Map",
    url_path="timing-map",
)
METHOD_PAGE_REF = st.Page(
    method_page,
    title="How It Works",
    url_path="how-it-works",
)
PRIVACY_PAGE_REF = st.Page(
    privacy_page,
    title="Privacy",
    url_path="privacy",
    visibility="hidden",
)
PAYMENT_SUCCESS_REF = st.Page(
    payment_success_page,
    title="Your Report",
    url_path="payment-success",
    visibility="hidden",
)

MONTHLY_PAGE_REFS = {
    sign: st.Page(
        make_monthly_page(sign),
        title=f"{sign} August 2026",
        url_path=f"august-2026-{sign_slug(sign)}",
        visibility="hidden",
    )
    for sign in SIGNS
}

ALL_PAGES = [
    HOME_PAGE_REF,
    DAILY_PAGE_REF,
    WEEKLY_PAGE_REF,
    WEEKLY_STUDIO_REF,
    MONTHLY_INDEX_REF,
    MONTHLY_PREVIEW_REF,
    EDITORIAL_PREVIEW_REF,
    FORECAST_LIBRARY_REF,
    EPHEMERIS_ADMIN_REF,
    REPORTS_PAGE_REF,
    HOUSES_PAGE_REF,
    SAMPLE_PAGE_REF,
    SOLAR_YEAR_PAGE_REF,
    NATAL_SNAPSHOT_REF,
    TIMING_MAP_REF,
    METHOD_PAGE_REF,
    PRIVACY_PAGE_REF,
    PAYMENT_SUCCESS_REF,
    *MONTHLY_PAGE_REFS.values(),
]

current_page = st.navigation(ALL_PAGES, position="hidden")

brand_header()
top_navigation(current_page.url_path)
_render_site_solar_wave(current_page.url_path)
install_google_analytics(
    f"{current_page.title} | {BRAND_NAME}",
    "/" if not current_page.url_path else f"/{current_page.url_path}",
)
install_statcounter()

current_page.run()
footer()
