from __future__ import annotations

from datetime import date
from calendar import month_name
from pathlib import Path
from html import escape
import base64
from PIL import Image

import streamlit as st

from astrology_engine import SIGNS
from customer_experience import free_daily_reading, prepared_order_email
from synthesis import house_reference_matrix
from site_config import (
    BRAND_NAME,
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
REPORT_REQUEST_URL = secret("REPORT_REQUEST_URL")
NEWSLETTER_URL = secret("NEWSLETTER_URL")
CONTACT_EMAIL = secret("CONTACT_EMAIL", "your-email@example.com")


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

html, body, [class*="css"] {
    color: var(--ink);
    font-family: "Josefin Sans", "Avenir Next", "Century Gothic", Arial, sans-serif;
}

.stApp {
    background: var(--white);
}

.block-container {
    max-width: 1280px;
    padding-top: 2.2rem;
    padding-bottom: 5rem;
    padding-left: clamp(1rem, 4vw, 4.5rem);
    padding-right: clamp(1rem, 4vw, 4.5rem);
}

header[data-testid="stHeader"] {
    display:none !important;
    height:0 !important;
}

#MainMenu, footer {
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

.price {
    font-family:"Josefin Sans", sans-serif;
    font-size:2.8rem;
    line-height:1;
    font-weight:500;
    margin:.6rem 0 1rem;
}

.pill {
    display:inline-block;
    border-radius:0;
    padding:.34rem .55rem;
    margin:.25rem .28rem .1rem 0;
    border:1px solid var(--black);
    background:var(--white);
    color:var(--black);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.67rem;
    font-weight:500;
    text-transform:uppercase;
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
        padding-left:1rem;
        padding-right:1rem;
        padding-top:.65rem;
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
  <div class="brand-note">Strategic astrology / planetary timing / convergence</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def navigation() -> str:
    if "page" not in st.session_state:
        st.session_state.page = "Home"
    chosen = st.radio(
        "Main navigation",
        NAV_ITEMS,
        index=NAV_ITEMS.index(st.session_state.page),
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.page = chosen
    return chosen


def payment_button(label: str, url: str, key: str) -> None:
    if url:
        st.link_button(label, url, use_container_width=True)
    else:
        st.button(
            f"{label} — link not connected",
            key=key,
            disabled=True,
            use_container_width=True,
        )


def report_cta() -> None:
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("## Choose the depth you need")
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown(
            f"""
<div class="card">
  <div class="eyebrow">Monthly strategic report</div>
  <div class="price">{MONTHLY_PRICE}</div>
  <p>Major transitions, convergence points, retrogrades, work, money, relationships and important dates.</p>
  <span class="pill">One zodiac sign</span>
  <span class="pill">One month</span>
  <span class="pill">Manual delivery</span>
</div>
            """,
            unsafe_allow_html=True,
        )
        payment_button("Get the monthly report", MONTHLY_PAYMENT_URL, "monthly-disabled")
    with right:
        st.markdown(
            f"""
<div class="card">
  <div class="eyebrow">Year-ahead strategic report</div>
  <div class="price">{YEARLY_PRICE}</div>
  <p>Nine strategic chapters, eclipse sequence, full retrograde cycles, convergence windows and a month-by-month map.</p>
  <span class="pill">One zodiac sign</span>
  <span class="pill">Full year</span>
  <span class="pill">Detailed report</span>
</div>
            """,
            unsafe_allow_html=True,
        )
        payment_button("Get the year-ahead report", YEARLY_PAYMENT_URL, "yearly-disabled")


def daily_controls(prefix: str = "daily") -> tuple[str, date, str]:
    c1, c2, c3 = st.columns([1.05, 1, 1.25], gap="medium")
    with c1:
        sign = st.selectbox(
            "Your zodiac sign",
            SIGNS,
            index=SIGNS.index(DEFAULT_SIGN),
            key=f"{prefix}-sign",
        )
    with c2:
        reading_date = st.date_input(
            "Date",
            value=date.today(),
            min_value=date(1900, 1, 1),
            max_value=date(2100, 12, 31),
            key=f"{prefix}-date",
        )
    with c3:
        timezone_name = st.selectbox(
            "Timezone",
            TIMEZONES,
            index=TIMEZONES.index(DEFAULT_TIMEZONE),
            key=f"{prefix}-timezone",
        )
    return sign, reading_date, timezone_name


def render_free_reading(sign: str, reading_date: date, timezone_name: str) -> None:
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

    st.markdown(
        f"""
<div class="reading-card">
  <div class="eyebrow" >Free daily reading</div>
  <h3>{escape(reading.sign)} — {reading.reading_date.strftime("%A, %B %d, %Y")}</h3>
  <p><strong>{escape(reading.daily_theme)}</strong></p>
  <p class="muted-white">{reading.conclusion}</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### The wider context")
    st.markdown(reading.wider_context)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(
            f"""
<div class="card">
  <div class="eyebrow">Opportunity</div>
  <h3>House {reading.sun_house}</h3>
  <p>{escape(reading.opportunity.capitalize())}.</p>
  <p><strong>Best move:</strong> {escape(reading.best_move.capitalize())}.</p>
</div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
<div class="card">
  <div class="eyebrow">Caution</div>
  <h3>House {reading.moon_house}</h3>
  <p>{escape(reading.caution.capitalize())}.</p>
  <p><strong>Rule:</strong> React after the facts and responsibilities are clear.</p>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Three dominant aspects")
    for item in reading.aspects:
        st.markdown(item)

    with st.expander("Open the 12-house reference matrix"):
        st.markdown(reading.house_matrix)

    st.markdown(
        """
<div class="callout">
<strong>What the free reading does:</strong> identifies today's active houses, the main opportunity,
the immediate caution and the wider convergence context. Paid reports add the full transition map,
retrograde phases, important dates and strategic chapters.
</div>
        """,
        unsafe_allow_html=True,
    )


def home_page() -> None:
    left, right = st.columns([1.2, .8], gap="large")
    with left:
        st.markdown('<div class="eyebrow">Astrology / timing / practical interpretation</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="editorial-title">{escape(TAGLINE)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="hero-subtitle">{escape(SUBTITLE)}</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-rule"></div>', unsafe_allow_html=True)

        sign = st.selectbox(
            "Choose your sign",
            SIGNS,
            index=SIGNS.index(DEFAULT_SIGN),
            key="home-sign",
        )
        if st.button("Read today's free horoscope", type="primary", use_container_width=True):
            st.session_state.page = "Daily Horoscope"
            st.session_state["daily-sign"] = sign
            st.rerun()

    with right:
        try:
            reading = free_daily_reading(DEFAULT_SIGN, date.today(), DEFAULT_TIMEZONE)
            st.markdown(
                f"""
<div class="reading-card">
  <div class="eyebrow" >Today's example</div>
  <h3>{DEFAULT_SIGN}</h3>
  <p><strong>House {reading.sun_house}</strong>: {escape(reading.opportunity.capitalize())}.</p>
  <p><strong>House {reading.moon_house}</strong>: watch for {escape(reading.caution)}.</p>
  <p class="muted-white">{reading.conclusion}</p>
</div>
                """,
                unsafe_allow_html=True,
            )
        except Exception:
            st.markdown(
                """
<div class="reading-card">
  <div class="eyebrow" >Today's reading</div>
  <h3>Clear astrology, practical meaning</h3>
  <p>See the active houses, opportunity, caution and wider transition in one clean reading.</p>
</div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
<div class="trust-strip">
  <div class="trust-item">Swiss Ephemeris calculations</div>
  <div class="trust-item">Whole-sign house explanations</div>
  <div class="trust-item">Retrograde-cycle analysis</div>
  <div class="trust-item">Convergence-point interpretation</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    report_cta()

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("## Why this is different")
    c1, c2, c3 = st.columns(3, gap="large")
    items = [
        (
            "The houses are explained",
            "The report keeps the house number but also explains the life area: income, career, contracts, creativity, travel or home.",
        ),
        (
            "Events are connected",
            "A convergence point shows why several transitions matter together rather than listing unrelated planetary events.",
        ),
        (
            "The conclusion is practical",
            "Each reading separates opportunity, risk and the action most likely to make the transition useful.",
        ),
    ]
    for column, (title, body) in zip((c1, c2, c3), items):
        with column:
            st.markdown(
                f'<div class="card"><h3>{escape(title)}</h3><p>{escape(body)}</p></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("## Learn the twelve houses while you read")
    st.markdown(
        "For Sagittarius, for example, house 2 concerns income and pricing, house 7 concerns "
        "partners and contracts, and house 9 concerns travel, publishing and foreign markets."
    )
    st.markdown(house_reference_matrix(DEFAULT_SIGN, {2, 7, 9}))

    if NEWSLETTER_URL:
        st.markdown("## Receive the monthly forecast")
        st.link_button("Join the forecast email list", NEWSLETTER_URL)


def daily_page() -> None:
    st.markdown('<div class="eyebrow">Free daily horoscope</div>', unsafe_allow_html=True)
    st.markdown("# Read today in context")
    st.markdown(
        "The daily forecast identifies the active houses and places today's trigger inside the wider monthly and yearly pattern."
    )
    sign, reading_date, timezone_name = daily_controls()
    if st.button("Generate my daily reading", type="primary", use_container_width=True):
        st.session_state.force_daily = True
    if st.session_state.get("force_daily"):
        render_free_reading(sign, reading_date, timezone_name)
        report_cta()


def reports_page() -> None:
    st.markdown('<div class="eyebrow">Paid reports</div>', unsafe_allow_html=True)
    st.markdown("# Choose the depth you need")
    st.markdown(
        "Launch pricing is deliberately simple: one monthly product and one year-ahead product. "
        "Reports are generated with the calculation engine and checked before manual delivery."
    )
    report_cta()

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("## How ordering works")
    c1, c2, c3 = st.columns(3, gap="large")
    steps = [
        ("1. Pay", "Use the secure payment link for the monthly or year-ahead report."),
        ("2. Send details", "Provide your email, zodiac sign, requested period and timezone."),
        ("3. Receive the report", "The finished report is delivered manually during the validation phase."),
    ]
    for column, (title, body) in zip((c1, c2, c3), steps):
        with column:
            st.markdown(
                f'<div class="card"><h3>{escape(title)}</h3><p>{escape(body)}</p></div>',
                unsafe_allow_html=True,
            )

    st.markdown("## Send your report details")
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
            sign = st.selectbox("Zodiac sign", SIGNS, index=SIGNS.index(DEFAULT_SIGN))
        with c2:
            requested_period = st.text_input(
                "Requested month or year",
                placeholder="Example: August 2026 or 2027",
            )
            timezone_name = st.selectbox(
                "Timezone",
                TIMEZONES,
                index=TIMEZONES.index(DEFAULT_TIMEZONE),
            )
            payment_reference = st.text_input(
                "Payment reference",
                placeholder="Optional at this stage",
            )
        submitted = st.form_submit_button("Prepare my order email", type="primary")

    if submitted:
        if not customer_name or not customer_email or not requested_period:
            st.error("Enter your name, email and requested month or year.")
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
            )
            st.link_button("Open the prepared email", mailto, use_container_width=True)

    if REPORT_REQUEST_URL:
        st.link_button("Use the online order-details form instead", REPORT_REQUEST_URL)


def houses_page() -> None:
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


def sample_page() -> None:
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

    report_cta()


def method_page() -> None:
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
        "The public daily reading requires no account. Paid orders initially use manual fulfilment, "
        "so the site only needs the minimum details required to deliver the report."
    )


install_css()
brand_header()
page = navigation()
st.divider()

if page == "Home":
    home_page()
elif page == "Daily Horoscope":
    daily_page()
elif page == "Reports":
    reports_page()
elif page == "House Guide":
    houses_page()
elif page == "Sample Report":
    sample_page()
else:
    method_page()

st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
st.divider()
st.markdown(
    f"""
<div class="small-note">
<strong>{escape(BRAND_NAME)}</strong> — tropical geocentric astrology using whole-sign houses.
Astrology is a symbolic interpretive framework and is not a substitute for professional advice.
</div>
    """,
    unsafe_allow_html=True,
)
