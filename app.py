from __future__ import annotations

from datetime import date
from functools import lru_cache
import json
from calendar import month_name
from pathlib import Path
from html import escape
import base64
from PIL import Image

import streamlit as st

from astrology_engine import SIGNS, HOUSE_NAMES
from customer_experience import free_daily_reading, prepared_order_email
from synthesis import house_reference_matrix, house_aware_conclusion, period_report
from interpretation_library import HOUSE_STRATEGY
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
GA_MEASUREMENT_ID = secret("GA_MEASUREMENT_ID", "G-TE5HPKV94D")
PUBLIC_SITE_URL = "https://luna-convergence.streamlit.app"
DAILY_PAGE_REF = None


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
    padding:.42rem .62rem;
    color:var(--black) !important;
    text-decoration:none !important;
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.66rem;
    text-transform:uppercase;
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


def top_navigation(current_path: str) -> None:
    path = current_path or ""
    items = [
        ("", "Home"),
        ("daily-horoscope", "Daily horoscope"),
        ("august-2026-horoscopes", "August 2026"),
        ("reports", "Reports"),
        ("house-guide", "House guide"),
        ("sample-report", "Sample report"),
        ("how-it-works", "How it works"),
    ]
    links = []
    for item_path, label in items:
        active = " active" if path == item_path else ""
        href = "/" if not item_path else f"/{item_path}"
        links.append(
            f'<a class="{active.strip()}" href="{href}">'
            f'<span class="nav-dot"></span>{escape(label)}</a>'
        )
    st.markdown(
        '<nav class="top-nav" aria-label="Primary navigation">'
        + "".join(links)
        + "</nav>",
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
) -> None:
    if url:
        safe_url = escape(url, quote=True)
        safe_label = escape(label)
        st.html(
            f"""
<a class="payment-link"
   href="{safe_url}"
   target="_blank"
   rel="noopener noreferrer"
   onclick="if(window.gtag){{window.gtag('event','{event_name}',{{
      event_category:'conversion',
      link_url:'{safe_url}',
      value:1
   }});}}">
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
        payment_button(
            "Get the monthly report",
            MONTHLY_PAYMENT_URL,
            "monthly-disabled",
            "monthly_report_click",
        )
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
        payment_button(
            "Get the year-ahead report",
            YEARLY_PAYMENT_URL,
            "yearly-disabled",
            "yearly_report_click",
        )


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
  <div class="daily-kicker">Free daily reading / {escape(reading.sign)}</div>
  <div class="daily-headline">{escape(reading.headline)}</div>
  <div class="daily-date">{reading.reading_date.strftime("%A, %B %d, %Y")}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    paragraphs = "".join(
        f"<p>{escape(paragraph)}</p>"
        for paragraph in reading.forecast_paragraphs
    )
    st.markdown(
        f'<div class="forecast-copy">{paragraphs}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="best-move">
  <div class="best-move-label">Your best move</div>
  <div class="best-move-copy">{escape(reading.best_move)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## Questions for today")
    question_html = "".join(
        f'<div class="question-item">{escape(question)}</div>'
        for question in reading.reflection_questions
    )
    st.markdown(
        f'<div class="question-list">{question_html}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="area-strip">
  <div class="area-note">
    <div class="eyebrow">Love</div>
    <p>{escape(reading.love_note)}</p>
  </div>
  <div class="area-note">
    <div class="eyebrow">Work</div>
    <p>{escape(reading.work_note)}</p>
  </div>
  <div class="area-note">
    <div class="eyebrow">Money</div>
    <p>{escape(reading.money_note)}</p>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## The active houses")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(
            f"""
<div class="card">
  <div class="eyebrow">The opening</div>
  <h3>House {reading.sun_house}</h3>
  <p><strong>{escape(HOUSE_NAMES[reading.sun_house].capitalize())}</strong></p>
  <p>{escape(reading.opportunity)}</p>
</div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
<div class="card">
  <div class="eyebrow">The sensitivity</div>
  <h3>House {reading.moon_house}</h3>
  <p><strong>{escape(HOUSE_NAMES[reading.moon_house].capitalize())}</strong></p>
  <p>{escape(reading.caution)}</p>
</div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("Why this reading — planetary detail"):
        st.markdown(reading.daily_theme)
        if reading.anchor_aspect:
            anchor = reading.anchor_aspect
            st.markdown(
                f"""
<div class="technical-line">
<strong>Dominant aspect:</strong> {escape(anchor.label)} · orb {anchor.orb:.2f}°<br>
<strong>{escape(anchor.planet1)}:</strong> {escape(anchor.position1)} · house {anchor.house1}<br>
<strong>{escape(anchor.planet2)}:</strong> {escape(anchor.position2)} · house {anchor.house2}
</div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### The wider convergence context")
        st.markdown(reading.wider_context)

        st.markdown("### Three dominant aspects")
        for item in reading.aspects:
            st.markdown(item)

        st.markdown("### House-based conclusion")
        st.markdown(reading.conclusion)

        st.markdown("### The 12-house reference matrix")
        st.markdown(reading.house_matrix)

    st.markdown(
        """
<div class="callout">
<strong>What is grounded beneath the writing:</strong> the headline, forecast, questions and practical
action are translated from the calculated planetary positions, whole-sign houses, dominant aspects and
active convergence pattern. The wording remains conditional because a general sign reading cannot know
the reader's exact personal circumstances.
</div>
        """,
        unsafe_allow_html=True,
    )


def home_page() -> None:
    set_page_metadata(
        "Luna Convergence | Strategic Astrology",
        "Free daily horoscopes and detailed monthly and year-ahead astrology reports using whole-sign houses, retrogrades and convergence analysis.",
        "/",
    )
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
            st.session_state["daily-sign"] = sign
            track_event(
                "daily_reading_start",
                {"source": "homepage", "zodiac_sign": sign},
            )
            if DAILY_PAGE_REF is not None:
                st.switch_page(DAILY_PAGE_REF)

    with right:
        try:
            reading = free_daily_reading(DEFAULT_SIGN, date.today(), DEFAULT_TIMEZONE)
            st.markdown(
                f"""
<div class="reading-card">
  <div class="daily-kicker">Today's example / {DEFAULT_SIGN}</div>
  <div class="daily-headline" style="font-size:clamp(2.2rem,4vw,4.4rem);">
    {escape(reading.headline)}
  </div>
  <p class="muted-white">{escape(reading.forecast_paragraphs[0])}</p>
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
    set_page_metadata(
        "Free Daily Horoscope | Luna Convergence",
        "Read a warm, human daily horoscope grounded in calculated active houses, planetary aspects and the wider convergence context.",
        "/daily-horoscope",
    )
    st.markdown('<div class="eyebrow">Free daily horoscope</div>', unsafe_allow_html=True)
    st.markdown("# A personal reading with the astrology underneath")
    st.markdown(
        "Begin with the human meaning of the day, then open the planetary detail to see the houses, aspects and convergence pattern beneath it."
    )
    sign, reading_date, timezone_name = daily_controls()
    if st.button("Generate my daily reading", type="primary", use_container_width=True):
        st.session_state.force_daily = True
        track_event(
            "daily_reading_generated",
            {
                "zodiac_sign": sign,
                "reading_date": reading_date.isoformat(),
                "timezone": timezone_name,
            },
        )
    if st.session_state.get("force_daily"):
        render_free_reading(sign, reading_date, timezone_name)
        report_cta()


def reports_page() -> None:
    set_page_metadata(
        "Monthly and Year-Ahead Astrology Reports | Luna Convergence",
        "Order a monthly strategic astrology report or a detailed year-ahead forecast delivered electronically.",
        "/reports",
    )
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

    report_cta()


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
    set_page_metadata(
        "August 2026 Horoscopes for Every Zodiac Sign | Luna Convergence",
        "Read the free August 2026 horoscope overview for Aries through Pisces, including active houses, important dates, opportunities and cautions.",
        "/august-2026-horoscopes",
    )
    st.markdown('<div class="eyebrow">Monthly horoscope library</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="editorial-title">August 2026<br>horoscopes</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Choose your Sun sign or rising sign. Each page uses the same planetary sky "
        "but maps it into a different whole-sign house pattern, producing a distinct "
        "focus for work, money, relationships, home and long-term direction."
    )

    cards = []
    for sign in SIGNS:
        data = monthly_seo_data(sign)
        primary = data["dominant_houses"][0]
        key_event = data["major_transitions"][0]
        cards.append(
            f"""
<a class="sign-card" href="/august-2026-{sign_slug(sign)}">
  <div class="eyebrow">{escape(sign)}</div>
  <div class="sign-card-title">House {primary['house']}</div>
  <div class="sign-card-copy"><strong>{escape(primary['topic'].capitalize())}</strong></div>
  <div class="sign-card-copy">{escape(key_event['title'])}</div>
</a>
            """
        )
    st.markdown(
        '<div class="sign-grid">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("## What the free monthly overview includes")
    st.markdown(
        """
- the two strongest active houses;
- major ingresses, eclipses and lunations;
- work, money and relationship implications;
- the leading convergence period;
- a direct opportunity, caution and practical conclusion.
        """
    )
    report_cta()


def monthly_sign_page(sign: str) -> None:
    data = monthly_seo_data(sign)
    primary = data["dominant_houses"][0]
    secondary = data["dominant_houses"][1]
    title = f"{sign} August 2026 Horoscope | Luna Convergence"
    description = (
        f"{sign} August 2026 horoscope covering active houses, major transitions, "
        "important dates, work, money, relationships, opportunities and cautions."
    )
    path = f"/august-2026-{sign_slug(sign)}"
    set_page_metadata(title, description, path)

    st.markdown('<div class="eyebrow">Free monthly horoscope</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="editorial-title">{escape(sign)}<br>August 2026</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"For **{sign}**, August 2026 is led by house {primary['house']}: "
        f"**{primary['topic']}**. The secondary pressure point is house "
        f"{secondary['house']}: **{secondary['topic']}**. The month works best "
        "when expansion, timing and responsibility are treated as one connected system."
    )

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown(
            f"""
<div class="card">
  <div class="eyebrow">Opportunity</div>
  <h3>Build through house {primary['house']}</h3>
  <p>{escape(HOUSE_STRATEGY[primary['house']]['opportunity'].capitalize())}.</p>
  <p><strong>Best move:</strong> {escape(HOUSE_STRATEGY[primary['house']]['action'].capitalize())}.</p>
</div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""
<div class="card">
  <div class="eyebrow">Caution</div>
  <h3>Protect house {secondary['house']}</h3>
  <p>{escape(HOUSE_STRATEGY[secondary['house']]['risk'].capitalize())}.</p>
  <p><strong>Rule:</strong> do not mistake urgency for a complete decision.</p>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("## Important dates and transitions")
    rows = []
    for event in data["major_transitions"][:7]:
        event_date = date.fromisoformat(event["event_date"]).strftime("%B %d")
        rows.append(
            f"""
<div class="date-row">
  <div class="date-label">{escape(event_date)}</div>
  <div class="date-line"><strong>{escape(event['title'])}</strong><br>{escape(event['detail'])}</div>
</div>
            """
        )
    st.markdown(
        '<div class="date-list">' + "".join(rows) + "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("## Work and direction")
    st.markdown(focus_paragraph(data, {6, 10}, "work and career"))

    st.markdown("## Money and obligations")
    st.markdown(focus_paragraph(data, {2, 8}, "money and financial commitments"))

    st.markdown("## Relationships and alliances")
    st.markdown(focus_paragraph(data, {5, 7, 11}, "relationships and alliances"))

    st.markdown("## The leading convergence point")
    if data["convergences"]:
        convergence = data["convergences"][0]
        start = date.fromisoformat(convergence["start_date"]).strftime("%B %d")
        end = date.fromisoformat(convergence["end_date"]).strftime("%B %d")
        house_list = ", ".join(str(house) for house in convergence["houses"])
        st.markdown(
            f"**{convergence['title']} — {start} to {end}.** "
            f"This cluster connects houses {house_list} through "
            f"{len(convergence['events'])} overlapping events. Its value comes from "
            "reading the events together: opportunity is strongest when contracts, "
            "money, communication and operational capacity support the same decision."
        )
    else:
        st.markdown(
            "No high-density convergence met the engine's threshold. "
            "The dominant-house pattern is therefore the clearest guide."
        )

    st.markdown("## Practical conclusion")
    st.info(
        house_aware_conclusion(
            sign,
            primary["house"],
            secondary["house"],
        )
    )

    st.markdown("## Read another August 2026 sign")
    links = [
        f'<a href="/august-2026-{sign_slug(item)}">{escape(item)}</a>'
        for item in SIGNS
    ]
    st.markdown(
        '<div class="related-signs">' + "".join(links) + "</div>",
        unsafe_allow_html=True,
    )
    report_cta()


def make_monthly_page(sign: str):
    def page() -> None:
        monthly_sign_page(sign)

    page.__name__ = f"{sign_slug(sign).replace('-', '_')}_august_2026"
    return page


def privacy_page() -> None:
    set_page_metadata(
        "Privacy and Analytics | Luna Convergence",
        "How Luna Convergence uses Google Analytics, Stripe and customer information for digital astrology reports.",
        "/privacy",
    )
    st.markdown('<div class="eyebrow">Privacy</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="editorial-title">Privacy and<br>analytics</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
Luna Convergence uses **Google Analytics 4** to understand website visits,
page use, free-reading generation and clicks leading to Stripe checkout.
Google Analytics may process device, browser, approximate location and usage
information according to Google's own privacy terms.

Payments are processed by **Stripe**. Luna Convergence does not receive or
store complete card details. Stripe supplies the payment status, customer
email and any checkout information the customer submits.

Paid reports are currently fulfilled manually. Information such as name,
email, zodiac sign, requested period and timezone is used only to prepare,
deliver and support the purchased report.

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
- year-ahead report checkout clicks.
        """
    )


def footer() -> None:
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.divider()
    st.markdown(
        f"""
<div class="small-note">
<strong>{escape(BRAND_NAME)}</strong> — tropical geocentric astrology using whole-sign houses.
Astrology is a symbolic interpretive framework and is not a substitute for professional advice.
<br><a href="/privacy">Privacy and analytics</a> ·
<a href="/august-2026-horoscopes">August 2026 horoscopes</a>
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
    REPORTS_PAGE_REF,
    HOUSES_PAGE_REF,
    SAMPLE_PAGE_REF,
    METHOD_PAGE_REF,
    PRIVACY_PAGE_REF,
    *MONTHLY_PAGE_REFS.values(),
]

current_page = st.navigation(ALL_PAGES, position="hidden")

brand_header()
top_navigation(current_page.url_path)
install_google_analytics(
    f"{current_page.title} | {BRAND_NAME}",
    "/" if not current_page.url_path else f"/{current_page.url_path}",
)

current_page.run()
footer()
