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
    city_input_help,
    daily_solar_convergence,
    representative_city_name,
    resolve_location,
    solar_gate_label,
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
        st.session_state.get("landing-daily-sign")
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
        (monthly_path, "This Month"),
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
) -> None:
    question_value = personal_question or "No optional question supplied"
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

        with st.form(f"{key_context}-monthly-checkout"):
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
            st.caption(
                "Instant delivery: after Stripe confirms payment, your report opens immediately and Luna emails your private return link."
            )
            submitted = st.form_submit_button(
                f"Prepare monthly checkout — {MONTHLY_PRICE}",
                type="primary",
                use_container_width=True,
            )

        state_key = f"prepared-order::{key_context}::monthly"
        if submitted:
            if not valid_email(delivery_email):
                st.error("Enter a valid delivery email before continuing to payment.")
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


def _render_lean_daily(path: str) -> None:
    set_page_metadata(
        "Daily Horoscope | Luna Convergence",
        "Read today's Luna Convergence horoscope for your zodiac sign, with one clear interpretation and one practical move.",
        path,
    )

    sign = st.selectbox(
        "Your zodiac sign",
        SIGNS,
        index=SIGNS.index(DEFAULT_SIGN),
        key="landing-daily-sign",
        label_visibility="collapsed",
    )
    st.session_state["daily-sign"] = sign

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
</section>
        """,
        unsafe_allow_html=True,
    )


def home_page() -> None:
    _render_lean_daily("/")


def daily_page() -> None:
    # Keep the established /daily-horoscope URL alive for bookmarks and links,
    # while showing the same stripped-back Daily experience as the homepage.
    _render_lean_daily("/daily-horoscope")


def render_monthly_preview_workspace() -> None:
    """Generate a complete monthly report without exposing the paid checkout flow."""
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
    return period_report(
        sign,
        date(SEO_YEAR, SEO_MONTH, 1),
        date(SEO_YEAR, SEO_MONTH, 31),
        DEFAULT_TIMEZONE,
        f"{SEO_MONTH_NAME} {SEO_YEAR}",
        transition_count=7,
    )


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


def monthly_sign_page(sign: str) -> None:
    data = monthly_seo_data(sign)
    narrative = build_monthly_narrative(
        data,
        main_focus="General overview",
    )
    title = f"{sign} August 2026 Horoscope | Luna Convergence"
    description = (
        f"{sign} August 2026 horoscope with a concise Luna narrative, "
        "relationship meaning, concrete scenarios and evidence available on demand."
    )
    path = f"/august-2026-{sign_slug(sign)}"
    set_page_metadata(title, description, path)

    if EDITOR_PREVIEW_ENABLED:
        st.warning(
            f"Editorial preview mode — {BUILD_LABEL}. "
            "The full report and browser print controls are visible without Stripe."
        )
        render_monthly_experience(
            narrative,
            data,
            show_print=True,
            preview=False,
        )
    else:
        render_monthly_experience(
            _august_preview_narrative(narrative),
            data,
            show_print=False,
            preview=True,
        )

    st.markdown(
        '<div class="eyebrow monthly-other-signs-label">Read another August 2026 sign</div>',
        unsafe_allow_html=True,
    )
    links = [
        f'<a href="/august-2026-{sign_slug(item)}">{escape(item)}</a>'
        for item in SIGNS
    ]
    st.markdown(
        '<div class="related-signs">' + "".join(links) + "</div>",
        unsafe_allow_html=True,
    )

    if not EDITOR_PREVIEW_ENABLED:
        st.markdown("## Get the complete personalised month")
        st.markdown(
            "The paid report adds the three-act timeline, love/work/money guidance, "
            "your selected focus, Solar Convergence, key dates and full evidence "
            "dropdowns while keeping the main page sparse."
        )
        report_cta(
            context=f"august-2026-{sign_slug(sign)}",
            prefill_sign=sign,
            prefill_month=f"{SEO_MONTH_NAME} {SEO_YEAR}",
        )
    else:
        st.caption(
            "Checkout is temporarily hidden on this page while editorial preview mode is active."
        )


def make_monthly_page(sign: str):
    def page() -> None:
        monthly_sign_page(sign)

    page.__name__ = f"{sign_slug(sign).replace('-', '_')}_august_2026"
    return page


def solar_year_page() -> None:
    set_page_metadata(
        "The Solar Year | Luna Convergence",
        "Explore the twelve tropical solar phases, four equinox and solstice gates, local daylight movement and the activated whole-sign house.",
        "/solar-year",
    )
    st.markdown('<div class="eyebrow">Explainable astrology / solar structure</div>', unsafe_allow_html=True)
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

To request correction or deletion of order information, use the contact
email displayed during checkout or in the report-delivery message.
        """
    )
    st.markdown("## Analytics events used")
    st.markdown(
        """
- page views;
- free daily reading generation;
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
<br><a href="/privacy">Privacy</a>
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
    MONTHLY_INDEX_REF,
    MONTHLY_PREVIEW_REF,
    EDITORIAL_PREVIEW_REF,
    FORECAST_LIBRARY_REF,
    EPHEMERIS_ADMIN_REF,
    REPORTS_PAGE_REF,
    HOUSES_PAGE_REF,
    SAMPLE_PAGE_REF,
    SOLAR_YEAR_PAGE_REF,
    METHOD_PAGE_REF,
    PRIVACY_PAGE_REF,
    PAYMENT_SUCCESS_REF,
    *MONTHLY_PAGE_REFS.values(),
]

current_page = st.navigation(ALL_PAGES, position="hidden")

brand_header()
top_navigation(current_page.url_path)
install_google_analytics(
    f"{current_page.title} | {BRAND_NAME}",
    "/" if not current_page.url_path else f"/{current_page.url_path}",
)
install_statcounter()

current_page.run()
footer()
