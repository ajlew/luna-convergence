from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
import json
import hashlib
import math
import re
import secrets
from calendar import month_name, monthrange
from pathlib import Path
from zoneinfo import ZoneInfo
from html import escape
import base64
import difflib
from PIL import Image

import streamlit as st
import streamlit.components.v1 as components

from astrology_engine import SIGNS, HOUSE_NAMES, positions_for_date
from date_display import human_date
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
from plain_readings import load_reading as load_plain_reading, reading_html as plain_reading_html, split_move as split_plain_move
from reading_facts import build_packet as build_plain_packet
from monthly_voice_publisher import build_public_monthly_event_facts
from monthly_narrative_v1 import build_monthly_narrative
from monthly_experience_v1 import render_monthly_experience, build_monthly_reader_chronology
from monthly_report_pipeline import (
    build_production_monthly_report,
    render_production_monthly_report,
)
from yearly_experience_v1 import render_yearly_experience
from forecast_inventory import EDITORIAL_STATUSES, build_inventory, inventory_json
from ephemeris_admin import render_ephemeris_admin
from luna_voice import (
    convergent_bridge,
    finalize_customer_prose,
    human_arc,
    human_arc_sentence,
    imperative_for,
    inline_story_title,
    life_domain,
    life_scene,
    luna_dry_truth,
    narrator_principle,
    simplify_life_area,
    voice_profile,
)
from solar_cycle import (
    CITY_LOCATIONS,
    city_input_help,
    daily_solar_convergence,
    representative_city_name,
    resolve_location,
    solar_gate_label,
)
from natal_snapshot import (
    birth_date_luminary_calculations,
    build_natal_snapshot,
    natal_wheel_svg,
    encode_natal_profile,
    decode_natal_profile,
    natal_profile_summary,
    NatalPosition,
    NatalSnapshot,
    NATAL_PROFILE_ORDER,
    detect_natal_aspects,
    _build_signatures,
)
from birthday_card import (
    birthday_card_filename,
    build_birthday_card,
    render_birthday_card_pdf,
    render_birthday_card_png,
)
from birthday_card_voice import (
    BirthdayPoemError,
    build_birthday_poem_facts,
    generate_birthday_poem,
)
from monthly_natal_overlay import build_monthly_natal_overlay
from paid_forecast_context import (
    monthly_calculation_base,
    contextualize_monthly,
    yearly_calculation_base,
    contextualize_yearly,
    load_monthly_calculation_base,
    monthly_required_story_anchors,
)
from concentration_theme import build_monthly_concentration_theme
from solar_year_wave import solar_year_wave_svg
from weekly_view import (
    default_week_start,
    monday_for,
)
import luna_guided_voice as _luna_guided_voice_module
from luna_guided_voice import (
    generate_guided_collection_copy,
    generate_guided_voice_copy,
    validate_guided_collection_copy,
    validate_guided_voice_copy,
)
from luna_voice_provider import generate_openai_compatible_json
from luna_report_bundle import assemble_report_bundle
from timing_map import (
    build_timing_map,
    month_intensity,
)
from major_event_registry import group_personal_activations, group_serialized_personal_activations, personalize_serialized_signals
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
    verify_one_time_price,
)
from email_delivery import send_report_email
from report_pdf import build_report_pdf, report_filename
from site_config import (
    BRAND_NAME,
    BUILD_LABEL as CONFIG_BUILD_LABEL,
    EDITOR_PREVIEW_ENABLED,
    TAGLINE,
    SUBTITLE,
    MONTHLY_PRICE,
    YEARLY_PRICE,
    BIRTHDAY_PRICE,
    DEFAULT_SIGN,
    DEFAULT_TIMEZONE,
    TIMEZONES,
    NAV_ITEMS,
)

# Live deployment identifier. Keep this in app.py so a single-file update
# visibly confirms which application build is running in Streamlit.
APP_VERSION = "v3.68"
BUILD_LABEL = f"Luna {APP_VERSION} — Monthly Adaptive Preflight"
PAID_MONTHLY_STORY_REVISION = "prebuilt-month-base-adaptive-1"


ASSET_DIR = Path(__file__).parent / "assets"
FAVICON_PATH = ASSET_DIR / "saturn_hex_favicon.png"
BRAND_ICON_PATH = ASSET_DIR / "saturn_hex_brand.png"
WEEKLY_BACKGROUND_PATH = ASSET_DIR / "luna_weekly_video_background_1080x1920.png"

st.set_page_config(
    page_title=f"{BRAND_NAME} | Strategic Horoscopes",
    page_icon=Image.open(FAVICON_PATH) if FAVICON_PATH.is_file() else None,
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
STRIPE_BIRTHDAY_PRICE_ID = secret("STRIPE_BIRTHDAY_PRICE_ID")
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
LUNA_YOUTUBE_FEATURED_VIDEO_WEEK_START = secret("LUNA_YOUTUBE_FEATURED_VIDEO_WEEK_START")
LUNA_VOICE_MODE = secret("LUNA_VOICE_MODE", "published").strip().lower()
LUNA_VOICE_BASE_URL = secret("LUNA_VOICE_BASE_URL")
LUNA_VOICE_MODEL = secret("LUNA_VOICE_MODEL")
LUNA_VOICE_API_KEY = secret("LUNA_VOICE_API_KEY")
LUNA_ADMIN_KEY = secret("LUNA_ADMIN_KEY")
PUBLIC_SITE_URL = "https://luna-convergence.streamlit.app"
_VOICE_ERRORS: dict[str, str] = {}

ADMIN_SESSION_KEY = "luna-admin-authenticated-v1"


def _admin_access_unlocked() -> bool:
    return bool(st.session_state.get(ADMIN_SESSION_KEY, False))


def _admin_access_panel(context: str) -> bool:
    """Unlock owner output on the current customer page without exposing the secret."""
    key_context = re.sub(r"[^a-z0-9]+", "-", str(context).lower()).strip("-") or "page"
    if _admin_access_unlocked():
        with st.container(border=True):
            columns = st.columns([4, 1], gap="small")
            with columns[0]:
                st.success("Luna owner access is unlocked for this browser session.")
            with columns[1]:
                if st.button(
                    "Lock",
                    key=f"{key_context}-admin-lock",
                    use_container_width=True,
                ):
                    st.session_state.pop(ADMIN_SESSION_KEY, None)
                    st.rerun()
        return True

    with st.expander("Luna owner access", expanded=False):
        st.caption("Enter the private admin key to generate owner copies without payment.")
        with st.form(f"{key_context}-admin-form", clear_on_submit=True):
            candidate = st.text_input(
                "Admin key",
                type="password",
                key=f"{key_context}-admin-key",
                autocomplete="off",
            )
            submitted = st.form_submit_button(
                "Unlock owner access",
                use_container_width=True,
            )
        if submitted:
            if not LUNA_ADMIN_KEY:
                st.error("LUNA_ADMIN_KEY is not configured in Streamlit secrets.")
            elif secrets.compare_digest(candidate, LUNA_ADMIN_KEY):
                st.session_state[ADMIN_SESSION_KEY] = True
                st.rerun()
            else:
                st.error("That admin key is not valid.")
    return False

_LUNA_STRATEGIC_MOVE_RULE = (
    "Every your_move must improve the reader's position rather than merely repeat the affirmation, warning or summary. "
    "Make the advice strategically asymmetrical where the evidence supports it: preserve optionality, reduce exposure, "
    "make information, reciprocity, cost or commitment visible before committing more, and use leverage only where it is real. "
    "When direct force is wasteful, be cohesive like water: redirect pressure, narrow the problem, wait for the stronger opening, "
    "or move around resistance instead of colliding with it. Give one concrete imperative action and make clear why it improves "
    "the position. Do not recommend deception, coercion, exploitation or harm."
)

# Apply the strategic-move rule at the central voice layer so Daily, Weekly,
# Monthly, Yearly, Natal and collection-generated advice all follow the same
# discipline without forking the astrology engines.
for _product_name, _product_rule in list(getattr(_luna_guided_voice_module, "_PRODUCT_RULES", {}).items()):
    if _LUNA_STRATEGIC_MOVE_RULE not in _product_rule:
        _luna_guided_voice_module._PRODUCT_RULES[_product_name] = (
            _product_rule + " " + _LUNA_STRATEGIC_MOVE_RULE
        )
for _collection_name, _collection_rule in list(getattr(_luna_guided_voice_module, "_COLLECTION_RULES", {}).items()):
    if _LUNA_STRATEGIC_MOVE_RULE not in _collection_rule:
        _luna_guided_voice_module._COLLECTION_RULES[_collection_name] = (
            _collection_rule + " " + _LUNA_STRATEGIC_MOVE_RULE
        )

_VOICE_LOADING_LABELS = {
    "daily": "Luna is reading today's calculated sky. Keep this page openâ€¦",
    "monthly": "Luna is connecting your month. Keep this page openâ€¦",
    "monthly_events": "Luna is writing the dated turning points. Keep this page openâ€¦",
    "personal_events": "Luna is connecting the transits to the natal chart. Keep this page openâ€¦",
    "yearly": "Luna is building the strategic year. Keep this page openâ€¦",
    "yearly_transits": "Luna is writing the major transit chapters. Keep this page openâ€¦",
    "weekly_signs": "Luna is translating the week for all 12 signs. Keep this page openâ€¦",
    "weekly_days": "Luna is connecting Monday through Sunday. Keep this page openâ€¦",
}


def _voice_loading_label(product: str) -> str:
    return _VOICE_LOADING_LABELS.get(
        product,
        "Luna is connecting the calculated evidence. Keep this page openâ€¦",
    )


def _record_voice_error(product: str, error: object) -> None:
    """Keep a safe per-run diagnostic without exposing credentials."""
    message = " ".join(str(error or "Unknown voice error").split())
    if LUNA_VOICE_API_KEY:
        message = message.replace(LUNA_VOICE_API_KEY, "[redacted]")
    _VOICE_ERRORS[product] = message[:700]


def _voice_error(product: str) -> str:
    return _VOICE_ERRORS.get(product, "No provider response was accepted.")


def _word_count(value: object) -> int:
    return len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", str(value or "")))


def _move_token_overlap(a: object, b: object) -> float:
    stop = {
        "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "is", "it",
        "that", "this", "your", "you", "be", "as", "at", "by", "from", "when", "then", "than",
    }
    def tokens(value: object) -> set[str]:
        return {
            token for token in re.findall(r"[a-z]+", str(value or "").lower())
            if len(token) > 2 and token not in stop
        }
    left, right = tokens(a), tokens(b)
    if not left or not right:
        return 0.0
    return len(left & right) / max(1, min(len(left), len(right)))


def _strategic_move_quality(move: object, *, remember: object = "", story: object = "") -> tuple[bool, str]:
    """Keep Your Move concrete, asymmetrical and distinct from the explanatory copy."""
    text = " ".join(str(move or "").split())
    if _word_count(text) < 9:
        return False, "your_move is too vague."
    if remember and _move_token_overlap(text, remember) >= 0.72:
        return False, "your_move repeats the remember/affirmation line."
    if story and _move_token_overlap(text, story) >= 0.82:
        return False, "your_move repeats the story instead of changing the position."
    return True, ""


def _guided_voice_complete(copy: dict) -> tuple[bool, tuple[str, ...]]:
    """Reject structurally valid but visibly incomplete Luna copy before publication."""
    errors: list[str] = []
    if not isinstance(copy, dict):
        return False, ("Luna copy is not an object.",)

    minimum_words = {
        "headline": 3,
        "opening": 8,
        "affirmation": 6,
        "your_move": 9,
    }
    for key, minimum in minimum_words.items():
        if _word_count(copy.get(key)) < minimum:
            errors.append(f"{key} is incomplete.")

    story = copy.get("story") or []
    if isinstance(story, str):
        story = [story]
    if not isinstance(story, (list, tuple)) or not story:
        errors.append("story is missing.")
    else:
        for index, paragraph in enumerate(story, 1):
            if _word_count(paragraph) < 12:
                errors.append(f"story paragraph {index} is incomplete.")

    move_ok, move_error = _strategic_move_quality(
        copy.get("your_move"),
        remember=copy.get("affirmation"),
        story=" ".join(str(item or "") for item in (story or [])),
    )
    if not move_ok:
        errors.append(move_error)

    return not errors, tuple(errors)


def _guided_collection_complete(copy: dict) -> tuple[bool, tuple[str, ...]]:
    """Apply the same completeness floor to generated card collections globally."""
    errors: list[str] = []
    if not isinstance(copy, dict):
        return False, ("Luna collection is not an object.",)
    items = copy.get("items") or []
    if not isinstance(items, list) or not items:
        return False, ("Luna collection is empty.",)
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            errors.append(f"item {index} is not an object.")
            continue
        for key, minimum in (("headline", 3), ("story", 18), ("affirmation", 5), ("your_move", 9)):
            if _word_count(item.get(key)) < minimum:
                errors.append(f"item {index} {key} is incomplete.")
        move_ok, move_error = _strategic_move_quality(
            item.get("your_move"),
            remember=item.get("affirmation"),
            story=item.get("story"),
        )
        if not move_ok:
            errors.append(f"item {index} {move_error}")
    return not errors, tuple(errors)


@st.cache_data(show_spinner=False, ttl=86400)
def _cached_guided_luna_copy(
    product: str,
    facts_json: str,
    base_url: str,
    model: str,
    _api_key: str,
) -> dict:
    facts = json.loads(facts_json)
    last_errors: tuple[str, ...] = ()
    for _attempt in range(3):
        copy = generate_guided_voice_copy(
            product,
            facts,
            base_url=base_url,
            model=model,
            api_key=_api_key,
        )
        valid, schema_errors = validate_guided_voice_copy(product, copy, facts)
        complete, completeness_errors = _guided_voice_complete(copy)
        if valid and complete:
            return copy
        last_errors = tuple(schema_errors) + tuple(completeness_errors)
    raise ValueError("Luna voice failed validation after three attempts: " + "; ".join(last_errors))


@st.cache_data(show_spinner=False, ttl=86400)
def _cached_guided_luna_collection(
    product: str,
    facts_json: str,
    base_url: str,
    model: str,
    _api_key: str,
) -> dict:
    """Generate a collection once at app level.

    The provider helper already retries malformed individual items, and
    validate_guided_collection_copy already enforces completeness, total word
    ranges, provenance and imperative moves. Avoid multiplying those calls at
    the Streamlit layer because large collections can hold a page open.
    """
    facts = json.loads(facts_json)
    copy = generate_guided_collection_copy(
        product,
        facts,
        base_url=base_url,
        model=model,
        api_key=_api_key,
    )
    valid, errors = validate_guided_collection_copy(product, copy, facts)
    complete, completeness_errors = _guided_collection_complete(copy)
    if valid and complete:
        return copy
    all_errors = tuple(errors) + tuple(completeness_errors)
    raise ValueError("Luna collection failed validation: " + "; ".join(all_errors))


@st.cache_data(show_spinner=False, ttl=86400)
def _cached_birthday_poem(
    facts_json: str,
    base_url: str,
    model: str,
    _api_key: str,
) -> str:
    return generate_birthday_poem(
        json.loads(facts_json),
        base_url=base_url,
        model=model,
        api_key=_api_key,
    )


def _guided_luna_copy(product: str, facts: dict) -> dict | None:
    """Return validated generated prose; never block the calculated fallback."""
    if LUNA_VOICE_MODE not in {"published", "live"}:
        _record_voice_error(product, f"LUNA_VOICE_MODE is {LUNA_VOICE_MODE or 'empty'}, not published/live.")
        return None
    if not (LUNA_VOICE_BASE_URL and LUNA_VOICE_MODEL and LUNA_VOICE_API_KEY):
        missing = [
            name for name, value in (
                ("LUNA_VOICE_BASE_URL", LUNA_VOICE_BASE_URL),
                ("LUNA_VOICE_MODEL", LUNA_VOICE_MODEL),
                ("LUNA_VOICE_API_KEY", LUNA_VOICE_API_KEY),
            ) if not value
        ]
        _record_voice_error(product, "Missing Streamlit secret(s): " + ", ".join(missing))
        return None
    try:
        return _cached_guided_luna_copy(
            product,
            json.dumps(facts, ensure_ascii=False, sort_keys=True, default=str),
            LUNA_VOICE_BASE_URL,
            LUNA_VOICE_MODEL,
            LUNA_VOICE_API_KEY,
        )
    except Exception as exc:
        _record_voice_error(product, exc)
        return None


def _guided_luna_collection(product: str, facts: dict) -> dict | None:
    """Return a validated multi-item Luna collection, cached by its calculated facts."""
    if LUNA_VOICE_MODE not in {"published", "live"}:
        _record_voice_error(product, f"LUNA_VOICE_MODE is {LUNA_VOICE_MODE or 'empty'}, not published/live.")
        return None
    if not (LUNA_VOICE_BASE_URL and LUNA_VOICE_MODEL and LUNA_VOICE_API_KEY):
        missing = [
            name for name, value in (
                ("LUNA_VOICE_BASE_URL", LUNA_VOICE_BASE_URL),
                ("LUNA_VOICE_MODEL", LUNA_VOICE_MODEL),
                ("LUNA_VOICE_API_KEY", LUNA_VOICE_API_KEY),
            ) if not value
        ]
        _record_voice_error(product, "Missing Streamlit secret(s): " + ", ".join(missing))
        return None
    try:
        return _cached_guided_luna_collection(
            product,
            json.dumps(facts, ensure_ascii=False, sort_keys=True, default=str),
            LUNA_VOICE_BASE_URL,
            LUNA_VOICE_MODEL,
            LUNA_VOICE_API_KEY,
        )
    except Exception as exc:
        _record_voice_error(product, exc)
        return None


def _luna_voice_ready() -> bool:
    return bool(
        LUNA_VOICE_MODE in {"published", "live"}
        and LUNA_VOICE_BASE_URL
        and LUNA_VOICE_MODEL
        and LUNA_VOICE_API_KEY
    )


def _render_voice_unavailable(*, facts_label: str = "calculated evidence below") -> None:
    """Legacy callers retain their calculated panels; never fabricate prose."""
    return




def _luna_evidence_panel(label: str = "Why Luna sees this", *, expanded: bool = False):
    """Global customer-facing home for technical astrology/calculation evidence."""
    return st.expander(label, expanded=expanded)


def _snapshot_page_heading(eyebrow: str, title: str, intro: str = "") -> None:
    """One customer-facing page heading system, based on Natal Snapshot."""
    title_html = escape(str(title or "")).replace("\n", "<br>")
    st.markdown(f'<div class="eyebrow">{escape(str(eyebrow or ""))}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="editorial-title">{title_html}</div>', unsafe_allow_html=True)
    if intro:
        st.markdown(f'<div class="natal-intro">{escape(str(intro))}</div>', unsafe_allow_html=True)


def _render_guided_luna_story(copy: dict, kicker: str) -> None:
    """Render Luna copy without assuming every product has identical fields."""
    if not isinstance(copy, dict):
        return

    headline = str(copy.get("headline") or "").strip()
    opening = str(copy.get("opening") or "").strip()
    affirmation = str(copy.get("affirmation") or "").strip()
    your_move = str(copy.get("your_move") or "").strip()

    story = copy.get("story") or []

    if isinstance(story, str):
        story = [story]
    elif not isinstance(story, (list, tuple)):
        story = [str(story)] if story else []

    paragraphs = "".join(
        f"<p>{escape(str(paragraph).strip())}</p>"
        for paragraph in story
        if str(paragraph).strip()
    )

    headline_html = (
        f'<div class="weekly-sign-heading" role="heading" aria-level="2">'
        f'{escape(headline)}</div>'
        if headline
        else ""
    )

    opening_html = (
        f"<p><strong>{escape(opening)}</strong></p>"
        if opening
        else ""
    )

    affirmation_html = (
        f'<div class="luna-guidance-line luna-remember-line">'
        f'<span class="luna-guidance-label">Remember</span>'
        f'<p>{escape(affirmation)}</p></div>'
        if affirmation
        else ""
    )

    move_html = (
        f'<div class="luna-guidance-line luna-move-line">'
        f'<span class="luna-guidance-label">Your move</span>'
        f'<p>{escape(your_move)}</p></div>'
        if your_move
        else ""
    )

    st.markdown(
        f"""<section class="weekly-synthesis luna-guided-story">
<div class="weekly-kicker">{escape(kicker)}</div>
{headline_html}
{opening_html}
{paragraphs}
{affirmation_html}
{move_html}
</section>""",
        unsafe_allow_html=True,
    )


def _render_signature_style_story(copy: dict, kicker: str) -> None:
    """Render a Luna narrative with the exact visual grammar of Snapshot signatures."""
    if not isinstance(copy, dict):
        return
    headline = " ".join(str(copy.get("headline") or "").split())
    opening = " ".join(str(copy.get("opening") or "").split())
    affirmation = " ".join(str(copy.get("affirmation") or "").split())
    your_move = " ".join(str(copy.get("your_move") or "").split())
    story = copy.get("story") or []
    if isinstance(story, str):
        story = [story]
    elif not isinstance(story, (list, tuple)):
        story = [str(story)] if story else []

    body_parts = []
    if opening:
        body_parts.append(f"<p>{escape(opening)}</p>")
    body_parts.extend(
        f"<p>{escape(' '.join(str(paragraph).split()))}</p>"
        for paragraph in story
        if str(paragraph).strip()
    )

    meta_parts = []
    if affirmation:
        meta_parts.append(f'<div><span>Remember</span>{escape(affirmation)}</div>')
    if your_move:
        meta_parts.append(f'<div><span>Your move</span>{escape(your_move)}</div>')
    meta_html = ""
    if meta_parts:
        meta_class = "natal-signature-meta" if len(meta_parts) > 1 else "natal-signature-meta natal-signature-meta-single"
        meta_html = f'<div class="{meta_class}">{"".join(meta_parts)}</div>'

    st.markdown(
        f"""<div class="natal-signature-reading report-story-reading">
  <div class="natal-evidence">{escape(kicker)}</div>
  {f'<h3>{escape(headline)}</h3>' if headline else ''}
  {''.join(body_parts)}
  {meta_html}
</div>""",
        unsafe_allow_html=True,
    )
LUNA_TRUST_STATEMENT = (
    "The astrology is calculated, not guessed. Ephemeris data and programmed rules determine "
    "what is happening in your chart; Luna turns those signals into interpretation."
)
LUNA_TRUST_DISCLOSURE = (
    "Luna uses ephemeris data and programmed calculations to identify planetary positions, aspects, "
    "houses and timing. Astrology is interpretive, and calculations or interpretations may occasionally contain errors."
)
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


def _rolling_year_end(start_date: date) -> date:
    """Return the inclusive final day of a rolling 12-month window."""
    try:
        anniversary = start_date.replace(year=start_date.year + 1)
    except ValueError:
        # 29 February has no direct anniversary in a non-leap year.
        anniversary = date(start_date.year + 1, 3, 1)
    return anniversary - timedelta(days=1)


def _yearly_period_code(start_date: date, end_date: date | None = None) -> str:
    """Encode a rolling yearly window compactly for Stripe/order metadata."""
    resolved_end = end_date or _rolling_year_end(start_date)
    return f"{start_date.isoformat()}|{resolved_end.isoformat()}"


def _yearly_period_window(period_code: str) -> tuple[date, date, str]:
    """Decode rolling yearly periods while preserving legacy YYYY orders."""
    code = str(period_code or "").strip()
    if re.fullmatch(r"\d{4}", code):
        year = int(code)
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        return start_date, end_date, str(year)

    if "|" in code:
        start_text, end_text = code.split("|", 1)
        start_date = date.fromisoformat(start_text.strip())
        end_date = date.fromisoformat(end_text.strip())
    else:
        # Tolerate a start-date-only code if one was ever persisted manually.
        start_date = date.fromisoformat(code)
        end_date = _rolling_year_end(start_date)

    if end_date < start_date:
        raise ValueError("Year-ahead report end date cannot precede its start date.")
    return start_date, end_date, f"{start_date.isoformat()} to {end_date.isoformat()}"


def _yearly_period_label(start_date: date, end_date: date) -> str:
    """Customer-facing label for a rolling 12-month report window."""
    return f"{human_date(start_date)} – {human_date(end_date)}"


def timezone_select_index() -> int:
    """Select the browser timezone when Luna offers it, otherwise use the default."""
    timezone_name = browser_timezone_name()
    if timezone_name in TIMEZONES:
        return TIMEZONES.index(timezone_name)
    return TIMEZONES.index(DEFAULT_TIMEZONE)


def sign_select_index(value: str | None = None) -> int | None:
    """Return a saved/prefilled sign index, otherwise keep the selector neutral."""
    return SIGNS.index(value) if value in SIGNS else None


def month_end(year: int, month: int) -> date:
    """Return the actual last day of any selected calendar month."""
    return date(int(year), int(month), monthrange(int(year), int(month))[1])


def monthly_period_from_result(result: dict, narrative=None) -> tuple[int, int, str]:
    """Resolve the selected report period from calculated data, never a fixed campaign date."""
    try:
        selected = date.fromisoformat(str(result.get("start") or result.get("start_date")))
        return selected.year, selected.month, f"{month_name[selected.month]} {selected.year}"
    except Exception:
        pass

    label = str(getattr(narrative, "label", "") or result.get("label") or "").strip()
    try:
        selected = datetime.strptime(label, "%B %Y")
        return selected.year, selected.month, label
    except Exception:
        today = browser_local_date()
        return today.year, today.month, f"{month_name[today.month]} {today.year}"


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
@import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,400;6..96,500;6..96,600&family=IBM+Plex+Mono:wght@400;500;600&family=Josefin+Sans:wght@400;500;600;700&display=swap');

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
    font-size:clamp(1.9rem, 2.7vw, 2.2rem) !important;
    line-height:1.04 !important;
    margin-top:3rem !important;
    margin-bottom:.95rem !important;
}

h3,
[data-testid="stMarkdownContainer"] h3 {
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, "Times New Roman", serif !important;
    font-size:clamp(1.3rem, 1.8vw, 1.5rem) !important;
    line-height:1.16 !important;
    margin-top:1.35rem !important;
    margin-bottom:.65rem !important;
}

p, li {
    font-family: "Josefin Sans", "Avenir Next", "Century Gothic", Arial, sans-serif;
    font-size:1.03rem;
    line-height:1.65;
    font-weight:400;
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
    font-weight:400;
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
    font-weight:400;
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
    content:"âˆ’";
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

.lean-daily-major-event {
    display:inline-block;
    margin:-1.55rem 0 1.3rem;
    padding:.4rem .5rem;
    border:1px solid var(--black);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.68rem;
    letter-spacing:.035em;
    text-transform:uppercase;
}

.lean-daily-supporting-event {
    margin:-.8rem 0 1.5rem;
    color:var(--muted);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.63rem;
    letter-spacing:.025em;
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

.stMarkdown p strong,
.stMarkdown li strong,
.stMarkdown blockquote strong,
.timing-story-copy strong,
.chart-motion-summary strong,
.luna-connection strong {
    font-size: inherit !important;
    line-height: inherit !important;
}

.luna-prose {
    max-width:760px;
    margin:0 0 1.35rem;
    font-family:"Josefin Sans","Avenir Next","Century Gothic",Arial,sans-serif;
    font-size:clamp(1rem,1.15vw,1.08rem);
    line-height:1.72;
    font-weight:400;
    letter-spacing:0;
    color:var(--black);
}
.luna-prose strong,
.luna-connection strong,
.timing-story-copy p strong,
.natal-signature-reading p strong {
    font-size:inherit !important;
    line-height:inherit !important;
    font-weight:inherit !important;
}
.luna-connection {
    max-width:760px;
    margin:1.45rem 0 2rem;
    padding-left:1rem;
    border-left:1px solid rgba(17,17,17,.22);
    font-family:"Josefin Sans","Avenir Next","Century Gothic",Arial,sans-serif;
    font-size:1rem;
    line-height:1.72;
    font-weight:400;
}
.timing-story-copy p {
    max-width:760px;
    margin:0 0 1.15rem;
    line-height:1.72;
    font-weight:400;
}
.timing-story {
    padding-bottom:2.7rem;
}
.timing-story h2 {
    margin-bottom:1.15rem;
}

.lean-daily-meaning {
    max-width:680px;
    margin:-1.1rem 0 2rem;
    padding-left:1rem;
    border-left:1px solid var(--black);
    font-size:1rem;
    line-height:1.65;
    color:var(--muted);
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

.lean-monthly-window {
    display:flex;
    align-items:baseline;
    gap:.75rem;
    margin:2rem 0 1.35rem;
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.68rem;
    letter-spacing:.035em;
    text-transform:uppercase;
}

.lean-monthly-window span {
    color:var(--muted);
}

.lean-monthly-window strong {
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

/* Paid personal reports deliberately inherit the Natal Snapshot hierarchy.
   H2 = section, H3 = reading/card title, paragraph = body, natal-evidence = calculation.
   Do not introduce a second report-specific font or weight system here. */
.report-story-reading p {
    max-width:720px;
}

.paid-monthly-longform h3 {
    max-width:820px;
}
.paid-monthly-longform p,
.paid-key-date p {
    max-width:780px;
    margin:.45rem 0 1rem !important;
    font-family:"Josefin Sans","Avenir Next","Century Gothic",Arial,sans-serif !important;
    font-size:1.03rem !important;
    line-height:1.7 !important;
    font-weight:400 !important;
    letter-spacing:0 !important;
}
.paid-key-date {
    padding:1rem 0 1.1rem;
}
.paid-key-date p + p {
    margin-top:-.2rem !important;
}

/* One quiet sans-serif treatment for secondary paid-report rows.
   Activation titles, phase titles, key-date consequences and their body copy
   deliberately share one size and one light weight. Hierarchy comes from the
   Bodoni section heading and mono evidence line, not extra bold text. */
.report-flat-reading h3,
.report-flat-reading p {
    font-family:"Josefin Sans","Avenir Next","Century Gothic",Arial,sans-serif !important;
    font-size:1.02rem !important;
    line-height:1.65 !important;
    font-weight:400 !important;
    letter-spacing:0 !important;
}
.report-flat-reading h3 {
    margin:.28rem 0 .55rem !important;
}
.report-flat-reading p {
    margin:.35rem 0 .7rem !important;
}
.report-flat-reading p strong {
    font-weight:inherit !important;
}

.luna-guidance-line {
    max-width:700px;
    margin:1.15rem 0 0;
    padding-top:.95rem;
    border-top:1px solid var(--line);
}

.luna-guidance-label {
    display:block;
    margin:0 0 .32rem;
    color:var(--muted);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.64rem;
    line-height:1.4;
    letter-spacing:.04em;
    text-transform:uppercase;
    font-weight:500;
}

.luna-guidance-line p {
    margin:0 !important;
    max-width:680px;
    font-family:"Josefin Sans","Avenir Next","Century Gothic",Arial,sans-serif !important;
    font-size:1rem !important;
    line-height:1.6 !important;
    font-weight:400 !important;
}

.luna-move-line {
    border-top-color:var(--black);
}

.natal-signature-meta {
    display:grid;
    grid-template-columns:repeat(2,minmax(0,1fr));
    gap:1rem;
    margin-top:.85rem;
    font-size:.84rem;
    line-height:1.55;
}

.natal-signature-meta-single {
    grid-template-columns:1fr;
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
    max-width:760px;
    margin:0 auto;
    padding:.5rem 0 3.5rem;
}

.weekly-kicker,
.weekly-range,
.weekly-card-meta,
.weekly-evidence,
.weekly-major-event,
.weekly-supporting-event,
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
    display:block;
    margin:.45rem 0 2.65rem;
    padding:0;
    font-size:.68rem;
    color:var(--muted);
}

.weekly-page-title {
    max-width:760px;
    margin:0 0 1.1rem;
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, serif;
    font-size:clamp(3rem,7vw,5.6rem);
    line-height:.92;
    letter-spacing:-.055em;
    font-weight:400;
}

.weekly-section-heading,
.weekly-sign-heading {
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, serif;
    font-weight:400;
    letter-spacing:-.025em;
}

.weekly-section-heading {
    margin:2.3rem 0 1rem;
    font-size:clamp(1.65rem,3.2vw,2.6rem);
    line-height:1.05;
}

.weekly-sign-heading {
    margin:.25rem 0 1rem;
    font-size:clamp(1.25rem,2.4vw,1.9rem);
    line-height:1.1;
}

.weekly-synthesis {
    max-width:760px;
    margin:1.5rem 0 2.8rem;
    padding:0 0 .2rem;
    border:0;
    background:transparent;
}

.weekly-synthesis p {
    max-width:680px;
    margin:0 0 1.1rem;
    font-family:"Josefin Sans", "Avenir Next", "Century Gothic", Arial, sans-serif;
    font-size:clamp(1.08rem, 1.7vw, 1.28rem);
    line-height:1.68;
    font-weight:400;
}

.weekly-synthesis-rule {
    margin:1.7rem 0 1.15rem !important;
    padding-top:1.15rem;
    border-top:1px solid var(--black);
    font-weight:400 !important;
}

.weekly-intro {
    max-width:760px;
    margin:0 0 2.5rem;
    color:var(--muted);
    font-size:1.02rem;
    line-height:1.6;
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

.weekly-major-event {
    margin:1.05rem 0 .35rem;
    padding:.5rem .55rem;
    border:1px solid var(--black);
    font-size:.64rem;
    line-height:1.45;
    font-weight:500;
}

.weekly-supporting-event {
    margin:-.25rem 0 .75rem;
    color:var(--muted);
    font-size:.61rem;
    line-height:1.45;
}

.weekly-card-title {
    min-height:2.3em;
    margin:.2rem 0 1rem;
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, serif;
    font-size:clamp(1.65rem,2.3vw,2.15rem);
    line-height:1.08;
    letter-spacing:-.035em;
    font-weight:400;
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
    font-family:"Bodoni MT", "Bodoni 72", "Bodoni Moda", Didot, Georgia, serif;
    font-size:1.25rem;
    font-weight:400;
    line-height:1.28;
}

.weekly-sign-layer {
    max-width:760px;
    margin:2.4rem 0 2.8rem;
    padding:1.4rem 0 0;
    border-top:1px solid var(--black);
}

.weekly-where-lands {
    max-width:680px;
    margin:.15rem 0 1.5rem;
    color:var(--muted);
    font-family:"IBM Plex Mono", "Courier New", monospace;
    font-size:.67rem;
    line-height:1.65;
    letter-spacing:.025em;
    text-transform:uppercase;
}

.weekly-sign-story {
    max-width:680px;
    margin:0 0 1.1rem;
    font-family:"Josefin Sans", "Avenir Next", "Century Gothic", Arial, sans-serif;
    font-size:clamp(1.08rem, 1.7vw, 1.28rem);
    line-height:1.68;
    font-weight:400;
}

.weekly-studio-controls {
    margin:1rem 0 2rem;
    padding:1.15rem;
    border:1px solid var(--black);
    background:var(--soft);
}

@media print {
    @page {
        size:A4 portrait;
        margin:12mm;
    }

    /* The printed product is the whole rendered report, never the visible viewport. */
    html,
    body,
    #root,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    .main,
    .block-container {
        width:100% !important;
        height:auto !important;
        min-height:0 !important;
        max-height:none !important;
        overflow:visible !important;
        position:static !important;
        contain:none !important;
    }

    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stMain"] > div,
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"],
    [data-testid="column"] {
        height:auto !important;
        max-height:none !important;
        overflow:visible !important;
    }

    .brand-row,
    .top-nav,
    .mobile-nav,
    .solar-year-wave-wrap,
    .weekly-studio-controls,
    .luna-print-control,
    [data-testid="stDownloadButton"],
    [data-testid="stForm"],
    [data-testid="stSelectbox"],
    [data-testid="stDateInput"],
    [data-testid="stTextInput"],
    [data-testid="stTextArea"],
    [data-testid="stNumberInput"],
    [data-testid="stCheckbox"],
    [data-testid="stRadio"],
    [data-testid="stButton"],
    [data-testid="stLinkButton"],
    [data-testid="stCode"],
    .weekly-copy-heading,
    iframe {
        display:none !important;
    }

    .block-container {
        max-width:none !important;
        padding:0 !important;
    }

    h1, h2, h3, h4 {
        break-after:avoid-page;
        page-break-after:avoid;
    }

    p, li, .timing-date-box, .timing-move, .relationship-card {
        orphans:3;
        widows:3;
    }

    .weekly-card,
    .timing-date-box,
    .timing-summary-grid,
    .chart-natal-reference,
    .house-key-item {
        break-inside:avoid;
        page-break-inside:avoid;
    }

    /* Long Monthly/Yearly/Transit prose is allowed to flow across pages. */
    .forecast-copy,
    .timing-shell,
    .timing-story,
    .natal-shell,
    .relationship-card,
    .card {
        height:auto !important;
        max-height:none !important;
        overflow:visible !important;
    }
    /* Print every evidence/house-key expander open, even if the reader left it collapsed. */
    [data-testid="stExpander"] {
        display:block !important;
        visibility:visible !important;
        overflow:visible !important;
        break-inside:auto !important;
        page-break-inside:auto !important;
    }
    [data-testid="stExpander"] details,
    details[data-testid="stExpander"] {
        display:block !important;
        overflow:visible !important;
    }
    [data-testid="stExpander"] details > *:not(summary),
    details[data-testid="stExpander"] > *:not(summary),
    [data-testid="stExpanderDetails"] {
        display:block !important;
        visibility:visible !important;
        height:auto !important;
        max-height:none !important;
        overflow:visible !important;
        opacity:1 !important;
    }
    [data-testid="stExpander"] summary {
        display:block !important;
        cursor:default !important;
        list-style:none !important;
        border-bottom:1px solid var(--line);
        margin-bottom:.35rem;
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
    .weekly-page-title {
        font-size:clamp(3rem,14vw,4.4rem);
    }
    .weekly-intro {
        margin-bottom:2rem;
    }
    .weekly-grid {
        grid-template-columns:1fr;
    }
    .weekly-card-title {
        min-height:0;
        font-size:1.75rem;
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


.timing-product-subtitle{
    margin:-.6rem 0 1rem;
    font-family:"Josefin Sans",sans-serif;
    font-size:clamp(1.15rem,2vw,1.6rem);
    font-weight:500;
    letter-spacing:.025em;
}
.timing-plain-grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:1px;
    background:var(--line);
    border:1px solid var(--line);
    margin:.8rem 0 1rem;
}
.timing-plain-grid > div{background:#fff;padding:.8rem .9rem;}
.timing-plain-grid span,
.timing-phase-grid span{
    display:block;
    font:500 .62rem "IBM Plex Mono",monospace;
    letter-spacing:.07em;
    text-transform:uppercase;
    color:var(--muted);
    margin-bottom:.28rem;
}
.timing-plain-grid strong{font-family:"Josefin Sans",sans-serif;font-size:1rem;line-height:1.35;}
.timing-phase-grid{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:1px;
    background:var(--line);
    border:1px solid var(--line);
    margin:.8rem 0 1rem;
}
.timing-phase-grid > div{background:#fff;padding:.7rem .8rem;}
.timing-phase-grid strong{font-family:"Josefin Sans",sans-serif;font-size:.95rem;}
.timing-confidence{
    display:inline-block;
    padding:.18rem .42rem;
    border:1px solid var(--line);
    font:500 .66rem "IBM Plex Mono",monospace;
    letter-spacing:.05em;
    text-transform:uppercase;
}
.chart-motion-summary{max-width:850px;font-size:1.06rem;line-height:1.55;margin:.3rem 0 1rem;}
.chart-motion-legend{display:flex;flex-wrap:wrap;gap:1rem;margin:.7rem 0 .3rem;}
.chart-motion-key{display:flex;align-items:center;gap:.42rem;font-size:.86rem;}
.chart-motion-swatch{width:.8rem;height:.8rem;border-radius:50%;display:inline-block;}
.chart-motion-swatch.house{background:#d9ddff;}
.chart-motion-swatch.natal{background:#6757c7;}
.chart-motion-swatch.transit{background:#e58a2f;}
@media(max-width:720px){
    .timing-plain-grid,.timing-phase-grid{grid-template-columns:1fr;}
}


.chart-natal-reference{
    display:grid;
    grid-template-columns:repeat(6,minmax(0,1fr));
    gap:1px;
    background:var(--line);
    border:1px solid var(--line);
    margin:.7rem 0 1rem;
}
.chart-natal-reference > div{
    background:#fff;
    padding:.62rem .7rem;
    min-width:0;
}
.chart-natal-reference span{
    display:block;
    font:500 .58rem "IBM Plex Mono",monospace;
    letter-spacing:.065em;
    text-transform:uppercase;
    color:var(--muted);
    margin-bottom:.2rem;
}
.chart-natal-reference strong{
    display:block;
    font-family:"Josefin Sans",sans-serif;
    font-size:.93rem;
    line-height:1.2;
}
.chart-reader-label{
    font:500 .62rem "IBM Plex Mono",monospace;
    letter-spacing:.07em;
    text-transform:uppercase;
    color:var(--muted);
    margin:.85rem 0 .35rem;
}
.chart-active-houses{
    display:flex;
    flex-wrap:wrap;
    gap:.42rem;
    margin:.3rem 0 .8rem;
}
.chart-house-chip{
    border:1px solid var(--line);
    padding:.34rem .5rem;
    background:#fff;
    font-size:.82rem;
    line-height:1.2;
}
.chart-house-chip strong{
    font-family:"IBM Plex Mono",monospace;
    font-size:.72rem;
    margin-right:.28rem;
}
.house-key-grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:0 1rem;
}
.house-key-item{
    display:grid;
    grid-template-columns:1.8rem 1fr;
    gap:.45rem;
    padding:.38rem 0;
    border-bottom:1px solid rgba(0,0,0,.08);
    font-size:.86rem;
}
.house-key-item strong{
    font-family:"IBM Plex Mono",monospace;
}
@media(max-width:900px){
    .chart-natal-reference{grid-template-columns:repeat(3,minmax(0,1fr));}
}
@media(max-width:620px){
    .chart-natal-reference{grid-template-columns:repeat(2,minmax(0,1fr));}
    .house-key-grid{grid-template-columns:1fr;}
}

</style>
        """,
        unsafe_allow_html=True,
    )



def install_complete_report_print_support() -> None:
    """Make browser printing capture the complete rendered Luna report.

    This is deliberately global so Weekly, Monthly, Yearly and Personal
    Transits all use the same print behaviour, including report renderers
    imported from other modules.
    """
    st.html(
        """
<script>
(() => {
  const rootWindow = window;
  const rootDocument = document;

  function allDocuments() {
    const docs = [rootDocument];
    try {
      if (window.parent && window.parent.document && window.parent.document !== rootDocument) {
        docs.push(window.parent.document);
      }
    } catch (e) {}
    return docs;
  }

  function openAllLunaExpandersForPrint() {
    allDocuments().forEach((doc) => {
      const selectors = [
        '[data-testid="stExpander"] details',
        'details[data-testid="stExpander"]',
        '[data-testid="stExpander"]'
      ];
      doc.querySelectorAll(selectors.join(",")).forEach((node) => {
        const details = node.tagName === "DETAILS" ? node : node.querySelector("details");
        if (details && !details.open) {
          details.dataset.lunaPrintOpened = "1";
          details.open = true;
        }
      });

      /* Streamlit can retain collapsed-state styles on descendants. */
      doc.querySelectorAll(
        '[data-testid="stExpanderDetails"], [data-testid="stExpander"] [role="region"]'
      ).forEach((node) => {
        node.dataset.lunaPrintForcedVisible = "1";
        node.style.setProperty("display", "block", "important");
        node.style.setProperty("visibility", "visible", "important");
        node.style.setProperty("height", "auto", "important");
        node.style.setProperty("max-height", "none", "important");
        node.style.setProperty("overflow", "visible", "important");
        node.style.setProperty("opacity", "1", "important");
      });
    });
  }

  function restoreLunaExpandersAfterPrint() {
    allDocuments().forEach((doc) => {
      doc.querySelectorAll('details[data-luna-print-opened="1"]').forEach((details) => {
        details.open = false;
        delete details.dataset.lunaPrintOpened;
      });
      doc.querySelectorAll('[data-luna-print-forced-visible="1"]').forEach((node) => {
        node.style.removeProperty("display");
        node.style.removeProperty("visibility");
        node.style.removeProperty("height");
        node.style.removeProperty("max-height");
        node.style.removeProperty("overflow");
        node.style.removeProperty("opacity");
        delete node.dataset.lunaPrintForcedVisible;
      });
    });
  }

  function installOn(win) {
    try {
      if (win.__lunaCompleteReportPrintInstalled) return;
      win.__lunaCompleteReportPrintInstalled = true;
      win.addEventListener("beforeprint", openAllLunaExpandersForPrint);
      win.addEventListener("afterprint", restoreLunaExpandersAfterPrint);
    } catch (e) {}
  }

  installOn(rootWindow);
  try { installOn(window.parent); } catch (e) {}

  /* Expose one stable function for Luna print buttons in this and imported renderers. */
  try {
    window.parent.__lunaPrintCompleteReport = () => {
      openAllLunaExpandersForPrint();
      setTimeout(() => {
        try { window.parent.print(); }
        catch (e) { window.print(); }
      }, 220);
    };
  } catch (e) {
    window.__lunaPrintCompleteReport = () => {
      openAllLunaExpandersForPrint();
      setTimeout(() => window.print(), 220);
    };
  }
})();
</script>
        """,
        unsafe_allow_javascript=True,
    )


def complete_report_print_button(
    label: str = "Print / Save complete report",
    *,
    key: str = "complete-report",
) -> None:
    """A report-level browser print button that never prints only its iframe."""
    safe_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", key).strip("-") or "complete-report"
    components.html(
        f"""
<div class="luna-print-control" style="margin:8px 0 12px 0;font-family:Arial,sans-serif;">
  <button id="luna-complete-print-{safe_id}" type="button" style="
      min-height:44px;padding:10px 16px;border:1px solid #111;background:#111;color:#fff;
      font-size:13px;letter-spacing:.04em;text-transform:uppercase;cursor:pointer;">
    {escape(label)}
  </button>
  <span id="luna-complete-print-status-{safe_id}" style="margin-left:10px;font-size:12px;color:#666;"></span>
</div>
<script>
(() => {{
  const button = document.getElementById("luna-complete-print-{safe_id}");
  const status = document.getElementById("luna-complete-print-status-{safe_id}");
  button.addEventListener("click", () => {{
    status.textContent = "Preparing complete reportâ€¦";
    try {{
      if (window.parent.__lunaPrintCompleteReport) {{
        window.parent.__lunaPrintCompleteReport();
      }} else {{
        window.parent.print();
      }}
    }} catch (e) {{
      window.print();
    }}
    setTimeout(() => {{ status.textContent = ""; }}, 1200);
  }});
}})();
</script>
        """,
        height=68,
    )

def brand_header() -> None:
    icon_html = ""
    if BRAND_ICON_PATH.is_file():
        encoded_icon = base64.b64encode(BRAND_ICON_PATH.read_bytes()).decode("ascii")
        icon_html = f'<img class="brand-icon" src="data:image/png;base64,{encoded_icon}" alt="Saturn hexagon mark">'
    st.markdown(
        f"""
<div class="brand-row">
  <div class="brand-lockup">
    {icon_html}
    <div class="brand-name">{escape(BRAND_NAME)}</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def top_navigation(current_path: str) -> None:
    path = current_path or ""
    # Monthly now has one stable public destination: /monthly.
    # Legacy campaign/sign-specific routes remain only as redirects.
    if path in {"", "daily-horoscope"}:
        nav_path = ""
    elif path == "monthly" or path == "august-2026-horoscopes" or path.startswith("august-2026-"):
        nav_path = "monthly"
    else:
        nav_path = path

    monthly_path = "monthly"

    # Public navigation is intentionally minimal. Routes used for checkout,
    # fulfilment, previews and administration still exist but stay out of sight.
    items = [
        ("", "Daily Horoscope"),
        ("weekly-view", "Weekly View"),
        ("birthday-card", "Birthday Card"),
        (monthly_path, "This Month"),
        ("reports", "Reports"),
        ("timing-map", "Your Year Ahead"),
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
    if code == "BIRTHDAY":
        price_id = resolve_price_id(
            STRIPE_SECRET_KEY,
            explicit_price_id=STRIPE_BIRTHDAY_PRICE_ID,
        )
        if price_id:
            verify_one_time_price(
                STRIPE_SECRET_KEY,
                price_id,
                expected_unit_amount=240,
                expected_currency="aud",
            )
        return price_id
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
            "Luna could not resolve the Stripe Price ID for this product. Add the "
            "matching STRIPE_MONTHLY_PRICE_ID, STRIPE_YEARLY_PRICE_ID or "
            "STRIPE_BIRTHDAY_PRICE_ID to Streamlit Secrets."
        )
    order = dict(order)
    order["product_code"] = product_code
    session = create_checkout_session(
        STRIPE_SECRET_KEY,
        price_id=price_id,
        order=order,
        public_site_url=PUBLIC_SITE_URL,
        cancel_path=("/birthday-card" if str(product_code).upper() == "BIRTHDAY" else "/reports"),
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


def _render_paid_birthday_card(session: dict, metadata: dict[str, str]) -> None:
    """Rebuild and deliver the exact Birthday Card prepared before checkout."""
    session_id = str(session.get("id") or "")
    recipient_name = str(metadata.get("birthday_name") or "").strip()
    birth_date_text = str(metadata.get("birthday_date") or "").strip()
    timezone_name = str(metadata.get("timezone") or DEFAULT_TIMEZONE)
    time_known = str(metadata.get("birthday_time_known") or "").lower() == "true"
    birth_time_text = str(metadata.get("birthday_time") or "").strip()
    theme = str(metadata.get("birthday_theme") or "painted_blue")
    poem = str(metadata.get("birthday_poem") or "").strip()

    if not recipient_name or not birth_date_text or not poem:
        raise ValueError("The paid Birthday Card is missing required fulfilment details.")

    birth_date_value = date.fromisoformat(birth_date_text)
    birth_time_value = None
    if time_known:
        birth_time_value = datetime.strptime(birth_time_text, "%H:%M").time()

    snapshot = build_natal_snapshot(
        birth_date=birth_date_value,
        birth_time_known=time_known,
        birth_time=birth_time_value,
        timezone_name=timezone_name,
    )
    card = build_birthday_card(
        recipient_name=recipient_name,
        birth_date=birth_date_value,
        snapshot=snapshot,
        poem=poem,
        date_only_calculations=(
            birth_date_luminary_calculations(birth_date_value, timezone_name)
            if not time_known else None
        ),
        theme=theme,
    )
    png_bytes = render_birthday_card_png(card)
    pdf_bytes = render_birthday_card_pdf(card)
    png_name = birthday_card_filename(card, "png")
    pdf_name = birthday_card_filename(card, "pdf")

    st.image(png_bytes, use_container_width=True)
    download_columns = st.columns(2, gap="medium")
    with download_columns[0]:
        st.download_button(
            "Download Instagram Reel/Story PNG",
            data=png_bytes,
            file_name=png_name,
            mime="image/png",
            use_container_width=True,
            key=f"paid-birthday-png-{session_id}",
        )
    with download_columns[1]:
        st.download_button(
            "Download printable PDF",
            data=pdf_bytes,
            file_name=pdf_name,
            mime="application/pdf",
            use_container_width=True,
            key=f"paid-birthday-pdf-{session_id}",
        )
    _email_paid_report(
        session,
        attachment_bytes=pdf_bytes,
        attachment_filename=pdf_name,
    )


def payment_success_page() -> None:
    set_page_metadata(
        "Your Luna Report Is Ready | Luna Convergence",
        "Secure paid-report fulfilment for Luna Convergence.",
        "/payment-success",
    )
    st.markdown('<div class="eyebrow">Payment confirmed</div>', unsafe_allow_html=True)

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

    if product_code == "BIRTHDAY":
        st.markdown("# Your Luna Birthday Card is ready")
        st.markdown(
            f"**For {escape(metadata.get('birthday_name', 'your recipient'))}**  "
            f"  \nOrder reference: `{escape(order_reference)}`"
        )
    else:
        st.markdown("# Your Luna report is ready")
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
        if product_code == "BIRTHDAY":
            _render_paid_birthday_card(session, metadata)
        elif product_code == "MONTHLY":
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
                result["natal_profile"] = natal_profile_value
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
            _render_snapshot_monthly_report(
                narrative,
                result,
                order_reference=order_reference,
            )
        elif product_code in {"YEAR", "YEARLY"}:
            start_date, end_date, period_key = _yearly_period_window(period_code)
            result = period_report(
                sign,
                start_date,
                end_date,
                timezone_name,
                period_key,
                transition_count=9,
                nearest_city=nearest_city,
                main_focus=main_focus,
            )
            if natal_profile_value:
                result["natal_profile"] = natal_profile_value
                result["natal_summary"] = natal_summary_value
                result["natal_precision"] = natal_precision_value
                _prepare_paid_yearly_personal_layer(result)
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
            _render_snapshot_yearly_report(
                result,
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



def _natal_input_fields(
    key_prefix: str,
    *,
    prefill: dict | None = None,
    not_listed_label: str = "Not listed — planetary snapshot only",
) -> dict:
    """Render the canonical Natal Snapshot birth-detail controls for personal products."""
    prefill = dict(
        st.session_state.get("luna_natal_checkout_prefill") or {}
        if prefill is None
        else prefill
    )
    try:
        prefill_date = date.fromisoformat(str(prefill.get("birth_date") or ""))
    except Exception:
        prefill_date = None
    prefill_time_text = str(prefill.get("birth_time") or "12:00")
    try:
        prefill_time = datetime.strptime(prefill_time_text, "%H:%M").time()
    except Exception:
        prefill_time = datetime.strptime("12:00", "%H:%M").time()

    birth_date_value = st.date_input(
        "Birth date",
        value=prefill_date,
        min_value=date(1900, 1, 1),
        max_value=browser_local_date(),
        key=f"{key_prefix}-birth-date",
    )
    time_known_value = st.checkbox(
        "I know my birth time exactly",
        value=bool(prefill.get("time_known", False)),
        key=f"{key_prefix}-time-known",
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
        "not_listed_label": not_listed_label,
    }

    if not time_known_value:
        st.caption(
            "Birth time unknown: Luna uses the reliable planetary geometry and leaves "
            "Ascendant, Midheaven and houses out rather than inventing precision."
        )
        return values

    values["birth_time"] = st.time_input(
        "Birth time",
        value=prefill_time,
        key=f"{key_prefix}-birth-time",
        help=(
            "Normally enter the local clock time at the place of birth. "
            "If your source explicitly gives Universal Time, choose UTC below."
        ),
    )
    basis_options = ["Local time at birthplace", "Universal Time (UTC)"]
    prefill_basis = str(prefill.get("time_basis") or basis_options[0])
    values["time_basis"] = st.selectbox(
        "Time basis",
        basis_options,
        index=basis_options.index(prefill_basis) if prefill_basis in basis_options else 0,
        key=f"{key_prefix}-time-basis",
        help="Most birth certificates use local time. Some astrology records state UT/UTC directly.",
    )

    city_options = sorted(CITY_LOCATIONS) + [
        "Other city — enter manually",
        not_listed_label,
    ]
    prefill_choice = str(prefill.get("city_choice") or "")
    if prefill_choice not in city_options and str(prefill.get("location_name") or "").strip():
        prefill_choice = "Other city — enter manually"
    values["city_choice"] = st.selectbox(
        "Birth city",
        city_options,
        index=city_options.index(prefill_choice) if prefill_choice in city_options else None,
        placeholder="Choose your birth city",
        key=f"{key_prefix}-city",
        help=(
            "Choose Other city if the birthplace is not listed. "
            "Coordinates keep the Ascendant and houses precise."
        ),
    )

    if values["city_choice"] == "Other city — enter manually":
        st.caption(
            "City not listed? Enter it directly. Coordinates keep the Ascendant and houses precise "
            "without sending the birthplace to an external geocoding service."
        )
        manual_cols = st.columns(2, gap="medium")
        with manual_cols[0]:
            location_seed = str(prefill.get("manual_city") or prefill.get("location_name") or "")
            values["manual_city"] = st.text_input(
                "City / town",
                value=location_seed.split(",", 1)[0],
                key=f"{key_prefix}-manual-city",
            )
            values["manual_latitude"] = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=float(prefill.get("latitude") or 0.0),
                step=0.0001,
                format="%.4f",
                key=f"{key_prefix}-manual-lat",
            )
        with manual_cols[1]:
            values["manual_country"] = st.text_input(
                "Country",
                value=str(prefill.get("manual_country") or ""),
                key=f"{key_prefix}-manual-country",
            )
            values["manual_longitude"] = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=float(prefill.get("longitude") or 0.0),
                step=0.0001,
                format="%.4f",
                key=f"{key_prefix}-manual-lon",
            )
        if values["time_basis"] == "Local time at birthplace":
            values["manual_timezone"] = st.text_input(
                "Birth timezone · IANA name",
                value=str(prefill.get("timezone_name") or browser_timezone_name()),
                key=f"{key_prefix}-manual-timezone",
                help="Examples: Pacific/Port_Moresby, Australia/Sydney, Europe/London, America/New_York.",
            )
        else:
            values["manual_timezone"] = "UTC"
            st.caption(
                "Universal Time selected: Luna uses the entered time directly as UTC while retaining "
                "the birth coordinates for Ascendant and houses."
            )
    elif values["city_choice"] == not_listed_label:
        if values["time_basis"] == "Local time at birthplace":
            prefill_tz = str(prefill.get("timezone_name") or DEFAULT_TIMEZONE)
            values["unlisted_timezone"] = st.selectbox(
                "Birth timezone",
                TIMEZONES,
                index=TIMEZONES.index(prefill_tz) if prefill_tz in TIMEZONES else timezone_select_index(),
                key=f"{key_prefix}-unlisted-timezone",
                help=(
                    "This places the planets at the correct moment, but without coordinates "
                    "Luna will not calculate the Ascendant or houses."
                ),
            )
        else:
            values["unlisted_timezone"] = "UTC"

    return values


def _build_natal_from_values(values: dict):
    """Build one canonical Natal Player from the shared Snapshot-style controls."""
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
        prefill_out = {
            "birth_date": birth_date_value.isoformat(),
            "time_known": False,
            "birth_time": "",
            "time_basis": "Local time at birthplace",
            "city_choice": "",
            "location_name": "",
            "timezone_name": "UTC",
            "latitude": None,
            "longitude": None,
            "manual_city": "",
            "manual_country": "",
        }
        return snapshot, "Birth time unknown · angles and houses omitted", prefill_out

    birth_time_value = values.get("birth_time")
    if birth_time_value is None:
        raise ValueError("Enter the exact birth time or untick 'I know my birth time exactly'.")

    city_choice = str(values.get("city_choice") or "")
    not_listed_label = str(values.get("not_listed_label") or "Not listed — planetary snapshot only")
    if not city_choice:
        raise ValueError("Choose the birth city, enter another city, or choose the planetary-only option.")

    latitude = longitude = None
    location_name = None
    time_basis = str(values.get("time_basis") or "Local time at birthplace")
    timezone_name = "UTC"
    manual_city = str(values.get("manual_city") or "").strip()
    manual_country = str(values.get("manual_country") or "").strip()

    if city_choice in CITY_LOCATIONS:
        location = CITY_LOCATIONS[city_choice]
        timezone_name = "UTC" if time_basis == "Universal Time (UTC)" else location.timezone
        latitude = location.latitude
        longitude = location.longitude
        location_name = f"{location.name}, {location.country}"
    elif city_choice == "Other city — enter manually":
        if not manual_city:
            raise ValueError("Enter the birth city or town name.")
        timezone_name = (
            "UTC"
            if time_basis == "Universal Time (UTC)"
            else str(values.get("manual_timezone") or "").strip()
        )
        if time_basis == "Local time at birthplace":
            try:
                ZoneInfo(timezone_name)
            except Exception as exc:
                raise ValueError(
                    "That birth timezone is not recognised. Use an IANA name such as "
                    "Pacific/Port_Moresby or Australia/Sydney."
                ) from exc
        latitude = float(values.get("manual_latitude") or 0.0)
        longitude = float(values.get("manual_longitude") or 0.0)
        location_name = manual_city
        if manual_country:
            location_name += f", {manual_country}"
    elif city_choice == not_listed_label or city_choice.startswith("Not listed"):
        timezone_name = (
            "UTC"
            if time_basis == "Universal Time (UTC)"
            else str(values.get("unlisted_timezone") or DEFAULT_TIMEZONE)
        )
    else:
        raise ValueError("Choose a birth city, use Other city, or choose the planetary-only option.")

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
        precision = (
            "Exact birth time supplied · birthplace coordinates unavailable, "
            "so angles and houses omitted"
        )

    prefill_out = {
        "birth_date": birth_date_value.isoformat(),
        "time_known": True,
        "birth_time": birth_time_value.strftime("%H:%M"),
        "time_basis": time_basis,
        "city_choice": city_choice,
        "location_name": location_name or "",
        "timezone_name": timezone_name,
        "latitude": latitude,
        "longitude": longitude,
        "manual_city": manual_city,
        "manual_country": manual_country,
    }
    return snapshot, precision, prefill_out


def _monthly_natal_checkout_fields(key_context: str) -> dict:
    """Compatibility wrapper: Paid Monthly reuses the canonical Snapshot birth controls."""
    return _natal_input_fields(
        f"{key_context}-monthly-natal",
        not_listed_label="Not listed — planetary snapshot only",
    )


def _build_monthly_checkout_natal(values: dict):
    """Compatibility wrapper around the one canonical Natal Player builder."""
    snapshot, precision, _ = _build_natal_from_values(values)
    return snapshot, precision

def _owner_report_output(order: dict) -> dict:
    """Build the same paid output after session-scoped owner authentication."""
    product_code = str(order.get("product_code") or "").upper()
    period_code = str(order.get("period_code") or "")
    sign = str(order.get("sign") or "")
    timezone_name = str(order.get("timezone") or DEFAULT_TIMEZONE)
    nearest_city = str(order.get("nearest_city") or "")
    main_focus = str(order.get("main_focus") or "General overview")
    personal_question = str(order.get("personal_question") or "")
    order_reference = str(order.get("reference") or "OWNER-PREVIEW")

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
        natal_profile_value = str(order.get("natal_profile") or "")
        if natal_profile_value:
            result["natal_profile"] = natal_profile_value
            result["natal_overlay"] = build_monthly_natal_overlay(natal_profile_value, result)
            result["natal_summary"] = str(order.get("natal_summary") or "")
            result["natal_precision"] = str(order.get("natal_precision") or "")
        pdf_bytes = build_report_pdf(
            result,
            main_focus=main_focus,
            personal_question=personal_question,
            order_reference=order_reference,
        )
        return {
            "product_code": product_code,
            "narrative": narrative,
            "result": result,
            "pdf": pdf_bytes,
            "pdf_name": report_filename(result),
        }

    if product_code in {"YEAR", "YEARLY"}:
        start_date, end_date, period_key = _yearly_period_window(period_code)
        result = period_report(
            sign,
            start_date,
            end_date,
            timezone_name,
            period_key,
            transition_count=9,
            nearest_city=nearest_city,
            main_focus=main_focus,
        )
        if str(order.get("natal_profile") or ""):
            result["natal_profile"] = str(order.get("natal_profile") or "")
            result["natal_summary"] = str(order.get("natal_summary") or "")
            result["natal_precision"] = str(order.get("natal_precision") or "")
            _prepare_paid_yearly_personal_layer(result)
        pdf_bytes = build_report_pdf(
            result,
            main_focus=main_focus,
            personal_question=personal_question,
            order_reference=order_reference,
        )
        return {
            "product_code": product_code,
            "result": result,
            "pdf": pdf_bytes,
            "pdf_name": report_filename(result),
        }

    raise ValueError("Owner access received an unrecognised report type.")


def _render_owner_report(order: dict, key_context: str) -> None:
    output_key = f"owner-report-output::{key_context}::{str(order.get('product_code') or '').lower()}"
    if st.button(
        "Generate owner report — no payment",
        type="primary",
        use_container_width=True,
        key=f"{key_context}-owner-report-generate-{str(order.get('product_code') or '').lower()}",
    ):
        try:
            with st.spinner("Building the complete owner report..."):
                st.session_state[output_key] = _owner_report_output(order)
        except Exception as exc:
            st.error("Luna could not generate the owner report on this run.")
            if EDITOR_PREVIEW_ENABLED:
                st.exception(exc)
            return

    output = st.session_state.get(output_key)
    if not output:
        return

    st.session_state["reports-generated-result-visible"] = True
    st.success("Owner copy generated. No Stripe payment was created.")
    st.download_button(
        "Download owner PDF",
        data=output["pdf"],
        file_name=output["pdf_name"],
        mime="application/pdf",
        use_container_width=True,
        key=f"{key_context}-owner-pdf-{str(order.get('product_code') or '').lower()}",
    )
    if output["product_code"] == "MONTHLY":
        _render_snapshot_monthly_report(
            output["narrative"],
            output["result"],
            order_reference=str(order.get("reference") or "OWNER-PREVIEW"),
        )
    else:
        _render_snapshot_yearly_report(
            output["result"],
            order_reference=str(order.get("reference") or "OWNER-PREVIEW"),
        )

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

    admin_unlocked = _admin_access_panel(f"{key_context}-paid-reports")

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    monthly_tab, yearly_tab = st.tabs(
        [
            f"Personal Monthly — {MONTHLY_PRICE}",
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
        with st.container(border=True):
            st.markdown("### Build your Personal Monthly")
            st.caption("Start with the same natal baseline used by Luna's Snapshot, then add the month you want mapped.")
            natal_values = _monthly_natal_checkout_fields(key_context)
            m1, m2 = st.columns(2)
            with m1:
                delivery_email = st.text_input(
                    "Delivery email",
                    key=f"{key_context}-monthly-email",
                    placeholder="name@example.com",
                )
            with m2:
                month_label = st.selectbox(
                    "Report month",
                    month_labels,
                    index=month_labels.index(chosen_default_month),
                    key=f"{key_context}-monthly-period",
                )

            m3, m4 = st.columns(2)
            with m3:
                timezone_name = st.selectbox(
                    "Timezone",
                    TIMEZONES,
                    index=timezone_select_index(),
                    key=f"{key_context}-monthly-timezone",
                )
            with m4:
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
            if admin_unlocked:
                st.caption(
                    "Owner access: generate the complete report here without Stripe. "
                    "Raw birth details remain in this app session."
                )
            else:
                st.caption(
                    "Instant delivery: after Stripe confirms payment, your report opens immediately and Luna emails your private return link. "
                    "Raw birth details are used to calculate the natal chart in this session; Stripe receives only the derived natal geometry needed for fulfilment."
                )
            submitted = st.button(
                (
                    "Prepare owner monthly report"
                    if admin_unlocked
                    else f"Prepare monthly checkout — {MONTHLY_PRICE}"
                ),
                type="primary",
                use_container_width=True,
                key=f"{key_context}-monthly-submit",
            )

        state_key = f"prepared-order::{key_context}::monthly"
        if submitted:
            st.session_state.pop(
                f"owner-report-output::{key_context}-monthly::monthly",
                None,
            )
            if not admin_unlocked and not valid_email(delivery_email):
                st.error("Enter a valid delivery email before continuing to payment.")
                st.session_state.pop(state_key, None)
            else:
                try:
                    natal_snapshot, natal_precision = _build_monthly_checkout_natal(natal_values)
                except Exception as exc:
                    st.error(f"Natal details need attention: {exc}")
                    st.session_state.pop(state_key, None)
                else:
                    sign = _monthly_sun_sign_from_snapshot(natal_snapshot)
                    if sign not in SIGNS:
                        st.error("Luna could not calculate your Sun sign from the natal details supplied.")
                        st.session_state.pop(state_key, None)
                        return
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
                        "report_name": "Personal Monthly Report",
                        "email": delivery_email.strip() or "Not required for owner access",
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
                    if admin_unlocked:
                        order["admin_preview"] = True
                        st.session_state[state_key] = order
                        track_event(
                            "monthly_owner_report_prepared",
                            {
                                "zodiac_sign": sign,
                                "report_period": period_code,
                                "timezone": timezone_name,
                                "main_focus": main_focus,
                                "natal_time_known": bool(natal_values.get("time_known")),
                            },
                        )
                    else:
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
        if order and bool(order.get("admin_preview")) != admin_unlocked:
            st.session_state.pop(state_key, None)
            order = None
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
            if admin_unlocked:
                _render_owner_report(order, f"{key_context}-monthly")
            else:
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
        default_start_date = browser_local_date()

        with st.container(border=True):
            st.markdown("### Build your Year Ahead")
            st.caption(
                "Start with the same natal baseline used by Luna's Snapshot, then add the rolling 12-month window you want mapped."
            )
            yearly_natal_values = _natal_input_fields(
                f"{key_context}-yearly-natal",
                not_listed_label="Not listed — planetary snapshot only",
            )

            y1, y2 = st.columns(2)
            with y1:
                delivery_email = st.text_input(
                    "Delivery email",
                    key=f"{key_context}-yearly-email",
                    placeholder="name@example.com",
                )
            with y2:
                selected_start_date = st.date_input(
                    "Start date",
                    value=default_start_date,
                    key=f"{key_context}-yearly-period",
                    help="Your Year Ahead runs for 12 rolling months from this date.",
                )
                selected_end_date = _rolling_year_end(selected_start_date)
                st.caption(
                    f"12-month window: {_yearly_period_label(selected_start_date, selected_end_date)}"
                )

            y3, y4 = st.columns(2)
            with y3:
                timezone_name = st.selectbox(
                    "Timezone",
                    TIMEZONES,
                    index=timezone_select_index(),
                    key=f"{key_context}-yearly-timezone",
                )
            with y4:
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
                help="This guides which themes receive extra emphasis in the personalised report.",
            )
            personal_question = st.text_area(
                "Optional decision or transition",
                key=f"{key_context}-yearly-question",
                max_chars=QUESTION_MAX_CHARS,
                placeholder="Is there a major decision, relationship or transition to consider?",
                help=f"Optional. Maximum {QUESTION_MAX_CHARS} characters. It is stored with your secure Stripe checkout so Luna can personalise the report after payment.",
            )
            if admin_unlocked:
                st.caption(
                    "Owner access: generate the complete year-ahead report here without Stripe. "
                    "Raw birth details remain in this app session."
                )
            else:
                st.caption(
                    "Instant delivery: after Stripe confirms payment, your report opens immediately and Luna emails your private return link. "
                    "Raw birth details are used to calculate the natal chart in this session; Stripe receives only the derived natal geometry needed for fulfilment."
                )
            submitted = st.button(
                (
                    "Prepare owner year-ahead report"
                    if admin_unlocked
                    else f"Prepare year-ahead checkout — {YEARLY_PRICE}"
                ),
                type="primary",
                use_container_width=True,
                key=f"{key_context}-yearly-submit",
            )

        state_key = f"prepared-order::{key_context}::yearly"
        if submitted:
            st.session_state.pop(
                f"owner-report-output::{key_context}-yearly::year",
                None,
            )
            if not admin_unlocked and not valid_email(delivery_email):
                st.error("Enter a valid delivery email before continuing to payment.")
                st.session_state.pop(state_key, None)
            else:
                try:
                    natal_snapshot, natal_precision, natal_prefill = _build_natal_from_values(yearly_natal_values)
                except Exception as exc:
                    st.error(f"Natal details need attention: {exc}")
                    st.session_state.pop(state_key, None)
                else:
                    sign = _monthly_sun_sign_from_snapshot(natal_snapshot)
                    if sign not in SIGNS:
                        st.error("Luna could not calculate your Sun sign from the natal details supplied.")
                        st.session_state.pop(state_key, None)
                    else:
                        st.session_state["luna_natal_checkout_prefill"] = natal_prefill
                        selected_end_date = _rolling_year_end(selected_start_date)
                        period_code = _yearly_period_code(selected_start_date, selected_end_date)
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
                            "email": delivery_email.strip() or "Not required for owner access",
                            "sign": sign,
                            "period": _yearly_period_label(selected_start_date, selected_end_date),
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
                        if admin_unlocked:
                            order["admin_preview"] = True
                            st.session_state[state_key] = order
                            track_event(
                                "yearly_owner_report_prepared",
                                {
                                    "zodiac_sign": sign,
                                    "report_period": period_code,
                                    "timezone": timezone_name,
                                    "main_focus": main_focus,
                                    "natal_time_known": bool(yearly_natal_values.get("time_known")),
                                },
                            )
                        else:
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
                                        "natal_time_known": bool(yearly_natal_values.get("time_known")),
                                    },
                                )

        order = st.session_state.get(state_key)
        if order and bool(order.get("admin_preview")) != admin_unlocked:
            st.session_state.pop(state_key, None)
            order = None
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
            if admin_unlocked:
                _render_owner_report(order, f"{key_context}-yearly")
            else:
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


def daily_controls(prefix: str = "daily") -> tuple[str | None, date, str, str]:
    first_row = st.columns(2, gap="medium")
    with first_row[0]:
        sign = st.selectbox(
            "What is your Sun sign (star sign)?",
            SIGNS,
            index=None,
            placeholder="Select your star sign",
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


def _daily_guided_facts(narrative, sign: str, reading_date: date, timezone_name: str) -> dict:
    evidence = narrative.evidence
    return {
        "sign": sign,
        "date": reading_date.isoformat(),
        "timezone": timezone_name,
        "major_event": getattr(narrative, "major_event_label", ""),
        "supporting_events": list(getattr(narrative, "supporting_events", ()) or ()),
        "active_planets": list(evidence.active_planets),
        "aspect": evidence.aspect_label,
        "aspect_type": evidence.aspect_type,
        "orb": evidence.orb,
        "configured_orb": evidence.configured_orb,
        "phase": evidence.phase,
        "activated_houses": list(evidence.activated_houses),
        "house_meanings": list(evidence.house_meanings),
        "strongest_influence": evidence.strongest_influence,
        "active_window": evidence.active_window,
        "strength_score": evidence.strength_score,
        "confidence": evidence.confidence_label,
        "convergence": evidence.convergence_label,
        "convergence_score": evidence.convergence_score,
        "convergence_window": evidence.convergence_window,
        "technical_aspects": list(narrative.technical_aspects),
        "sun_house": narrative.sun_house,
        "moon_house": narrative.moon_house,
    }


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
    # A URL without a dated week can remain stale forever. Require the date lock.
    if not LUNA_YOUTUBE_FEATURED_VIDEO_WEEK_START:
        return
    try:
        configured_week = date.fromisoformat(LUNA_YOUTUBE_FEATURED_VIDEO_WEEK_START)
    except ValueError:
        return
    if configured_week != monday_for(browser_local_date()):
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


@st.cache_data(show_spinner=False, ttl=3600)
def _cached_plain_packet(product: str, period: date, sign: str, timezone_name: str) -> dict:
    return build_plain_packet(product, period, sign, timezone_name)


def _render_free_plain(product: str, period: date, sign: str) -> None:
    packet = _cached_plain_packet(product, period, sign, DEFAULT_TIMEZONE)
    reading = load_plain_reading(packet)
    st.markdown(plain_reading_html(packet, reading), unsafe_allow_html=True)


def _render_lean_daily(path: str) -> None:
    set_page_metadata(
        "Daily Horoscope | Luna Convergence",
        "Read today's Luna Convergence horoscope for your zodiac sign, with one clear interpretation and one practical move.",
        path,
    )

    _snapshot_page_heading(
        "Free · Daily Horoscope",
        "Your Daily Horoscope",
        "Choose your Sun sign. Luna keeps the reading simple: the calculated sky, one connected interpretation and one practical move.",
    )

    saved_sign = st.session_state.get("landing-daily-sign-v3195") or _query_daily_sign()
    saved_index = SIGNS.index(saved_sign) if saved_sign in SIGNS else None
    st.markdown(
        '<div class="daily-sign-picker-label">What is your Sun sign (star sign)?</div>',
        unsafe_allow_html=True,
    )
    sign = st.selectbox(
        "What is your Sun sign (star sign)?",
        SIGNS,
        index=saved_index,
        placeholder="Choose your star sign",
        key="landing-daily-sign-v3195",
        label_visibility="collapsed",
        persist_state="session",
    )

    # A neutral first state is deliberate: Luna must never imply any sign for a
    # new visitor. It also turns the first sign choice into a real
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

    reading_date = datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date()
    _render_free_plain("daily", reading_date, sign)
    st.markdown(f'<a class="lean-monthly-link" href="/monthly">See your {escape(month_name[reading_date.month])} forecast →</a>',
                unsafe_allow_html=True)
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
    full = clean in {"", "daily-horoscope", "monthly", "solar-year"}
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
    set_page_metadata("Weekly Astrology | Luna Convergence",
                      "Your sign's week ahead, calculated and interpreted by Luna.", "/weekly-view")
    _snapshot_page_heading(
        "Free · Week Ahead",
        "Your Week Ahead",
        "Choose your Sun sign and week. Luna keeps the same editorial hierarchy used across the site, then adds the calculated weekly story and your move.",
    )
    today = datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date()
    sign = st.selectbox("What is your Sun sign (star sign)?", SIGNS, index=None,
                        placeholder="Choose your star sign", key="weekly-sign-v331")
    current_monday = default_week_start(today)
    week_options = _weekly_choice_options(today)
    monday = st.selectbox("Choose week", week_options,
                          index=week_options.index(current_monday),
                          format_func=lambda value: _weekly_choice_label(value, current_monday),
                          key="weekly-view-week-v332")
    if sign is None:
        return
    _render_free_plain("weekly", monday, sign)
    complete_report_print_button("Print / Save complete Week Ahead", key="weekly-view-complete-report")
    st.markdown('<a class="lean-monthly-link" href="/daily-horoscope">Open your Daily Horoscope →</a>',
                unsafe_allow_html=True)



def weekly_studio_page() -> None:
    """Production tools reuse scheduled prose; opening this page never calls the LLM."""
    from studio_readings import studio_packet, COLLECTIVE, publishing_copy, sign_card, deduplicated_caption
    set_page_metadata("Weekly Video Studio | Luna Convergence",
                      "Weekly video, twelve sign cards and seven daily clips.", "/weekly-studio")
    st.markdown("## Weekly video studio")
    today = datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date()
    options = _weekly_choice_options(today)
    current = default_week_start(today)
    monday = st.selectbox("Choose week", options, index=options.index(current),
                          format_func=lambda value: _weekly_choice_label(value, current))
    st.caption(f"{_weekly_choice_label(monday, current)} · {DEFAULT_TIMEZONE}")
    with st.expander("How to use this studio", expanded=True):
        st.markdown("""1. Use **One changing sky** for the weekly master voiceover, approximately 45 seconds.
2. Copy the **1080 × 1920 sign cards** into your portrait design.
3. Use **Monday–Sunday clips** for seven separate short videos, approximately 8–12 seconds each.
4. Copy the publishing text into YouTube and Instagram. Check the spoken timing before export.
5. Download the scripts below. Keep the full sign reading on the website.

One shared sky. Twelve sign readings. Export artwork at **1080 × 1920 (9:16)**.""")
    master_packet = studio_packet("studio_weekly", monday, COLLECTIVE, DEFAULT_TIMEZONE)
    master = load_plain_reading(master_packet)
    st.markdown("### Weekly overview · One changing sky")
    if master:
        st.markdown(plain_reading_html(master_packet, master), unsafe_allow_html=True)
        with st.expander("Copy the master voiceover"):
            st.code(master["voice_body"], language=None, wrap_lines=True)
        st.download_button("Download 45-second master script", master["voice_body"],
                           file_name=f"luna-master-{monday}.txt", mime="text/plain")
    with st.expander("The shared sky · Seven calculated days"):
        for row in master_packet["events"]:
            st.markdown(f"**{row['date']} · {row['event']}**")
            for support in row["supporting_events"]:
                st.write(f"Also active · {support}")
    st.markdown("### This Week in Seven Sky Cards")
    st.caption("Monday–Sunday · protected event first, otherwise the strongest calculated event.")

    for card in master_packet.get("sky_cards", []):
        day = date.fromisoformat(card["date"])
        st.markdown(f"**{day:%A · %d %B}**")

        if card.get("has_event"):
            st.markdown(f"**{card['event']}**")

            timing_parts = []
            if card.get("timing"):
                timing_parts.append(str(card["timing"]))
            if card.get("timezone_label"):
                timing_parts.append(str(card["timezone_label"]))
            elif card.get("timezone"):
                timing_parts.append(str(card["timezone"]))

            if timing_parts:
                st.caption(" · ".join(timing_parts))

            if card.get("technical"):
                st.caption(str(card["technical"]))
        else:
            st.caption("No separate card event selected from the calculated sky for this day.")

    from luna_reading_style import meaning_html
    st.markdown("### Day-by-day astrological breakdown")
    meanings = []
    for offset in range(7):
        day = monday + timedelta(days=offset)
        packet = studio_packet("studio_meaning", day, COLLECTIVE, DEFAULT_TIMEZONE)
        reading = load_plain_reading(packet)
        if reading:
            event = packet["events"][0]["event"]
            st.markdown(meaning_html(day, event, reading["voice_body"]), unsafe_allow_html=True)
            meanings.append(f"{day:%A %d %B} · {event}\n\n{reading['voice_body']}")
    if meanings:
        st.download_button("Download meaning & energy", "\n\n".join(meanings),
                           file_name=f"luna-meaning-energy-{monday}.txt", mime="text/plain")
    st.markdown("### Week Ahead publishing copy")
    if master:
        package = publishing_copy(monday, master["voice_body"], PUBLIC_SITE_URL)
        for label, text in package.items():
            st.markdown(f"**{label}**")
            st.code(text, language=None, wrap_lines=True)
        st.download_button("Download Week Ahead publishing copy",
                           "\n\n".join(f"{k}\n{v}" for k, v in package.items()),
                           file_name=f"luna-publishing-{monday}.txt", mime="text/plain")
    st.markdown("### 12 sign cards · 1080 × 1920")
    cards, narrations = [], []
    for sign in SIGNS:
        packet = _cached_plain_packet("weekly", monday, sign, DEFAULT_TIMEZONE)
        reading = load_plain_reading(packet)
        with st.expander(sign):
            st.markdown(plain_reading_html(packet, reading), unsafe_allow_html=True)
            if reading:
                card = sign_card(sign, monday, reading["voice_body"])
                st.markdown("**1080 × 1920 social card copy**")
                st.code(card, language=None, wrap_lines=True)
                st.markdown("**Full website / sign narration**")
                st.code(reading["voice_body"], language=None, wrap_lines=True)
                cards.append(card)
                narrations.append(f"{sign}\n\n{reading['voice_body']}")
    if cards:
        st.download_button(f"Download sign cards copy ({len(cards)}/12)", "\n\n---\n\n".join(cards),
                           file_name=f"luna-sign-cards-{monday}.txt", mime="text/plain")
        st.download_button("Download Weekly narration", "\n\n---\n\n".join(narrations),
                           file_name=f"luna-weekly-{monday}.txt", mime="text/plain")
    st.markdown("### Monday–Sunday clips")
    scripts = []
    for offset in range(7):
        day = monday + timedelta(days=offset)
        packet = studio_packet("studio_daily", day, COLLECTIVE, DEFAULT_TIMEZONE)
        reading = load_plain_reading(packet)
        with st.expander(day.strftime("%A · %d %B")):
            for line in packet["calculation_header"]:
                st.write(line)
            if reading:
                text = reading["voice_body"]
                st.markdown("**8–12 second script**")
                st.code(text, language=None, wrap_lines=True)
                st.markdown("**Title**")
                st.code(f"{day:%A %d %B} | {packet['events'][0]['event']}", language=None)
                st.markdown("**Caption**")
                caption = deduplicated_caption(
                    text,
                    packet["events"][0]["event"],
                    day.strftime("%A %d %B"),
                    f"{PUBLIC_SITE_URL}/weekly-view",
                )
                st.code(f"{caption}\n\n#astrology #horoscope #LunaConvergence", language=None)
                scripts.append(f"{day:%A %d %B}\n\n{text}")
    if scripts:
        st.download_button(f"Download daily scripts ({len(scripts)}/7)", "\n\n---\n\n".join(scripts),
                           file_name=f"luna-daily-clips-{monday}.txt", mime="text/plain")
    if WEEKLY_BACKGROUND_PATH.exists():
        st.download_button("Download 1080 × 1920 background", WEEKLY_BACKGROUND_PATH.read_bytes(),
                           file_name=WEEKLY_BACKGROUND_PATH.name, mime="image/png")
    st.caption(f"Saved for this week: {len(cards)}/12 sign scripts · {len(scripts)}/7 daily clips · "
               f"{1 if master else 0}/1 weekly master · {len(meanings)}/7 meaning & energy readings.")


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
    """
    Build a broad prior-month candidate pool.
    Reader-facing selection happens later per event, using both house emphasis
    and the actual transition-family tokens for that event.
    """
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
            past_house_set = set(past_sig["houses"])

            shared_houses = [h for h in current_sig["houses"] if h in past_house_set]
            current_only = [h for h in current_sig["houses"] if h not in past_house_set]
            past_only = [h for h in past_sig["houses"] if h not in set(current_sig["houses"])]

            matches.append({
                "year": past_year,
                "score": score,
                "shared_houses": shared_houses,
                "current_only": current_only,
                "past_only": past_only,
                "past_first_title": (past_sig["titles"][0] if past_sig["titles"] else ""),
                "past_titles": past_sig["titles"],
                "past_tokens": sorted(past_sig["tokens"]),
                "past_houses": past_sig["houses"],
            })
        except Exception:
            continue

    matches.sort(key=lambda item: item["score"], reverse=True)

    # Keep a wider candidate pool than the old top-three month match.
    # The event-specific selector below decides what is actually worth showing.
    return matches[:10]


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

    st.markdown("## Have you been somewhere like this before?")
    st.markdown(
        "Luna looks backward for earlier months with a similar **sky structure**. "
        "The point is not to say that the same event repeats. It is to give the present month a reference point."
    )

    for index, item in enumerate(matches[:2], start=1):
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

    if len(matches) > 2:
        with st.expander(f"Show {len(matches) - 2} more earlier echoes"):
            for item in matches[2:]:
                past_year = int(item["year"])
                past_label = f"{month_name[int(month)]} {past_year}"
                shared = item.get("shared_houses") or []
                shared_text = " and ".join(_house_short(h) for h in shared[:2]) if shared else "a similar sky structure"
                st.markdown(f"**{past_label}** · {shared_text}")

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
    """One recurrence. One memory prompt. No methodology narration."""
    earlier = _previous_transit_echo_date(story)
    if earlier is None:
        return

    st.markdown("### Have you been here before?")
    question = finalize_customer_prose(_timing_recurrence_question(story), product="timing")
    area = _timing_story_life_area(story)

    if birth_date_value and earlier >= birth_date_value:
        age = earlier.year - birth_date_value.year - (
            (earlier.month, earlier.day) < (birth_date_value.month, birth_date_value.day)
        )
        _render_luna_prose(
            f"Think back to {_timing_date_label(earlier)}. You were about {age}. "
            f"{question} The event can differ. The pressure can rhyme.",
            product="timing",
        )
    else:
        _render_luna_prose(
            f"Look further back: around {_timing_date_label(earlier)} a similar pressure was active. "
            f"{life_scene(area, f'older-{earlier.year}', count=1)} "
            "You may not have lived through it. Use the date as context, not biography.",
            product="timing",
        )

    polarity = str(getattr(story, "polarity", "") or "").lower()
    if "opportun" in polarity:
        close = "Use the room that exists now. Do not wait for the old event to repeat."
    elif "pressure" in polarity:
        close = "Name what you tolerated then. Set the clearer limit now."
    else:
        close = "Keep the old pattern as context. Make the present decision from present facts."
    _render_luna_prose(close, product="timing")

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
                "What is your Sun sign (star sign)?",
                SIGNS,
                index=None,
                placeholder="Select your star sign",
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
        if sign not in SIGNS:
            st.error("Select your star sign before generating the preview.")
            return
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
            history_context.get("sign") or result.get("sign"),
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
    if not _admin_access_panel("monthly-preview"):
        st.error("Owner authentication is required for the monthly preview.")
        return
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
    local_today = browser_local_date()
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
                "What is your Sun sign (star sign)?",
                SIGNS,
                index=None,
                placeholder="Select your star sign",
                key="report-generator-sign",
            )
        with first_row[1]:
            forecast_year = st.number_input(
                "Year",
                min_value=1950,
                max_value=2100,
                value=(
                    local_today.year
                    if report_type == "Monthly"
                    else default_year(local_today)
                ),
                step=1,
                key=f"report-generator-year-{report_type}",
            )
        with first_row[2]:
            selected_month = st.selectbox(
                "Month",
                list(range(1, 13)),
                index=local_today.month - 1,
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
        if sign not in SIGNS:
            st.error("Select your star sign before generating the report.")
            return
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
        f"{result.get('sign')} / {result.get('label')} â€¢ "
        f"{BUILD_LABEL} â€¢ Checkout bypassed"
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
            default=[],
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

    if not _admin_access_panel("editorial-preview"):
        st.error("Owner authentication is required for editorial preview.")
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
        "Personal Monthly and Year-Ahead Astrology Reports | Luna Convergence",
        "Order a natal-based Personal Monthly report or a detailed year-ahead forecast delivered electronically.",
        "/reports",
    )

    # Private monthly preview fallback. This deliberately uses the existing
    # /reports route so the preview remains reachable even if a deployment
    # has trouble recognising the separate /monthly-preview route.
    preview_mode = str(st.query_params.get("preview", "")).strip().lower()
    if preview_mode in {"monthly", "month", "monthly-report"}:
        if not _admin_access_panel("reports-monthly-preview"):
            st.error("Owner authentication is required for this preview.")
            return
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

    st.markdown('<section class="natal-shell">', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Paid reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="editorial-title">Choose the depth<br>you need</div>', unsafe_allow_html=True)
    st.markdown(
        "<div class=\"natal-intro\">Start with the same natal foundation used by Luna's Snapshot. "
        "Personal Monthly maps that player against one month; Year Ahead maps the same player across a rolling 12 months. "
        "Your Sun sign is calculated from the birth details rather than selected separately.</div>",
        unsafe_allow_html=True,
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
    st.session_state["reports-generated-result-visible"] = False
    report_cta(context="reports")

    if st.session_state.get("reports-generated-result-visible"):
        st.markdown('</section>', unsafe_allow_html=True)
        return

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("## How ordering works")
    c1, c2, c3 = st.columns(3, gap="large")
    steps = [
        (
            "1. Choose",
            "Select the report, birth details, period, timezone, main focus, optional question and delivery email.",
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

    with st.expander("Legacy payment recovery"):
        st.markdown(
            "Use this only for an earlier payment made before the natal-based checkout. "
            "It prepares an email with the legacy fulfilment details and your payment reference."
        )
        with st.form("report-order-details"):
            product = st.selectbox(
                "Report ordered",
                [
                    f"Personal Monthly Report — {MONTHLY_PRICE}",
                    f"Year-Ahead Strategic Report — {YEARLY_PRICE}",
                ],
            )
            c1, c2 = st.columns(2)
            with c1:
                customer_name = st.text_input("Name")
                customer_email = st.text_input("Email")
                sign = st.selectbox(
                    "What is your Sun sign (star sign)?",
                    SIGNS,
                    index=None,
                    placeholder="Select your star sign",
                )
            with c2:
                requested_period = st.text_input(
                    "Requested month or calendar year",
                    placeholder=(
                        f"Example: {month_name[browser_local_date().month]} "
                        f"{browser_local_date().year} or {default_year(browser_local_date())}"
                    ),
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
            if sign not in SIGNS:
                st.error("Select your star sign.")
            elif not customer_name or not valid_email(customer_email) or not requested_period:
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

    st.markdown('</section>', unsafe_allow_html=True)

def houses_page() -> None:
    set_page_metadata(
        "The 12 Astrological Houses | Luna Convergence",
        "Learn what the twelve astrological houses mean for identity, income, communication, home, work, relationships, career and long-term goals.",
        "/house-guide",
    )
    _snapshot_page_heading(
        "Free · House Guide",
        "The twelve areas of life",
        "Planets describe what force is operating. Signs describe how it behaves. Houses describe where in life it operates.",
    )
    sign = st.selectbox(
        "Show the whole-sign house map for",
        SIGNS,
        index=None,
        placeholder="Select your star sign",
        key="house-guide-sign",
    )
    if sign in SIGNS:
        st.markdown(house_reference_matrix(sign))
    else:
        st.info("Select your star sign to display its whole-sign house map.")

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
    report_cta(context="house-guide", prefill_sign=sign if sign in SIGNS else None)


def sample_page() -> None:
    set_page_metadata(
        "Live Astrology Report Sample | Luna Convergence",
        "Choose a star sign and period to see a live Luna Convergence report sample generated from the selected sky.",
        "/sample-report",
    )
    st.markdown('<div class="eyebrow">Live example</div>', unsafe_allow_html=True)
    st.markdown('<div class="editorial-title">Choose the sky.<br>Then read the sample.</div>', unsafe_allow_html=True)
    st.markdown(
        "Luna no longer uses a frozen sign or year as its example. Choose the star sign, "
        "month or year, timezone and focus below; the report controls and calculations use those selections."
    )
    render_report_generator_workspace()


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
7. The narrative layer translates the calculated signals into reader-facing interpretation without changing the astronomical facts.
        """
    )

    st.markdown("## Explainable Astrology")
    st.markdown(f"**{LUNA_TRUST_STATEMENT}**")
    st.markdown(
        "Luna Convergence presents the human story first, then answers three questions: "
        "**what changed, where it lands, and what evidence supports it**. "
        "The readable interpretation stays on top; positions, houses, aspects and orbs remain available underneath."
    )
    st.caption(LUNA_TRUST_DISCLOSURE)

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


@lru_cache(maxsize=384)
def monthly_seo_data(sign: str, year: int, month: int) -> dict:
    """Build cached metadata data for the exact sign and period requested."""
    year = int(year)
    month = int(month)
    result = period_report(
        sign,
        date(year, month, 1),
        month_end(year, month),
        DEFAULT_TIMEZONE,
        f"{month_name[month]} {year}",
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
    """Single public Monthly hub at /monthly.

    Luna starts with the reader's Sun sign (star sign) as whole-sign House 1.
    Birth details then add age/history and natal precision without replacing
    that first solar reference frame.
    """
    monthly_sign_page()



def _legacy_monthly_redirect(sign: str | None = None) -> None:
    """Send old Monthly URLs to the single /monthly route."""
    if sign in SIGNS:
        st.session_state["monthly-hub-sign-v1"] = sign
        st.session_state["landing-daily-sign-v3195"] = sign

    try:
        st.switch_page(MONTHLY_INDEX_REF)
    except Exception:
        components.html(
            """
            <script>
              try { window.parent.location.replace("/monthly"); }
              catch (e) { window.location.replace("/monthly"); }
            </script>
            """,
            height=0,
        )
        st.info("Monthly has moved to /monthly.")


def legacy_monthly_index_page() -> None:
    _legacy_monthly_redirect()


def _free_monthly_profile() -> tuple[str | None, str, str, int, int, bool]:
    """Sign-only public Monthly. Natal inputs belong to the paid report."""
    local_today = datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date()
    saved_sign = (
        st.session_state.get("free-monthly-sign-v338")
        or st.session_state.get("landing-daily-sign-v3195")
        or _query_daily_sign()
    )
    saved_index = SIGNS.index(saved_sign) if saved_sign in SIGNS else None
    _snapshot_page_heading(
        "Free · Monthly by Sign",
        "This Month",
        "Choose your Sun sign for the shared monthly story, key dates and whole-sign life areas. Birth details are only requested for the paid Personal Monthly report.",
    )
    sign = st.selectbox(
        "What is your Sun sign (star sign)?",
        SIGNS,
        index=saved_index,
        placeholder="Choose your star sign",
        key="free-monthly-sign-v338",
        label_visibility="collapsed",
        persist_state="session",
    )
    if sign is None:
        st.markdown(
            '<div class="lean-daily-empty">Choose your star sign to open this month\'s forecast.</div>',
            unsafe_allow_html=True,
        )
        return None, DEFAULT_TIMEZONE, "", local_today.year, local_today.month, False

    # One canonical timezone lets all visitors share the same pre-generated
    # document. Dated entries are labelled as Sydney dates; no birth precision
    # or visitor-specific timing is implied in the free product.
    timezone_name = DEFAULT_TIMEZONE
    st.session_state["landing-daily-sign-v3195"] = sign
    st.session_state["free-monthly-sign"] = sign
    _remember_daily_sign_in_url(sign)
    st.caption("Current month · dates use Australia/Sydney")
    return (
        sign,
        timezone_name,
        representative_city_name(timezone_name),
        local_today.year,
        local_today.month,
        True,
    )


def _monthly_sun_sign_from_snapshot(snapshot) -> str | None:
    """Return the calculated tropical Sun sign from the natal snapshot."""
    for item in list(getattr(snapshot, "positions", None) or []):
        if str(getattr(item, "planet", "") or "").strip().lower() == "sun":
            value = str(getattr(item, "sign", "") or "").strip()
            if value in SIGNS:
                return value
    return None


def _date_only_sun_sign_is_ambiguous(birth_date_value: date) -> bool:
    """True when the tropical Sun changes sign during the UTC date.

    Date-only natal snapshots use noon UTC.  This guard prevents Luna from
    presenting that neutral calculation point as certainty on an ingress date.
    """
    early = positions_for_date(birth_date_value, "UTC", 0)["Sun"].sign
    late = positions_for_date(birth_date_value, "UTC", 23)["Sun"].sign
    return early != late


_MONTHLY_READER_LABELS = {
    1: "identity + direction",
    2: "money + self-worth",
    3: "communication + movement",
    4: "home + family",
    5: "love + creativity",
    6: "work + routine",
    7: "relationships + agreements",
    8: "shared money + obligations",
    9: "travel + expansion",
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
    """Show earlier echoes as human memory prompts. Keep the matching method in evidence."""
    try:
        matches = _monthly_history_matches(sign, int(year), int(month), timezone_name)
    except Exception:
        return
    if not matches:
        return

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">PAST CONTEXT</div>', unsafe_allow_html=True)
    st.markdown("## Have you been somewhere like this before?")
    _render_luna_prose(
        "Use these dates as memory prompts. Do not force the old event to match the present one.",
        product="monthly",
    )

    for index, item in enumerate(matches[:3], start=1):
        past_year = int(item["year"])
        past_label = f"{month_name[int(month)]} {past_year}"
        shared = list(item.get("shared_houses") or [])
        now_only = list(item.get("current_only") or [])

        if shared:
            area = HOUSE_NAMES.get(int(shared[0]), "general")
        elif now_only:
            area = HOUSE_NAMES.get(int(now_only[0]), "general")
        else:
            area = "general"

        st.markdown("---")
        st.markdown(f"### {escape(past_label)}")

        if birth_date_value:
            ref_date = date(past_year, int(month), 15)
            if ref_date >= birth_date_value:
                age = ref_date.year - birth_date_value.year - (
                    (ref_date.month, ref_date.day) < (birth_date_value.month, birth_date_value.day)
                )
                _render_luna_prose(
                    f"Think back. You were about {age}. "
                    f"{life_scene(area, f'month-history-{past_year}-{index}', count=1)} "
                    "What changed after the first excitement, problem or invitation became real?",
                    product="monthly",
                )
                if now_only:
                    _render_luna_prose(
                        "Do not reuse the old answer automatically. A new condition is in the room now.",
                        product="monthly",
                    )
                continue

        _render_luna_prose(
            f"Use this as longer-cycle context, not biography. "
            f"{life_scene(area, f'month-history-{past_year}-{index}', count=1)}",
            product="monthly",
        )

    with _luna_evidence_panel("Why Luna sees these dates"):
        st.markdown(
            "Luna compares the month's dominant whole-sign houses and major planetary transitions "
            "with earlier months for the same sign. The similarity score stays in the evidence layer."
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



def _monthly_plain(value):
    from dataclasses import asdict, is_dataclass
    if is_dataclass(value):
        return {k: _monthly_plain(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _monthly_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_monthly_plain(v) for v in value]
    if hasattr(value, "__dict__") and not isinstance(value, (str, bytes, int, float, bool, date, datetime)):
        try:
            return {str(k): _monthly_plain(v) for k, v in vars(value).items() if not str(k).startswith("_")}
        except Exception:
            pass
    return value


def _monthly_walk(value, path=()):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _monthly_walk(child, path + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _monthly_walk(child, path + (str(index),))


def _monthly_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value).strip()


def _monthly_first(mapping: dict, keys: tuple[str, ...], default=""):
    lower = {str(k).lower(): v for k, v in mapping.items()}
    for key in keys:
        if key.lower() in lower:
            value = lower[key.lower()]
            if value not in (None, "", [], {}):
                return value
    return default


def _monthly_parse_day(value, fallback=99) -> int:
    if isinstance(value, (date, datetime)):
        return int(value.day)
    text = _monthly_text(value)
    for pattern in (
        r"\b(\d{1,2})\s*[-–]\s*\d{1,2}\s+[A-Za-z]+",
        r"\b(\d{1,2})\s+[A-Za-z]{3,9}\b",
        r"\b\d{4}[-/]\d{1,2}[-/](\d{1,2})\b",
    ):
        match = re.search(pattern, text, re.I)
        if match:
            return int(match.group(1))
    return fallback


def _monthly_event_from_dict(item: dict) -> dict | None:
    if not isinstance(item, dict):
        return None
    date_value = _monthly_first(item, ("date", "date_label", "display_date", "exact_date", "day", "window", "date_range", "period"))
    transit = _monthly_first(item, ("transit", "event", "event_label", "sky_event", "aspect", "technical_label", "subtitle"))
    title = _monthly_first(item, ("headline", "title", "story_title", "hook", "name"))
    body = _monthly_first(item, ("body", "story", "interpretation", "copy", "summary", "description", "text"))
    move = _monthly_first(item, ("move", "action", "luna_move", "best_move", "recommendation"))
    influence = _monthly_first(item, ("influence", "influence_window", "active", "active_window", "range"))

    joined = " ".join(_monthly_text(v) for v in (date_value, transit, title, body, move, influence))
    dateish = bool(re.search(
        r"\b(?:\d{1,2}\s*(?:[-–]\s*\d{1,2})?\s+[A-Za-z]{3,9}|"
        r"[A-Za-z]{3,9}\s+\d{1,2}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b",
        joined,
        re.I,
    ))
    eventish = bool(re.search(r"\b(?:eclipse|trine|sextile|square|opposition|conjunct|retrograde|station|ingress)\b", joined, re.I))
    if not (dateish or eventish):
        return None
    if not title and not body:
        return None

    return {
        "day": _monthly_parse_day(date_value or transit or title or joined),
        "date": _monthly_text(date_value),
        "transit": _monthly_text(transit),
        "title": _monthly_text(title),
        "body": _monthly_text(body),
        "move": _monthly_text(move),
        "influence": _monthly_text(influence),
    }


def _monthly_collect_structured_events(narrative, result) -> list[dict]:
    roots = [_monthly_plain(narrative), _monthly_plain(result)]
    candidates = []

    for root in roots:
        for path, value in _monthly_walk(root):
            if isinstance(value, list) and value and all(isinstance(x, dict) for x in value):
                events = [e for e in (_monthly_event_from_dict(x) for x in value) if e]
                if events:
                    unique_days = len({e["day"] for e in events if e["day"] < 99})
                    richness = sum(bool(e["title"]) + bool(e["body"]) + bool(e["move"]) for e in events)
                    path_text = " ".join(path).lower()
                    path_bonus = 12 if any(w in path_text for w in ("brief", "timeline", "unfold", "signal", "key", "date")) else 0
                    candidates.append((unique_days * 5 + richness + path_bonus, events))

    events = max(candidates, key=lambda pair: pair[0])[1] if candidates else []

    existing = {(e["day"], e["title"].lower()) for e in events}
    for root in roots:
        for path, value in _monthly_walk(root):
            if not isinstance(value, dict):
                continue
            event = _monthly_event_from_dict(value)
            if not event:
                continue
            path_text = " ".join(path).lower()
            joined = " ".join(_monthly_text(v) for v in value.values())
            supporting = any(w in path_text for w in ("signal", "relationship", "read", "window"))
            sig = (event["day"], event["title"].lower())
            if supporting and sig not in existing:
                events.append(event)
                existing.add(sig)

    if not events:
        for raw in (result.get("major_transitions") or []):
            if isinstance(raw, dict):
                event = _monthly_event_from_dict(raw)
                if event:
                    events.append(event)

    deduped, seen = [], set()
    for event in sorted(events, key=lambda e: (e["day"], e["title"] or e["transit"])):
        key = (event["day"], (event["title"] or event["transit"]).lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    return deduped[:7]


def _monthly_main_headline(narrative, sign: str) -> str:
    for key in ("hook_headline", "headline", "title", "monthly_headline"):
        value = getattr(narrative, key, None)
        if value:
            return str(value).strip()
    label = str(getattr(narrative, "label", "") or "This month").strip()
    return f"{sign} · {label}"


def _monthly_intro_copy(narrative, result) -> list[str]:
    plain = _monthly_plain(narrative)
    preferred = []
    if isinstance(plain, dict):
        for key in ("overview", "opening", "lead", "summary", "theme_copy", "story"):
            value = plain.get(key)
            if isinstance(value, str) and len(value.strip()) > 45:
                preferred.append(value.strip())
            elif isinstance(value, list):
                preferred.extend(str(x).strip() for x in value if isinstance(x, str) and len(x.strip()) > 45)
    if preferred:
        return preferred[:2]
    theme = result.get("concentration_theme")
    return [theme.strip()] if isinstance(theme, str) and theme.strip() else []


def _monthly_history_for_event(sign: str, year: int, month: int, timezone_name: str, birth_date_value: date | None, event_index: int) -> None:
    try:
        matches = _monthly_history_matches(sign, year, month, timezone_name)
    except Exception:
        return
    if not matches:
        return

    item = matches[min(event_index, len(matches) - 1)]
    past_year = int(item["year"])
    shared = item.get("shared_houses") or []
    now_only = item.get("current_only") or []
    then_only = item.get("past_only") or []

    st.markdown("---")
    st.markdown("#### Have you been here before?")

    age_text = ""
    if birth_date_value:
        ref_date = date(past_year, month, 15)
        if ref_date >= birth_date_value:
            age = ref_date.year - birth_date_value.year - (
                (ref_date.month, ref_date.day) < (birth_date_value.month, birth_date_value.day)
            )
            age_text = f" You were about **{age}**."

    st.markdown(f"Think back to **{month_name[month]} {past_year}**.{age_text}")

    if shared:
        shared_text = " + ".join(_monthly_reader_house_label(h) for h in shared[:2])
        st.markdown(f"**What rhymes:** **{shared_text}** was also unusually active.")
    if now_only and then_only:
        st.markdown(
            f"**What is different now:** {_monthly_reader_house_label(now_only[0])} is more active; "
            f"the earlier month leaned more toward {_monthly_reader_house_label(then_only[0])}."
        )
    elif now_only:
        st.markdown(f"**What is different now:** this month adds {_monthly_reader_house_label(now_only[0])}.")
    elif then_only:
        st.markdown(f"**What is different now:** the earlier month carried more {_monthly_reader_house_label(then_only[0])}.")

    st.caption("What do you remember changing then? The earlier month is context, not a replay.")


def _render_monthly_native_like_transits(narrative, result, *, sign: str, timezone_name: str, birth_date_value: date | None) -> None:
    forecast_year, forecast_month, forecast_label = monthly_period_from_result(result, narrative)
    st.markdown('<div class="eyebrow">MONTHLY · PERSONAL CONTEXT</div>', unsafe_allow_html=True)
    st.markdown(f"# {_monthly_main_headline(narrative, sign)}")

    for paragraph in _monthly_intro_copy(narrative, result):
        st.markdown(paragraph)

    events = _monthly_collect_structured_events(narrative, result)
    if events:
        st.markdown(f"## How {month_name[forecast_month]} unfolds")
        for index, event in enumerate(events):
            date_label = event["date"]
            if not date_label or len(date_label) > 40:
                month_abbr = month_name[forecast_month][:3].upper()
                date_label = f"{event['day']:02d} {month_abbr}" if event["day"] < 99 else month_name[forecast_month].upper()

            st.markdown("---")
            meta_parts = [p for p in (event["transit"], f"Influence: {event['influence']}" if event["influence"] else "") if p]
            st.markdown(
                f'<div class="timing-meta">{escape(date_label.upper())}'
                + (f" · {escape(' · '.join(meta_parts))}" if meta_parts else "")
                + "</div>",
                unsafe_allow_html=True,
            )

            st.markdown(f"### {event['title'] or event['transit'] or 'The month changes here'}")
            if event["body"]:
                for paragraph in re.split(r"\n\s*\n", event["body"]):
                    if paragraph.strip():
                        st.markdown(paragraph.strip())
            if event["move"]:
                st.markdown(
                    f'<div class="timing-move"><span class="timing-move-label">ACTION</span>'
                    f'<p>{escape(event["move"])}</p></div>',
                    unsafe_allow_html=True,
                )

            if index < 3:
                _monthly_history_for_event(sign, forecast_year, forecast_month, timezone_name, birth_date_value, index)
    else:
        st.info("Luna found the month, but this pipeline version did not expose the dated briefing structure.")

    _render_monthly_past_echo_strip(
        sign,
        forecast_year,
        forecast_month,
        timezone_name,
        birth_date_value,
    )

    st.markdown("## Where it lands")
    dominant = result.get("dominant_houses") or []
    for item in dominant[:3]:
        if not isinstance(item, dict):
            continue
        house = item.get("house")
        label = _monthly_reader_house_label(house).upper()
        st.markdown(f"**{label}**")
        try:
            st.markdown(HOUSE_STRATEGY[int(house)]["action"])
        except Exception:
            pass

    final_move = ""
    plain = _monthly_plain(narrative)
    if isinstance(plain, dict):
        for key in ("best_move", "final_move", "action", "your_move"):
            value = plain.get(key)
            if isinstance(value, str) and value.strip():
                final_move = value.strip()
                break
    if not final_move and events:
        final_move = next((e["move"] for e in reversed(events) if e["move"]), "")
    if final_move:
        st.markdown("## Action")
        st.markdown(final_move)

    with _luna_evidence_panel():
        st.markdown(
            f"Luna combines the calculated {month_name[forecast_month]} sky, whole-sign house emphasis, major transitions "
            "and the closest earlier monthly precedents. Historical echoes sit beside the current event they help explain."
        )



def _render_monthly_full_meat_unified(
    narrative,
    result,
    *,
    sign: str,
    timezone_name: str,
    birth_date_value: date | None,
) -> None:
    """
    Restore the complete production Monthly content.
    Only presentation is unified so it reads closer to Personal Transits.
    No event extraction, no DOM reordering, no narrative loss.
    """
    st.markdown(
        """
        <style>
        /* Keep the full production report, but remove the 'magazine insert' look. */
        .relationship-card{
            background:#fff !important;
            border-left:0 !important;
            border-right:0 !important;
            border-top:1px solid rgba(0,0,0,.55) !important;
            border-bottom:1px solid rgba(0,0,0,.55) !important;
            padding:1.15rem 0 !important;
            margin:1.35rem 0 !important;
        }
        .relationship-card h3{
            font-size:clamp(1.45rem,2.6vw,2rem) !important;
            line-height:1.08 !important;
            margin:.35rem 0 .55rem !important;
        }
        .relationship-card p{
            font-size:1rem !important;
            line-height:1.58 !important;
        }

        /* Dated monthly entries should feel like the transit stories: same rhythm, less card-ness. */
        .monthly-briefing,
        .briefing-row,
        .timeline-row,
        .monthly-timeline-row{
            background:#fff !important;
            box-shadow:none !important;
            border-radius:0 !important;
        }

        /* Consequence summaries should not compete with the main story. */
        .area-strip{
            margin:1.6rem 0 !important;
        }
        .area-note{
            padding:1rem !important;
        }
        .area-note h3,
        .area-note h4{
            font-size:1.15rem !important;
            line-height:1.12 !important;
        }

        /* Final move should read like the transit page's action block. */
        .best-move{
            grid-template-columns:8rem 1fr !important;
            margin:1.7rem 0 !important;
            padding:1rem 0 !important;
        }
        .best-move-copy{
            font-size:1.3rem !important;
            line-height:1.22 !important;
        }

        /* Reduce visual competition between section headings. */
        .forecast-copy h2,
        .forecast-copy h3{
            margin-top:1.4rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Full, original production renderer: this is where the "meat" lives.
    render_production_monthly_report(
        narrative,
        result,
        show_print=True,
    )

    # Historical context remains available immediately after the complete reading
    # until it can be attached to individual dated events inside the pipeline itself.
    forecast_year, forecast_month, _ = monthly_period_from_result(result, narrative)
    _render_monthly_history(
        sign,
        forecast_year,
        forecast_month,
        timezone_name,
        birth_date_value=birth_date_value,
    )



def _monthly_deep_strings(value, path=(), depth=0, max_depth=7):
    """Yield every meaningful string under a Monthly object with its structural path."""
    if depth > max_depth:
        return
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _monthly_deep_strings(child, path + (str(key),), depth + 1, max_depth)
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _monthly_deep_strings(child, path + (str(index),), depth + 1, max_depth)
    elif isinstance(value, (date, datetime)):
        yield path, value.isoformat()
    elif isinstance(value, str):
        cleaned = re.sub(r"\s+", " ", value).strip()
        if cleaned:
            yield path, cleaned


def _monthly_container_strings(value, max_depth=5):
    """Collect strings beneath a candidate container while keeping path hints."""
    return list(_monthly_deep_strings(value, max_depth=max_depth))


def _monthly_date_info(text: str):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    patterns = (
        (r"\b(\d{1,2})\s*[-–]\s*(\d{1,2})\s+([A-Za-z]{3,9})(?:\s+\d{4})?\b", "range"),
        (r"\b(\d{1,2})\s+([A-Za-z]{3,9})(?:\s+\d{4})?\b", "single"),
        (r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", "iso"),
    )
    for pattern, kind in patterns:
        m = re.search(pattern, text, re.I)
        if not m:
            continue
        if kind == "range":
            day = int(m.group(1))
            month_token = m.group(3)[:3].upper()
            label = f"{int(m.group(1)):02d}–{int(m.group(2)):02d} {month_token}"
        elif kind == "single":
            day = int(m.group(1))
            label = f"{day:02d} {m.group(2)[:3].upper()}"
        else:
            day = int(m.group(3))
            month_token = month_name[int(m.group(2))][:3].upper()
            label = f"{day:02d} {month_token}"
        return day, label
    return 99, ""


def _monthly_is_technical(text: str) -> bool:
    return bool(re.search(
        r"\b(?:trine|sextile|square|opposition|conjunct|conjunction|eclipse|retrograde|station|ingress|orb|sun|moon|mercury|venus|mars|jupiter|saturn|uranus|neptune|pluto)\b",
        text,
        re.I,
    ))



def _monthly_internal_text(text: str) -> bool:
    low = str(text or "").lower()
    internal_phrases = (
        "promoted through the connected event cluster",
        "connected event cluster",
        "convergence graph",
        "moves into house ",
        "scenario slug",
        "editorial_status",
        "travel_legal_disruption",
        "opportunity_convergence",
        "hierarchy background",
        "house weight",
        "direct event support",
        "relevance ",
        "relevance:",
        "/100",
        "debug",
        "internal",
    )
    return any(phrase in low for phrase in internal_phrases)


def _monthly_extract_houses(value) -> set[int]:
    houses: set[int] = set()

    def visit(node):
        if isinstance(node, dict):
            for key, child in node.items():
                low = str(key).lower()
                if low in {"house", "natal_house"}:
                    try:
                        number = int(child)
                        if 1 <= number <= 12:
                            houses.add(number)
                    except Exception:
                        pass
                elif low in {"houses", "house_numbers", "activated_houses"} and isinstance(child, (list, tuple, set)):
                    for item in child:
                        try:
                            number = int(item)
                            if 1 <= number <= 12:
                                houses.add(number)
                        except Exception:
                            pass
                visit(child)
        elif isinstance(node, (list, tuple)):
            for child in node:
                visit(child)

    visit(value)
    return houses


def _monthly_editorial_path_score(path_text: str) -> int:
    low = path_text.lower()
    score = 0
    for word in ("brief", "timeline", "unfold", "narrative", "editorial", "relationship", "signal", "story"):
        if word in low:
            score += 18
    for word in ("convergence", "graph", "technical", "evidence", "cluster", "scenario", "major_transition", "major_transitions"):
        if word in low:
            score -= 24
    return score


def _monthly_title_score(text: str, path_text: str = "") -> int:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if not value:
        return -999
    score = _monthly_editorial_path_score(path_text)
    if 18 <= len(value) <= 110:
        score += 30
    if "_" in value:
        score -= 80
    if _monthly_internal_text(value):
        score -= 120
    if _monthly_is_technical(value):
        score -= 12
    if re.match(r"^(the|a|an|chemistry|home|work|money|travel|relationships|visibility|shared|your)\b", value, re.I):
        score += 8
    return score


def _monthly_body_score(text: str, path_text: str = "") -> int:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) < 45:
        return -999
    score = _monthly_editorial_path_score(path_text)
    if 80 <= len(value) <= 520:
        score += 35
    elif len(value) > 900:
        score -= 25
    if "." in value:
        score += 10
    if _monthly_internal_text(value):
        score -= 150
    if value.lower().startswith("ask the question this development makes unavoidable"):
        score -= 220
    if value.lower().startswith("moves into house"):
        score -= 120
    if "astrology is a symbolic" in value.lower():
        score -= 150
    if "daily, weekly and monthly are free" in value.lower():
        score -= 150
    return score


def _monthly_move_score(text: str, path_text: str = "") -> int:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) < 8:
        return -999
    score = _monthly_editorial_path_score(path_text)
    if 25 <= len(value) <= 240:
        score += 30
    if _monthly_internal_text(value):
        score -= 150
    if value.lower().startswith(("ask the question this development", "promoted through")):
        score -= 80
    return score


def _monthly_candidate_from_container(value, path=()):
    strings = _monthly_container_strings(value, max_depth=5)
    if not strings:
        return None

    combined = " ".join(text for _, text in strings)
    day, date_label = _monthly_date_info(combined)
    if day == 99 and not _monthly_is_technical(combined):
        return None

    if sum(len(t) for _, t in strings) > 5200:
        return None

    titles, bodies, moves, technical, influence = [], [], [], [], []

    for pth, txt in strings:
        path_text = " ".join(pth)
        low_path = path_text.lower()
        low = txt.lower()

        if "influence" in low_path or low.startswith("influence:"):
            influence.append((txt, path_text))
            continue

        if low.startswith(("luna's move:", "lunaâ€™s move:")):
            moves.append((re.sub(r"^luna['â€™]s move:\s*", "", txt, flags=re.I), path_text))
            continue

        if any(k in low_path for k in ("move", "action", "recommend", "best_move", "luna_move")):
            moves.append((txt, path_text))
            continue

        if _monthly_is_technical(txt) and len(txt) <= 190:
            technical.append((txt, path_text))

        if any(k in low_path for k in ("headline", "title", "hook", "story_title", "name")):
            titles.append((txt, path_text))
            continue

        if 16 <= len(txt) <= 150 and txt.count(".") == 0 and not _monthly_is_technical(txt):
            titles.append((txt, path_text))
        elif len(txt) >= 45:
            bodies.append((txt, path_text))

    best_title = max(titles, key=lambda p: _monthly_title_score(p[0], p[1]), default=("", ""))
    best_move = max(moves, key=lambda p: _monthly_move_score(p[0], p[1]), default=("", ""))
    ranked_bodies = sorted(bodies, key=lambda p: _monthly_body_score(p[0], p[1]), reverse=True)

    body = []
    seen = set()
    for txt, pth in ranked_bodies:
        if _monthly_body_score(txt, pth) < 0:
            continue
        key = txt.lower()
        if key in seen or txt == best_title[0]:
            continue
        seen.add(key)
        body.append(txt)
        if len(body) >= 3:
            break

    transit = ""
    if technical:
        ranked_technical = sorted(
            technical,
            key=lambda p: (
                1 if re.search(r"\b(?:trine|sextile|square|opposition|eclipse)\b", p[0], re.I) else 0,
                -len(p[0]),
            ),
            reverse=True,
        )
        transit = ranked_technical[0][0]

    influence_text = influence[0][0] if influence else ""
    path_text = " / ".join(path)
    candidate_score = (
        _monthly_title_score(best_title[0], best_title[1])
        + sum(max(0, _monthly_body_score(txt, pth)) for txt, pth in ranked_bodies[:2])
        + max(0, _monthly_move_score(best_move[0], best_move[1]))
        + _monthly_editorial_path_score(path_text)
    )

    return {
        "day": day,
        "date": date_label,
        "transit": transit,
        "title": best_title[0],
        "body": body,
        "move": best_move[0],
        "influence": influence_text,
        "score": candidate_score,
        "path": path_text,
        "combined": combined,
        "houses": _monthly_extract_houses(value),
    }



def _monthly_clean_reader_paragraph(event_key: str, paragraph: str) -> str:
    """Remove template/debug/technical leakage and return ordinary human prose."""
    value = re.sub(r"\s+", " ", str(paragraph or "")).strip()
    if not value:
        return ""

    low = value.lower()
    if low.startswith("ask the question this development makes unavoidable"):
        return ""
    if low.startswith("a new opening enters the month and begins to shift the available future"):
        return ""
    if _monthly_internal_text(value):
        return ""

    if event_key == "solar_eclipse":
        aspect_hits = re.findall(
            r"\b(?:Mercury|Venus|Mars|Jupiter|Saturn|Uranus|Neptune|Pluto)\s+"
            r"(?:trine|sextile|square|opposition|conjunct(?:ion)?)\s+"
            r"(?:Mercury|Venus|Mars|Jupiter|Saturn|Uranus|Neptune|Pluto)\b",
            value,
            flags=re.I,
        )
        if len(aspect_hits) >= 2:
            return "Use the support. Keep the choice concrete."

    return finalize_customer_prose(value, product="monthly")

def _monthly_clean_context_paragraph(paragraph: str) -> str:
    """Turn concentration-theme prose into a command plus an ordinary-life scene."""
    value = re.sub(r"\s+", " ", str(paragraph or "")).strip()
    if not value or _monthly_internal_text(value):
        return ""

    low = value.lower()
    if (
        ("sun (" in low and "mercury (" in low and "jupiter (" in low)
        or "one connected story" in low
        or "reacting to each transit separately" in low
    ):
        area = "travel, publishing, law, education and foreign markets"
        return (
            f"{imperative_for(area, 'monthly-context')} "
            f"{life_scene(area, 'monthly-context', count=2)}"
        )

    return finalize_customer_prose(value, product="monthly")

def _monthly_clean_final_step(step: str) -> str:
    """Translate engine-ish action language into ordinary reader language."""
    value = re.sub(r"\s+", " ", str(step or "")).strip()
    replacements = (
        ("Complete essential travel and outward-facing decisions before late-month demands intensify.",
         "Complete essential travel, study or external commitments before late-month demands intensify."),
        ("Renegotiate unavoidable commitments as competing demands build.",
         "Renegotiate commitments that cannot simply be removed."),
        ("Let optional exposure pass when late-month demands reach home, family and private life.",
         "Let optional commitments wait when home, family or private life needs more from you."),
        ("before the pressure peak where possible", "before late-month demands intensify"),
        ("as the difficult cluster builds", "as competing demands build"),
        ("when late pressure spreads into", "when late-month demands reach"),
        ("wider opportunity", "opportunity"),
        ("wider horizons", "external plans"),
        ("optional exposure", "optional commitments"),
        ("private foundations", "private life"),
    )
    for old, new in replacements:
        value = value.replace(old, new)
    return finalize_customer_prose(value, product="monthly")



# ---------------------------------------------------------------------------
# LUNA VOICE V2
# Calculations stay locked. This layer only chooses among reviewed, meaning-
# equivalent editorial realisations, then audits the finished report for echoes.
# ---------------------------------------------------------------------------
_LUNA_VOICE_V2_BANK = {
    "sun_saturn": {
        "title": [
            {"text": "The first opening becomes practical", "metaphor": "build", "shape": "declaration", "verbs": ["becomes"]},
            {"text": "Possibility gets its first real foothold", "metaphor": "ground", "shape": "declaration", "verbs": ["gets"]},
            {"text": "What looked promising starts to become buildable", "metaphor": "build", "shape": "reversal", "verbs": ["starts", "become"]},
            {"text": "The idea finally has something solid to stand on", "metaphor": "ground", "shape": "image", "verbs": ["has", "stand"]},
        ],
        "lead": [
            {"text": "Something that lived in the maybe column now has enough structure to test.", "metaphor": "proof", "shape": "contrast", "verbs": ["lived", "test"]},
            {"text": "The promise is still early, but there is finally something concrete to measure.", "metaphor": "measure", "shape": "contrast", "verbs": ["measure"]},
            {"text": "Take the possibility seriously once it has enough weight to affect the calendar.", "metaphor": "weight", "shape": "declaration", "verbs": ["acquires", "taken"]},
        ],
        "move": [
            {"text": "Secure the part that makes the opportunity real; keep the rest reversible.", "metaphor": "structure", "shape": "instruction", "verbs": ["secure", "keep"]},
            {"text": "Build only the piece you can already support. Leave the rest flexible.", "metaphor": "build", "shape": "instruction", "verbs": ["build", "leave"]},
            {"text": "Make the useful part concrete before you commit to the whole idea.", "metaphor": "proof", "shape": "instruction", "verbs": ["make", "commit"]},
        ],
        "watch": [
            {"text": "Early support is useful evidence, not permission to overextend.", "metaphor": "evidence", "shape": "contrast", "verbs": ["overextend"]},
            {"text": "One workable piece does not mean the entire plan is ready.", "metaphor": "build", "shape": "warning", "verbs": ["mean"]},
            {"text": "Do not confuse the first green light with a blank cheque.", "metaphor": "signal", "shape": "image", "verbs": ["confuse"]},
        ],
    },
    "solar_eclipse": {
        "title": [
            {"text": "The opportunity now asks for commitment", "metaphor": "terms", "shape": "declaration", "verbs": ["asks"]},
            {"text": "The maybe has reached its deadline", "metaphor": "deadline", "shape": "image", "verbs": ["reached"]},
            {"text": "A promising route needs a real answer", "metaphor": "road", "shape": "declaration", "verbs": ["needs"]},
            {"text": "Interest turns into a decision", "metaphor": "turn", "shape": "compression", "verbs": ["turns"]},
        ],
        "lead": [
            {"text": "What looked exciting from a distance is close enough now to rearrange the calendar.", "metaphor": "distance", "shape": "reversal", "verbs": ["looked", "rearrange"]},
            {"text": "The invitation is real enough to require terms, timing and a practical yes or no.", "metaphor": "terms", "shape": "declaration", "verbs": ["require"]},
            {"text": "Put a price, date or obligation beside the possibility. It is no longer theoretical.", "metaphor": "cost", "shape": "contrast", "verbs": ["stops", "starts", "costing"]},
        ],
        "move": [
            {"text": "Identify the one practical condition that determines whether you can say yes.", "metaphor": "terms", "shape": "instruction", "verbs": ["identify", "determines"]},
            {"text": "Name the condition that has to be true before this deserves your commitment.", "metaphor": "threshold", "shape": "instruction", "verbs": ["name", "deserves"]},
            {"text": "Put one non-negotiable term on the table before enthusiasm makes the choice for you.", "metaphor": "table", "shape": "instruction", "verbs": ["put", "makes"]},
        ],
        "watch": [
            {"text": "A promising route still needs practical terms before it deserves a yes.", "metaphor": "road", "shape": "warning", "verbs": ["needs", "deserves"]},
            {"text": "Excitement can make an unfinished plan look more complete than it is.", "metaphor": "completion", "shape": "warning", "verbs": ["make", "look"]},
            {"text": "Do not let urgency negotiate the terms on your behalf.", "metaphor": "terms", "shape": "instruction", "verbs": ["negotiate"]},
        ],
    },
    "venus_jupiter": {
        "title": [
            {"text": "Chemistry gets a chance to prove itself", "metaphor": "proof", "shape": "declaration", "verbs": ["gets", "prove"]},
            {"text": "The spark is easy. Staying power is the question", "metaphor": "spark", "shape": "contrast", "verbs": ["staying"]},
            {"text": "Something enjoyable may have more life in it", "metaphor": "life", "shape": "possibility", "verbs": ["have"]},
            {"text": "Pleasure opens the conversation; consistency answers it", "metaphor": "conversation", "shape": "contrast", "verbs": ["opens", "answers"]},
        ],
        "lead": [
            {"text": "The easy part is attraction. The interesting part is what remains after ordinary life walks back into the room.", "metaphor": "room", "shape": "contrast", "verbs": ["remains", "walks"]},
            {"text": "A lighter moment can be more than relief if it keeps its shape once responsibility returns.", "metaphor": "shape", "shape": "condition", "verbs": ["keeps", "returns"]},
            {"text": "Enjoyment matters here, but follow-through tells you whether it has somewhere to go.", "metaphor": "direction", "shape": "contrast", "verbs": ["matters", "tells"]},
        ],
        "move": [
            {"text": "Enjoy what opens. Judge it by what remains when timing and responsibility return.", "metaphor": "opening", "shape": "instruction", "verbs": ["enjoy", "judge", "remains"]},
            {"text": "Let yourself enjoy the warmth, then watch what survives the return of ordinary demands.", "metaphor": "weather", "shape": "instruction", "verbs": ["enjoy", "watch", "survives"]},
            {"text": "Take the pleasure seriously without asking it to promise more than it has shown.", "metaphor": "promise", "shape": "instruction", "verbs": ["take", "asking", "shown"]},
        ],
        "watch": [
            {"text": "Attraction and ease are encouraging; durability still has to be demonstrated.", "metaphor": "durability", "shape": "contrast", "verbs": ["demonstrated"]},
            {"text": "A beautiful moment is not automatically a durable arrangement.", "metaphor": "durability", "shape": "warning", "verbs": ["is"]},
            {"text": "Do not ask chemistry to do the work of consistency.", "metaphor": "work", "shape": "instruction", "verbs": ["ask", "do"]},
        ],
    },
    "lunar_eclipse": {
        "title": [
            {"text": "The decision reaches home", "metaphor": "home", "shape": "declaration", "verbs": ["reaches"]},
            {"text": "The outside plan arrives at your front door", "metaphor": "door", "shape": "image", "verbs": ["arrives"]},
            {"text": "Expansion meets the life that has to carry it", "metaphor": "weight", "shape": "collision", "verbs": ["meets", "carry"]},
            {"text": "What changes outside now has an inside cost", "metaphor": "cost", "shape": "contrast", "verbs": ["changes", "has"]},
        ],
        "lead": [
            {"text": "By late month, the decision stops being abstract because home and private life have to absorb its consequences.", "metaphor": "weight", "shape": "cause", "verbs": ["stops", "absorb"]},
            {"text": "The plan can no longer be judged only by where it might take you; it also has to fit the life waiting at home.", "metaphor": "fit", "shape": "contrast", "verbs": ["judged", "fit"]},
            {"text": "Check what your private life can actually hold. Make capacity part of the answer.", "metaphor": "capacity", "shape": "collision", "verbs": ["meets", "hold", "becomes"]},
        ],
        "move": [
            {"text": "Protect the foundation the opportunity depends upon, especially your home and private life.", "metaphor": "foundation", "shape": "instruction", "verbs": ["protect", "depends"]},
            {"text": "Make room for the change without making home pay the entire bill.", "metaphor": "cost", "shape": "instruction", "verbs": ["make", "pay"]},
            {"text": "Strengthen the part of your private life that has to carry the decision after the excitement passes.", "metaphor": "weight", "shape": "instruction", "verbs": ["strengthen", "carry", "passes"]},
        ],
        "watch": [
            {"text": "Do not protect the opportunity by quietly overloading home or private life.", "metaphor": "weight", "shape": "instruction", "verbs": ["protect", "overloading"]},
            {"text": "A larger future is not useful if the private foundation has to crack to support it.", "metaphor": "foundation", "shape": "warning", "verbs": ["crack", "support"]},
            {"text": "Do not make home absorb a cost the opportunity should be able to justify.", "metaphor": "cost", "shape": "instruction", "verbs": ["absorb", "justify"]},
        ],
    },
}

_LUNA_VOICE_V2_AREA_BANK = {
    "LOVE": [
        ("Chemistry opens the door. Follow-through decides what stays.",
         "Enjoy the spark. A date, invitation or creative plan can be real without being durable. Watch what still works when calendars, money and ordinary responsibilities return."),
        ("The spark is welcome. Consistency decides whether it matters.",
         "Let the connection be enjoyable. Then watch who makes room, follows through and carries the inconvenient part without being chased."),
        ("Enjoyment gets a vote; staying power gets the final say.",
         "Give pleasure a place in the month. Do not ask one good night, one warm message or one creative high to prove more than it has shown."),
    ],
    "WORK": [
        ("The path moves from possibility to decision.",
         "Make the outside option survive a calendar, a budget and a clear owner. Ask who approves it, who pays and what has to move before you say yes."),
        ("A larger option becomes real enough to negotiate.",
         "Put the opportunity into dates and responsibilities. Check the commute, deadline, support and authority before you add the work to your life."),
        ("The interesting option now needs workable terms.",
         "Stop admiring the possibility from a distance. Put the hours, decision-maker, resources and next deadline on paper."),
    ],
    "MONEY": [
        ("Shared money needs a number, an owner and a boundary.",
         "Put the shared cost on paper. Name who pays, who owns, who owes and what happens if the plan changes."),
        ("Money gets awkward when the obligation stays unnamed.",
         "Name the financial responsibility before goodwill becomes an unpaid invoice, open-ended loan or recurring cost."),
        ("What is shared needs a number, an owner and a boundary.",
         "Clarify the debt, shared cost or outside funding before somebody treats an assumption as permission."),
    ],
}

_LUNA_VOICE_STOP = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "is", "it", "that",
    "this", "your", "you", "be", "as", "at", "by", "from", "into", "has", "have", "can", "may",
    "now", "what", "when", "before", "after", "more", "still", "than", "only", "part", "month",
}


def _luna_voice_tokens(text: str) -> set[str]:
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", str(text or "").lower())
    return {token for token in cleaned.split() if len(token) > 2 and token not in _LUNA_VOICE_STOP}


def _luna_voice_similarity(a: str, b: str) -> float:
    a_text = re.sub(r"\s+", " ", str(a or "").lower()).strip()
    b_text = re.sub(r"\s+", " ", str(b or "").lower()).strip()
    if not a_text or not b_text:
        return 0.0
    a_tokens = _luna_voice_tokens(a_text)
    b_tokens = _luna_voice_tokens(b_text)
    union = a_tokens | b_tokens
    jaccard = (len(a_tokens & b_tokens) / len(union)) if union else 0.0
    sequence = difflib.SequenceMatcher(None, a_text, b_text).ratio()
    return (0.62 * jaccard) + (0.38 * sequence)


def _luna_voice_seed(*parts) -> int:
    raw = "|".join(str(part) for part in parts)
    return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12], 16)


def _luna_voice_memory(anchor_texts=None) -> dict:
    memory = {
        "texts": [],
        "tokens": {},
        "metaphors": {},
        "shapes": {},
        "verbs": {},
    }
    for text in (anchor_texts or []):
        _luna_voice_register(memory, {"text": str(text or ""), "metaphor": "", "shape": "anchor", "verbs": []})
    return memory


def _luna_voice_register(memory: dict, candidate: dict) -> None:
    text = str(candidate.get("text") or "").strip()
    if not text:
        return
    memory["texts"].append(text)
    for token in _luna_voice_tokens(text):
        memory["tokens"][token] = memory["tokens"].get(token, 0) + 1
    metaphor = str(candidate.get("metaphor") or "").strip()
    if metaphor:
        memory["metaphors"][metaphor] = memory["metaphors"].get(metaphor, 0) + 1
    shape = str(candidate.get("shape") or "").strip()
    if shape:
        memory["shapes"][shape] = memory["shapes"].get(shape, 0) + 1
    for verb in candidate.get("verbs") or []:
        memory["verbs"][verb] = memory["verbs"].get(verb, 0) + 1


def _luna_voice_candidate_score(candidate: dict, memory: dict, salt: str) -> float:
    text = str(candidate.get("text") or "").strip()
    if not text:
        return -9999.0

    tokens = _luna_voice_tokens(text)
    token_penalty = sum(max(0, memory["tokens"].get(token, 0) - 1) for token in tokens) * 1.7
    metaphor = str(candidate.get("metaphor") or "").strip()
    metaphor_penalty = memory["metaphors"].get(metaphor, 0) * 7.0 if metaphor else 0.0
    shape = str(candidate.get("shape") or "").strip()
    shape_penalty = memory["shapes"].get(shape, 0) * 1.6 if shape else 0.0
    verb_penalty = sum(memory["verbs"].get(verb, 0) for verb in (candidate.get("verbs") or [])) * 1.4
    similarity_penalty = max((_luna_voice_similarity(text, used) for used in memory["texts"]), default=0.0) * 22.0

    # Stable tiny tie-break. Same sign/month always receives the same approved variant.
    tie = (_luna_voice_seed(salt, text) % 1000) / 10000.0
    return 20.0 + tie - token_penalty - metaphor_penalty - shape_penalty - verb_penalty - similarity_penalty


def _luna_voice_choose(candidates: list[dict], memory: dict, salt: str, *, register: bool = True) -> dict:
    if not candidates:
        return {"text": "", "metaphor": "", "shape": "", "verbs": []}
    ranked = sorted(candidates, key=lambda item: _luna_voice_candidate_score(item, memory, salt), reverse=True)
    chosen = dict(ranked[0])
    if register:
        _luna_voice_register(memory, chosen)
    return chosen


def _luna_voice_second_pass(
    events: list[dict],
    anchor_texts: list[str],
    sign: str,
    period_key: str,
) -> list[dict]:
    """Second audit: replace later echoing fields with another reviewed candidate."""
    memory = _luna_voice_memory(anchor_texts)
    audited = []
    for event in events:
        current = dict(event)
        bank = _LUNA_VOICE_V2_BANK.get(event.get("key"), {})
        for field, bank_field in (("title", "title"), ("voice_lead", "lead"), ("move", "move"), ("watch", "watch")):
            text = str(current.get(field) or "").strip()
            too_close = any(_luna_voice_similarity(text, prior) >= 0.48 for prior in memory["texts"]) if text else False
            if too_close and bank.get(bank_field):
                alternatives = [item for item in bank[bank_field] if item.get("text") != text]
                chosen = _luna_voice_choose(
                    alternatives or bank[bank_field],
                    memory,
                    f"audit:{sign}:{period_key}:{event.get('key')}:{field}",
                    register=False,
                )
                if chosen.get("text"):
                    current[field] = chosen["text"]
                    _luna_voice_register(memory, chosen)
                else:
                    _luna_voice_register(memory, {"text": text, "metaphor": "", "shape": field, "verbs": []})
            else:
                meta = next((item for item in bank.get(bank_field, []) if item.get("text") == text), None)
                _luna_voice_register(memory, meta or {"text": text, "metaphor": "", "shape": field, "verbs": []})
        audited.append(current)
    return audited


def _luna_voice_v2_events(
    events: list[dict],
    *,
    sign: str,
    period_key: str,
    hero: str = "",
    context: str = "",
) -> list[dict]:
    """
    First pass selects vivid, reviewed alternatives using metaphor/verb/shape memory.
    Second pass compares the finished event fields against one another and swaps any
    near-duplicate for another meaning-equivalent option.
    """
    anchors = [item for item in (hero, context) if item]
    memory = _luna_voice_memory(anchors)
    voiced = []

    for event in events:
        current = dict(event)
        bank = _LUNA_VOICE_V2_BANK.get(event.get("key"), {})
        for field, bank_field in (("title", "title"), ("voice_lead", "lead"), ("move", "move"), ("watch", "watch")):
            candidates = list(bank.get(bank_field) or [])
            existing = str(current.get(field) or "").strip()
            if existing and not any(item.get("text") == existing for item in candidates):
                candidates.append({"text": existing, "metaphor": "", "shape": field, "verbs": []})
            chosen = _luna_voice_choose(
                candidates,
                memory,
                f"voice:{sign}:{period_key}:{event.get('key')}:{field}",
            )
            if chosen.get("text"):
                current[field] = chosen["text"]
        voiced.append(current)

    return _luna_voice_second_pass(voiced, anchors, sign, period_key)


def _luna_voice_v2_areas(
    sign: str,
    used_texts: list[str],
    period_key: str,
) -> dict[str, tuple[str, str]]:
    memory = _luna_voice_memory(used_texts)
    output = {}
    for category in ("LOVE", "WORK", "MONEY"):
        pairs = _LUNA_VOICE_V2_AREA_BANK[category]
        candidates = []
        for title, body in pairs:
            combined = f"{title} {body}"
            candidates.append({"text": combined, "title": title, "body": body, "metaphor": category.lower(), "shape": "area", "verbs": []})
        chosen = _luna_voice_choose(candidates, memory, f"area:{sign}:{period_key}:{category}")
        output[category] = (chosen.get("title") or pairs[0][0], chosen.get("body") or pairs[0][1])
    return output


def _monthly_canonical_events(narrative, result) -> list[dict]:
    """Translate the engine's selected-period chronology into the page event model.

    The former implementation admitted four campaign-specific events only. This one
    consumes the same generic chronology used by the production report, so every
    selected month/year and all twelve signs follow identical calculation logic.
    """
    rows = build_monthly_reader_chronology(narrative, result)
    source_events = [dict(item) for item in (result.get("events") or []) if isinstance(item, dict)]
    output: list[dict] = []

    for index, row in enumerate(rows):
        date_iso = str(row.get("date") or "")
        technical = str(row.get("technical") or "").strip()
        same_day = [item for item in source_events if str(item.get("event_date") or "") == date_iso]
        matched = [
            item for item in same_day
            if technical and (
                technical.lower() in str(item.get("title") or "").lower()
                or str(item.get("title") or "").lower() in technical.lower()
            )
        ] or same_day

        houses: set[int] = set()
        planets: list[str] = []
        for item in matched:
            for value in item.get("houses") or []:
                try:
                    house = int(value)
                except Exception:
                    continue
                if 1 <= house <= 12:
                    houses.add(house)
            for planet in item.get("planets") or []:
                name = str(planet).upper()
                if name and name not in planets:
                    planets.append(name)

        try:
            event_date = date.fromisoformat(date_iso)
            day = event_date.day
            date_label = event_date.strftime("%d %b %Y").upper()
        except Exception:
            day = index + 1
            date_label = str(row.get("date_label") or "").upper()

        key_text = re.sub(r"[^a-z0-9]+", "-", f"{date_iso}-{technical}".lower()).strip("-")
        output.append({
            "key": key_text or f"monthly-event-{index + 1}",
            "day": day,
            "date": date_iso,
            "date_label": date_label,
            "transit": technical,
            "signal": str(row.get("badge") or "SKY EVENT").upper(),
            "influence": str(row.get("influence") or ""),
            "title": str(row.get("headline") or technical or "The month changes here"),
            "body": [str(value) for value in (row.get("body") or []) if str(value).strip()][:2],
            "move": _monthly_clean_final_step(str(row.get("move") or "")),
            "watch": "",
            "also": list(row.get("also") or []),
            "houses": houses,
            "planets": planets,
        })

    return output


def _monthly_context_section(narrative, result):
    roots = [("narrative", _monthly_plain(narrative)), ("result", _monthly_plain(result))]
    candidates = []

    def visit(value, path=(), depth=0):
        if depth > 6:
            return
        path_text = " ".join(path).lower()
        if isinstance(value, dict):
            if any(word in path_text for word in ("concentration", "gather", "theme")):
                strings = _monthly_container_strings(value, max_depth=4)
                titles = [(txt, " ".join(pth)) for pth, txt in strings if 16 <= len(txt) <= 120]
                bodies = [(txt, " ".join(pth)) for pth, txt in strings if len(txt) >= 60]
                title = max(titles, key=lambda p: _monthly_title_score(p[0], p[1]), default=("", ""))[0]
                ranked = sorted(bodies, key=lambda p: _monthly_body_score(p[0], p[1]), reverse=True)
                body = [txt for txt, pth in ranked if _monthly_body_score(txt, pth) > 0][:2]
                score = _monthly_title_score(title, path_text) + sum(max(0, _monthly_body_score(txt, pth)) for txt, pth in ranked[:2])
                if score > 0:
                    candidates.append((score, title, body))
            for key, child in value.items():
                visit(child, path + (str(key),), depth + 1)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, path + (str(index),), depth + 1)

    for root_name, root in roots:
        visit(root, (root_name,), 0)

    if not candidates:
        return "", []
    _, title, body = max(candidates, key=lambda item: item[0])
    if _monthly_internal_text(title) or "_" in title:
        title = ""
    return title, body


def _monthly_area_editorial(narrative, result, category: str):
    keywords = {
        "LOVE":("love","romance","relationship"),
        "WORK":("work","career","profession"),
        "MONEY":("money","finance","income","resource"),
    }[category]
    roots = [("narrative", _monthly_plain(narrative)), ("result", _monthly_plain(result))]
    candidates = []

    def visit(value, path=(), depth=0):
        if depth > 7:
            return
        path_text = " ".join(path).lower()
        if isinstance(value, dict):
            if any(word in path_text for word in keywords):
                strings = _monthly_container_strings(value, max_depth=4)
                titles = [(txt, " ".join(pth)) for pth, txt in strings if 14 <= len(txt) <= 130]
                bodies = [(txt, " ".join(pth)) for pth, txt in strings if len(txt) >= 45]
                title = max(titles, key=lambda p: _monthly_title_score(p[0], p[1]), default=("", ""))[0]
                body = max(bodies, key=lambda p: _monthly_body_score(p[0], p[1]), default=("", ""))[0]
                score = _monthly_title_score(title, path_text) + _monthly_body_score(body, path_text)
                if score > 0 and not _monthly_internal_text(title + " " + body):
                    candidates.append((score, title, body))
            for key, child in value.items():
                visit(child, path + (str(key),), depth + 1)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, path + (str(index),), depth + 1)

    for root_name, root in roots:
        visit(root, (root_name,), 0)

    if not candidates:
        return "", ""
    _, title, body = max(candidates, key=lambda item: item[0])
    if "_" in title:
        title = ""
    return title, body


def _monthly_action_plan(narrative, result):
    roots = [("narrative", _monthly_plain(narrative)), ("result", _monthly_plain(result))]
    candidates = []

    def visit(value, path=(), depth=0):
        if depth > 7:
            return
        path_text = " ".join(path).lower()
        if isinstance(value, dict):
            if any(word in path_text for word in ("move","action","plan","step","strategy")):
                title, steps = "", []
                for key, child in value.items():
                    low = str(key).lower()
                    if isinstance(child, str):
                        if low in {"headline","title","hook"} and 10 <= len(child) <= 140:
                            title = child.strip()
                        elif 18 <= len(child) <= 260 and not _monthly_internal_text(child):
                            steps.append(child.strip())
                    elif isinstance(child, list):
                        for item in child:
                            if isinstance(item, str) and 18 <= len(item) <= 260 and not _monthly_internal_text(item):
                                steps.append(item.strip())
                if len(steps) >= 2:
                    candidates.append((len(steps)*20 + _monthly_editorial_path_score(path_text), title, steps[:4]))
            for key, child in value.items():
                visit(child, path + (str(key),), depth + 1)
        elif isinstance(value, list):
            if any(word in path_text for word in ("move","action","plan","step","strategy")):
                steps = [str(item).strip() for item in value if isinstance(item, str) and 18 <= len(item) <= 260 and not _monthly_internal_text(item)]
                if len(steps) >= 2:
                    candidates.append((len(steps)*20 + _monthly_editorial_path_score(path_text), "", steps[:4]))
            for index, child in enumerate(value):
                visit(child, path + (str(index),), depth + 1)

    for root_name, root in roots:
        visit(root, (root_name,), 0)

    if not candidates:
        return "", []
    _, title, steps = max(candidates, key=lambda item: item[0])
    if "_" in title or _monthly_internal_text(title):
        title = ""
    return title, steps


def _monthly_history_match_for_event(matches, event, used_years):
    """
    Select precedent for the current event, not merely for the month as a whole.
    Scores transition-family token recurrence first, then relevant life-area overlap.
    Weak event matches are suppressed rather than shown as false precision.
    """
    if not matches:
        return None

    target_houses = {
        "sun_saturn": {9, 10, 11},
        "solar_eclipse": {9},
        "venus_jupiter": {5, 7},
        "lunar_eclipse": {4},
    }.get(event.get("key"), set())

    event_tokens = _history_tokens(event.get("transit", ""))
    scored = []

    for item in matches:
        year = int(item["year"])
        shared = set(item.get("shared_houses") or [])
        past_houses = set(item.get("past_houses") or [])
        past_tokens = set(item.get("past_tokens") or [])

        token_overlap = len(event_tokens & past_tokens)
        direct_house_overlap = len(target_houses & shared)
        past_house_overlap = len(target_houses & past_houses)

        event_score = (
            token_overlap * 14
            + direct_house_overlap * 10
            + past_house_overlap * 4
            + float(item.get("score") or 0) * 4
        )

        if year not in used_years:
            event_score += 4
        else:
            event_score -= 8

        scored.append({
            "score": event_score,
            "token_overlap": token_overlap,
            "direct_house_overlap": direct_house_overlap,
            "past_house_overlap": past_house_overlap,
            "item": item,
        })

    scored.sort(key=lambda row: row["score"], reverse=True)
    best = scored[0]

    # Do not manufacture an event-specific echo where none exists.
    if (
        best["token_overlap"] == 0
        and best["direct_house_overlap"] == 0
        and best["past_house_overlap"] == 0
    ):
        return None

    chosen = dict(best["item"])
    chosen["_event_token_overlap"] = best["token_overlap"]
    chosen["_event_direct_house_overlap"] = best["direct_house_overlap"]
    chosen["_event_past_house_overlap"] = best["past_house_overlap"]
    return chosen


def _monthly_echo_for_event(sign, timezone_name, birth_date_value, event, used_years, result):
    forecast_year, forecast_month, forecast_label = monthly_period_from_result(result)
    try:
        matches = _monthly_history_matches(sign, forecast_year, forecast_month, timezone_name)
    except Exception:
        return
    if not matches:
        return

    item = _monthly_history_match_for_event(matches, event, used_years)
    if not item:
        return

    past_year = int(item["year"])
    used_years.add(past_year)
    now_only = item.get("current_only") or []
    then_only = item.get("past_only") or []

    echo_heading = {
        "sun_saturn": "Have you been here before?",
        "solar_eclipse": "A similar turning point",
        "venus_jupiter": "This opening has an echo",
        "lunar_eclipse": "Think back",
    }.get(event.get("key"), "Have you been here before?")
    st.markdown(f"### {echo_heading}")

    age_text = ""
    if birth_date_value:
        ref = date(past_year, forecast_month, 15)
        if ref >= birth_date_value:
            age = ref.year - birth_date_value.year - (
                (ref.month, ref.day) < (birth_date_value.month, birth_date_value.day)
            )
            age_text = f" You were about **{age}**."

    st.markdown(f"Think back to **{month_name[forecast_month]} {past_year}**.{age_text}")

    event_echo = {
        "sun_saturn": "Then, as now, an opening was asking to become practical rather than remain only possible.",
        "solar_eclipse": "Then, as now, an external opportunity was moving toward a decision or commitment.",
        "venus_jupiter": "Then, as now, love, creativity, pleasure or connection had room to open.",
        "lunar_eclipse": "Then, as now, home, family or the foundations underneath a decision were carrying more weight.",
    }.get(event.get("key"), "")

    if event_echo:
        st.markdown(f"**What rhymes:** {event_echo}")

    if now_only and then_only:
        st.markdown(
            f"**What is different now:** **{_monthly_reader_house_label(now_only[0])}** carries more weight; "
            f"the earlier month leaned more toward **{_monthly_reader_house_label(then_only[0])}**."
        )
    elif now_only:
        st.markdown(
            f"**What is different now:** this month adds more emphasis to "
            f"**{_monthly_reader_house_label(now_only[0])}**."
        )
    elif then_only:
        st.markdown(
            f"**What is different now:** the earlier month carried more "
            f"**{_monthly_reader_house_label(then_only[0])}**."
        )

    st.caption("What do you remember changing then?")



def _monthly_motion_overlay_nodes(result: dict, event: dict) -> list[dict]:
    """Best-effort read of the existing natal overlay without changing its calculation."""
    overlay = result.get("natal_overlay") if isinstance(result, dict) else None
    if not overlay:
        return []

    event_tokens = _history_tokens(event.get("transit", "")) | _history_tokens(event.get("date_label", ""))
    nodes = []

    def visit(value, depth=0):
        if depth > 7:
            return
        if isinstance(value, dict):
            strings = []
            for key, child in value.items():
                if isinstance(child, (str, int, float)):
                    strings.append(f"{key} {child}")
            combined = " ".join(strings)
            tokens = _history_tokens(combined)
            if event_tokens & tokens:
                house = None
                for key in ("natal_house", "house", "activated_house", "target_house"):
                    if key in value:
                        try:
                            candidate = int(value[key])
                            if 1 <= candidate <= 12:
                                house = candidate
                                break
                        except Exception:
                            pass
                target = ""
                for key in ("natal_target", "natal_planet", "target", "target_planet"):
                    if value.get(key):
                        target = str(value.get(key)).strip()
                        break
                transit = ""
                for key in ("transit_planet", "transiting_planet", "planet", "transit"):
                    if value.get(key):
                        transit = str(value.get(key)).strip()
                        break
                if house or target or transit:
                    nodes.append({"house": house, "target": target, "transit": transit})
            for child in value.values():
                visit(child, depth + 1)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child, depth + 1)

    visit(overlay)
    return nodes


def _monthly_motion_planets(event: dict) -> list[str]:
    supplied = [str(value).upper() for value in (event.get("planets") or []) if str(value).strip()]
    if supplied:
        return list(dict.fromkeys(supplied))
    transit = str(event.get("transit") or "")
    return [
        planet.upper()
        for planet in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto")
        if re.search(rf"\b{planet}\b", transit, re.I)
    ]


def _monthly_motion_summary(events: list[dict], selected_key: str) -> str:
    if selected_key == "whole":
        if len(events) >= 4:
            return (
                "Start with what is solid. Make the decision when the evidence arrives. "
                "Use the lighter opening. Then change what no longer fits."
            )
        return "Follow the strongest date. Make one decision thread carry the month."

    event = next((item for item in events if item.get("key") == selected_key), None)
    if not event:
        return "Choose a date. Read the consequence. Make the move."
    move = str(event.get("move") or "").strip()
    lead = str(event.get("voice_lead") or "").strip()
    return finalize_customer_prose(" ".join(item for item in (lead, move) if item), product="monthly")

def _monthly_activation_wheel_svg(result: dict, events: list[dict], selected_key: str, size: int = 620) -> str:
    """
    Monthly version of the Year Ahead activation layer.
    Colour means activity only. It uses existing Monthly/natal-overlay evidence when
    available and falls back to the calculated Monthly house emphasis.
    """
    selected = events if selected_key == "whole" else [item for item in events if item.get("key") == selected_key]
    width = height = int(size)
    cx = cy = width / 2
    outer = width * 0.39
    inner = width * 0.25
    label_r = width * 0.345

    house_counts: dict[int, int] = {}
    house_targets: dict[int, list[str]] = {}
    house_planets: dict[int, list[str]] = {}

    for event in selected:
        overlay_nodes = _monthly_motion_overlay_nodes(result, event)
        event_houses = set()
        for node in overlay_nodes:
            house = node.get("house")
            if house:
                event_houses.add(int(house))
                if node.get("target"):
                    house_targets.setdefault(int(house), []).append(str(node["target"]))
                if node.get("transit"):
                    house_planets.setdefault(int(house), []).append(str(node["transit"]).upper())

        if not event_houses:
            event_houses = {int(h) for h in (event.get("houses") or set()) if 1 <= int(h) <= 12}

        # Keep the visual readable: an event can activate many technical houses,
        # but the chart foregrounds the first three strongest available sectors.
        event_houses = set(sorted(event_houses)[:3])
        for house in event_houses:
            house_counts[house] = house_counts.get(house, 0) + 1
            if not house_planets.get(house):
                house_planets.setdefault(house, []).extend(_monthly_motion_planets(event))

    max_count = max(house_counts.values(), default=1)

    def polar(radius, degrees):
        angle = math.radians(degrees - 90)
        return cx + radius * math.cos(angle), cy + radius * math.sin(angle)

    def sector_path(house):
        start_deg = (house - 1) * 30
        end_deg = house * 30
        x1, y1 = polar(outer, start_deg)
        x2, y2 = polar(outer, end_deg)
        x3, y3 = polar(inner, end_deg)
        x4, y4 = polar(inner, start_deg)
        return (
            f"M {x1:.2f},{y1:.2f} "
            f"A {outer:.2f},{outer:.2f} 0 0 1 {x2:.2f},{y2:.2f} "
            f"L {x3:.2f},{y3:.2f} "
            f"A {inner:.2f},{inner:.2f} 0 0 0 {x4:.2f},{y4:.2f} Z"
        )

    label = "WHOLE MONTH"
    if selected_key != "whole":
        event = next((item for item in events if item.get("key") == selected_key), None)
        if event:
            label = re.sub(r"\s+\d{4}$", "", event.get("date_label", "")).upper()

    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="Monthly natal activation layer">']

    for house in range(1, 13):
        count = house_counts.get(house, 0)
        opacity = 0.08 if count == 0 else 0.18 + (0.34 * count / max_count)
        fill = "#f4f4f1" if count == 0 else "#6977df"
        parts.append(
            f'<path d="{sector_path(house)}" fill="{fill}" fill-opacity="{opacity:.2f}" '
            f'stroke="#d8d8d3" stroke-width="1"/>'
        )
        lx, ly = polar(label_r, (house - 0.5) * 30)
        parts.append(
            f'<text x="{lx:.2f}" y="{ly:.2f}" text-anchor="middle" dominant-baseline="middle" '
            f'font-family="IBM Plex Mono, monospace" font-size="12" fill="#444">{house}</text>'
        )

    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{inner}" fill="#fff" stroke="#d8d8d3" stroke-width="1"/>')
    parts.append(
        f'<text x="{cx}" y="{cy-8}" text-anchor="middle" font-family="Bodoni MT, Georgia, serif" '
        f'font-size="25" fill="#151515">YOUR MONTH</text>'
    )
    parts.append(
        f'<text x="{cx}" y="{cy+16}" text-anchor="middle" font-family="IBM Plex Mono, monospace" '
        f'font-size="10" letter-spacing="1.2" fill="#696963">{escape(label)}</text>'
    )

    for house in sorted(house_counts):
        angle = (house - 0.5) * 30
        natal_x, natal_y = polar(inner + (outer-inner) * 0.38, angle)
        transit_x, transit_y = polar(outer + 23, angle)
        parts.append(
            f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{natal_x:.2f}" y2="{natal_y:.2f}" '
            f'stroke="#6757c7" stroke-width="2.2" stroke-opacity=".72"/>'
        )
        parts.append(f'<circle cx="{natal_x:.2f}" cy="{natal_y:.2f}" r="9" fill="#6757c7"/>')
        targets = house_targets.get(house) or []
        if targets:
            target = targets[0][:12]
            parts.append(
                f'<text x="{natal_x:.2f}" y="{natal_y-14:.2f}" text-anchor="middle" '
                f'font-family="Josefin Sans, sans-serif" font-size="11" font-weight="600" fill="#332a76">{escape(target)}</text>'
            )
        planets = []
        for item in house_planets.get(house) or []:
            if item and item not in planets:
                planets.append(item)
        planet_text = "/".join(planets[:2])
        parts.append(f'<circle cx="{transit_x:.2f}" cy="{transit_y:.2f}" r="8" fill="#e58a2f"/>')
        if planet_text:
            parts.append(
                f'<text x="{transit_x:.2f}" y="{transit_y-13:.2f}" text-anchor="middle" '
                f'font-family="IBM Plex Mono, monospace" font-size="9" fill="#7a4818">{escape(planet_text[:15])}</text>'
            )

    parts.append('</svg>')
    return ''.join(parts)



_CHART_HOUSE_KEY = {
    1: "You + direction",
    2: "Money + price",
    3: "Message + decision",
    4: "Home + family",
    5: "Attraction + creative work",
    6: "Workload + routine",
    7: "People + promises",
    8: "Shared money + trust",
    9: "Trip + course + outside plan",
    10: "Role + responsibility",
    11: "Friends + next plan",
    12: "Rest + closure",
}


def _chart_natal_reference_items(snapshot) -> list[tuple[str, str]]:
    """Reader-facing natal shorthand using values already calculated in the snapshot."""
    by_planet = {}
    for item in list(getattr(snapshot, "positions", None) or []):
        planet = str(getattr(item, "planet", "") or "")
        if planet:
            by_planet[planet] = item

    def sign_for(planet: str) -> str:
        item = by_planet.get(planet)
        return str(getattr(item, "sign", "") or "Not calculated")

    moon_value = sign_for("Moon")
    moon_uncertain = list(getattr(snapshot, "moon_uncertain", None) or [])
    if not bool(getattr(snapshot, "birth_time_known", False)) and len(moon_uncertain) > 1:
        moon_value = " / ".join(str(item) for item in moon_uncertain)

    ascendant = getattr(snapshot, "ascendant", None)
    rising = str(getattr(ascendant, "sign", "") or "Not calculated")

    return [
        ("Sun sign", sign_for("Sun")),
        ("Moon", moon_value),
        ("Rising", rising),
        ("Mercury", sign_for("Mercury")),
        ("Venus", sign_for("Venus")),
        ("Mars", sign_for("Mars")),
    ]


def _render_chart_natal_reference(snapshot) -> None:
    items = _chart_natal_reference_items(snapshot)
    cells = "".join(
        f'<div><span>{escape(label)}</span><strong>{escape(value)}</strong></div>'
        for label, value in items
    )
    st.markdown('<div class="chart-reader-label">YOUR NATAL REFERENCE</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chart-natal-reference">{cells}</div>', unsafe_allow_html=True)
    if any(label == "Rising" and value == "Not calculated" for label, value in items):
        st.caption("Rising sign is shown only when the supplied birth time and location support a reliable calculation.")


def _render_active_house_legend(houses: list[int], label: str = "Active in this view") -> None:
    clean = []
    for value in houses:
        try:
            house = int(value)
        except Exception:
            continue
        if 1 <= house <= 12 and house not in clean:
            clean.append(house)

    st.markdown(f'<div class="chart-reader-label">{escape(label)}</div>', unsafe_allow_html=True)
    if not clean:
        st.caption("No house passed the current activation threshold in this view.")
        return

    chips = "".join(
        f'<div class="chart-house-chip"><strong>{house}</strong>{escape(_CHART_HOUSE_KEY[house])}</div>'
        for house in clean
    )
    st.markdown(f'<div class="chart-active-houses">{chips}</div>', unsafe_allow_html=True)


def _render_house_key() -> None:
    with st.expander("House key · what the numbers 1–12 mean"):
        items = "".join(
            f'<div class="house-key-item"><strong>{house}</strong><span>{escape(_CHART_HOUSE_KEY[house])}</span></div>'
            for house in range(1, 13)
        )
        st.markdown(
            '<div class="small-note" style="margin-bottom:.55rem">'
            'The numbers are astrological houses — life areas, not scores. Colour means activity, not good or bad.'
            '</div>'
            f'<div class="house-key-grid">{items}</div>',
            unsafe_allow_html=True,
        )


def _monthly_active_house_numbers(result: dict, events: list[dict], selected_key: str) -> list[int]:
    """Return the same foregrounded house numbers used by the Monthly activation wheel."""
    selected = events if selected_key == "whole" else [
        item for item in events if item.get("key") == selected_key
    ]
    active = []

    for event in selected:
        overlay_nodes = _monthly_motion_overlay_nodes(result, event)
        event_houses = set()

        for node in overlay_nodes:
            house = node.get("house")
            if house:
                try:
                    number = int(house)
                    if 1 <= number <= 12:
                        event_houses.add(number)
                except Exception:
                    pass

        if not event_houses:
            for value in event.get("houses") or set():
                try:
                    number = int(value)
                    if 1 <= number <= 12:
                        event_houses.add(number)
                except Exception:
                    pass

        # Match the activation wheel's readability rule.
        event_houses = set(sorted(event_houses)[:3])
        for house in sorted(event_houses):
            if house not in active:
                active.append(house)

    return active


def _timing_active_house_numbers(active_stories: list) -> list[int]:
    houses = []
    for story in active_stories:
        value = getattr(story, "natal_house", None)
        try:
            house = int(value) if value else None
        except Exception:
            house = None
        if house and 1 <= house <= 12 and house not in houses:
            houses.append(house)
    return sorted(houses)



def _monthly_chart_in_motion(
    snapshot,
    result: dict,
    events: list[dict],
    sign: str,
    *,
    include_legacy_interpretation: bool = True,
) -> None:
    if snapshot is None or not events:
        return

    forecast_year, forecast_month, forecast_label = monthly_period_from_result(result)

    st.markdown("## Your Month in Motion")
    st.caption(
        f"Colour shows activity, not good or bad. Choose the whole month or one of the "
        f"{len(events)} key {month_name[forecast_month]} moments to see how the emphasis shifts against your natal reference."
    )

    _render_chart_natal_reference(snapshot)

    option_pairs = [("Whole Month", "whole")]
    for event in events:
        short_date = re.sub(r"\s+\d{4}$", "", str(event.get("date_label") or "")).title()
        option_pairs.append((short_date, event.get("key")))
    labels = [item[0] for item in option_pairs]
    chosen_label = st.radio(
        "Month view",
        labels,
        index=0,
        horizontal=True,
        key=f"monthly-motion-{sign_slug(sign)}-{forecast_year}-{forecast_month}",
    )
    selected_key = dict(option_pairs).get(chosen_label, "whole")

    if include_legacy_interpretation:
        st.markdown(
            f'<div class="chart-motion-summary">{escape(_monthly_motion_summary(events, selected_key))}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("### Read the month, not the picture")
        for paragraph in _monthly_chart_story(result, events, selected_key):
            _render_luna_prose(paragraph, product="monthly")

    monthly_active_houses = _monthly_active_house_numbers(result, events, selected_key)
    active_label = "ACTIVE IN THIS VIEW" if selected_key == "whole" else f"ACTIVE · {chosen_label.upper()}"
    _render_active_house_legend(monthly_active_houses, active_label)

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("**Natal reference**")
        st.markdown(natal_wheel_svg(snapshot, size=620), unsafe_allow_html=True)
    with right:
        st.markdown("**Activation layer**")
        st.markdown(_monthly_activation_wheel_svg(result, events, selected_key, size=620), unsafe_allow_html=True)
        st.markdown(
            '<div class="chart-motion-legend">'
            '<div class="chart-motion-key"><i class="chart-motion-swatch house"></i>Activated house</div>'
            '<div class="chart-motion-key"><i class="chart-motion-swatch natal"></i>Natal contact</div>'
            '<div class="chart-motion-key"><i class="chart-motion-swatch transit"></i>Transiting planet</div>'
            '</div><div class="small-note">The Monthly layer foregrounds concentration. Technical evidence remains under Why Luna sees this.</div>',
            unsafe_allow_html=True,
        )

    _render_house_key()


def _major_event_dict_selection(values, product: str, *, limit: int = 8, opportunity_slots: int = 2) -> list[dict]:
    product = str(product or "").lower()
    rows = [dict(item or {}) for item in (values or []) if dict(item or {}).get("display_label")]
    rows.sort(key=lambda item: (-float(item.get("sky_score", 0.0) or 0.0), str(item.get("event_date") or "")))
    mandatory = [item for item in rows if product in set(item.get("must_surface_products") or [])]
    opportunities = [item for item in rows if bool(item.get("opportunity")) and item not in mandatory][:max(0, opportunity_slots)]
    selected = []
    for item in mandatory + opportunities + rows:
        if item not in selected:
            selected.append(item)
        if len(selected) >= max(limit, len(mandatory) + len(opportunities)):
            break
    return sorted(selected, key=lambda item: (str(item.get("event_date") or ""), -float(item.get("sky_score", 0.0) or 0.0)))



def _major_event_badge(item: dict, product: str) -> str:
    event_class = str(item.get("event_class") or "")
    planets = set(item.get("planets") or ())
    if event_class == "solar_anchor":
        return "SOLAR ANCHOR"
    if event_class == "eclipse":
        return "TURNING POINT"
    if event_class == "cazimi":
        return "CLARITY POINT"
    if bool(item.get("opportunity")):
        return "OPENING"
    if event_class == "station":
        return "PIVOT"
    if event_class == "ingress" and planets & {"Mercury", "Venus", "Mars"}:
        return "TRIGGER"
    if event_class in {"ingress", "structural_alignment"}:
        return "STRUCTURAL SHIFT"
    if event_class == "lunation":
        return "LUNATION"
    return "SKY EVENT"


def _major_event_date_label(item: dict) -> str:
    raw = str(item.get("event_date") or "")
    try:
        return _timing_date_label(date.fromisoformat(raw))
    except Exception:
        return raw


def _render_major_sky_events(
    values,
    product: str,
    *,
    heading: str = "Key sky events",
    limit: int = 8,
    compact: bool = False,
) -> None:
    selected = _major_event_dict_selection(
        values, product, limit=limit, opportunity_slots=2
    )
    if not selected:
        return

    st.markdown(f"## {heading}")
    st.caption(
        "Keep the solar anchors, turning points and usable openings in view. "
        "Slower structural dates remain available below without competing for the same visual weight."
    )

    anchors = [
        item for item in selected
        if _major_event_badge(item, product) == "SOLAR ANCHOR"
    ]
    turning = [
        item for item in selected
        if _major_event_badge(item, product) in {"TURNING POINT", "CLARITY POINT"}
    ]
    openings = [
        item for item in selected
        if _major_event_badge(item, product) == "OPENING"
    ]
    supporting = [
        item for item in selected
        if item not in anchors and item not in turning and item not in openings
    ]

    if compact:
        priority = sorted(
            anchors + turning + openings,
            key=lambda row: str(row.get("event_date") or ""),
        )
        supporting_sorted = sorted(
            supporting,
            key=lambda row: str(row.get("event_date") or ""),
        )
        fill = max(0, 7 - len(priority))
        featured = priority + supporting_sorted[:fill]
        remaining = [item for item in selected if item not in featured]

        def compact_rows(items, include_action: bool = True) -> str:
            rows = []
            for item in sorted(items, key=lambda row: str(row.get("event_date") or "")):
                detail = ""
                if include_action:
                    action = finalize_customer_prose(str(item.get("action") or ""), product=product)
                    detail = f"<br>{escape(action)}" if action else ""
                rows.append(
                    f'<div class="compact-evidence-row">'
                    f'<div class="compact-evidence-label">'
                    f'{escape(_major_event_date_label(item))} · '
                    f'{escape(_major_event_badge(item, product))}</div>'
                    f'<div class="compact-evidence-value">'
                    f'<strong>{escape(str(item.get("display_label") or ""))}</strong>'
                    f'{detail}</div></div>'
                )
            return "".join(rows)

        st.markdown(
            f'<div class="compact-evidence-list">{compact_rows(featured)}</div>',
            unsafe_allow_html=True,
        )
        if remaining:
            with st.expander(f"Other structural dates · {len(remaining)}"):
                st.markdown(
                    f'<div class="compact-evidence-list">{compact_rows(remaining, include_action=True)}</div>',
                    unsafe_allow_html=True,
                )
        return

    if anchors:
        st.markdown("### Solar anchors")
        for item in sorted(
            anchors, key=lambda row: str(row.get("event_date") or "")
        ):
            st.markdown(
                f"""<article class="timing-story major-sky-story solar-anchor-story">
<div class="timing-meta">{escape(_major_event_date_label(item).upper())} · SOLAR ANCHOR</div>
<h3>{escape(str(item.get("display_label") or ""))}</h3>
<p>{escape(finalize_customer_prose(str(item.get("line_one") or ""), product=product))}</p>
<div class="timing-move"><div class="timing-move-label">Action</div><p>{escape(finalize_customer_prose(str(item.get("action") or ""), product=product))}</p></div>
</article>""",
                unsafe_allow_html=True,
            )

    if turning:
        st.markdown("### Major turning points")
        for item in sorted(
            turning, key=lambda row: str(row.get("event_date") or "")
        ):
            line_one = finalize_customer_prose(
                str(item.get("line_one") or ""), product=product
            )
            action = finalize_customer_prose(
                str(item.get("action") or ""), product=product
            )
            st.markdown(
                f"""<article class="timing-story major-sky-story">
<div class="timing-meta">{escape(_major_event_date_label(item).upper())} · {escape(_major_event_badge(item, product))}</div>
<h3>{escape(str(item.get("display_label") or item.get("technical_label") or ""))}</h3>
<p>{escape(line_one)}</p>
<div class="timing-move"><div class="timing-move-label">Action</div><p>{escape(action)}</p></div>
</article>""",
                unsafe_allow_html=True,
            )

    if openings:
        st.markdown("### Openings worth using")
        for item in sorted(
            openings, key=lambda row: str(row.get("event_date") or "")
        ):
            st.markdown(
                f"""<article class="timing-story major-sky-story compact-major-sky-story">
<div class="timing-meta">{escape(_major_event_date_label(item).upper())} · OPENING</div>
<h3>{escape(str(item.get("display_label") or ""))}</h3>
<p>{escape(finalize_customer_prose(str(item.get("line_one") or ""), product=product))}</p>
<div class="timing-move"><div class="timing-move-label">Use it</div><p>{escape(finalize_customer_prose(str(item.get("action") or ""), product=product))}</p></div>
</article>""",
                unsafe_allow_html=True,
            )

    if supporting:
        st.markdown("### Other dates worth keeping")
        rows = "".join(
            f'<div class="compact-evidence-row">'
            f'<div class="compact-evidence-label">'
            f'{escape(_major_event_date_label(item))} · '
            f'{escape(_major_event_badge(item, product))}</div>'
            f'<div class="compact-evidence-value">'
            f'{escape(str(item.get("display_label") or ""))}</div></div>'
            for item in sorted(
                supporting, key=lambda row: str(row.get("event_date") or "")
            )
        )
        st.markdown(
            f'<div class="compact-evidence-list">{rows}</div>',
            unsafe_allow_html=True,
        )


def _render_major_sky_evidence(values, product: str, *, heading: str, limit: int = 8) -> None:
    """Render calculated event labels only; no deterministic interpretation."""
    selected = _major_event_dict_selection(values, product, limit=limit, opportunity_slots=2)
    if not selected:
        return
    st.markdown(f"## {heading}")
    rows = "".join(
        f'<div class="compact-evidence-row">'
        f'<div class="compact-evidence-label">{escape(_major_event_date_label(item))} · '
        f'{escape(_major_event_badge(item, product))}</div>'
        f'<div class="compact-evidence-value"><strong>{escape(str(item.get("display_label") or item.get("technical_label") or ""))}</strong></div>'
        f'</div>'
        for item in selected
    )
    st.markdown(f'<div class="compact-evidence-list">{rows}</div>', unsafe_allow_html=True)


def _personal_item_value(item, key: str, default=""):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


_PERSONAL_TARGET_PHRASE = {
    "Ascendant": "how you show up and set boundaries",
    "Midheaven": "work and public responsibility",
    "Sun": "identity and direction",
    "Moon": "home and emotional security",
    "Mercury": "the conversation or decision",
    "Venus": "what you value in love or money",
    "Mars": "effort, conflict and the move you are making",
    "Jupiter": "growth and the larger option",
    "Saturn": "responsibility and limits",
    "Uranus": "freedom and the rule that needs changing",
    "Neptune": "the story that still needs evidence",
    "Pluto": "power, dependency and leverage",
    "True Node": "the route you are growing toward",
}


def _personal_event_group_copy(group) -> tuple[str, str]:
    """One sky event, one interpretation, however many natal contacts it makes."""
    items = list(group or [])
    if not items:
        return "", ""

    targets = [str(_personal_item_value(item, "natal_target", "") or "") for item in items]
    target_set = set(targets)
    first = items[0]
    event_class = str(_personal_item_value(first, "event_class", "") or "")
    first_interpretation = str(_personal_item_value(first, "interpretation", "") or "")
    action = str(_personal_item_value(first, "action", "") or "")

    if {"Moon", "Venus"} <= target_set:
        interpretation = (
            "Private security and what you want from relationships are moving together. "
            "An opening only works if home, habit and emotional capacity can carry it."
        )
        convergence_action = "Do not agree to anything your private life cannot actually support."
    elif {"Moon", "Mercury"} <= target_set:
        interpretation = (
            "Home and the decision now affect each other. "
            "A conversation, document or answer can change what your private life has to carry."
        )
        convergence_action = "Make the sentence work at home as well as on paper."
    elif {"Sun", "Saturn"} <= target_set:
        interpretation = (
            "Identity and responsibility are moving together. "
            "What you commit to now has to fit the person you are trying to become."
        )
        convergence_action = "Choose the commitment that still fits the direction you want."
    elif len(targets) >= 2:
        phrases = []
        for target in targets:
            phrase = _PERSONAL_TARGET_PHRASE.get(target, target.lower())
            if phrase and phrase not in phrases:
                phrases.append(phrase)
        if len(phrases) >= 3:
            joined = ", ".join(phrases[:-1]) + f" and {phrases[-1]}"
        elif len(phrases) == 2:
            joined = f"{phrases[0]} and {phrases[1]}"
        else:
            joined = phrases[0] if phrases else "two parts of life"
        interpretation = (
            f"{joined[:1].upper() + joined[1:]} are tied to the same event. "
            "Changing one changes the terms of the others."
        )
        convergence_action = "Choose one standard that every contact can live with."
    else:
        interpretation = first_interpretation
        convergence_action = ""

    if event_class == "eclipse" and len(targets) >= 2 and convergence_action:
        convergence_action = f"{convergence_action} Leave room for new facts before making the irreversible move."

    final_action = action
    if convergence_action and convergence_action not in final_action:
        final_action = f"{final_action} {convergence_action}".strip()
    return interpretation, final_action


def _personal_major_badge(item, group) -> str:
    event_class = str(_personal_item_value(item, "event_class", "") or "")
    planet = str(_personal_item_value(item, "transit_planet", "") or "")
    opportunity = any(bool(_personal_item_value(value, "opportunity", False)) for value in group)
    if event_class == "solar_anchor":
        return "PERSONAL SOLAR ANCHOR"
    if event_class == "eclipse":
        return "PERSONAL TURNING POINT"
    if event_class == "cazimi":
        return "PERSONAL CLARITY POINT"
    if opportunity:
        return "PERSONAL OPENING"
    if event_class == "station":
        return "PERSONAL PIVOT"
    if event_class == "ingress" and planet in {"Mercury", "Venus", "Mars"}:
        return "PERSONAL TRIGGER"
    return "PERSONAL HIT"


def _personal_contact_label(item) -> str:
    event_class = str(_personal_item_value(item, "event_class", "") or "")
    planet = str(_personal_item_value(item, "transit_planet", "") or "")
    aspect = str(_personal_item_value(item, "aspect", "") or "")
    target = str(_personal_item_value(item, "natal_target", "") or "")
    orb = float(_personal_item_value(item, "orb", 0.0) or 0.0)

    if event_class == "solar_anchor":
        subject = f"Solar anchor {planet}"
    elif event_class == "eclipse":
        subject = f"Eclipse {planet}"
    elif event_class == "station":
        subject = f"{planet} station"
    elif event_class == "ingress":
        subject = f"{planet} ingress"
    elif event_class == "cazimi":
        subject = f"Cazimi {planet}"
    else:
        subject = planet
    return f"{subject} {aspect} natal {target} · {orb:.2f}° orb"



def _render_personal_major_events(
    values,
    snapshot,
    timezone_name: str,
    product: str,
    *,
    limit: int = 6,
    prepared: tuple[list, dict[str, dict], dict | None] | None = None,
) -> None:
    if snapshot is None:
        return
    groups, voices, _generated = prepared or _personal_major_voice_data(
        values, snapshot, timezone_name, limit=limit
    )
    if not groups:
        return

    st.markdown("### Where the major sky hits your chart")
    st.caption(
        "One sky event appears once. If it touches several natal points, "
        "Luna shows the contacts together and interprets the combined pressure."
    )

    for index, group in enumerate(groups):
        first = group[0]
        badge = _personal_major_badge(first, group)
        voice = voices.get(f"personal:{index}")
        interpretation = str(voice["story"]) if voice else ""
        action = str(voice["your_move"]) if voice else ""
        headline = str(voice["headline"]) if voice else str(first.display_label)
        affirmation = (
            f'<p><strong>REMEMBER ·</strong> {escape(str(voice["affirmation"]))}</p>'
            if voice else ""
        )
        interpretation_html = f"<p>{escape(interpretation)}</p>" if interpretation else ""
        contacts = "".join(
            f'<li>{escape(_personal_contact_label(item))}</li>'
            for item in group
        )
        action_html = (
            f'<div class="timing-move"><div class="timing-move-label">Your move</div><p>{escape(action)}</p></div>'
            if action else ""
        )
        st.markdown(
            f"""<article class="timing-story personal-major-story">
<div class="timing-meta">{escape(_timing_date_label(first.event_date).upper())} · {escape(badge)}</div>
<h3>{escape(headline)}</h3>
{interpretation_html}
{affirmation}
<ul class="timing-scenarios">{contacts}</ul>
{action_html}
</article>""",
            unsafe_allow_html=True,
        )


def _personal_major_voice_data(
    values,
    snapshot,
    timezone_name: str,
    *,
    limit: int = 6,
) -> tuple[list, dict[str, dict], dict | None]:
    if snapshot is None:
        return [], {}, None
    activations = personalize_serialized_signals(
        values or [],
        snapshot,
        timezone_name,
        limit=max(limit * 3, 12),
    )
    groups = group_personal_activations(activations)[:limit]
    if not groups:
        return [], {}, None
    collection_facts = {
        "timezone": timezone_name,
        "items": [
            {
                "source_id": f"personal:{index}",
                "date": str(_personal_item_value(group[0], "event_date", "")),
                "display_label": str(_personal_item_value(group[0], "display_label", "")),
                "event_class": str(_personal_item_value(group[0], "event_class", "")),
                "contacts": [
                    {
                        "transiting_planet": str(_personal_item_value(item, "transit_planet", "")),
                        "aspect": str(_personal_item_value(item, "aspect", "")),
                        "natal_target": str(_personal_item_value(item, "natal_target", "")),
                        "orb": float(_personal_item_value(item, "orb", 0.0) or 0.0),
                        "house": _personal_item_value(item, "house", None),
                    }
                    for item in group
                ],
            }
            for index, group in enumerate(groups)
        ],
    }
    generated = _guided_luna_collection("personal_events", collection_facts)
    voices = {
        str(item["source_id"]): item for item in (generated or {}).get("items", [])
    }
    return groups, voices, generated

def _monthly_event_voice_collection(narrative, result, sign: str, timezone_name: str) -> dict[str, dict]:
    _generated, voices = _monthly_event_voice_data(narrative, result, sign, timezone_name)
    return voices


def _monthly_event_voice_data(narrative, result, sign: str, timezone_name: str) -> tuple[dict | None, dict[str, dict]]:
    facts = build_public_monthly_event_facts(narrative, result, sign, timezone_name)
    generated = _guided_luna_collection(
        "monthly_events",
        facts,
    )
    if not generated:
        return None, {}
    return generated, {str(item["source_id"]): item for item in generated["items"]}


def _render_monthly_reader_calendar_streamlit(
    narrative,
    result,
    *,
    sign: str,
    timezone_name: str,
    voice_items: dict[str, dict] | None = None,
) -> None:
    rows = build_monthly_reader_chronology(narrative, result)
    if not rows:
        return
    month_label = str(narrative.label).split()[0]
    st.markdown(f"## {month_label} — in order")
    st.caption(
        "Read the month in order. When more than one signal lands on the same day, Luna keeps them together."
    )
    voice_items = voice_items if voice_items is not None else _monthly_event_voice_collection(
        narrative, result, sign, timezone_name
    )
    for index, item in enumerate(rows):
        voice = voice_items.get(f"{item.get('date_label', index)}:{index}")
        if voice:
            body_html = (
                f"<p>{escape(str(voice['story']))}</p>"
                f"<p><strong>REMEMBER ·</strong> {escape(str(voice['affirmation']))}</p>"
            )
            headline = str(voice["headline"])
            move = str(voice["your_move"])
        else:
            body_html = ""
            headline = str(item.get("technical") or "Calculated date")
            move = ""
        technical = escape(str(item.get("technical") or ""))
        influence = escape(str(item.get("influence") or ""))
        influence_html = (
            f'<div class="timing-meta" style="margin:.3rem 0 .65rem;text-transform:none">Influence · {influence}</div>'
            if influence else ""
        )
        also_html = ""
        if item.get("also"):
            also_html = (
                '<div class="timing-move" style="margin-top:.8rem"><div class="timing-move-label">Also active</div>'
                + ''.join(f'<p>{escape(value)}</p>' for value in item["also"])
                + '</div>'
            )
        move_html = (
            '<div class="timing-move"><div class="timing-move-label">Your move</div>'
            f'<p>{escape(move)}</p></div>'
            if move else ""
        )
        st.markdown(
            f'''<article class="timing-story monthly-calendar-story">
<div class="timing-meta">{escape(item["date_label"])} · {escape(item["badge"])}</div>
<h3>{escape(headline)}</h3>
<p class="timing-transit-line">{technical}</p>
{influence_html}
<div class="timing-story-copy">{body_html}</div>
{also_html}
{move_html}
</article>''',
            unsafe_allow_html=True,
        )


def _render_monthly_transit_style_v3(narrative, result, *, sign: str, timezone_name: str, birth_date_value: date | None, snapshot=None) -> None:
    year, month, _ = monthly_period_from_result(result, narrative)
    _render_free_plain("monthly", date(year, month, 1), sign)
    with st.expander("Key dates", expanded=False):
        _render_monthly_reader_calendar_streamlit(
            narrative, result, sign=sign, timezone_name=timezone_name, voice_items={})
    events = _monthly_canonical_events(narrative, result)
    _monthly_chart_in_motion(snapshot, result, events, sign, include_legacy_interpretation=False)


def _render_monthly_result_actions(sign: str, year: int, month: int) -> None:
    """
    Reader controls for printing/saving the personalised report and sharing the public page.
    The public URL deliberately contains no birth data or session state.
    """
    title = f"{sign} {month_name[int(month)]} {int(year)} · Luna Convergence"
    safe_title = escape(title)
    monthly_share_url = "https://luna-convergence.streamlit.app/monthly"

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">KEEP OR SHARE YOUR READING</div>', unsafe_allow_html=True)

    components.html(
        f"""
        <div id="luna-result-actions" style="
            display:flex;flex-wrap:wrap;gap:10px;align-items:center;
            font-family:Arial,sans-serif;margin:0;padding:0 0 2px 0;">
          <button id="luna-print" type="button" style="
              min-height:44px;padding:10px 16px;border:1px solid #111;background:#111;color:#fff;
              font-size:13px;letter-spacing:.04em;text-transform:uppercase;cursor:pointer;">
            Print / Save PDF
          </button>
          <button id="luna-share" type="button" style="
              min-height:44px;padding:10px 16px;border:1px solid #111;background:#fff;color:#111;
              font-size:13px;letter-spacing:.04em;text-transform:uppercase;cursor:pointer;">
            Share page link
          </button>
          <span id="luna-action-status" style="font-size:12px;color:#666;min-width:160px;"></span>
        </div>

        <script>
        (() => {{
          const printBtn = document.getElementById("luna-print");
          const shareBtn = document.getElementById("luna-share");
          const status = document.getElementById("luna-action-status");

          function parentWindow() {{
            try {{ return window.parent; }} catch (e) {{ return window; }}
          }}

          function parentDocument() {{
            try {{ return window.parent.document; }} catch (e) {{ return null; }}
          }}

          function pageUrl() {{
            return "{monthly_share_url}";
          }}

          function openExpandersForPrint() {{
            const doc = parentDocument();
            if (!doc) return;
            const details = doc.querySelectorAll(
              '[data-testid="stExpander"] details, details[data-testid="stExpander"]'
            );
            details.forEach((node) => {{
              if (!node.open) {{
                node.dataset.lunaPrintOpened = "1";
                node.open = true;
              }}
            }});
          }}

          function restoreExpandersAfterPrint() {{
            const doc = parentDocument();
            if (!doc) return;
            doc.querySelectorAll('details[data-luna-print-opened="1"]').forEach((node) => {{
              node.open = false;
              delete node.dataset.lunaPrintOpened;
            }});
          }}

          try {{
            const parent = parentWindow();
            if (!parent.__lunaMonthlyPrintHooksInstalled) {{
              parent.__lunaMonthlyPrintHooksInstalled = true;
              parent.addEventListener("beforeprint", openExpandersForPrint);
              parent.addEventListener("afterprint", restoreExpandersAfterPrint);
            }}
          }} catch (e) {{}}

          printBtn.addEventListener("click", () => {{
            status.textContent = "Opening print dialogâ€¦";
            openExpandersForPrint();
            setTimeout(() => {{
              try {{ parentWindow().print(); }}
              catch (e) {{ window.print(); }}
              setTimeout(() => {{ status.textContent = ""; }}, 700);
            }}, 180);
          }});

          shareBtn.addEventListener("click", async () => {{
            const url = pageUrl();
            const payload = {{
              title: "{safe_title}",
              text: "Luna Convergence monthly astrology page. Personal birth details are not included in this link.",
              url
            }};

            if (navigator.share) {{
              try {{
                await navigator.share(payload);
                status.textContent = "Share sheet opened.";
                return;
              }} catch (e) {{
                if (e && e.name === "AbortError") {{
                  status.textContent = "";
                  return;
                }}
              }}
            }}

            try {{
              await navigator.clipboard.writeText(url);
              status.textContent = "Page link copied.";
            }} catch (e) {{
              window.prompt("Copy this Luna page link:", url);
              status.textContent = "Copy the link shown.";
            }}
          }});
        }})();
        </script>
        """,
        height=62,
        scrolling=False,
    )

    st.caption(
        "For a personalised copy, choose **Print / Save PDF**. On a phone, save the PDF and use your device's Share sheet "
        "to send the actual reading. **Share page link** shares only the public Monthly page — birth details and your session "
        "are deliberately not placed in the URL."
    )



@st.cache_data(show_spinner=False, ttl=2678400)
def _cached_public_monthly_report(
    sign: str,
    year: int,
    month: int,
    timezone_name: str,
    nearest_city: str,
):
    """Share one calculated sign/month result across visitors for up to 31 days."""
    return build_production_monthly_report(
        sign=sign,
        year=year,
        month=month,
        timezone_name=timezone_name,
        nearest_city=nearest_city,
        main_focus="General overview",
    )


def monthly_sign_page() -> None:
    """Fast free Monthly: current-month whole-sign forecast selected by Sun sign."""
    set_page_metadata(
        "Monthly Astrology | Luna Convergence",
        "Free monthly astrology by star sign with a connected story, key dates and whole-sign life areas.",
        "/monthly",
    )

    (
        sign,
        timezone_name,
        nearest_city,
        forecast_year,
        forecast_month,
        ready,
    ) = _free_monthly_profile()
    if not ready:
        return

    # The reader supplied this sign directly. It is the whole-sign House 1
    # reference for the free product; no natal precision is implied.
    st.session_state["monthly-calculated-sun-sign"] = sign
    st.session_state["free-monthly-sun-sign"] = sign
    st.session_state["landing-daily-sign-v3195"] = sign

    set_page_metadata(
        f"{sign} {month_name[forecast_month]} {forecast_year} Horoscope | Luna Convergence",
        f"Free {sign} {month_name[forecast_month]} {forecast_year} horoscope with a connected story, key dates and whole-sign life areas.",
        "/monthly",
    )

    try:
        with st.spinner(f"Opening {sign}'s {month_name[forecast_month]} forecastâ€¦"):
            narrative, result = _cached_public_monthly_report(
                sign,
                forecast_year,
                forecast_month,
                timezone_name,
                nearest_city,
            )
    except Exception as exc:
        st.error("Luna could not build this Monthly.")
        if EDITOR_PREVIEW_ENABLED:
            st.exception(exc)
        return

    _render_monthly_transit_style_v3(
        narrative,
        result,
        sign=sign,
        timezone_name=timezone_name,
        birth_date_value=None,
        snapshot=None,
    )

    _render_monthly_result_actions(sign, forecast_year, forecast_month)

    st.markdown("## Something specific on your mind?")
    st.markdown(
        "Daily, Weekly and Monthly by sign are free. Personal Monthly and Your Year Ahead use your natal chart for exact timing."
    )
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown(
            f"**Your Personal Month · {MONTHLY_PRICE}**<br>"
            "Add your birth date, time and place for exact natal contacts and personal timing.",
            unsafe_allow_html=True,
        )
        st.markdown('<a class="lean-monthly-link" href="/reports">Personalise this month →</a>', unsafe_allow_html=True)
    with c2:
        st.markdown(
            f"**Your Year Ahead · {YEARLY_PRICE}**<br>"
            "Personal Transits & Timing — see when your strongest natal activations build, peak, change and release.",
            unsafe_allow_html=True,
        )

def make_monthly_page(sign: str):
    def page() -> None:
        _legacy_monthly_redirect(sign)

    page.__name__ = f"{sign_slug(sign).replace('-', '_')}_legacy_monthly_redirect"
    return page


def birthday_card_page() -> None:
    set_page_metadata(
        "Personalised Astrology Birthday Card | Luna Convergence",
        "Create a personalised Luna birthday card from the recipient's calculated Sun and Moon signs, then download it for Instagram or print.",
        "/birthday-card",
    )
    st.markdown('<section class="natal-shell">', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Luna birthday sky · two keepsake designs</div>', unsafe_allow_html=True)
    st.markdown('<div class="editorial-title">Give them<br>their sky.</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="natal-intro">Enter the recipientâ€™s full birth date so Luna can calculate the card accurately. '
        'The birth year remains private: only the day and month appear on the finished card.</div>',
        unsafe_allow_html=True,
    )

    admin_unlocked = _admin_access_panel("birthday-card")
    if not admin_unlocked:
        # Never let an owner preview survive after the private session is
        # locked; public downloads must come only from verified payment.
        st.session_state.pop("birthday-card-result-v1", None)
        st.markdown(f"### Personalised Birthday Card · {BIRTHDAY_PRICE}")
        st.caption("One payment includes the finished 1080 × 1920 PNG and matching printable PDF.")

    with st.container(border=True):
        delivery_email = ""
        if not admin_unlocked:
            delivery_email = st.text_input(
                "Delivery email",
                placeholder="you@example.com",
                help="Stripe uses this email for your receipt. Luna also emails your private return link and PDF.",
            )
        name = st.text_input(
            "Recipientâ€™s first name",
            placeholder="Fiona",
            max_chars=40,
        )
        birth_date_value = st.date_input(
            "Full date of birth",
            value=None,
            min_value=date(1900, 1, 1),
            max_value=browser_local_date(),
            help="The year is used for the astrology calculation but is never printed on the card.",
        )
        birth_timezone = st.selectbox(
            "Birth timezone",
            TIMEZONES,
            index=timezone_select_index(),
            help="This lets Luna check the Moon across the correct local birth date.",
        )
        st.markdown("**Choose the finished look**")
        preview_dir = Path(__file__).resolve().parent / "assets" / "birthday-previews"
        preview_columns = st.columns(2, gap="small")
        with preview_columns[0]:
            st.image(
                str(preview_dir / "lara-midnight-painted.png"),
                caption="Midnight Painted",
                use_container_width=True,
            )
        with preview_columns[1]:
            st.image(
                str(preview_dir / "lara-ivory-letter.png"),
                caption="Ivory Letter",
                use_container_width=True,
            )
        st.caption(
            "Style samples only. Your finished card uses the recipientâ€™s calculated birth sky and Lunaâ€™s unique poem."
        )
        card_style = st.radio(
            "Card style",
            ("Midnight Painted", "Ivory Letter"),
            horizontal=True,
            help="Midnight Painted uses warm-white type over hand-painted blue paper. Ivory Letter uses dark type over tactile ivory paper.",
            key="birthday-card-style-v1",
        )
        card_theme = {
            "Midnight Painted": "painted_blue",
            "Ivory Letter": "ivory_paper",
        }[card_style]
        time_known = st.checkbox(
            "I know the birth time",
            value=False,
            help="A known time makes the Moon position more precise. It is not printed on the card.",
        )
        birth_time_value = None
        if time_known:
            birth_time_value = st.time_input(
                "Birth time",
                value=datetime.strptime("12:00", "%H:%M").time(),
            )
        custom_poem = st.text_area(
            "Optional personal message",
            placeholder="Leave blank and Luna will write a unique poem from the calculated birth sky.",
            help="If supplied, this message replaces Lunaâ€™s generated poem. Long messages are automatically resized to fit.",
            max_chars=240,
        )
        submitted = st.button(
            (
                "Create owner birthday card — no payment"
                if admin_unlocked
                else f"Prepare secure checkout — {BIRTHDAY_PRICE}"
            ),
            use_container_width=True,
            key="birthday-card-submit-v1",
            type="primary",
        )

    if submitted:
        st.session_state.pop("birthday-card-result-v1", None)
        st.session_state.pop("birthday-card-order-v1", None)
        if not str(name or "").strip():
            st.error("Enter the recipientâ€™s first name.")
        elif birth_date_value is None:
            st.error("Choose the recipientâ€™s full date of birth.")
        elif not admin_unlocked and not valid_email(delivery_email):
            st.error("Enter a valid delivery email before continuing to payment.")
        else:
            try:
                snapshot = build_natal_snapshot(
                    birth_date=birth_date_value,
                    birth_time_known=time_known,
                    birth_time=birth_time_value,
                    timezone_name=birth_timezone,
                )
                clean_custom_poem = " ".join(str(custom_poem or "").split()).strip()
                if clean_custom_poem:
                    poem = clean_custom_poem
                else:
                    if not _luna_voice_ready():
                        raise BirthdayPoemError(
                            "Luna's voice provider is not configured for live Birthday Card generation."
                        )
                    poem_facts = build_birthday_poem_facts(
                        snapshot=snapshot,
                        variation_key=secrets.token_hex(8),
                    )
                    with st.spinner("Luna is writing from the calculated birth sky. Keep this page openâ€¦"):
                        poem = _cached_birthday_poem(
                            json.dumps(poem_facts, ensure_ascii=False, sort_keys=True),
                            LUNA_VOICE_BASE_URL,
                            LUNA_VOICE_MODEL,
                            LUNA_VOICE_API_KEY,
                        )
                card = build_birthday_card(
                    recipient_name=name,
                    birth_date=birth_date_value,
                    snapshot=snapshot,
                    poem=poem,
                    date_only_calculations=(
                        birth_date_luminary_calculations(birth_date_value, birth_timezone)
                        if not time_known else None
                    ),
                    theme=card_theme,
                )
                if admin_unlocked:
                    st.session_state["birthday-card-result-v1"] = {
                        "card": card,
                        "png": render_birthday_card_png(card),
                        "pdf": render_birthday_card_pdf(card),
                    }
                    track_event(
                        "birthday_card_owner_generated",
                        {
                            "birth_time_known": bool(time_known),
                            "birth_year_hidden": True,
                            "card_theme": card_theme,
                        },
                    )
                else:
                    reference = build_order_reference(
                        "BIRTHDAY",
                        card.sun_sign,
                        birth_date_value.isoformat(),
                        birth_timezone,
                        _order_token("birthday-card", "BIRTHDAY"),
                    )
                    order = {
                        "product_code": "BIRTHDAY",
                        "report_name": "Personalised Astrology Birthday Card",
                        "email": delivery_email.strip(),
                        "sign": card.sun_sign,
                        "period": card.date_label.title(),
                        "period_code": birth_date_value.isoformat(),
                        "timezone": birth_timezone,
                        "reference": reference,
                        "birthday_name": card.recipient_name,
                        "birthday_date": birth_date_value.isoformat(),
                        "birthday_time_known": "true" if time_known else "false",
                        "birthday_time": (
                            birth_time_value.strftime("%H:%M")
                            if time_known and birth_time_value else ""
                        ),
                        "birthday_theme": card_theme,
                        "birthday_poem": card.poem,
                    }
                    order["checkout_url"] = _create_instant_checkout(order, "BIRTHDAY")
                    st.session_state["birthday-card-order-v1"] = order
                    track_event(
                        "birthday_card_order_prepared",
                        {
                            "birth_time_known": bool(time_known),
                            "card_theme": card_theme,
                            "order_reference": reference,
                            "value": 2.40,
                            "currency": "AUD",
                        },
                    )
            except BirthdayPoemError as exc:
                _record_voice_error("birthday_card", exc)
                st.error(
                    "Luna could not write a verified birthday poem, so no card was created. Please try again shortly."
                )
            except Exception as exc:
                st.error("Luna could not create this card. Check the birth details and try again.")
                if EDITOR_PREVIEW_ENABLED:
                    st.exception(exc)

    prepared_order = st.session_state.get("birthday-card-order-v1")
    if prepared_order and not admin_unlocked:
        st.success("Your personalised card is prepared. Complete payment to unlock both files.")
        st.markdown(
            f"**For {escape(prepared_order['birthday_name'])} · {escape(prepared_order['period'])}**  "
            f"  \n{escape(card_style)} · Order `{escape(prepared_order['reference'])}`"
        )
        payment_button(
            f"Continue to secure payment — {BIRTHDAY_PRICE}",
            prepared_order["checkout_url"],
            "birthday-card-payment-disabled",
            "birthday_card_checkout_click",
            {
                "order_reference": prepared_order["reference"],
                "value": 2.40,
                "currency": "AUD",
            },
        )
        st.markdown(
            '<div class="checkout-note">Stripe opens securely in a new tab. After payment, '
            "Luna returns you to the finished card with both downloads and emails the PDF plus "
            "your private return link.</div>",
            unsafe_allow_html=True,
        )

    result = st.session_state.get("birthday-card-result-v1")
    if not result:
        st.caption("Choose a keepsake style. The selected 9:16 design becomes an Instagram Reel/Story PNG and a matching PDF.")
        st.markdown('</section>', unsafe_allow_html=True)
        return

    card = result["card"]
    st.markdown("## Your Luna Birthday Card")
    st.image(result["png"], use_container_width=True)
    if len(card.poem) > 240:
        st.warning(
            "The message fits, but it is long for an Instagram card. Shortening it will make the type larger and easier to read. The download remains available."
        )
    if not card.birth_time_known and "/" in card.sun_sign:
        st.info(
            f"The Sun changed signs on this birth date. With no birth time supplied, Luna has shown both possible Sun signs: {card.sun_sign}."
        )
    if not card.birth_time_known and "/" in card.moon_label:
        st.info(
            f"The Moon changed signs on this birth date. With no birth time supplied, Luna has shown both possible Moon signs: {card.moon_label}."
        )
    elif not card.birth_time_known:
        st.caption("Birth time was not supplied. The Moon remained in the same sign across this date, so the card can name it safely.")

    download_columns = st.columns(2, gap="medium")
    with download_columns[0]:
        st.download_button(
            "Download Instagram Reel/Story PNG",
            data=result["png"],
            file_name=birthday_card_filename(card, "png"),
            mime="image/png",
            use_container_width=True,
        )
    with download_columns[1]:
        st.download_button(
            "Download printable PDF",
            data=result["pdf"],
            file_name=birthday_card_filename(card, "pdf"),
            mime="application/pdf",
            use_container_width=True,
        )
    st.caption(
        "PNG · 1080 × 1920 px for Instagram Reels and Stories. PDF · one matching 9:16 page. "
        "Both downloads use the identical narrow Luna composition."
    )
    st.markdown('</section>', unsafe_allow_html=True)


def _render_natal_signature_grid(snapshot, heading: str = "Your natal signature") -> None:
    """Render the clean Snapshot signature grid for every personal Luna product."""
    by_planet = {item.planet: item for item in snapshot.positions}
    moon_value = by_planet["Moon"].sign
    if not bool(getattr(snapshot, "birth_time_known", False)) and len(snapshot.moon_uncertain) > 1:
        moon_value = " / ".join(snapshot.moon_uncertain)
    st.markdown(f"## {heading}")
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


def _snapshot_sign_from_longitude(longitude: float) -> str:
    return SIGNS[int((float(longitude) % 360.0) // 30.0)]


def _snapshot_dominance_from_positions(positions) -> tuple[str, str]:
    element_by_sign = {
        "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
        "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
        "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
        "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
    }
    mode_by_sign = {
        "Aries": "Cardinal", "Cancer": "Cardinal", "Libra": "Cardinal", "Capricorn": "Cardinal",
        "Taurus": "Fixed", "Leo": "Fixed", "Scorpio": "Fixed", "Aquarius": "Fixed",
        "Gemini": "Mutable", "Virgo": "Mutable", "Sagittarius": "Mutable", "Pisces": "Mutable",
    }
    weights = {
        "Sun": 2.0, "Moon": 2.0, "Mercury": 1.4, "Venus": 1.4, "Mars": 1.4,
        "Jupiter": 1.0, "Saturn": 1.0, "Uranus": 0.7, "Neptune": 0.7, "Pluto": 0.7,
    }
    elements = {key: 0.0 for key in ("Fire", "Earth", "Air", "Water")}
    modes = {key: 0.0 for key in ("Cardinal", "Fixed", "Mutable")}
    for item in positions:
        weight = weights.get(str(item.planet), 1.0)
        elements[element_by_sign[item.sign]] += weight
        modes[mode_by_sign[item.sign]] += weight
    return max(elements, key=elements.get), max(modes, key=modes.get)


def _snapshot_from_encoded_natal_profile(profile_value: str, *, timezone_name: str = "UTC"):
    """Restore the derived natal geometry stored for paid reports."""
    profile = decode_natal_profile(profile_value)
    if not profile:
        return None

    longitudes = list(profile.get("p") or [])
    houses = list(profile.get("h") or [])
    positions = []
    for index, name in enumerate(NATAL_PROFILE_ORDER):
        longitude = float(longitudes[index]) % 360.0
        house_value = None
        if index < len(houses):
            try:
                parsed_house = int(houses[index] or 0)
            except (TypeError, ValueError):
                parsed_house = 0
            house_value = parsed_house or None
        positions.append(
            NatalPosition(
                planet=name,
                longitude=longitude,
                sign=_snapshot_sign_from_longitude(longitude),
                degree=longitude % 30.0,
                retrograde=False,
                house=house_value,
                speed=0.0,
            )
        )

    angles = list(profile.get("a") or [])
    ascendant = None
    midheaven = None
    if len(angles) >= 1 and angles[0] is not None:
        longitude = float(angles[0]) % 360.0
        ascendant = NatalPosition(
            "Ascendant", longitude, _snapshot_sign_from_longitude(longitude),
            longitude % 30.0, False, 1, 0.0,
        )
    if len(angles) >= 2 and angles[1] is not None:
        longitude = float(angles[1]) % 360.0
        midheaven = NatalPosition(
            "Midheaven", longitude, _snapshot_sign_from_longitude(longitude),
            longitude % 30.0, False, None, 0.0,
        )

    aspects = tuple(detect_natal_aspects(positions))
    dominant_element, dominant_modality = _snapshot_dominance_from_positions(positions)
    moon = next((item for item in positions if item.planet == "Moon"), None)
    return NatalSnapshot(
        birth_date=date(1900, 1, 1),
        birth_time_known=bool(profile.get("t")),
        timezone_name=timezone_name,
        location_name=None,
        positions=tuple(positions),
        aspects=aspects,
        ascendant=ascendant,
        midheaven=midheaven,
        sun_uncertain=(),
        moon_uncertain=(moon.sign,) if moon is not None else (),
        themes=(),
        signatures=(),
        concentration_theme={},
        dominant_element=dominant_element,
        dominant_modality=dominant_modality,
    )


def _snapshot_natal_facts(snapshot) -> dict:
    return {
        "birth_time_precision": "known" if bool(getattr(snapshot, "birth_time_known", False)) else "unknown",
        "dominant_element": str(getattr(snapshot, "dominant_element", "")),
        "dominant_modality": str(getattr(snapshot, "dominant_modality", "")),
        "moon_uncertain_between": list(getattr(snapshot, "moon_uncertain", ()) or ()),
        "positions": [
            {
                "planet": item.planet,
                "sign": item.sign,
                "degree": round(float(item.degree), 2),
                "house": item.house,
            }
            for item in (getattr(snapshot, "positions", ()) or ())
        ],
        "ascendant": snapshot.ascendant.sign if getattr(snapshot, "ascendant", None) else None,
        "midheaven": snapshot.midheaven.sign if getattr(snapshot, "midheaven", None) else None,
        "aspects": [
            {
                "planet_1": item.planet1,
                "aspect": item.name,
                "planet_2": item.planet2,
                "orb": round(float(item.orb), 2),
                "strength": round(float(item.strength), 3),
            }
            for item in list(getattr(snapshot, "aspects", ()) or ())[:12]
        ],
    }


def _snapshot_natal_fallback_story(snapshot) -> dict:
    """Complete deterministic fallback so Read the pattern never publishes a fragment."""
    positions = {item.planet: item for item in (getattr(snapshot, "positions", ()) or ())}
    sun = positions.get("Sun")
    moon = positions.get("Moon")
    aspects = list(getattr(snapshot, "aspects", ()) or ())
    strongest = aspects[0] if aspects else None

    if strongest is not None:
        headline = f"{strongest.planet1} and {strongest.planet2} set the strongest recurring pattern"
        opening = (
            f"The tightest calculated pattern is {strongest.planet1} {strongest.name} {strongest.planet2}. "
            "Treat it as a recurring tension or capacity to work with, not a fixed verdict about who you are."
        )
        story = [
            (
                f"Your Sun is in {sun.sign if sun else 'its calculated sign'} and your Moon is in "
                f"{moon.sign if moon else 'its calculated sign'}. The chart therefore begins with the relationship "
                "between conscious direction and instinctive response, then shows where the strongest aspect keeps bringing that relationship back into view."
            ),
            (
                f"The chart is weighted toward {getattr(snapshot, 'dominant_element', 'a dominant element')} "
                f"and {getattr(snapshot, 'dominant_modality', 'a dominant mode')}. Use that as context rather than a label: "
                "the useful question is how consistently you can choose your response when the familiar pattern appears."
            ),
        ]
    else:
        headline = "Your chart has a recognisable baseline"
        opening = "The calculated planetary positions describe a recurring baseline rather than a fixed personality verdict."
        story = [
            f"Your Sun is in {sun.sign if sun else 'its calculated sign'} and your Moon is in {moon.sign if moon else 'its calculated sign'}. Read them together rather than as separate labels.",
            f"The chart is weighted toward {getattr(snapshot, 'dominant_element', 'its dominant element')} and {getattr(snapshot, 'dominant_modality', 'its dominant mode')}. Notice how that pattern shows up in repeated choices, not just in descriptions that sound familiar.",
        ]

    return {
        "headline": headline,
        "opening": opening,
        "story": story,
        "affirmation": "A recurring pattern becomes more useful once you can recognise it without automatically obeying it.",
        # Advice is deliberately left to Luna's voice layer. If voice is
        # unavailable, show the calculated interpretation without inventing a
        # deterministic Your Move.
        "your_move": "",
    }


@st.cache_data(show_spinner=False, ttl=86400)
def _cached_signature_move_voice(
    facts_json: str,
    base_url: str,
    model: str,
    _api_key: str,
) -> dict:
    facts = json.loads(facts_json)
    items = list(facts.get("items") or [])
    item_count = len(items)
    if not item_count:
        return {"moves": []}
    prompt = (
        "You are Luna. The following natal signatures are closed calculated interpretations. "
        "Do not recalculate or invent astrology. Write only the strategic YOUR MOVE for each signature, in the supplied order. "
        "Do not paraphrase the Remember/strength/watch material. The move must change the reader's position. "
        "Be Machiavellian in the strategic sense, never manipulative: preserve optionality, reveal information or reciprocity before commitment, "
        "reduce exposure, use leverage only where it exists, and let the other side or the situation show its hand before spending more. "
        "When direct force wastes energy, behave like water: redirect, narrow, wait, sequence or move around resistance. "
        "Choose the best path supported by the supplied signature. One concrete imperative sentence, roughly twelve to twenty-eight words. "
        "No deception, coercion, exploitation, diagnosis, guarantees or mystical padding. Return JSON only.\n\n"
        "CALCULATED SIGNATURES:\n" + json.dumps(facts, ensure_ascii=False, indent=2, default=str)
    )
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "luna_signature_moves",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "moves": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source_id": {"type": "string"},
                                "your_move": {"type": "string"},
                            },
                            "required": ["source_id", "your_move"],
                            "additionalProperties": False,
                        },
                        "minItems": item_count,
                        "maxItems": item_count,
                    }
                },
                "required": ["moves"],
                "additionalProperties": False,
            },
        },
    }
    return generate_openai_compatible_json(
        prompt,
        base_url=base_url,
        model=model,
        api_key=_api_key,
        timeout=25,
        max_tokens=900,
        response_format=response_format,
        rate_limit_retries=0,
    )


def _strategic_signature_moves(snapshot) -> dict[str, str]:
    """One bounded voice request for all natal-signature moves; no hard-coded move fallback."""
    signatures = list(getattr(snapshot, "signatures", ()) or ())
    if not signatures or not _luna_voice_ready():
        return {}
    facts = {
        "items": [
            {
                "source_id": f"signature:{index}",
                "title": str(getattr(signature, "title", "") or ""),
                "interpretation": str(getattr(signature, "text", "") or ""),
                "strength": str(getattr(signature, "strength", "") or ""),
                "watch": str(getattr(signature, "watch", "") or ""),
                "question": str(getattr(signature, "question", "") or ""),
                "evidence": str(getattr(signature, "evidence", "") or ""),
            }
            for index, signature in enumerate(signatures[:6])
        ]
    }
    try:
        generated = _cached_signature_move_voice(
            json.dumps(facts, ensure_ascii=False, sort_keys=True, default=str),
            LUNA_VOICE_BASE_URL,
            LUNA_VOICE_MODEL,
            LUNA_VOICE_API_KEY,
        )
    except Exception as exc:
        _record_voice_error("natal_signature_moves", exc)
        return {}
    expected = {item["source_id"]: item for item in facts["items"]}
    output: dict[str, str] = {}
    for item in list((generated or {}).get("moves") or []):
        if not isinstance(item, dict):
            continue
        source_id = str(item.get("source_id") or "")
        move = " ".join(str(item.get("your_move") or "").split())
        source = expected.get(source_id)
        if not source:
            continue
        valid, _reason = _strategic_move_quality(
            move,
            remember=f"{source.get('strength', '')} {source.get('watch', '')}",
            story=source.get("interpretation", ""),
        )
        if valid:
            output[source_id] = move
    return output


def _render_snapshot_natal_evidence(snapshot) -> None:
    """Render natal calculation evidence without creating another expander."""
    if snapshot is None:
        return
    reconstructed = getattr(snapshot, "birth_date", None) == date(1900, 1, 1)
    rows = [
        {
            "Point": item.planet,
            "Position": (
                f"{int(item.degree)}°{int(round((float(item.degree) - int(item.degree)) * 60)):02d}′ {item.sign}"
                if reconstructed else item.label()
            ),
            "House": item.house if item.house is not None else "—",
        }
        for item in (getattr(snapshot, "positions", ()) or ())
    ]
    if rows:
        st.markdown("**Natal positions**")
        st.dataframe(rows, use_container_width=True, hide_index=True)
    if getattr(snapshot, "aspects", None):
        st.markdown("**Strongest natal aspects**")
        for aspect in list(snapshot.aspects)[:10]:
            st.markdown(f"- {aspect.planet1} {aspect.name} {aspect.planet2} · {aspect.orb:.2f}° orb")


def _render_snapshot_natal_core(
    snapshot,
    *,
    precision_note: str = "",
    birth_confirmation_html: str = "",
    evidence_label: str = "Why Luna sees this · chart evidence",
    show_evidence: bool = True,
    use_live_voice: bool = True,
    use_live_signature_moves: bool = True,
) -> None:
    """Canonical Snapshot body shared by free Natal and both paid personal reports."""
    if snapshot is None:
        return

    _render_natal_signature_grid(snapshot)
    # Paid Monthly already has one expensive, subject-aware voice pass below.
    # Re-running a separate natal LLM before the month adds latency without
    # improving the monthly story, so callers can use the deterministic natal
    # interpretation here and reserve Luna's live voice for Read the month.
    guided_natal = (
        _guided_luna_copy("natal", _snapshot_natal_facts(snapshot))
        if use_live_voice
        else None
    )
    st.markdown("## Read the pattern")
    _render_guided_luna_story(
        guided_natal or _snapshot_natal_fallback_story(snapshot),
        "Luna reads the whole chart",
    )

    if birth_confirmation_html:
        st.markdown(birth_confirmation_html, unsafe_allow_html=True)

    st.markdown(natal_wheel_svg(snapshot, size=760), unsafe_allow_html=True)
    if precision_note:
        st.caption(precision_note)
    elif bool(getattr(snapshot, "birth_time_known", False)) and getattr(snapshot, "ascendant", None) is not None:
        st.caption("Tropical geocentric positions · Whole-sign houses · Swiss Ephemeris")
    else:
        st.caption("Birth time or location precision is limited; Luna leaves unavailable angles or houses out rather than inventing them.")

    # The strongest signatures are deterministic natal-engine output. Do not
    # block the rest of a report on a second multi-item LLM request here.
    signatures = list(getattr(snapshot, "signatures", ()) or ())
    if not signatures:
        signatures = list(_build_signatures(list(getattr(snapshot, "aspects", ()) or ()), limit=6))
    if signatures:
        st.markdown("## Your strengths")
        st.caption("The strongest capacities in your natal pattern when you use them deliberately. The calculation evidence stays available in Why Luna sees this.")
        signature_moves = (
            _strategic_signature_moves(snapshot)
            if use_live_signature_moves
            else {}
        )
        for index, signature in enumerate(signatures[:6]):
            strength = str(getattr(signature, "strength", "") or "").strip()
            watch = str(getattr(signature, "watch", "") or "").strip()
            remember_bits = []
            if strength:
                remember_bits.append(strength)
            if watch:
                watch_lower = watch[:1].lower() + watch[1:] if len(watch) > 1 else watch.lower()
                remember_bits.append(f"Watch for {watch_lower}")
            remember = " ".join(remember_bits)
            move = str(signature_moves.get(f"signature:{index}") or "").strip()
            move_html = (
                f'<div><span>Your move</span>{escape(move)}</div>'
                if move else ""
            )
            meta_class = "natal-signature-meta" if move else "natal-signature-meta natal-signature-meta-single"
            html = (
                '<div class="natal-signature-reading">'
                f'<div class="natal-evidence">{escape(str(getattr(signature, "evidence", "Calculated natal aspect") or "Calculated natal aspect"))}</div>'
                f'<h3>{escape(str(getattr(signature, "title", "Natal signature") or "Natal signature"))}</h3>'
                f'<p>{escape(str(getattr(signature, "text", "") or ""))}</p>'
                f'<div class="{meta_class}">'
                f'<div><span>Remember</span>{escape(remember)}</div>'
                f'{move_html}'
                '</div></div>'
            )
            st.markdown(html, unsafe_allow_html=True)

    if show_evidence:
        with _luna_evidence_panel(evidence_label):
            _render_snapshot_natal_evidence(snapshot)



def _render_paid_natal_signature_summary(result: dict) -> None:
    """Reuse the Snapshot signature-grid treatment for paid personal reports."""
    summary = str(result.get("natal_summary") or "").strip()
    precision = str(result.get("natal_precision") or "").strip()
    items: list[tuple[str, str]] = []
    for bit in (part.strip() for part in summary.split("·") if part.strip()):
        if " " not in bit:
            continue
        label, value = bit.split(" ", 1)
        label = label.strip()
        value = value.strip()
        if label and value:
            items.append((label, value))
    if precision:
        items.append(("Precision", precision))
    if not items:
        return
    st.markdown("## Your natal signature")
    signature_html = "".join(
        f'<div><span>{escape(label)}</span><strong>{escape(value)}</strong></div>'
        for label, value in items
    )
    st.markdown(
        f'<div class="natal-signature">{signature_html}</div>',
        unsafe_allow_html=True,
    )


def _snapshot_monthly_story(narrative) -> dict:
    """Translate the existing Monthly narrative into the shared Luna story renderer."""
    story = [str(item).strip() for item in (getattr(narrative, "luna_says", ()) or ()) if str(item).strip()]
    if not story:
        central = str(getattr(narrative, "central_storyline", "") or "").strip()
        if central:
            story = [central]
    action_plan = [str(item).strip() for item in (getattr(narrative, "action_plan", ()) or ()) if str(item).strip()]
    return {
        "headline": str(getattr(narrative, "headline", "") or getattr(narrative, "hook_headline", "") or "Your month in motion"),
        "opening": str(getattr(narrative, "subtitle", "") or getattr(narrative, "central_storyline", "") or ""),
        "story": story,
        "affirmation": str(getattr(narrative, "validation_rule", "") or getattr(narrative, "agency_rule", "") or ""),
        # Strategic advice is a Luna voice responsibility. If live voice is
        # unavailable, keep the calculated story but do not fabricate a move.
        "your_move": "",
    }


def _monthly_required_story_anchors(narrative, result: dict) -> list[dict]:
    """Return structural monthly events that must be named in Read the month."""
    anchors: list[dict] = []
    seen: set[str] = set()

    def add(title: object, date_label: object = "", paragraph: object = "") -> None:
        clean_title = " ".join(str(title or "").split())
        if not clean_title:
            return
        lowered = clean_title.lower()
        if not any(token in lowered for token in ("retrograde", "station", "eclipse")):
            return
        key = re.sub(r"[^a-z0-9]+", " ", lowered).strip()
        if not key or key in seen:
            return
        seen.add(key)
        anchors.append({
            "title": clean_title,
            "date_label": " ".join(str(date_label or "").split()),
            "paragraph": " ".join(str(paragraph or "").split()),
        })

    for chapter in list(getattr(narrative, "chapters", ()) or ()):
        title = str(getattr(chapter, "title", "") or getattr(chapter, "hook", "") or "")
        date_label = str(getattr(chapter, "date_range", "") or getattr(chapter, "label", "") or "")
        paragraphs = [
            " ".join(str(item or "").split())
            for item in (getattr(chapter, "paragraphs", ()) or ())
            if str(item or "").strip()
        ]
        add(title, date_label, paragraphs[0] if paragraphs else "")

    for item in list(result.get("major_sky_events") or []) + list(result.get("major_transitions") or []):
        if not isinstance(item, dict):
            continue
        title = item.get("display_label") or item.get("technical_label") or item.get("title")
        date_label = item.get("event_date") or item.get("date") or ""
        add(title, date_label, "")

    return anchors[:4]


def _monthly_copy_with_required_anchors(copy: dict, narrative, result: dict) -> dict:
    """Guarantee defining stations/eclipses are named in the top Monthly story."""
    if not isinstance(copy, dict):
        copy = {}
    merged = dict(copy)
    story = merged.get("story") or []
    if isinstance(story, str):
        story = [story]
    elif not isinstance(story, (list, tuple)):
        story = [str(story)] if story else []
    story = [" ".join(str(item or "").split()) for item in story if str(item or "").strip()]

    combined = " ".join(
        [str(merged.get("headline") or ""), str(merged.get("opening") or ""), *story]
    ).lower()
    additions: list[str] = []
    for anchor in _monthly_required_story_anchors(narrative, result):
        title = anchor["title"]
        tokens = [token for token in re.findall(r"[a-z]+", title.lower()) if len(token) > 3]
        # Require the defining planet/event words to appear, not merely a vague synonym.
        present = bool(tokens) and all(token in combined for token in tokens[:3])
        if present:
            continue
        date_label = anchor.get("date_label") or ""
        paragraph = anchor.get("paragraph") or ""
        lead = title + (f" · {date_label}" if date_label else "")
        additions.append(lead + (f". {paragraph}" if paragraph else "."))
        combined += " " + title.lower()

    if additions:
        story = additions + story
    merged["story"] = story
    return merged




def _serialize_paid_monthly_snapshot(snapshot) -> dict:
    """Readable natal evidence for the paid Monthly voice; never raw birth details."""
    if snapshot is None:
        return {}
    return {
        "positions": [
            {
                "planet": str(getattr(item, "planet", "")),
                "sign": str(getattr(item, "sign", "")),
                "degree": round(float(getattr(item, "degree", 0.0) or 0.0), 3),
                "house": getattr(item, "house", None),
                "retrograde": bool(getattr(item, "retrograde", False)),
            }
            for item in (getattr(snapshot, "positions", ()) or ())
        ],
        "aspects": [
            {
                "planet_1": str(getattr(item, "planet1", "")),
                "aspect": str(getattr(item, "name", "")),
                "planet_2": str(getattr(item, "planet2", "")),
                "orb": round(float(getattr(item, "orb", 0.0) or 0.0), 3),
                "strength": round(float(getattr(item, "strength", 0.0) or 0.0), 3),
            }
            for item in (getattr(snapshot, "aspects", ()) or ())
        ],
        "strengths": [
            {
                "title": str(getattr(item, "title", "")),
                "interpretation": str(getattr(item, "text", "")),
                "strength": str(getattr(item, "strength", "")),
                "watch": str(getattr(item, "watch", "")),
                "evidence": str(getattr(item, "evidence", "")),
            }
            for item in (getattr(snapshot, "signatures", ()) or ())
        ],
        "dominant_element": str(getattr(snapshot, "dominant_element", "") or ""),
        "dominant_modality": str(getattr(snapshot, "dominant_modality", "") or ""),
        "birth_time_known": bool(getattr(snapshot, "birth_time_known", False)),
    }


def _paid_monthly_voice_facts(narrative, result: dict, snapshot=None) -> dict:
    """Load the reusable sign/month base, then attach this customer's Natal Player."""
    # Runtime only needs a light deterministic overlay. The expensive shared
    # month background (Free Monthly arc + 31 Daily grounded briefs) belongs in
    # the pre-generated GitHub base and must not be rebuilt for each customer.
    live_base = monthly_calculation_base(
        narrative,
        result,
        required_story_anchors=monthly_required_story_anchors(narrative, result),
        include_story_background=False,
    )

    stored_base = None
    start_value = str(result.get("start") or "")
    try:
        start_date = date.fromisoformat(start_value[:10])
    except ValueError:
        start_date = None
    timezone_name = str(result.get("timezone_name") or DEFAULT_TIMEZONE)
    sign = str(result.get("sign") or "")
    if start_date is not None and sign:
        stored_base = load_monthly_calculation_base(
            sign,
            start_date.year,
            start_date.month,
            timezone_name,
        )

    # The stored file is the canonical reusable sign/month skeleton. The live
    # deterministic result may contain reader-specific focus/city refinements;
    # overlay only those fields without replacing the canonical sky chronology.
    base = stored_base or live_base
    if stored_base:
        base = json.loads(json.dumps(stored_base, ensure_ascii=False, default=str))
        shared = dict(base.get("shared_sky") or {})
        live_shared = dict(live_base.get("shared_sky") or {})
        for key in (
            "nearest_city", "solar_convergence", "monthly_arc",
            "monthly_trajectory", "monthly_decision", "key_dates",
        ):
            if key in live_shared:
                shared[key] = live_shared[key]
        # Refresh only missing derived writing views. The canonical stored sky
        # remains the source; these views are deterministic projections of it.
        if not shared.get("daily_briefs"):
            shared["daily_briefs"] = live_shared.get("daily_briefs") or []
        if not shared.get("transit_threads"):
            shared["transit_threads"] = live_shared.get("transit_threads") or []
        if not shared.get("daily_story_ledger"):
            shared["daily_story_ledger"] = live_shared.get("daily_story_ledger") or []
        if not shared.get("story_skeleton"):
            shared["story_skeleton"] = live_shared.get("story_skeleton") or []
        base["shared_sky"] = shared

    reader_context = {
        "main_focus": str(result.get("main_focus") or getattr(narrative, "main_focus", "") or "General overview"),
        "personal_question": str(getattr(narrative, "personal_question", "") or ""),
        "nearest_city": str(result.get("nearest_city") or ""),
        "timezone": timezone_name,
    }
    return contextualize_monthly(
        base,
        snapshot=snapshot,
        natal_overlay=dict(result.get("natal_overlay") or {}),
        reader_context=reader_context,
    )


def _monthly_event_present(title: str, text: str) -> bool:
    title_text = str(title or "").casefold()
    body = str(text or "").casefold()
    if not title_text:
        return True
    if "new moon" in title_text:
        return "new moon" in body
    if "full moon" in title_text:
        return "full moon" in body
    if "eclipse" in title_text:
        return "eclipse" in body
    planets = re.findall(r"\b(?:sun|moon|mercury|venus|mars|jupiter|saturn|uranus|neptune|pluto|true node)\b", title_text)
    if planets and not all(planet in body for planet in planets):
        return False
    if "retrograde" in title_text and "retrograde" not in body:
        return False
    if "stations direct" in title_text and not ("direct" in body or "station" in body):
        return False
    if " enters " in title_text:
        sign_match = re.search(r"\b(?:aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces)\b", title_text)
        if sign_match and sign_match.group(0) not in body:
            return False
    for source, alternatives in (
        ("conjunction", ("conjunction", "conjunct")),
        ("opposition", ("opposition", "opposite")),
        ("square", ("square",)),
        ("trine", ("trine",)),
        ("sextile", ("sextile",)),
    ):
        if source in title_text and not any(value in body for value in alternatives):
            return False
    return True


@st.cache_data(show_spinner=False, ttl=86400)
def _cached_paid_monthly_daily_briefs(sign: str, start_iso: str, end_iso: str, timezone_name: str) -> list[dict]:
    """Use the exact calculation packet and grounding path used by free Daily."""
    from reading_facts import build_packet
    from reading_quality import grounded_brief

    start_date = date.fromisoformat(start_iso)
    end_date = date.fromisoformat(end_iso)
    rows: list[dict] = []
    current = start_date
    while current <= end_date:
        packet = build_packet("daily", current, sign, timezone_name)
        rows.append({
            "source_id": f"daily-brief:{current.isoformat()}",
            "date": current.isoformat(),
            "daily_brief": grounded_brief(packet),
        })
        current = date.fromordinal(current.toordinal() + 1)
    return rows


def _paid_monthly_compact_daily_briefs(source_days: list[dict]) -> list[dict]:
    """Compact the exact Free Daily grounding into a chronology/detail layer.

    Paid Monthly must benefit from Daily's better signal selection without turning
    the month into 28-31 diary entries.  Keep only the primary Daily signal,
    supporting labels and supplied life areas; the final Monthly writer decides
    which of these details actually move the month-long story.
    """
    compact: list[dict] = []
    for row in source_days:
        brief = dict(row.get("daily_brief") or row.get("brief") or {})
        event_rows = [item for item in list(brief.get("events") or []) if isinstance(item, dict)]
        primary = event_rows[0] if event_rows else {}
        primary_aspect = " ".join(str(primary.get("aspect") or primary.get("event") or "").split())
        primary_life_areas = [
            str(item.get("life_area"))
            for item in (primary.get("event_life_areas") or [])
            if isinstance(item, dict) and item.get("life_area")
        ] or [str(item) for item in (primary.get("house_meanings") or []) if str(item).strip()]

        supporting: list[str] = []
        for value in list(brief.get("calculated_labels") or []):
            text = " ".join(str(value or "").split())
            lower = text.casefold()
            if not text or text == primary_aspect:
                continue
            if lower.startswith("orb") or lower in {"exact", "applying", "separating", "closest to exact today"}:
                continue
            if text not in supporting:
                supporting.append(text)

        major_events: list[dict] = []
        for event in list(brief.get("major_events") or []):
            if not isinstance(event, dict):
                continue
            label = " ".join(str(event.get("event") or event.get("technical") or "").split())
            if not label:
                continue
            major_events.append({
                "event": label,
                "technical": str(event.get("technical") or ""),
                "tier": event.get("tier"),
                "life_areas": [
                    str(item.get("life_area"))
                    for item in (event.get("event_life_areas") or [])
                    if isinstance(item, dict) and item.get("life_area")
                ],
            })

        compact.append({
            "date": str(row.get("date") or ""),
            "primary": {
                "aspect": primary_aspect,
                "phase": primary.get("phase"),
                "orb": primary.get("orb"),
                "life_areas": list(dict.fromkeys(primary_life_areas)),
            },
            "supporting": supporting,
            "major_events": major_events,
            "required_turning_points": list(brief.get("required_turning_points") or []),
        })
    return compact


@st.cache_data(show_spinner=False, ttl=86400)
def _cached_paid_monthly_collective_scaffold(
    sign: str,
    month_start_iso: str,
    timezone_name: str,
) -> dict:
    """Reuse Free Monthly's proven macro-story process as paid-story scaffolding.

    The pre-generated Free Monthly prose is not customer copy for the paid report;
    it is a collective sign-level arc that helps the final writer see the month as
    a beginning, development and resolution before natal context changes the story.
    """
    from reading_quality import grounded_brief

    month_start = date.fromisoformat(month_start_iso).replace(day=1)
    packet = build_plain_packet("monthly", month_start, sign, timezone_name)
    brief = grounded_brief(packet)
    reading = load_plain_reading(packet) or {}

    monthly_events: list[dict] = []
    for event in list(brief.get("events") or []):
        if not isinstance(event, dict):
            continue
        monthly_events.append({
            "date": str(event.get("date") or ""),
            "event": str(event.get("event") or event.get("aspect") or ""),
            "aspect": str(event.get("aspect") or ""),
            "phase": event.get("phase"),
            "orb": event.get("orb"),
            "life_areas": [
                str(item.get("life_area"))
                for item in (event.get("event_life_areas") or [])
                if isinstance(item, dict) and item.get("life_area")
            ],
        })

    major_events: list[dict] = []
    for event in list(brief.get("major_events") or []):
        if not isinstance(event, dict):
            continue
        major_events.append({
            "date": str(event.get("date") or ""),
            "event": str(event.get("event") or event.get("technical") or ""),
            "technical": str(event.get("technical") or ""),
            "tier": event.get("tier"),
            "life_areas": [
                str(item.get("life_area"))
                for item in (event.get("event_life_areas") or [])
                if isinstance(item, dict) and item.get("life_area")
            ],
        })

    return {
        "collective_story": " ".join(str(reading.get("voice_body") or "").split()),
        "monthly_events": monthly_events,
        "major_events": major_events,
        "dominant_life_areas": list(packet.get("life_areas") or []),
        "required_turning_points": list(brief.get("required_turning_points") or []),
    }


def _paid_monthly_transit_threads(source_days: list[dict]) -> list[dict]:
    """Detect neighbouring repeated Daily influences without inventing month-long spans."""
    occurrences: dict[str, list[date]] = {}
    display: dict[str, str] = {}
    for row in source_days:
        try:
            day = date.fromisoformat(str(row.get("date") or "")[:10])
        except ValueError:
            continue
        brief = dict(row.get("daily_brief") or row.get("brief") or {})
        labels = list(brief.get("calculated_labels") or [])
        for event in list(brief.get("major_events") or []):
            if isinstance(event, dict):
                labels.append(event.get("event") or event.get("technical") or "")
        for raw in labels:
            text = " ".join(str(raw or "").split())
            lower = text.casefold()
            if not text or lower.startswith("orb") or lower in {"exact", "applying", "separating", "closest to exact today"}:
                continue
            if not re.search(r"\b(?:sun|moon|mercury|venus|mars|jupiter|saturn|uranus|neptune|pluto|true node)\b", lower):
                continue
            key = re.sub(r"[^a-z0-9]+", " ", lower).strip()
            if not key:
                continue
            display.setdefault(key, text)
            occurrences.setdefault(key, []).append(day)

    threads: list[dict] = []
    for key, values in occurrences.items():
        ordered = sorted(set(values))
        if not ordered:
            continue
        runs: list[list[date]] = [[ordered[0]]]
        for current in ordered[1:]:
            if (current - runs[-1][-1]).days <= 2:
                runs[-1].append(current)
            else:
                runs.append([current])
        structural = any(token in key for token in ("retrograde", "station", "eclipse", "new moon", "full moon", "equinox", "solstice"))
        for run in runs:
            if len(run) < 2 and not structural:
                continue
            threads.append({
                "label": display.get(key, key),
                "start": run[0].isoformat(),
                "end": run[-1].isoformat(),
                "days_seen": len(run),
            })
    return sorted(threads, key=lambda row: (str(row.get("start") or ""), str(row.get("label") or "")))


def _paid_monthly_subject_dossier(snapshot, context: dict) -> dict:
    """Internal protagonist model. Evidence for Luna; never customer-facing copy."""
    natal = dict(context.get("natal_player") or {})
    positions = [dict(item) for item in list(natal.get("positions") or []) if isinstance(item, dict)]
    raw_strengths = [dict(item) for item in list(natal.get("strengths") or []) if isinstance(item, dict)]
    aspects = [dict(item) for item in list(natal.get("aspects") or []) if isinstance(item, dict)]

    core_positions: dict[str, dict] = {}
    for item in positions:
        planet = str(item.get("planet") or "")
        if planet in {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}:
            core_positions[planet] = item

    if snapshot is not None:
        ascendant = getattr(snapshot, "ascendant", None)
        midheaven = getattr(snapshot, "midheaven", None)
        if ascendant is not None:
            core_positions["Ascendant"] = {
                "planet": "Ascendant",
                "sign": str(getattr(ascendant, "sign", "") or ""),
                "degree": round(float(getattr(ascendant, "degree", 0.0) or 0.0), 3),
                "house": getattr(ascendant, "house", None),
            }
        if midheaven is not None:
            core_positions["Midheaven"] = {
                "planet": "Midheaven",
                "sign": str(getattr(midheaven, "sign", "") or ""),
                "degree": round(float(getattr(midheaven, "degree", 0.0) or 0.0), 3),
                "house": getattr(midheaven, "house", None),
            }

    strengths = []
    for index, item in enumerate(raw_strengths[:6], 1):
        strengths.append({"id": f"strength:{index}", **item})

    personal = dict(context.get("personal_month") or {})
    activations = []
    for index, item in enumerate(
        [dict(row) for row in list(personal.get("activations") or []) if isinstance(row, dict)], 1
    ):
        activations.append({"id": f"activation:{index}", **item})

    return {
        "core_positions": core_positions,
        "dominant_element": str(natal.get("dominant_element") or ""),
        "dominant_modality": str(natal.get("dominant_modality") or ""),
        "strengths": strengths,
        "natal_aspects": aspects[:12],
        "personal_activations": activations,
        "reader_context": dict(context.get("reader_context") or {}),
        "birth_time_known": bool(natal.get("birth_time_known")),
    }


def _paid_monthly_prompt_material(facts: dict, *, compact_level: int = 0) -> dict:
    """Prepare the paid month before Luna writes, with adaptive compaction.

    The GitHub base remains the full audit source. This function creates only
    the minimum story packet the creative model needs. If the first packet is
    too large for the provider ceiling, Python can rebuild it more compactly
    BEFORE the one and only LLM call; production is never stopped merely because
    optional context made the first prompt too large.
    """
    subject = dict(facts.get("subject") or {})
    month = dict(facts.get("month_context") or {})
    collective = dict(facts.get("collective_month") or {})

    level = max(0, min(3, int(compact_level or 0)))
    free_arc_chars = (760, 600, 460, 300)[level]
    strength_limit = (4, 4, 3, 2)[level]
    strength_text = (120, 105, 90, 72)[level]
    watch_text = (90, 75, 60, 48)[level]
    activation_text = (145, 125, 105, 90)[level]
    thread_limit = (5, 4, 2, 0)[level]
    cycle_limit = (4, 3, 2, 2)[level]
    structural_cap = (7, 6, 4, 3)[level]
    texture_cap = (2, 1, 1, 0)[level]
    area_cap = (4, 3, 3, 2)[level]

    # Keep the personal fingerprint, not every chart field.
    allowed_core = (
        "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
        "Ascendant", "Midheaven",
    )
    raw_core = dict(subject.get("core_positions") or {})
    core = {}
    for planet in allowed_core:
        item = raw_core.get(planet)
        if not isinstance(item, dict):
            continue
        sign = " ".join(str(item.get("sign") or "").split())
        if sign:
            core[planet] = sign

    strengths = []
    for item in list(subject.get("strengths") or [])[:strength_limit]:
        if not isinstance(item, dict):
            continue
        strengths.append([
            " ".join(str(item.get("title") or "").split())[:72],
            " ".join(str(item.get("strength") or item.get("interpretation") or "").split())[:strength_text],
            " ".join(str(item.get("watch") or "").split())[:watch_text],
            " ".join(str(item.get("evidence") or "").split())[:62],
        ])

    # Personal activations are never silently dropped; only their wording is
    # compacted more aggressively at higher levels.
    activations = []
    for item in list(subject.get("personal_activations") or []):
        if not isinstance(item, dict):
            continue
        date_label = str(item.get("date_label") or item.get("date") or item.get("exact_date") or "")[:24]
        signal = " ".join(str(item.get("signal") or "").split())
        if not signal:
            transit = str(item.get("transit") or item.get("transit_planet") or item.get("transiting_planet") or "")
            aspect = str(item.get("aspect") or "")
            target = str(item.get("target") or item.get("natal_target") or item.get("natal_planet") or "")
            signal = " ".join(bit for bit in (transit, aspect, (f"natal {target}" if target else "")) if bit).strip()
        activations.append([date_label, signal[:activation_text]])

    reader = dict(subject.get("reader_context") or {})
    reader_context = {
        key: " ".join(str(reader.get(key) or "").split())[:90 if level < 2 else 60]
        for key in ("main_focus", "focus", "personal_question", "question")
        if str(reader.get(key) or "").strip()
    }

    # Anchors are protected; keep all of them and their dates.
    anchors = []
    for item in list(month.get("required_story_anchors") or []):
        if not isinstance(item, dict):
            continue
        anchors.append([
            " ".join(str(item.get("title") or "").split())[:82],
            " ".join(str(item.get("date_label") or item.get("date") or "").split())[:22],
        ])

    threads = []
    for item in list(month.get("transit_threads") or [])[:thread_limit]:
        if isinstance(item, dict):
            threads.append([
                " ".join(str(item.get("label") or "").split())[:70],
                str(item.get("start") or "")[:10],
                str(item.get("end") or "")[:10],
            ])

    cycles = []
    for item in list(month.get("retrograde_cycles") or [])[:cycle_limit]:
        if not isinstance(item, dict):
            continue
        label = item.get("title") or item.get("label") or item.get("planet") or "Retrograde"
        start_value = item.get("retrograde_start") or item.get("pre_shadow_start") or item.get("start_date") or item.get("start") or ""
        end_value = item.get("direct_date") or item.get("post_shadow_end") or item.get("end_date") or item.get("end") or ""
        cycles.append([
            " ".join(str(label).split())[:68],
            str(start_value)[:10],
            str(end_value)[:10],
        ])

    daily_rows = [row for row in list(facts.get("daily_signals") or []) if isinstance(row, dict)]

    # Five chronological story beats preserve the whole month while preventing
    # 31 Daily rows from becoming 31 mini-horoscopes.
    beat_bounds = ((1, 6), (7, 12), (13, 18), (19, 24), (25, 31))
    beats = []
    for start_day, end_day in beat_bounds:
        structural = []
        texture = []
        areas = []
        seen_structural = set()
        seen_texture = set()

        for row in daily_rows:
            date_text = str(row.get("date") or "")[:10]
            try:
                day_num = int(date_text[-2:])
            except (TypeError, ValueError):
                continue
            if not (start_day <= day_num <= end_day):
                continue

            primary = dict(row.get("primary") or {})
            primary_label = " ".join(str(primary.get("aspect") or "").split())
            primary_areas = [
                " ".join(str(v or "").split())
                for v in list(primary.get("life_areas") or [])
                if str(v or "").strip()
            ][:2]
            for area in primary_areas:
                if area not in areas:
                    areas.append(area)

            major_labels = []
            for event in list(row.get("major_events") or [])[:3]:
                if not isinstance(event, dict):
                    continue
                label = " ".join(str(event.get("event") or event.get("technical") or "").split())
                if label:
                    major_labels.append(label)

            support_labels = [
                " ".join(str(v or "").split())
                for v in list(row.get("supporting") or [])
                if str(v or "").strip()
            ]

            # Major events and non-lunar aspects drive the story.
            candidates = [*major_labels]
            if primary_label and "moon" not in primary_label.casefold():
                candidates.append(primary_label)
            candidates.extend(
                label for label in support_labels
                if "moon" not in label.casefold()
            )
            for label in candidates:
                key = (date_text, label.casefold())
                if key not in seen_structural:
                    structural.append([date_text, label[:82]])
                    seen_structural.add(key)

            # Lunar Daily signals remain optional texture only.
            if texture_cap and primary_label and "moon" in primary_label.casefold():
                key = (date_text, primary_label.casefold())
                if key not in seen_texture:
                    texture.append([date_text, primary_label[:74], primary_areas[:2]])
                    seen_texture.add(key)

        # Major events were appended first, so trimming retains the strongest
        # protected structure before optional supporting material.
        structural = structural[:structural_cap]
        if len(texture) > texture_cap:
            if texture_cap == 1:
                texture = [texture[len(texture) // 2]]
            else:
                texture = [texture[0], texture[-1]][:texture_cap]

        beats.append({
            "range": f"{start_day:02d}-{end_day:02d}",
            "structural": structural,
            "texture": texture[:texture_cap],
            "areas": areas[:area_cap],
        })

    return {
        "subject": {
            "core": core,
            "element": str(subject.get("dominant_element") or ""),
            "mode": str(subject.get("dominant_modality") or ""),
            "strengths": strengths,
            "activations": activations,
            "reader": reader_context,
            "birth_time_known": bool(subject.get("birth_time_known")),
        },
        "month": {
            "label": str(month.get("label") or ""),
            "free_arc": " ".join(str(collective.get("collective_story") or "").split())[:free_arc_chars],
            "anchors": anchors,
            "threads": threads,
            "retrogrades": cycles,
            "beats": beats,
        },
    }

def _paid_monthly_weave_prompt(facts: dict, *, compact_level: int = 0) -> str:
    return (
        "Write Luna's paid Personal Monthly interpretation as one continuous article. "
        "Python owns every astrology fact. The SUBJECT is the protagonist; the sky is the changing environment. "
        "Never invent astrology, biography or guaranteed events.\n"
        "Before writing, silently plan one month-long story from month.free_arc and the five chronological month.beats. "
        "Beats are evidence ranges, not sections to recite. Merge them into one wave: beginning, development, pressure/opening, reversal and ending. "
        "Do not write a day-by-day sequence or mini-horoscopes. Mention dates only for supplied events, anchors, activations or genuine turning points.\n"
        "Astronomy discipline: preserve every supplied planet pair, aspect/station state and date exactly. "
        "Never infer an unlisted conjunction, opposition, station, New Moon, Full Moon or direct station. "
        "Lunar texture is brief background only, never a new structural event. If a fact is not supplied, omit it.\n"
        "Personalise the whole arc through subject.core, strengths and activations. "
        "Strength rows are [title,strength,watch,evidence]; activation rows are [date,signal]. "
        "Weave every activation naturally, use at least two strengths when available, and include every supplied anchor. "
        "Never invent angles or houses when birth time is unknown.\n"
        "Later paragraphs must remember earlier pressures, openings and choices rather than resetting. "
        "Do not explain transits one by one, repeat astronomical claims, or recycle prose to reach length. Stop when the story is complete.\n"
        "Return PLAIN PROSE ONLY: no JSON, metadata, ids, hashes, Markdown, headings, bullets, day labels, house numbers, engine language, Remember or Your move labels. "
        "Aim for about 1,400-1,650 words in 9-13 substantial paragraphs separated by blank lines. "
        "Silently check before finishing that the story reaches the end of the month, covers anchors/activations, preserves supplied astronomy and does not repeat itself.\n"
        "CALCULATED MATERIAL:\n"
        + json.dumps(
            _paid_monthly_prompt_material(facts, compact_level=compact_level),
            ensure_ascii=False,
            separators=(',', ':'),
        )
    )

def _paid_monthly_clean_plain_story(value: object) -> str:
    text = str(value or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].lstrip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    # Free Luna uses plain prose. Remove accidental emphasis delimiters only;
    # do not rewrite the model's wording or paragraph structure.
    return re.sub(r"\*{1,3}|_{2,3}|`+", "", text).strip()


def _paid_monthly_estimated_tokens(text: str) -> int:
    """Estimate request tokens with tiktoken when available, otherwise safely approximate."""
    try:
        import tiktoken  # optional; Streamlit deploy does not require it
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(str(text or "")))
    except Exception:
        # Conservative approximation for English + compact JSON input.
        return max(1, math.ceil(len(str(text or "")) / 4.0))


def _paid_monthly_preflight_tokens(prompt: str, completion_tokens: int) -> tuple[int, int]:
    """Measure a candidate request; never make this helper a production stop."""
    raw_input = _paid_monthly_estimated_tokens(prompt) + 80
    buffered_input = math.ceil(raw_input * 1.15)
    return buffered_input, buffered_input + int(completion_tokens)


def _paid_monthly_prepare_request(facts: dict) -> tuple[str, int, int, int]:
    """Fit the one Paid Monthly request before it reaches Groq.

    Try progressively more compact Python-built packets. This is not an LLM
    retry: no provider call has happened yet. The full GitHub base remains
    untouched; only optional duplicate/context wording is removed from the
    creative prompt until the request fits safely below the observed provider
    ceiling.
    """
    target_total = 5350
    preferred_completion = 2500

    for level in range(4):
        prompt = _paid_monthly_weave_prompt(facts, compact_level=level)
        buffered_input, total = _paid_monthly_preflight_tokens(prompt, preferred_completion)
        if total <= target_total:
            return prompt, preferred_completion, buffered_input, level

    # Extremely activation-heavy subjects can still enlarge the prompt. Rather
    # than stopping production, keep the most compact evidence packet and give
    # the remaining safe budget to the prose, with a useful minimum.
    prompt = _paid_monthly_weave_prompt(facts, compact_level=3)
    buffered_input, _ = _paid_monthly_preflight_tokens(prompt, 0)
    completion_tokens = max(1900, min(preferred_completion, target_total - buffered_input))
    return prompt, completion_tokens, buffered_input, 3


@st.cache_data(show_spinner=False, ttl=1800)
def _cached_paid_monthly_weave(
    facts_json: str,
    base_url: str,
    model: str,
    _api_key: str,
) -> str:
    """One provider call, plain prose out. No JSON schema and no automatic retry."""
    import requests

    facts = json.loads(facts_json)
    prompt, max_completion_tokens, _estimated_input_tokens, _compact_level = (
        _paid_monthly_prepare_request(facts)
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Write Luna's interpretation from the supplied calculations. "
                    "Return plain prose only. Python owns the facts and validation."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.58,
        "max_completion_tokens": max_completion_tokens,
    }
    if str(model or "").startswith("openai/gpt-oss"):
        payload["reasoning_effort"] = "low"
        payload["include_reasoning"] = False

    try:
        response = requests.post(
            f"{str(base_url).rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=150,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Voice provider request failed: {exc}") from exc

    if response.status_code in (413, 429):
        body = " ".join(str(response.text or "").split())[:500]
        raise RuntimeError(f"Voice provider HTTP {response.status_code}: {body}")
    if response.status_code >= 400:
        body = " ".join(str(response.text or "").split())[:500]
        raise RuntimeError(f"Voice provider HTTP {response.status_code}: {body}")

    try:
        choice = response.json()["choices"][0]
        body = choice["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError("Voice provider returned no usable prose.") from exc

    if str(choice.get("finish_reason") or "") == "length":
        raise RuntimeError("Voice provider truncated the Paid Monthly story at the completion limit.")

    clean = _paid_monthly_clean_plain_story(body)
    if not clean:
        raise RuntimeError("Voice provider returned an empty Paid Monthly story.")
    return clean


# All content requirements for Paid Monthly are instructions to Luna before the
# provider call. After the call, Python does not judge whether Luna mentioned a
# preferred strength, activation, anchor, word target or stylistic feature.
# Post-call handling is transport-only: usable non-truncated prose is published.

def _paid_monthly_story_paragraphs(body: object) -> list[str]:
    """Normalise plain prose without making formatting a publication blocker.

    Groq sometimes returns a complete article with too few blank-line breaks.
    When the prose is substantial, split it deterministically into readable
    paragraph-sized sentence groups instead of rejecting a good report.
    """
    text = _paid_monthly_clean_plain_story(body)
    paragraphs = [
        " ".join(part.split())
        for part in re.split(r"\n\s*\n+", text)
        if str(part or "").strip()
    ]
    if len(paragraphs) >= 8 or _word_count(text) < 1200:
        return paragraphs

    # A long single/short block is a transport-format issue, not a failed story.
    sentences = [
        " ".join(item.split())
        for item in re.split(r"(?<=[.!?])\s+", text)
        if str(item or "").strip()
    ]
    if len(sentences) < 8:
        return paragraphs

    target = max(8, min(14, round(_word_count(text) / 165)))
    per_group = max(1, (len(sentences) + target - 1) // target)
    rebuilt = [
        " ".join(sentences[index:index + per_group]).strip()
        for index in range(0, len(sentences), per_group)
    ]
    return [item for item in rebuilt if item]



def _paid_monthly_weave_fallback(_facts: dict) -> dict:
    """Never publish raw Daily/calculation fragments as a paid Monthly story."""
    return {"headline": "", "paragraphs": [], "voice_complete": False}


def _generate_paid_monthly_weave(facts: dict) -> dict:
    """Exactly one paid-story call; any usable non-truncated plain prose is published.

    Content requirements are prompt instructions evaluated by Luna before it
    finishes the response. Python performs no post-generation editorial or
    factual completeness gate that could suppress an otherwise usable story.
    """
    if not _luna_voice_ready():
        _record_voice_error("paid_monthly_story_weave", "Luna voice is not configured.")
        return _paid_monthly_weave_fallback(facts)

    facts_json = json.dumps(facts, ensure_ascii=False, sort_keys=True, default=str)
    try:
        body = _cached_paid_monthly_weave(
            facts_json, LUNA_VOICE_BASE_URL, LUNA_VOICE_MODEL, LUNA_VOICE_API_KEY
        )
    except Exception as exc:
        _record_voice_error("paid_monthly_story_weave", exc)
        return _paid_monthly_weave_fallback(facts)

    paragraphs = _paid_monthly_story_paragraphs(body)
    if not paragraphs:
        _record_voice_error("paid_monthly_story_weave", "Voice provider returned no usable prose.")
        return _paid_monthly_weave_fallback(facts)

    return {
        "headline": "",
        "paragraphs": paragraphs,
        "voice_complete": True,
        "quality_tier": "published",
        "quality_note": "",
    }

def _paid_monthly_longform(narrative, result: dict, snapshot=None) -> dict:
    """Free-Monthly macro arc + Daily detail + one natal subject -> one paid story."""
    context = _paid_monthly_voice_facts(narrative, result, snapshot)
    sign = str(result.get("sign") or "")
    timezone_name = str(result.get("timezone_name") or DEFAULT_TIMEZONE)
    try:
        start_date = date.fromisoformat(str(result.get("start") or "")[:10])
        end_date = date.fromisoformat(str(result.get("end") or "")[:10])
    except ValueError:
        return {"headline": "", "paragraphs": [], "story_word_count": 0, "voice_complete": False, "context": context}

    shared = dict(context.get("shared_sky") or {})

    # Preferred path: the GitHub sign/month JSON has already done the shared
    # work.  It contains the Free Monthly macro arc and the same grounded Daily
    # calculation briefs used by the public Daily.  Runtime should add only the
    # customer's natal subject and personal contacts.
    collective_month = dict(shared.get("collective_month") or {})
    source_days = [
        dict(item) for item in list(shared.get("daily_briefs") or [])
        if isinstance(item, dict)
    ]
    expected_days = monthrange(start_date.year, start_date.month)[1]
    if (
        not bool(shared.get("story_background_ready"))
        or not collective_month.get("collective_story")
        or len(source_days) != expected_days
    ):
        _record_voice_error(
            "paid_monthly_story_weave",
            "Paid Monthly preflight failed: the prebuilt GitHub sign/month background is missing or incomplete. "
            f"Expected {expected_days} Daily briefs and a published Free Monthly arc; found {len(source_days)} Daily briefs.",
        )
        return {
            "headline": "", "paragraphs": [], "story_word_count": 0,
            "voice_complete": False, "context": context, "background_source": "preflight-failed",
        }

    daily_signals = _paid_monthly_compact_daily_briefs(source_days)
    subject = _paid_monthly_subject_dossier(snapshot, context)
    core_positions = dict(subject.get("core_positions") or {})
    if not isinstance(core_positions.get("Sun"), dict) or not isinstance(core_positions.get("Moon"), dict):
        _record_voice_error(
            "paid_monthly_story_weave",
            "Paid Monthly preflight failed: the Subject dossier does not contain both Sun and Moon.",
        )
        return {
            "headline": "", "paragraphs": [], "story_word_count": 0,
            "voice_complete": False, "context": context, "subject": subject,
            "background_source": "preflight-failed",
        }
    background_source = "prebuilt"
    raw_anchors = shared.get("required_story_anchors") or monthly_required_story_anchors(narrative, result)
    required_anchors = [
        {"id": f"anchor:{index}", **dict(item)}
        for index, item in enumerate(
            [row for row in list(raw_anchors or []) if isinstance(row, dict)], 1
        )
    ]
    month_context = {
        "label": str(shared.get("label") or result.get("label") or ""),
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        "transit_threads": list(shared.get("transit_threads") or []) or _paid_monthly_transit_threads(source_days),
        "retrograde_cycles": shared.get("retrograde_cycles") or result.get("retrograde_cycles") or [],
        "required_story_anchors": required_anchors,
    }
    weave_facts = {
        "story_revision": PAID_MONTHLY_STORY_REVISION,
        "subject": subject,
        "month_context": month_context,
        "collective_month": collective_month,
        "daily_signals": daily_signals,
    }

    with st.spinner("Luna is turning the calculated month into your personal story. Keep this page open…"):
        woven = _generate_paid_monthly_weave(weave_facts)

    paragraphs = [
        " ".join(str(item or "").split())
        for item in (woven.get("paragraphs") or [])
        if str(item or "").strip()
    ]
    return {
        "headline": " ".join(str(woven.get("headline") or "").split()),
        "paragraphs": paragraphs,
        "story_word_count": _word_count(" ".join(paragraphs)),
        "voice_complete": bool(woven.get("voice_complete", False)),
        "quality_tier": str(woven.get("quality_tier") or ""),
        "context": context,
        "subject": subject,
        "daily_signal_count": len(daily_signals),
        "collective_story_available": bool(collective_month.get("collective_story")),
        "background_source": background_source,
    }


def _select_three_monthly_chapters(chapters) -> list:
    """Compress the paid month to an opening, middle and closing phase."""
    values = list(chapters or ())
    if len(values) <= 3:
        return values
    indices = (0, len(values) // 2, len(values) - 1)
    selected = []
    for index in indices:
        item = values[index]
        if item not in selected:
            selected.append(item)
    return selected[:3]


def _compact_monthly_paragraphs(chapter, maximum: int = 2) -> list[str]:
    values = [
        " ".join(str(item or "").split())
        for item in (getattr(chapter, "paragraphs", ()) or ())
        if str(item or "").strip()
    ]
    if len(values) <= maximum:
        return values
    return [values[0], values[-1]]




def _render_snapshot_monthly_report(
    narrative,
    result: dict,
    *,
    order_reference: str = "",
) -> None:
    """Paid Monthly: natal baseline, one integrated long-form month, then compact dates/evidence."""
    st.markdown('<section class="natal-shell paid-monthly-shell">', unsafe_allow_html=True)
    title = str(getattr(narrative, "hook_headline", "") or getattr(narrative, "headline", "") or "Your Personal Monthly")
    st.markdown(f'<div class="editorial-title">{escape(title)}</div>', unsafe_allow_html=True)
    label = str(getattr(narrative, "label", "") or result.get("label") or "This month")
    intro = str(getattr(narrative, "central_storyline", "") or getattr(narrative, "subtitle", "") or "")
    intro_text = label + (f" · {intro}" if intro else "")
    st.markdown(f'<div class="natal-intro">{escape(intro_text)}</div>', unsafe_allow_html=True)

    paid_snapshot = _snapshot_from_encoded_natal_profile(
        str(result.get("natal_profile") or ""),
        timezone_name=str(result.get("timezone_name") or DEFAULT_TIMEZONE),
    )
    if paid_snapshot is not None:
        _render_snapshot_natal_core(
            paid_snapshot,
            precision_note=str(result.get("natal_precision") or ""),
            show_evidence=False,
            use_live_voice=False,
            use_live_signature_moves=False,
        )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("## Read the month")
    with st.spinner("Luna is weaving the calculated month around your natal chart…"):
        longform = _paid_monthly_longform(narrative, result, paid_snapshot)
    paid_context = dict(longform.get("context") or {})

    story_paragraphs = [
        " ".join(str(item or "").split())
        for item in (longform.get("paragraphs") or [])
        if str(item or "").strip()
    ]
    story_headline = " ".join(str(longform.get("headline") or "").split())
    if not longform.get("voice_complete", False):
        st.error("Luna could not complete this report cleanly. Please regenerate it.")
        if _admin_access_unlocked():
            diagnostic = _voice_error("paid_monthly_story_weave")
            if diagnostic and diagnostic != "No provider response was accepted.":
                with st.expander("Owner diagnostic", expanded=False):
                    st.caption(diagnostic)
    else:
        story_body = "".join(f"<p>{escape(paragraph)}</p>" for paragraph in story_paragraphs)
        if story_headline or story_body:
            st.markdown(
                '<div class="natal-signature-reading paid-monthly-longform paid-monthly-article">'
                + (f'<h3>{escape(story_headline)}</h3>' if story_headline else '')
                + story_body
                + '</div>',
                unsafe_allow_html=True,
            )

    # Key Dates are now a compact reference index only. The full interpretation
    # already appears in Read the month and is not repeated here.
    key_dates = list(getattr(narrative, "key_dates", ()) or ())[:6]
    if key_dates:
        st.markdown("## Key dates")
        st.caption("Quick reference only — the interpretation is already in Read the month.")
        for item in key_dates:
            date_label = str(getattr(item, "date_label", "") or "")
            evidence = " ".join(str(getattr(item, "evidence", "") or "").split())
            if evidence.casefold() in {"", "transition", "convergence"}:
                consequence = " ".join(str(getattr(item, "consequence", "") or "").split())
                first_sentence = re.split(r"(?<=[.!?])\s+", consequence, maxsplit=1)[0].strip()
                words = first_sentence.split()
                evidence = " ".join(words[:22]).rstrip(",;:") + ("…" if len(words) > 22 else "")
            st.markdown(
                '<div class="natal-signature-reading paid-key-date">'
                f'<div class="natal-evidence">{escape(date_label)}</div>'
                f'<p>{escape(evidence)}</p>'
                '</div>',
                unsafe_allow_html=True,
            )

    # No second/bottom Your Move. Strategic choices belong inside the long-form
    # interpretation rather than appearing again as generic bullets.
    overlay = dict(result.get("natal_overlay") or {})
    activations = list(overlay.get("activations") or [])
    with _luna_evidence_panel("Why Luna sees this · chart evidence"):
        paid_facts = paid_context or _paid_monthly_voice_facts(narrative, result, paid_snapshot)
        strengths = list((paid_facts.get("natal_player") or {}).get("strengths") or [])
        if strengths:
            st.markdown("**Natal strengths used in the interpretation**")
            for item in strengths[:8]:
                st.markdown(f"- {item.get('evidence', '')} · {item.get('title', '')}")
        if activations:
            st.markdown("**Personal natal contacts**")
            for item in activations:
                label_bits = [
                    str(item.get("date_label") or item.get("date") or ""),
                    str(item.get("signal") or ""),
                ]
                st.markdown("- " + " · ".join(bit for bit in label_bits if bit))
        registry = list(result.get("major_sky_registry") or [])
        if registry:
            st.markdown("**Authoritative monthly sky**")
            for item in registry:
                if not isinstance(item, dict):
                    continue
                label_text = item.get("display_label") or item.get("technical_label") or item.get("source_title") or "Sky event"
                st.markdown(f"- {human_date(item.get('event_date'))} · {label_text}")
        transitions = list(result.get("major_transitions") or [])
        if transitions:
            st.markdown("**Major monthly transitions**")
            for item in transitions:
                st.markdown(f"- {human_date(item.get('event_date'))} · {item.get('title', 'Transition')}")
        convergences = list(result.get("convergences") or [])
        if convergences:
            st.markdown("**Calculated convergence windows**")
            for item in convergences:
                if not isinstance(item, dict):
                    continue
                start_label = item.get("start_date") or ""
                end_label = item.get("end_date") or ""
                title_text = item.get("title") or item.get("label") or "Convergence"
                window = human_date(start_label) if start_label == end_label else f"{human_date(start_label)} – {human_date(end_label)}"
                st.markdown(f"- {window} · {title_text}")
        dominant = list(result.get("dominant_houses") or [])
        if dominant:
            st.markdown("**Dominant calculated life areas**")
            for item in dominant:
                st.markdown(
                    f"- House {item.get('house')} · {item.get('topic', '')} · weight {float(item.get('weight', 0.0) or 0.0):.1f}"
                )
        st.markdown(f"**{LUNA_TRUST_STATEMENT}**")
        st.caption(LUNA_TRUST_DISCLOSURE)

    if order_reference:
        st.caption(f"Order reference · {order_reference}")
    st.markdown('</section>', unsafe_allow_html=True)

def _render_snapshot_yearly_report(
    result: dict,
    *,
    order_reference: str = "",
) -> None:
    """Render paid Year Ahead from the Snapshot baseline plus personal rolling transits."""
    st.markdown('<section class="natal-shell paid-yearly-shell">', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Paid · Your Year Ahead</div>', unsafe_allow_html=True)

    paid_snapshot = _snapshot_from_encoded_natal_profile(
        str(result.get("natal_profile") or ""),
        timezone_name=str(result.get("timezone_name") or DEFAULT_TIMEZONE),
    )
    timing_report = result.get("paid_timing_report")
    if paid_snapshot is not None and timing_report is None:
        paid_snapshot, timing_report = _prepare_paid_yearly_personal_layer(result)

    label = str(result.get("label") or "Rolling 12 months")
    st.markdown('<div class="editorial-title">Your year, in the order it actually happens</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="natal-intro">{escape(label)} · Start with the natal baseline, then follow the personal contacts in chronological order.</div>',
        unsafe_allow_html=True,
    )

    if paid_snapshot is not None:
        _render_snapshot_natal_core(
            paid_snapshot,
            precision_note=str(result.get("natal_precision") or ""),
            show_evidence=False,
        )

    if timing_report is None:
        st.error("Luna could not build the personal 12-month timing layer for this report.")
        if order_reference:
            st.caption(f"Order reference · {order_reference}")
        st.markdown('</section>', unsafe_allow_html=True)
        return

    try:
        display_end = date.fromisoformat(str(result.get("end") or ""))
    except ValueError:
        display_end = timing_report.end_date

    st.markdown('<div class="eyebrow" style="margin-top:2.5rem">Your Year Ahead</div>', unsafe_allow_html=True)
    st.markdown("## Read the year")
    year_facts = _paid_yearly_timing_facts(timing_report)
    guided_year = _guided_luna_copy("yearly", year_facts)
    if guided_year:
        _render_signature_style_story(guided_year, "Luna's strategic map")
    else:
        _render_voice_unavailable(facts_label="personal year-ahead calculation")

    ranked = sorted(list(timing_report.stories), key=lambda story: (-float(story.score), story.first_date))
    themes = ranked[:3]
    if themes:
        st.markdown("## Three themes organise the year")
        st.caption("These are the highest-ranked personal patterns. They are themes, not three extra forecasts.")
        for story in themes:
            area = _timing_story_life_area(story)
            st.markdown(
                f"""<div class="natal-signature-reading report-flat-reading yearly-theme-reading">
  <div class="natal-evidence">{escape(_timing_signal_type(story))} · {escape(story.polarity)}</div>
  <h3>{escape(str(story.headline))}</h3>
  <p>{escape(area)}</p>
</div>""",
                unsafe_allow_html=True,
            )

    strongest = ranked[:6]
    if strongest:
        st.markdown("## Your strongest personal transits")
        st.caption("Six contacts only. Timing and action stay visible; raw calculation detail stays collapsed.")
        transit_facts = {
            "start_date": timing_report.start_date.isoformat(),
            "end_date": display_end.isoformat(),
            "timezone": timing_report.timezone_name,
            "items": [
                {
                    "source_id": f"paid-year-transit:{index}",
                    "transiting_planet": story.transit_planet,
                    "aspect": story.aspect,
                    "natal_target": story.natal_target,
                    "natal_house": story.natal_house,
                    "polarity": story.polarity,
                    "score": round(story.score, 3),
                    "active_periods": [{"start": period.start_date.isoformat(), "end": period.end_date.isoformat()} for period in story.periods],
                    "exact_hits": [{"date": hit.exact_date.isoformat(), "orb": round(hit.orb, 3), "retrograde": hit.retrograde} for hit in story.hits],
                }
                for index, story in enumerate(strongest)
            ],
        }
        # These chapters already contain calculated timing-map interpretation.
        # Keep them immediate instead of making six more live voice requests
        # after the natal chart.
        for story in sorted(strongest, key=lambda item: item.first_date):
            periods_label = " · ".join(_timing_range_label(item.start_date, item.end_date) for item in story.periods)
            starts = _timing_story_start(story)
            ends = _timing_story_end(story)
            timing_line = (
                f"Starts {_timing_date_label(starts) if starts else '—'} · "
                f"Strongest {_timing_story_peak_label(story)} · "
                f"Eases {_timing_date_label(ends) if ends else '—'}"
            )
            headline = str(story.headline)
            body = str(story.summary)
            st.markdown(
                f"""<div class="natal-signature-reading report-flat-reading yearly-transit-reading">
  <div class="natal-evidence">{escape(story.transit_planet)} {escape(story.aspect)} natal {escape(story.natal_target)} · active {escape(periods_label)}</div>
  <h3>{escape(headline)}</h3>
  <p>{escape(body)}</p>
  <p><strong>Timing ·</strong> {escape(timing_line)}</p>
</div>""",
                unsafe_allow_html=True,
            )

    roadmap = _paid_yearly_roadmap(timing_report, display_end=display_end)
    if roadmap:
        st.markdown("## The year in twelve moves")
        st.caption("This is a rolling roadmap from the selected start date—not a January-to-December calendar year. Each stage carries the previous stage forward.")
        previous_signal = ""
        for row in roadmap:
            carry = f"<p><strong>Carry forward ·</strong> {escape(previous_signal)}</p>" if previous_signal else ""
            st.markdown(
                f"""<div class="natal-signature-reading report-flat-reading yearly-roadmap-reading">
  <div class="natal-evidence">{escape(row['stage'])} · {escape(human_date(row['start']))} – {escape(human_date(row['end']))}</div>
  <h3>{escape(row['headline'])}</h3>
  <p><strong>Main signal ·</strong> {escape(row['signal'] + row['exact_label'])}</p>
  <p>{escape(row['summary'])}</p>
  {carry}
</div>""",
                unsafe_allow_html=True,
            )
            previous_signal = str(row["signal"])

    # The strategic move belongs to Luna's voiced year reading above.
    # Do not append deterministic timing-map actions as extra "Your move" advice.

    with _luna_evidence_panel("Why Luna sees this · yearly calculations"):
        st.markdown("**Calculated personal transits**")
        for story in timing_report.stories:
            periods = "; ".join(f"{human_date(period.start_date)}–{human_date(period.end_date)}" for period in story.periods)
            st.markdown(f"- {story.transit_planet} {story.aspect} natal {story.natal_target} · {story.polarity} · {periods}")
        shared = list(getattr(timing_report, "major_sky_events", ()) or ())
        if shared:
            st.markdown("**Shared-sky milestones inside your year**")
            for item in shared[:12]:
                if isinstance(item, dict):
                    st.markdown(f"- {human_date(item.get('event_date'))} · {item.get('display_label', item.get('technical_label', 'Sky event'))}")
        st.markdown(f"**{LUNA_TRUST_STATEMENT}**")
        st.caption(LUNA_TRUST_DISCLOSURE)

    if order_reference:
        st.caption(f"Order reference · {order_reference}")
    st.markdown('</section>', unsafe_allow_html=True)

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
        '<div class="natal-intro">Start with the baseline. Read your Sun, Moon, Rising, Mercury, Venus and Mars as parts of one person: you. '
        'Give the birth time only if you know it. If the time or location is uncertain, Luna leaves the angles out rather than inventing precision.</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        natal_values = _natal_input_fields(
            "natal-v323",
            prefill={},
            not_listed_label="Not listed — planetary snapshot only",
        )
        submitted = st.button(
            "Create my free snapshot",
            use_container_width=True,
            key="natal-submit-v323",
        )

    if not submitted:
        st.markdown(
            '<div class="lean-bookmark-note">Birth details stay out of the page URL. This free snapshot is calculated in the current app session and is not sent to Stripe.</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</section>', unsafe_allow_html=True)
        return

    try:
        snapshot, natal_precision, prefill_out = _build_natal_from_values(natal_values)
    except Exception as exc:
        st.error(str(exc))
        st.markdown('</section>', unsafe_allow_html=True)
        return

    birth_date = natal_values.get("birth_date")
    time_known = bool(natal_values.get("time_known"))
    birth_time_value = natal_values.get("birth_time")
    time_basis = str(natal_values.get("time_basis") or "Local time at birthplace")
    city_choice = str(natal_values.get("city_choice") or "")
    manual_city_name = str(natal_values.get("manual_city") or "")
    manual_country = str(natal_values.get("manual_country") or "")
    timezone_name = str(prefill_out.get("timezone_name") or "UTC")
    location_name = str(prefill_out.get("location_name") or "") or None
    latitude = prefill_out.get("latitude")
    longitude = prefill_out.get("longitude")

    calculated_sign = _monthly_sun_sign_from_snapshot(snapshot)
    if not calculated_sign:
        st.error("Luna could not calculate your Sun sign from the birth information supplied.")
        st.markdown('</section>', unsafe_allow_html=True)
        return
    natal_sun_sign = calculated_sign
    st.caption(f"Calculated Sun sign · {calculated_sign}")

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
    birth_confirmation_html = (
        f'<div class="natal-birth-confirm"><strong>Birth data</strong> · {escape(" · ".join(birth_bits))}'
        f'<br><span>{escape(birth_precision)}</span></div>'
    )

    if not time_known and len(snapshot.moon_uncertain) > 1:
        precision_note = (
            "Birth time is unknown, and the Moon changed sign during this date. "
            f"Luna will not choose between {' / '.join(snapshot.moon_uncertain)} without a time."
        )
    elif not time_known:
        precision_note = (
            "Birth time unknown: planetary positions are shown as a date-only snapshot. "
            "Ascendant, Midheaven and houses are intentionally omitted."
        )
    elif snapshot.ascendant is None:
        precision_note = (
            "Exact time supplied, but the birth location was not available. "
            "Planetary positions use the selected timezone; Ascendant and houses are intentionally omitted."
        )
    else:
        precision_note = "Tropical geocentric positions · Whole-sign houses · Swiss Ephemeris"

    _render_snapshot_natal_core(
        snapshot,
        precision_note=precision_note,
        birth_confirmation_html=birth_confirmation_html,
    )

    st.markdown(
        '<a class="lean-monthly-link" href="/timing-map">Build your Year Ahead →</a>',
        unsafe_allow_html=True,
    )
    st.markdown('</section>', unsafe_allow_html=True)

def _luna_inline_story_title(value: str) -> str:
    """Standalone headings may use caps. Inline prose does not."""
    return inline_story_title(value)

def _luna_plain_prose(value: str, product: str = "timing") -> str:
    """One global customer-prose gate for every Luna product."""
    return finalize_customer_prose(value, product=product)

def _render_luna_prose(value: str, product: str = "timing") -> None:
    clean = _luna_plain_prose(value, product=product)
    if clean:
        st.markdown(
            f'<p class="luna-prose">{escape(clean)}</p>',
            unsafe_allow_html=True,
        )

def _brief_story_date(value: str) -> str:
    """Make engine date labels read like prose while preserving their selected year."""
    raw = re.sub(r"\s+", " ", str(value or "")).strip()
    match = re.fullmatch(r"0?(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})", raw)
    if match:
        day, month, year = match.groups()
        return f"{int(day)} {month.title()} {year}"
    return raw.title() if raw.isupper() else raw


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
    """Collect the Year Ahead birth details through the shared Natal Snapshot controls."""
    values = _natal_input_fields(
        "timing-v330",
        not_listed_label="Not listed — planetary timing only",
    )
    try:
        snapshot, _, prefill_out = _build_natal_from_values(values)
    except Exception as exc:
        return None, str(exc), None
    return snapshot, "", prefill_out



def _timing_signal_type(story) -> str:
    """Translate a transit story into a human signal type."""
    planet = str(getattr(story, "transit_planet", ""))
    polarity = str(getattr(story, "polarity", "")).lower()
    aspect = str(getattr(story, "aspect", "")).lower()
    supportive = aspect in {"trine", "sextile"}
    hard = aspect in {"square", "opposition"}

    if planet == "Jupiter":
        return "OPENING" if supportive or aspect == "conjunction" or "opportun" in polarity else "CAPACITY TEST"
    if planet == "Saturn":
        return "TERMS TEST" if hard else "STRUCTURE"
    if planet == "Uranus":
        return "FREER OPTION" if supportive else "CHANGE"
    if planet == "Neptune":
        return "IMAGINATION + FACTS" if supportive else "CLARITY TEST"
    if planet == "Pluto":
        return "POWER OPENING" if supportive else "POWER SHIFT"
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


def _timing_story_first_sentence(value: str) -> str:
    """Keep the annual synthesis readable by taking the first complete idea."""
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    if not value:
        return ""
    match = re.match(r"^(.+?[.!?])(?:\s|$)", value)
    return match.group(1).strip() if match else value


def _timing_story_sort_date(story, fallback: date) -> date:
    """Chronological anchor used by the annual narrator."""
    periods = list(getattr(story, "periods", None) or [])
    if periods:
        return min(item.start_date for item in periods)
    hits = list(getattr(story, "hits", None) or [])
    if hits:
        return min(hit.exact_date for hit in hits)
    return fallback


def _timing_story_arc_verb(story) -> str:
    """Turn Luna's neutral signal taxonomy into a concise narrative verb."""
    signal = _timing_signal_type(story)
    return {
        "TERMS TEST": "DEFINE",
        "STRUCTURE": "STABILISE",
        "OPENING": "OPEN",
        "CAPACITY TEST": "TEST CAPACITY",
        "FREER OPTION": "OPEN",
        "CHANGE": "CHANGE",
        "POWER OPENING": "OPEN",
        "POWER SHIFT": "SEE POWER",
        "IMAGINATION + FACTS": "VERIFY",
        "CLARITY TEST": "VERIFY",
        "SUPPORT": "USE SUPPORT",
        "FRICTION": "TEST",
        "MIXED": "SORT",
    }.get(signal, signal)


def _timing_pick_story_anchors(ordered: list, limit: int = 6) -> list:
    """
    Select anchors across the whole year instead of simply taking the first
    few stories. This keeps the synthesis representative of the 12-month arc.
    """
    if len(ordered) <= limit:
        return ordered

    last = len(ordered) - 1
    raw_indices = [
        0,
        1,
        round(last * 0.35),
        round(last * 0.55),
        round(last * 0.78),
        last,
    ]
    selected = []
    seen = set()
    for index in raw_indices:
        index = max(0, min(last, int(index)))
        story = ordered[index]
        headline = str(getattr(story, "headline", "") or "").strip().upper()
        identity = headline or id(story)
        if identity in seen:
            continue
        seen.add(identity)
        selected.append(story)
    return selected[:limit]


def _timing_year_story(report) -> dict:
    """Tell the annual human argument before the transit catalogue. Avoid repeated stock lines."""
    if not report.stories:
        return {}

    ordered = sorted(
        report.stories,
        key=lambda story: _timing_story_sort_date(story, report.end_date),
    )
    anchors = _timing_pick_story_anchors(ordered, limit=6)
    if not anchors:
        return {}

    areas = [simplify_life_area(_timing_story_life_area(story)) for story in anchors]
    used_commands: set[str] = set()
    used_scenes: set[str] = set()

    def command(area: str, seed: str) -> str:
        candidate = ""
        for index in range(8):
            candidate = imperative_for(area, f"{seed}-{index}")
            if candidate not in used_commands:
                used_commands.add(candidate)
                return candidate
        return candidate

    def scene(area: str, seed: str) -> str:
        candidate = ""
        for index in range(8):
            candidate = life_scene(area, f"{seed}-{index}", count=1)
            if candidate not in used_scenes:
                used_scenes.add(candidate)
                return candidate
        return candidate

    paragraphs = []
    first = areas[0]
    second = areas[1] if len(areas) > 1 else first
    paragraphs.append(
        "Set the terms first. "
        f"{command(first, 'year-start-a')} "
        f"{command(second, 'year-start-b')} "
        f"{scene(second, 'year-start')} "
        "Do not prove that you can handle more. Decide whether more deserves you."
    )

    if len(areas) >= 4:
        third, fourth = areas[2], areas[3]
        paragraphs.append(
            "Widen the field without widening the mess. "
            f"{command(third, 'year-middle-a')} "
            f"{scene(third, 'year-middle')} "
            f"{command(fourth, 'year-middle-b')} "
            + luna_dry_truth("general", third + fourth)
        )
    elif len(areas) >= 3:
        third = areas[2]
        paragraphs.append(
            "Widen the field. "
            f"{command(third, 'year-middle')} "
            f"{scene(third, 'year-middle')}"
        )

    if len(areas) >= 5:
        later = areas[4]
        final = areas[5] if len(areas) > 5 else later
        topic = life_domain(final)
        paragraphs.append(
            "Test what survives ordinary life. "
            f"{command(later, 'year-late-a')} "
            f"{scene(later, 'year-late')} "
            f"{command(final, 'year-late-b')} "
            "Stop compensating for an old arrangement once the choice is clear. "
            + luna_dry_truth(topic, later + final)
        )

    arc = list(human_arc(_timing_story_arc_verb(story) for story in ordered))

    chart_bridge = (
        "Use the chart to test the trade-off. "
        f"{command(first, 'chart-a')} "
        f"{command(second, 'chart-b')} "
        "Finish the decision in real life, not on the diagram."
    )
    return {"paragraphs": paragraphs, "arc": arc, "chart_bridge": chart_bridge}


def _timing_reader_move(story) -> str:
    """
    Keep the Timing Map calculation untouched while removing repeated template
    language from the reader-facing move.
    """
    headline = str(getattr(story, "headline", "") or "").strip().upper()
    move = str(getattr(story, "move", "") or "").strip()

    replacements = {
        "HOME NEEDS MORE AIR": (
            "Redesign the living or care arrangement so safety and breathing room can coexist. "
            "Remove the arrangement that works only because you keep absorbing the strain."
        ),
        "DISCIPLINE BECOMES LEVERAGE": (
            "Set the workload, deadline and stopping point before effort becomes its own justification. "
            "Cut the obligation that only works because you keep over-functioning."
        ),
        "THE AGREEMENT GETS TESTED": (
            "Define what is mutual, what it costs and what happens if the terms stay unequal. "
            "Renegotiate the term that survives only because one side keeps carrying more."
        ),
    }

    if headline in replacements:
        return replacements[headline]

    return move



def _timing_story_life_area(story) -> str:
    house = getattr(story, "natal_house", None)
    if house:
        try:
            return simplify_life_area(str(HOUSE_NAMES.get(int(house)) or f"House {int(house)}"))
        except Exception:
            return f"House {house}"
    target = str(getattr(story, "natal_target", "") or "").strip()
    if target:
        return simplify_life_area(f"Natal {target}")
    return "personal timing"


def _timing_target_house_bridge(story) -> str:
    """Explain why a natal target and its activated house can describe different but connected parts of life."""
    target = str(getattr(story, "natal_target", "") or "").strip()
    area = _timing_story_life_area(story)
    domain = life_domain(area)

    special = {
        ("Moon", "shared"): (
            "Home changes because the shared part changes with it: money, care or responsibility "
            "has to be renegotiated before the extra room becomes sustainable."
        ),
        ("Sun", "relationship"): (
            "The shift is personal, but another person or agreement is where you find out whether "
            "the new version of you actually fits."
        ),
        ("Ascendant", "shared"): (
            "The boundary starts with you, but shared money, trust or responsibility is where the new terms become measurable."
        ),
        ("Ascendant", "career"): (
            "The change starts with how you show up, but work is where the new boundary acquires a title, workload and consequence."
        ),
        ("Venus", "relationship"): (
            "What you value becomes measurable through the other person's effort, timing and willingness to carry the inconvenient part."
        ),
        ("Pluto", "travel"): (
            "The power shift becomes concrete through the outside route: permission, money, paperwork or who can actually move the plan forward."
        ),
        ("Neptune", "travel"): (
            "The uncertainty becomes concrete through the outside plan. Verify the booking, advice, paperwork or promise before you commit."
        ),
    }
    if (target, domain) in special:
        return special[(target, domain)]

    target_phrase = {
        "Ascendant": "how you show up and set boundaries",
        "Midheaven": "work and public responsibility",
        "Sun": "identity and direction",
        "Moon": "home and emotional security",
        "Mercury": "the conversation or decision",
        "Venus": "what you value in love or money",
        "Mars": "effort and the move you are making",
        "Jupiter": "growth and the larger option",
        "Saturn": "responsibility and limits",
        "Uranus": "freedom and the rule that needs changing",
        "Neptune": "the story that still needs evidence",
        "Pluto": "power and leverage",
        "True Node": "the route you are growing toward",
    }.get(target, "")

    house_phrase = {
        "identity": "how you show up",
        "home": "home and private life",
        "relationship": "the other person and the agreement",
        "shared": "shared money, trust or responsibility",
        "career": "work and public responsibility",
        "travel": "the trip, course, application or outside plan",
        "routine": "the workload and ordinary week",
        "money": "the real number",
        "communication": "the message or decision",
        "romance": "the person, pleasure or creative project",
        "friends": "the people and next plan",
        "rest": "what needs rest or closure",
    }.get(domain, area)

    if not target_phrase or target_phrase.lower() in house_phrase.lower() or house_phrase.lower() in target_phrase.lower():
        return ""
    return (
        f"The first question is {target_phrase}; {house_phrase} is where you will see whether the answer actually works."
    )


def _timing_story_start(story) -> date | None:
    periods = list(getattr(story, "periods", None) or [])
    return min((item.start_date for item in periods), default=None)


def _timing_story_end(story) -> date | None:
    periods = list(getattr(story, "periods", None) or [])
    return max((item.end_date for item in periods), default=None)


def _timing_story_peak_label(story) -> str:
    hits = list(getattr(story, "hits", None) or [])
    if not hits:
        return "—"
    return " · ".join(_timing_date_label(hit.exact_date) for hit in hits[:3])


def _timing_story_confidence(story) -> str:
    hits = list(getattr(story, "hits", None) or [])
    if not hits:
        return "Moderate"
    min_orb = min(float(getattr(hit, "orb", 9.0) or 9.0) for hit in hits)
    if min_orb <= 0.50:
        return "High"
    if min_orb <= 1.00:
        return "Medium"
    return "Moderate"


def _timing_story_overlap(story, start_date: date, end_date: date) -> bool:
    for period in list(getattr(story, "periods", None) or []):
        if period.start_date <= end_date and period.end_date >= start_date:
            return True
    return False


def _timing_period_window(report, mode: str) -> tuple[date, date]:
    reference = report.start_date
    if mode == "Now":
        return reference, reference
    if mode == "30 Days":
        return reference, min(report.end_date, reference + timedelta(days=30))
    if mode == "90 Days":
        return reference, min(report.end_date, reference + timedelta(days=90))
    return reference, report.end_date


def _timing_active_stories(report, mode: str) -> list:
    start_date, end_date = _timing_period_window(report, mode)
    stories = [story for story in report.stories if _timing_story_overlap(story, start_date, end_date)]

    def nearest_hit(story):
        hits = list(getattr(story, "hits", None) or [])
        if not hits:
            return 999999
        return min(abs((hit.exact_date - start_date).days) for hit in hits)

    return sorted(stories, key=nearest_hit)



def _timing_motion_summary(report, mode: str, stories: list) -> str:
    if not stories:
        if mode == "Now":
            return "The chart is comparatively quiet at the selected starting point. Finish what is already open rather than inventing a crisis."
        return f"The selected {mode.lower()} window is comparatively quiet. Finish what is already open before you add another demand."

    period_text = {
        "Now": "At the selected starting point",
        "30 Days": "Over the next 30 days",
        "90 Days": "Over the next 90 days",
        "12 Months": "Across the next 12 months",
    }[mode]

    first = stories[0]
    first_area = _timing_story_life_area(first)
    first_domain = life_domain(first_area)
    first_commands = {
        "identity": "start with how you show up, where you set boundaries and what version of you other people are meeting",
        "home": "start with home, family and what the private life can actually carry",
        "relationship": "start with the person across the table and the promises between you",
        "shared": "start with shared money, trust and responsibility",
        "career": "start with the job, role or public responsibility attached to your name",
        "travel": "start with the trip, course, application or outside opportunity",
        "routine": "start with the workload and ordinary week you actually have to live",
        "money": "start with the number, price or financial commitment",
        "communication": "start with the conversation, document or decision",
        "romance": "start with the person, pleasure or creative project pulling your attention",
        "friends": "start with the people and plan you are trying to build with",
        "rest": "start with what needs privacy, rest or a clean ending",
    }
    first_sentence = first_commands.get(first_domain, f"start with {first_area}")

    if len(stories) > 1:
        second = stories[1]
        second_area = _timing_story_life_area(second)
        second_domain = life_domain(second_area)
        second_labels = {
            "identity": "how you show up",
            "home": "home and private life",
            "relationship": "the other person and the agreement",
            "shared": "shared money or responsibility",
            "career": "work and public responsibility",
            "travel": "the outside plan and its logistics",
            "routine": "the workload and ordinary week",
            "money": "the real number",
            "communication": "the message or decision",
            "romance": "the person or project you want",
            "friends": "the people and next plan",
            "rest": "what needs rest or closure",
        }
        second_label = second_labels.get(second_domain, second_area)
        return (
            f"{period_text}, {first_sentence}. "
            f"Then test the first move against {second_label}. "
            "The change is real only if it can survive both places."
        )
    return (
        f"{period_text}, {first_sentence}. "
        "Make the first move concrete enough that ordinary life can test it."
    )



def _timing_activation_wheel_svg(report, mode: str, size: int = 620) -> str:
    """
    Restrained activation layer. Colour encodes activity only:
    shaded sectors = activated houses, violet = natal target, orange = transiting planet.
    """
    stories = _timing_active_stories(report, mode)
    width = height = int(size)
    cx = cy = width / 2
    outer = width * 0.39
    inner = width * 0.25
    label_r = width * 0.345

    house_counts: dict[int, int] = {}
    house_stories: dict[int, list] = {}
    for story in stories:
        house = getattr(story, "natal_house", None)
        try:
            house = int(house) if house else None
        except Exception:
            house = None
        if house and 1 <= house <= 12:
            house_counts[house] = house_counts.get(house, 0) + 1
            house_stories.setdefault(house, []).append(story)

    max_count = max(house_counts.values(), default=1)

    def polar(radius, degrees):
        angle = math.radians(degrees - 90)
        return cx + radius * math.cos(angle), cy + radius * math.sin(angle)

    def sector_path(house):
        start_deg = (house - 1) * 30
        end_deg = house * 30
        x1, y1 = polar(outer, start_deg)
        x2, y2 = polar(outer, end_deg)
        x3, y3 = polar(inner, end_deg)
        x4, y4 = polar(inner, start_deg)
        return (
            f"M {x1:.2f},{y1:.2f} "
            f"A {outer:.2f},{outer:.2f} 0 0 1 {x2:.2f},{y2:.2f} "
            f"L {x3:.2f},{y3:.2f} "
            f"A {inner:.2f},{inner:.2f} 0 0 0 {x4:.2f},{y4:.2f} Z"
        )

    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="Natal chart activation layer">'
    ]

    for house in range(1, 13):
        count = house_counts.get(house, 0)
        opacity = 0.08 if count == 0 else 0.18 + (0.34 * count / max_count)
        fill = "#f4f4f1" if count == 0 else "#6977df"
        parts.append(
            f'<path d="{sector_path(house)}" fill="{fill}" fill-opacity="{opacity:.2f}" '
            f'stroke="#d8d8d3" stroke-width="1"/>'
        )
        lx, ly = polar(label_r, (house - 0.5) * 30)
        parts.append(
            f'<text x="{lx:.2f}" y="{ly:.2f}" text-anchor="middle" dominant-baseline="middle" '
            f'font-family="IBM Plex Mono, monospace" font-size="12" fill="#444">{house}</text>'
        )

    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{inner}" fill="#fff" stroke="#d8d8d3" stroke-width="1"/>'
    )
    parts.append(
        f'<text x="{cx}" y="{cy-8}" text-anchor="middle" '
        f'font-family="Bodoni MT, Georgia, serif" font-size="25" fill="#151515">YOUR CHART</text>'
    )
    parts.append(
        f'<text x="{cx}" y="{cy+16}" text-anchor="middle" '
        f'font-family="IBM Plex Mono, monospace" font-size="10" letter-spacing="1.4" fill="#696963">'
        f'{escape(mode.upper())}</text>'
    )

    for house, house_items in house_stories.items():
        angle = (house - 0.5) * 30
        natal_x, natal_y = polar(inner + (outer-inner) * 0.38, angle)
        transit_x, transit_y = polar(outer + 23, angle)
        story = house_items[0]
        target = str(getattr(story, "natal_target", "") or "").strip()
        transit = str(getattr(story, "transit_planet", "") or "").strip()

        hits = list(getattr(story, "hits", None) or [])
        min_orb = min((float(getattr(hit, "orb", 2.0) or 2.0) for hit in hits), default=2.0)
        line_width = max(1.2, 3.2 - min(min_orb, 2.0))
        applying = True
        if hits:
            nearest = min(hits, key=lambda hit: abs((hit.exact_date - report.start_date).days))
            applying = nearest.exact_date >= report.start_date
        dash = "" if applying else ' stroke-dasharray="6 5"'

        parts.append(
            f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{natal_x:.2f}" y2="{natal_y:.2f}" '
            f'stroke="#6757c7" stroke-width="{line_width:.2f}" stroke-opacity=".72"{dash}/>'
        )
        parts.append(f'<circle cx="{natal_x:.2f}" cy="{natal_y:.2f}" r="9" fill="#6757c7"/>')
        if target:
            parts.append(
                f'<text x="{natal_x:.2f}" y="{natal_y-14:.2f}" text-anchor="middle" '
                f'font-family="Josefin Sans, sans-serif" font-size="11" font-weight="600" fill="#332a76">'
                f'{escape(target[:12])}</text>'
            )
        parts.append(f'<circle cx="{transit_x:.2f}" cy="{transit_y:.2f}" r="8" fill="#e58a2f"/>')
        if transit:
            parts.append(
                f'<text x="{transit_x:.2f}" y="{transit_y-13:.2f}" text-anchor="middle" '
                f'font-family="IBM Plex Mono, monospace" font-size="9" fill="#7a4818">'
                f'{escape(transit[:8].upper())}</text>'
            )

    parts.append("</svg>")
    return "".join(parts)



def _luna_first_sentence(value: str) -> str:
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    if not value:
        return ""
    match = re.match(r"^(.+?[.!?])(?:\s|$)", value)
    return match.group(1).strip() if match else value


_SIGN_IDENTITY = {
    "Aries": 'direct, self-starting and impatient with permission',
    "Taurus": 'steady, value-conscious and slow to abandon what has proved reliable',
    "Gemini": 'curious, mentally mobile and comfortable keeping several possibilities alive',
    "Cancer": 'protective, emotionally responsive and highly aware of loyalty and belonging',
    "Leo": 'expressive, proud and driven to create something worth being seen for',
    "Virgo": 'observant, improvement-minded and quick to notice what could work better',
    "Libra": 'relationship-aware, fairness-conscious and sensitive to reciprocity and reasonable terms',
    "Scorpio": 'private, intense and unwilling to live indefinitely with superficial explanations',
    "Sagittarius": 'future-facing, freedom-seeking and drawn toward a larger field of possibility',
    "Capricorn": 'responsibility-conscious, strategic and willing to build slowly when the structure deserves it',
    "Aquarius": 'independent-minded, pattern-aware and resistant to rules that no longer make sense',
    "Pisces": 'imaginative, receptive and highly responsive to atmosphere, meaning and emotional undercurrents',
}

_SIGN_EMOTION = {
    "Aries": 'react quickly and usually know what you feel before you can explain why',
    "Taurus": 'need steadiness and may hold on too long before admitting something no longer feels safe',
    "Gemini": 'process feeling through thought, language and comparison',
    "Cancer": 'remember emotional tone deeply and protect what matters long after other people move on',
    "Leo": 'need warmth, loyalty and proof that your heart is being met openly',
    "Virgo": 'try to solve the feeling by improving the situation',
    "Libra": 'look for balance and may delay confrontation while you understand both sides',
    "Scorpio": 'feel deeply, notice what is unsaid and remember what people did more than what they promised',
    "Sagittarius": 'recover through movement, perspective and proof that life is still opening',
    "Capricorn": 'contain emotion until there is a practical reason or safe structure for showing it',
    "Aquarius": 'need space and perspective before you can name the feeling cleanly',
    "Pisces": "absorb atmosphere easily and need solitude to separate your feelings from everyone else's",
}

_SIGN_RISING = {
    "Aries": 'direct, self-contained and ready to act before the inside of you feels ready',
    "Taurus": 'calm, steady and harder to move than the inside of you may feel',
    "Gemini": 'quick, adaptable and mentally alert',
    "Cancer": 'careful, receptive and protective',
    "Leo": 'visible, expressive and self-possessed',
    "Virgo": 'observant, useful and composed',
    "Libra": 'socially aware, measured and diplomatic',
    "Scorpio": 'contained, watchful and difficult to read quickly',
    "Sagittarius": 'open, mobile and future-facing',
    "Capricorn": 'competent, contained and ready to carry responsibility',
    "Aquarius": 'independent, slightly detached and difficult to categorise',
    "Pisces": 'soft-edged, receptive and impressionable',
}

_SIGN_MERCURY = {
    "Aries": 'think quickly and prefer a straight answer',
    "Taurus": 'think deliberately and trust what can be made concrete',
    "Gemini": 'think by connecting, comparing and talking things through',
    "Cancer": 'think through memory, context and emotional meaning',
    "Leo": 'think in large themes and want the point to matter',
    "Virgo": 'think diagnostically and spot errors, omissions and practical improvements',
    "Libra": 'think relationally and weigh fairness, alternatives and how each side will receive the message',
    "Scorpio": 'think beneath the surface and look for motive, leverage and what has not been said',
    "Sagittarius": 'think in principles, patterns and larger meaning',
    "Capricorn": 'think strategically and ask what is workable and sustainable',
    "Aquarius": 'think systemically and care more about the pattern than the convention',
    "Pisces": 'think associatively, intuitively and through images or atmosphere',
}

_SIGN_VENUS = {
    "Aries": 'need aliveness, honesty and room for each person to remain themselves',
    "Taurus": 'value loyalty, consistency, touch and proof over performance',
    "Gemini": 'need conversation, curiosity and a relationship that keeps moving mentally',
    "Cancer": 'value emotional safety, care and a sense of home with another person',
    "Leo": 'need warmth, loyalty and visible appreciation',
    "Virgo": 'show love through usefulness, reliability and attention to detail',
    "Libra": 'need reciprocity, good faith and terms that feel fair',
    "Scorpio": 'need depth, loyalty and emotional truth more than surface harmony',
    "Sagittarius": 'need honesty, space and a relationship that enlarges life rather than shrinking it',
    "Capricorn": 'value reliability, maturity and relationships that can carry real-world weight',
    "Aquarius": 'need friendship, independence and a bond that does not erase individuality',
    "Pisces": 'value tenderness, emotional resonance and meaningful connection',
}

_SIGN_MARS = {
    "Aries": 'act quickly and would rather test something than discuss it forever',
    "Taurus": 'act slowly but become formidable once committed',
    "Gemini": 'act through movement, conversation and experimentation',
    "Cancer": 'act protectively and become highly motivated when security is at stake',
    "Leo": 'act boldly when pride, creativity or loyalty is involved',
    "Virgo": 'act by fixing, organising, improving and taking responsibility for what is not working',
    "Libra": 'act through negotiation and may hesitate until you have considered every side',
    "Scorpio": 'act strategically and rarely spend force casually',
    "Sagittarius": 'act toward freedom, experience and a larger horizon',
    "Capricorn": 'act methodically and will carry a long effort when the objective is worth it',
    "Aquarius": 'act independently and will break a pattern other people have normalised',
    "Pisces": 'act intuitively and move strongly when imagination, compassion or meaning is engaged',
}


def _timing_repeated_transit_themes(report) -> list[str]:
    """Return the dominant slower-planet themes actually present in this report."""
    counts = {}
    for story in list(getattr(report, "stories", None) or []):
        planet = str(getattr(story, "transit_planet", "") or "").strip()
        if planet:
            counts[planet] = counts.get(planet, 0) + 1
    return [planet for planet, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]



def _timing_natal_person_summary(snapshot, report=None) -> list[str]:
    """Natal baseline only. Current transits belong in the year-pattern section."""
    refs = dict(_chart_natal_reference_items(snapshot))
    sun = refs.get("Sun sign", "Not calculated")
    moon = refs.get("Moon", "Not calculated")
    rising = refs.get("Rising", "Not calculated")
    mercury = refs.get("Mercury", "Not calculated")
    venus = refs.get("Venus", "Not calculated")
    mars = refs.get("Mars", "Not calculated")

    paragraphs = []

    if sun in _SIGN_IDENTITY and moon in _SIGN_EMOTION:
        paragraphs.append(
            f"Notice the contradiction. You are {_SIGN_IDENTITY[sun]}. You {_SIGN_EMOTION[moon]}. "
            "Do not confuse the surface with the decision-making underneath."
        )
    elif sun in _SIGN_IDENTITY:
        paragraphs.append(
            f"Start with the baseline. You are {_SIGN_IDENTITY[sun]}. "
            "Do not turn that tendency into a fixed identity."
        )

    if rising in _SIGN_RISING and mercury in _SIGN_MERCURY:
        paragraphs.append(
            f"Watch how you enter a room. {rising} Rising makes you look {_SIGN_RISING[rising]}. "
            f"Mercury in {mercury} means you {_SIGN_MERCURY[mercury]}. "
            "Trust what you notice. Verify it before you act."
        )
    elif mercury in _SIGN_MERCURY:
        paragraphs.append(
            f"Watch your thinking. Mercury in {mercury} means you {_SIGN_MERCURY[mercury]}. "
            "Name the assumption before it becomes a conclusion."
        )

    if venus in _SIGN_VENUS and mars in _SIGN_MARS:
        paragraphs.append(
            f"Name what you need. Venus in {venus} means you {_SIGN_VENUS[venus]}. "
            f"Mars in {mars} means you {_SIGN_MARS[mars]}. "
            "What you want from another person is not always how you behave when something goes wrong. "
            "Stop compensating before the imbalance becomes invisible."
        )

    return paragraphs


def _timing_year_pattern_summary(report) -> list[str]:
    """Current slow-transit pattern, separated from the natal baseline."""
    paragraphs = []
    themes = _timing_repeated_transit_themes(report)

    if "Saturn" in themes and "Uranus" in themes:
        paragraphs.append(
            "Count the load. Saturn asks you to define responsibility. "
            "Uranus asks where the structure has become too restrictive. "
            "You can keep a bad arrangement alive because you are capable. "
            "Capability is not proof that the arrangement deserves you."
        )
        paragraphs.append(
            "Break the cycle earlier. Notice the problem. Fix it. Carry more. "
            "Keep going. Get tired. Want out immediately. "
            "Stop before freedom requires destruction."
        )
    elif "Saturn" in themes:
        paragraphs.append(
            "Count what you are carrying. Saturn keeps returning to responsibility, limits and terms. "
            "Do not ask only whether you can handle it. Ask whether you should still be the person handling it."
        )

    relationship_relevant = False
    for story in report.stories:
        target = str(getattr(story, "natal_target", "") or "").lower()
        area = _timing_story_life_area(story).lower()
        house = str(getattr(story, "natal_house", "") or "")
        if target == "venus" or house == "7" or "relationship" in area or "agreement" in area:
            relationship_relevant = True
            break

    if relationship_relevant:
        paragraphs.append(
            "Test the bond. You do not necessarily struggle to form relationships. "
            "The harder risk is keeping them alive after the terms stop being equal. "
            "When the agreement is tested, ask who is carrying the relationship. "
            "Stop compensating. Keep what remains mutual."
        )
    return paragraphs


def _timing_recurrence_question(story, age: int | None = None) -> str:
    """One human memory prompt derived from transit + target and adjusted for life stage."""
    planet = str(getattr(story, "transit_planet", "") or "")
    target = str(getattr(story, "natal_target", "") or "")
    area = _timing_story_life_area(story)
    young = age is not None and age < 18

    if planet == "Saturn" and target == "Midheaven":
        if young:
            return (
                "Were expectations becoming heavier? Did school, family, a teacher, coach or another authority "
                "start asking you to become more responsible, visible or self-controlled than before?"
            )
        return (
            "Were expectations becoming heavier? Did work, family or another authority start asking you to carry "
            "more responsibility, visibility or self-control than before?"
        )
    if planet == "Saturn" and target == "Venus":
        return (
            "Did a relationship, friendship or agreement reveal an imbalance in effort, loyalty, money or responsibility? "
            "Were you learning what you would and would not continue carrying for somebody else?"
        )
    if planet == "Jupiter" and target == "Ascendant":
        return (
            "Did life suddenly feel larger — more people, confidence, movement or permission to become a different version of yourself?"
        )
    if planet == "Jupiter" and target == "Moon":
        if young:
            return (
                "Did something at home or in the family expand or change enough that you had to become more adaptable or responsible?"
            )
        return (
            "Did home, family or money start requiring more from you than the original plan allowed?"
        )
    if planet == "Uranus":
        return (
            f"Did something in {area} stop feeling inevitable? "
            "Were you testing a new rule, more distance or a different way of doing it?"
        )
    if planet == "Pluto":
        return (
            f"Did something in {area} make the real balance of power harder to ignore? "
            "Who could decide, withhold, leave or change the terms?"
        )
    if target == "Venus":
        return "What was changing between you and another person? What were each of you actually promising?"
    if target == "Moon":
        return "What changed at home, in the family or in what you needed to feel secure?"
    if target == "Mercury":
        return "What conversation, document or decision became harder to postpone?"
    if target == "Sun":
        return "What role or direction stopped fitting as cleanly as it had before?"
    return f"What changed in {area}, and what did you have to decide because of it?"



def _timing_past_pattern_summary(report, birth_date_value: date | None) -> list[str]:
    """Use recurrence as memory. Never invent biography or expose transit-family jargon."""
    if not birth_date_value:
        return []

    rows = []
    seen = set()
    for story in report.stories:
        earlier = _previous_transit_echo_date(story)
        if earlier is None or earlier < birth_date_value:
            continue

        key = (str(story.transit_planet), str(story.natal_target), earlier.year)
        if key in seen:
            continue
        seen.add(key)

        age = earlier.year - birth_date_value.year - (
            (earlier.month, earlier.day) < (birth_date_value.month, birth_date_value.day)
        )
        area = _timing_story_life_area(story)
        rows.append(
            f"{_timing_date_label(earlier)} · about age {age}. "
            f"Think back. {_timing_recurrence_question(story, age=age)} "
            f"{life_scene(area, f'history-{earlier.year}', count=1, age=age)} "
            "The event can differ. The pressure can rhyme. Name what you learned to carry then."
        )
        if len(rows) >= 3:
            break
    return rows

def _timing_relationship_timing(report) -> dict:
    """Find relationship-opening and relationship-testing windows from the ranked transit stories."""
    opening_candidates = []
    test_candidates = []

    for story in report.stories:
        target = str(getattr(story, "natal_target", "") or "")
        planet = str(getattr(story, "transit_planet", "") or "")
        area = _timing_story_life_area(story).lower()
        house = getattr(story, "natal_house", None)
        signal = _timing_signal_type(story).upper()
        polarity = str(getattr(story, "polarity", "") or "").lower()

        relationship_relevant = (
            target.lower() == "venus"
            or str(house) == "7"
            or life_domain(area) == "relationship"
        )
        if not relationship_relevant:
            continue

        if planet == "Jupiter" or signal in {"OPENING", "EXPANSION", "SUPPORT"} or "opportun" in polarity:
            opening_candidates.append(story)
        if planet == "Saturn" or signal in {"DECISION", "STRUCTURE", "FRICTION"} or "pressure" in polarity:
            test_candidates.append(story)

    def start_of(story):
        return _timing_story_start(story) or report.end_date

    result = {}
    if opening_candidates:
        story = sorted(opening_candidates, key=start_of)[0]
        result["opening"] = story
    if test_candidates:
        story = sorted(test_candidates, key=start_of)[0]
        result["test"] = story
    return result


def _timing_story_phase_label(story, limit: int = 3) -> str:
    periods = list(getattr(story, "periods", None) or [])
    if not periods:
        return "—"
    labels = []
    for period in periods[:limit]:
        labels.append(
            f"{_timing_date_label(period.start_date)} → {_timing_date_label(period.end_date)}"
        )
    return " · ".join(labels)



def _timing_relationship_overlaps(opening, test) -> list[tuple[date, date]]:
    if opening is None or test is None:
        return []

    overlaps = []
    for left in list(getattr(opening, "periods", None) or []):
        for right in list(getattr(test, "periods", None) or []):
            start = max(left.start_date, right.start_date)
            end = min(left.end_date, right.end_date)
            if start <= end:
                overlaps.append((start, end))
    overlaps.sort()
    return overlaps


def _render_timing_person_relationship_summary(report, snapshot, birth_date_value: date | None) -> None:
    st.markdown("## The person behind the transits")
    for paragraph in _timing_natal_person_summary(snapshot, report):
        _render_luna_prose(paragraph)

    year_pattern = _timing_year_pattern_summary(report)
    if year_pattern:
        st.markdown("### The pattern this year activates")
        for paragraph in year_pattern:
            _render_luna_prose(paragraph)

    past = _timing_past_pattern_summary(report, birth_date_value)
    if past:
        st.markdown("### What may have repeated before")
        _render_luna_prose(
            "Think back. Use these dates as memory prompts. Do not force the old event to match the present one."
        )
        for paragraph in past:
            _render_luna_prose(paragraph)

    relationship = _timing_relationship_timing(report)
    if relationship:
        st.markdown("## Relationship timing")
        _render_luna_prose(
            "Treat the first window as an opening. Not a promise. Let someone get closer. Keep your eyes open. "
            "Use the later window to test whether the relationship can carry equal terms when chemistry stops doing all the work."
        )

        opening = relationship.get("opening")
        if opening:
            start = _timing_story_start(opening)
            end = _timing_story_end(opening)
            _render_luna_prose(
                f"Opening phases · {_timing_story_phase_label(opening)}. "
                f"Strongest around {_timing_story_peak_label(opening)}. "
                "Meet people. Widen the field. Let an existing connection grow only if the effort stays mutual."
            )

        test = relationship.get("test")
        if test:
            _render_luna_prose(
                f"Seriousness phases · {_timing_story_phase_label(test)}. "
                f"Strongest around {_timing_story_peak_label(test)}. "
                "Watch what happens when life becomes ordinary. Keep what is mutual. Renegotiate what is not."
            )

        overlaps = _timing_relationship_overlaps(opening, test)
        if overlaps:
            overlap_label = " · ".join(
                f"{_timing_date_label(start)} → {_timing_date_label(end)}"
                for start, end in overlaps[:2]
            )
            _render_luna_prose(
                f"Key overlap · {overlap_label}. Opportunity and reality testing are active together. "
                "A connection can open and immediately show whether it can carry equal terms."
            )

def _timing_chart_story(report, snapshot, mode: str, stories: list) -> list[str]:
    if not stories:
        return ["Do not force a story here. Use the quiet window to finish what is already open."]

    raw_areas = []
    for story in stories[:4]:
        area = _timing_story_life_area(story)
        if area not in raw_areas:
            raw_areas.append(area)

    first = raw_areas[0]
    if len(raw_areas) >= 2:
        second = raw_areas[1]
        return [
            f"{imperative_for(first, f'chart-{mode}-a')} "
            f"{life_scene(first, f'chart-{mode}-a', count=1)}",
            f"{imperative_for(second, f'chart-{mode}-b')} "
            "Check who pays, waits or reorganises when you make the first move.",
        ]
    return [
        f"{imperative_for(first, f'chart-{mode}')} "
        f"{life_scene(first, f'chart-{mode}', count=1)}"
    ]

def _monthly_story_of_month(events: list[dict], sign: str) -> dict:
    """One human sequence: possibility -> choice -> consequence."""
    if not events:
        return {}

    chosen = events[:4]
    first = chosen[0]
    first_sentence = _luna_first_sentence(
        first.get("voice_lead") or (first.get("body") or [""])[0]
    )
    first_sentence = first_sentence[:1].lower() + first_sentence[1:] if first_sentence else "a possibility becomes real"

    paragraphs = [
        f"Around {_brief_story_date(first['date_label'])}, {first_sentence}. "
        "Do not commit before the details hold."
    ]

    if len(chosen) >= 2:
        second = chosen[1]
        second_sentence = _luna_first_sentence(
            second.get("voice_lead") or (second.get("body") or [""])[0]
        )
        second_sentence = second_sentence[:1].lower() + second_sentence[1:] if second_sentence else "interest becomes a decision"
        paragraphs.append(
            f"By {_brief_story_date(second['date_label'])}, {second_sentence}. "
            "Choose what has substance. Let the weaker option lose priority."
        )

    if len(chosen) >= 3:
        last = chosen[-1]
        last_sentence = _luna_first_sentence(
            last.get("voice_lead") or (last.get("body") or [""])[0]
        )
        last_sentence = last_sentence[:1].lower() + last_sentence[1:] if last_sentence else "the plan reaches daily life"
        paragraphs.append(
            f"Later, {last_sentence}. Keep what still works once the excitement wears off. "
            + luna_dry_truth("general", str(last.get("title") or sign))
        )

    return {
        "paragraphs": paragraphs,
        "arc": list(human_arc(str(event.get("signal") or "") for event in chosen)),
    }

def _monthly_chart_story(result: dict, events: list[dict], selected_key: str) -> list[str]:
    selected = events if selected_key == "whole" else [e for e in events if e.get("key") == selected_key]
    if not selected:
        return []

    houses = _monthly_active_house_numbers(result, events, selected_key)
    raw_areas = [HOUSE_NAMES.get(h, f"House {h}") for h in houses[:2]]

    if selected_key == "whole":
        if len(raw_areas) >= 2:
            return [
                f"{imperative_for(raw_areas[0], 'month-chart-a')} "
                f"{life_scene(raw_areas[0], 'month-chart-a', count=1)}",
                f"{imperative_for(raw_areas[1], 'month-chart-b')} "
                "Keep one standard while the dates change.",
            ]
        if raw_areas:
            return [convergent_bridge(raw_areas[0], seed_text="month-chart", include_scene=True)]
        return ["Follow the strongest date. Make the move concrete."]

    event = selected[0]
    move = str(event.get("move") or "").strip()
    area = raw_areas[0] if raw_areas else str(event.get("title") or "general")
    return [
        f"{imperative_for(area, f'month-date-{selected_key}')} "
        f"{life_scene(area, f'month-date-{selected_key}', count=1)}",
        finalize_customer_prose(move, product="monthly")
        if move else "Name what becomes harder to postpone. Decide from there.",
    ]

def _timing_chart_in_motion(report, snapshot, *, include_legacy_interpretation: bool = True) -> None:
    st.markdown("## Your Chart in Motion")
    st.caption(
        "Colour shows activity, not good or bad. The natal chart stays restrained; the activation layer shows which houses and natal targets are being contacted in the selected period. Solid lines are approaching contacts; dashed lines are separating."
    )

    _render_chart_natal_reference(snapshot)

    mode = st.radio(
        "Chart period",
        ["Now", "30 Days", "90 Days", "12 Months"],
        index=2,
        horizontal=True,
        key="timing-chart-period-v401",
    )
    active_stories = _timing_active_stories(report, mode)
    if include_legacy_interpretation:
        st.markdown(
            f'<div class="chart-motion-summary">{escape(_timing_motion_summary(report, mode, active_stories))}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("### Read the pressure, not the picture")
        for paragraph in _timing_chart_story(report, snapshot, mode, active_stories):
            _render_luna_prose(paragraph, product="timing")

    timing_active_houses = _timing_active_house_numbers(active_stories)
    active_label = "ACTIVE NOW" if mode == "Now" else f"MOST ACTIVE · {mode.upper()}"
    _render_active_house_legend(timing_active_houses, active_label)

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("**Natal reference**")
        st.markdown(natal_wheel_svg(snapshot, size=620), unsafe_allow_html=True)
    with right:
        st.markdown("**Activation layer**")
        st.markdown(_timing_activation_wheel_svg(report, mode, size=620), unsafe_allow_html=True)
        st.markdown(
            '<div class="chart-motion-legend">'
            '<div class="chart-motion-key"><i class="chart-motion-swatch house"></i>Activated house</div>'
            '<div class="chart-motion-key"><i class="chart-motion-swatch natal"></i>Natal target</div>'
            '<div class="chart-motion-key"><i class="chart-motion-swatch transit"></i>Transiting planet</div>'
            '</div><div class="small-note">Line weight increases as the orb tightens.</div>',
            unsafe_allow_html=True,
        )

    _render_house_key()




def _render_timing_result_actions() -> None:
    """
    Reader controls for printing/saving the personalised Year Ahead report
    and sharing the public Timing Map page.

    This intentionally mirrors the working Monthly action row.
    The shared URL contains no birth data or session state.
    """
    title = "Your Year Ahead · Personal Transits & Timing · Luna Convergence"
    safe_title = escape(title)
    timing_share_url = "https://luna-convergence.streamlit.app/timing-map"

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">KEEP OR SHARE YOUR READING</div>', unsafe_allow_html=True)

    components.html(
        f"""
        <div id="luna-timing-result-actions" style="
            display:flex;flex-wrap:wrap;gap:10px;align-items:center;
            font-family:Arial,sans-serif;margin:0;padding:0 0 2px 0;">
          <button id="luna-timing-print" type="button" style="
              min-height:44px;padding:10px 16px;border:1px solid #111;background:#111;color:#fff;
              font-size:13px;letter-spacing:.04em;text-transform:uppercase;cursor:pointer;">
            Print / Save PDF
          </button>
          <button id="luna-timing-share" type="button" style="
              min-height:44px;padding:10px 16px;border:1px solid #111;background:#fff;color:#111;
              font-size:13px;letter-spacing:.04em;text-transform:uppercase;cursor:pointer;">
            Share page link
          </button>
          <span id="luna-timing-action-status" style="font-size:12px;color:#666;min-width:160px;"></span>
        </div>

        <script>
        (() => {{
          const printBtn = document.getElementById("luna-timing-print");
          const shareBtn = document.getElementById("luna-timing-share");
          const status = document.getElementById("luna-timing-action-status");

          function parentWindow() {{
            try {{ return window.parent; }} catch (e) {{ return window; }}
          }}

          function parentDocument() {{
            try {{ return window.parent.document; }} catch (e) {{ return null; }}
          }}

          function pageUrl() {{
            return "{timing_share_url}";
          }}

          function openExpandersForPrint() {{
            const doc = parentDocument();
            if (!doc) return;
            const details = doc.querySelectorAll(
              '[data-testid="stExpander"] details, details[data-testid="stExpander"]'
            );
            details.forEach((node) => {{
              if (!node.open) {{
                node.dataset.lunaPrintOpened = "1";
                node.open = true;
              }}
            }});
          }}

          function restoreExpandersAfterPrint() {{
            const doc = parentDocument();
            if (!doc) return;
            doc.querySelectorAll('details[data-luna-print-opened="1"]').forEach((node) => {{
              node.open = false;
              delete node.dataset.lunaPrintOpened;
            }});
          }}

          try {{
            const parent = parentWindow();
            if (!parent.__lunaTimingPrintHooksInstalled) {{
              parent.__lunaTimingPrintHooksInstalled = true;
              parent.addEventListener("beforeprint", openExpandersForPrint);
              parent.addEventListener("afterprint", restoreExpandersAfterPrint);
            }}
          }} catch (e) {{}}

          printBtn.addEventListener("click", () => {{
            status.textContent = "Opening print dialogâ€¦";
            openExpandersForPrint();
            setTimeout(() => {{
              try {{ parentWindow().print(); }}
              catch (e) {{ window.print(); }}
              setTimeout(() => {{ status.textContent = ""; }}, 700);
            }}, 180);
          }});

          shareBtn.addEventListener("click", async () => {{
            const url = pageUrl();
            const payload = {{
              title: "{safe_title}",
              text: "Luna Convergence Year Ahead astrology page. Personal birth details are not included in this link.",
              url
            }};

            if (navigator.share) {{
              try {{
                await navigator.share(payload);
                status.textContent = "Share sheet opened.";
                return;
              }} catch (e) {{
                if (e && e.name === "AbortError") {{
                  status.textContent = "";
                  return;
                }}
              }}
            }}

            try {{
              await navigator.clipboard.writeText(url);
              status.textContent = "Page link copied.";
            }} catch (e) {{
              window.prompt("Copy this Luna page link:", url);
              status.textContent = "Copy the link shown.";
            }}
          }});
        }})();
        </script>
        """,
        height=62,
        scrolling=False,
    )

    st.caption(
        "For a personalised copy, choose **Print / Save PDF**. "
        "**Share page link** shares only the public Year Ahead page — "
        "birth details and your session are deliberately not placed in the URL."
    )


def _timing_target_human_meaning(story) -> str:
    """Translate the natal target into the ordinary decision it affects."""
    target = str(getattr(story, "natal_target", "") or "").strip()
    mapping = {
        "Ascendant": "your appearance, boundaries and the version of you other people are meeting now",
        "Midheaven": "the job, title, manager or public responsibility attached to your name",
        "Sun": "the role, identity or direction that still deserves your energy",
        "Moon": "home, family, care and the routine your nervous system has to live with",
        "Mercury": "the message, document, conversation or decision that needs a clear answer",
        "Venus": "the person you want, the value you place on the bond and whether effort is mutual",
        "Mars": "the workload, conflict or desire that makes you stop accommodating and act",
        "Jupiter": "the bigger option and whether your actual life has room for it",
        "Saturn": "the responsibility, deadline or limit that needs proper terms",
        "Uranus": "the rule, routine or arrangement that no longer leaves enough room",
        "Neptune": "the promise, fear or story that still needs evidence",
        "Pluto": "the dependency, leverage or power arrangement that can no longer stay vague",
        "True Node": "the unfamiliar route that becomes possible when the old one stops fitting",
    }
    return mapping.get(target, simplify_life_area(_timing_story_life_area(story)))

def _timing_story_connection(report, story_index: int) -> list[str]:
    """The Year Story carries the convergence. Do not expose connector machinery between chapters."""
    return []

def _monthly_event_connection(events: list[dict], index: int) -> list[str]:
    """The Month Story carries the convergence. Do not repeat a connection template after every event."""
    return []


def _weekly_connected_interpretation(summary: dict) -> list[str]:
    """One thesis, one lived scene, one weekly standard."""
    raw_areas = list(summary.get("raw_areas") or summary.get("areas") or [])
    move = str(
        summary.get("move") or "keep the facts visible before committing"
    ).strip().rstrip(".")
    first = raw_areas[0] if raw_areas else "general"
    seed = f"{summary.get('sign', '')}-weekly"
    return [
        f"{life_scene(first, seed, count=1)} "
        "Act on what becomes concrete, not on applause or momentum alone.",
        f"{move.capitalize()}. Keep that rule all week. "
        "The mood can change. The standard does not have to.",
    ]

def _daily_connected_meaning(narrative) -> str:
    """Daily already has a Your Move block. Do not repeat it in the story."""
    return ""

def _solar_connected_meaning(solar) -> str:
    area = str(getattr(solar, "activated_house_name", "") or "general")
    seed = f"solar-{getattr(solar, 'solar_sign', '')}"
    return (
        f"{imperative_for(area, seed)} "
        f"{life_scene(area, seed, count=1)} "
        f"{str(getattr(solar, 'focus_meaning', '') or '').strip()}"
    ).strip()

def timing_map_page() -> None:
    set_page_metadata(
        "Your Year Ahead | Personal Transits & Timing | Luna Convergence",
        "A personalised 12-month transit map showing when major natal activations strengthen, peak, change and release.",
        "/timing-map",
    )
    st.markdown('<section class="natal-shell timing-shell">', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Personal timing</div>', unsafe_allow_html=True)
    st.markdown('<div class="editorial-title">Your Year Ahead</div><div class="timing-product-subtitle">Personal Transits &amp; Timing</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="timing-intro">A personal timing map for the next 12 months. Luna compares your natal chart with Jupiter, Saturn, Uranus, Neptune and Pluto, then overlays eclipses, stations and key sky events inside your year. It shows when the strongest personal contacts start, peak and ease, where they become visible in ordinary life, and what decision they ask from you.</div>',
        unsafe_allow_html=True,
    )
    st.caption("Tropical geocentric astrology · day-level timing · symbolic interpretation, not a prediction or professional advice.")

    with st.container(border=True):
        st.markdown("### Tell Luna when you were born")
        st.caption("Use the same natal baseline as Luna's Snapshot. If the birth time is unknown, Luna leaves Ascendant, Midheaven and houses out rather than inventing precision.")
        snapshot, validation_message, prefill_out = _timing_birth_snapshot()
        st.markdown("### Choose the 12-month window")
        start_date = st.date_input(
            "Start the 12 months on",
            value=browser_local_date(),
            min_value=date(1950, 1, 1),
            max_value=date(2100, 12, 31),
            key="timing-start-date-v330",
            help="This defaults to today in your browser timezone. Choose another start date if you want a different 12-month window.",
        )
        st.caption(f"12-month window: {_yearly_period_label(start_date, _rolling_year_end(start_date))}")
        generate = st.button("Build my Year Ahead", type="primary", use_container_width=True, key="timing-generate-v330")

    if generate:
        if snapshot is None:
            st.error(validation_message or "Complete the birth details first.")
        else:
            snapshot_birth_date = getattr(snapshot, "birth_date", None)
            calculated_sign = _monthly_sun_sign_from_snapshot(snapshot)
            if (
                not bool(getattr(snapshot, "birth_time_known", False))
                and isinstance(snapshot_birth_date, date)
                and _date_only_sun_sign_is_ambiguous(snapshot_birth_date)
            ):
                st.error(
                    "The Sun changed signs during your birth date. Add your birth time and birthplace so Luna can "
                    "calculate the correct Sun sign instead of guessing."
                )
            elif not calculated_sign:
                st.error("Luna could not calculate your Sun sign from the natal information supplied.")
            else:
                st.session_state["luna_natal_checkout_prefill"] = prefill_out or {}
                st.session_state["timing-calculated-sun-sign-v336"] = calculated_sign
                with st.spinner("Luna is ranking the strongest 12-month contactsâ€¦"):
                    report = build_timing_map(
                        snapshot,
                        start_date=start_date,
                        timezone_name=browser_timezone_name(),
                        max_stories=10,
                    )
                st.session_state["timing-map-report-v330"] = report
                st.session_state["timing-map-snapshot-v401"] = snapshot
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
            '<div class="lean-bookmark-note">Birth details stay out of the page URL and analytics. The natal geometry is calculated inside the current app session.</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</section>', unsafe_allow_html=True)
        return

    profile_summary = str(st.session_state.get("timing-map-summary-v330") or "Personal natal profile")
    timing_snapshot = st.session_state.get("timing-map-snapshot-v401")
    if timing_snapshot is not None:
        _render_natal_signature_grid(timing_snapshot)

    st.markdown("## The year at a glance")
    calculated_sign = str(st.session_state.get("timing-calculated-sun-sign-v336") or "")
    sign_prefix = f"Calculated Sun sign: {calculated_sign} · " if calculated_sign else ""
    st.caption(f"{sign_prefix}{profile_summary} · {_timing_date_label(report.start_date)} → {_timing_date_label(report.end_date)}")

    _render_timing_result_actions()

    yearly_facts = {
        "start_date": report.start_date.isoformat(),
        "end_date": report.end_date.isoformat(),
        "timezone": report.timezone_name,
        "recurring_themes": report.major_games,
        "exact_dates": report.turning_points,
        "major_shifts": report.rule_changes,
        "transits": [
            {
                "transiting_planet": story.transit_planet,
                "natal_target": story.natal_target,
                "aspect": story.aspect,
                "natal_house": story.natal_house,
                "score": round(story.score, 3),
                "polarity": story.polarity,
                "active_periods": [
                    {"start": period.start_date.isoformat(), "end": period.end_date.isoformat()}
                    for period in story.periods
                ],
                "exact_hits": [
                    {
                        "date": hit.exact_date.isoformat(),
                        "orb": round(hit.orb, 3),
                        "retrograde": hit.retrograde,
                    }
                    for hit in story.hits
                ],
            }
            for story in report.stories
        ],
        "major_sky_events": [
            {
                key: item.get(key)
                for key in ("event_date", "display_label", "technical_label", "tier", "planets", "aspect", "phase")
                if item.get(key) is not None
            }
            for item in (getattr(report, "major_sky_events", ()) or ())
            if isinstance(item, dict)
        ],
        "personal_major_contacts": [
            {
                key: item.get(key)
                for key in ("event_date", "display_label", "natal_target", "aspect", "orb", "house")
                if item.get(key) is not None
            }
            for item in (getattr(report, "personal_major_events", ()) or ())
            if isinstance(item, dict)
        ],
    }
    guided_year = _guided_luna_copy("yearly", yearly_facts)
    personal_events = list(getattr(report, "personal_major_events", ()) or ())
    personal_groups = group_serialized_personal_activations(personal_events)[:6]
    personal_items = {
        "items": [
            {
                "source_id": f"year-personal:{index}",
                "date": str(group[0].get("event_date") or ""),
                "display_label": str(group[0].get("display_label") or ""),
                "event_class": str(group[0].get("event_class") or ""),
                "contacts": [
                    {
                        "transiting_planet": str(item.get("transit_planet") or ""),
                        "aspect": str(item.get("aspect") or ""),
                        "natal_target": str(item.get("natal_target") or ""),
                        "orb": float(item.get("orb") or 0.0),
                        "house": item.get("house"),
                    }
                    for item in group
                ],
            }
            for index, group in enumerate(personal_groups)
        ]
    }
    personal_generated = (
        _guided_luna_collection("personal_events", personal_items)
        if personal_groups else None
    )
    personal_voices = {
        str(item["source_id"]): item for item in (personal_generated or {}).get("items", [])
    }
    transit_collection_facts = {
        "start_date": report.start_date.isoformat(),
        "end_date": report.end_date.isoformat(),
        "timezone": report.timezone_name,
        "items": [
            {
                "source_id": f"year-transit:{index}",
                "transiting_planet": story.transit_planet,
                "aspect": story.aspect,
                "natal_target": story.natal_target,
                "natal_house": story.natal_house,
                "polarity": story.polarity,
                "score": round(story.score, 3),
                "active_periods": [
                    {"start": period.start_date.isoformat(), "end": period.end_date.isoformat()}
                    for period in story.periods
                ],
                "exact_hits": [
                    {"date": hit.exact_date.isoformat(), "orb": round(hit.orb, 3), "retrograde": hit.retrograde}
                    for hit in story.hits
                ],
            }
            for index, story in enumerate(report.stories)
        ],
    }
    transit_generated = (
        _guided_luna_collection("yearly_transits", transit_collection_facts)
        if report.stories else None
    )
    transit_voices = {
        str(item["source_id"]): item for item in (transit_generated or {}).get("items", [])
    }
    year_sections: dict[str, object] = {}
    year_required: list[str] = []
    if personal_groups:
        year_sections["personal_contacts"] = personal_generated or {}
        year_required.append("personal_contacts")
    if report.stories:
        year_sections["transit_stories"] = transit_generated or {}
        year_required.append("transit_stories")
    year_bundle = assemble_report_bundle(
        "yearly",
        main=guided_year,
        sections=year_sections,
        required_sections=tuple(year_required),
    )
    st.session_state["yearly-voice-bundle-v336"] = {
        key: year_bundle[key]
        for key in ("report_id", "status", "complete", "missing_sections", "component_status")
    }

    if year_bundle["complete"]:
        st.markdown("### Read the year")
        _render_guided_luna_story(guided_year, "Luna's strategic map")
    else:
        _render_voice_unavailable(facts_label="complete Year Ahead document")

    if personal_groups and year_bundle["complete"]:
        st.markdown("### Key sky events that activate your chart")
        st.caption(
            "These are shared-sky events that make a direct contact to your natal chart. "
            "Luna shows the meaning here; the exact contacts stay inside the calculation dropdown."
        )
        for index, group in enumerate(personal_groups):
            first = group[0]
            event_date = str(first.get("event_date") or "")
            try:
                date_label = _timing_date_label(date.fromisoformat(event_date))
            except Exception:
                date_label = event_date

            voice = personal_voices.get(f"year-personal:{index}")
            interpretation = str(voice["story"]) if voice else "Luna voice unavailable; calculated contacts are shown below."
            action = str(voice["your_move"]) if voice else ""
            headline = str(voice["headline"]) if voice else str(first.get("display_label") or "Calculated natal contact")
            affirmation_html = (
                f'<p><strong>REMEMBER ·</strong> {escape(str(voice["affirmation"]))}</p>'
                if voice else ""
            )
            contacts = "".join(
                f'<li>{escape(_personal_contact_label(item))}</li>'
                for item in group
            )
            badge = _personal_major_badge(first, group)
            action_html = (
                f'<div class="timing-move"><div class="timing-move-label">Your move</div><p>{escape(action)}</p></div>'
                if action else ""
            )
            st.markdown(
                f"""<article class="timing-story personal-major-story">
<div class="timing-meta">{escape(date_label.upper())} · {escape(badge)}</div>
<h3>{escape(headline)}</h3>
<p>{escape(interpretation)}</p>
{affirmation_html}
{action_html}
</article>""",
                unsafe_allow_html=True,
            )
            with _luna_evidence_panel("Why Luna sees this · calculations"):
                st.markdown("**Exact natal contacts**")
                for item in group:
                    st.markdown(f"- {_personal_contact_label(item)}")

    if not report.stories:
        st.info("No major exact contacts passed the current threshold in this 12-month window. Try a different start date.")
    elif year_bundle["complete"]:
        st.markdown("## Your personal transits")
        st.caption(
            "These are the strongest moving-planet contacts to your natal chart across this rolling 12-month year. "
            "Luna translates each one into timing, the life area it touches and the move it asks from you."
        )
        for number, story in enumerate(report.stories, start=1):
            voice = transit_voices.get(f"year-transit:{number - 1}")
            periods_label = " · ".join(_timing_range_label(item.start_date, item.end_date) for item in story.periods)
            story_start = _timing_story_start(story)
            story_end = _timing_story_end(story)
            starts_label = _timing_date_label(story_start) if story_start else "—"
            strongest_label = _timing_story_peak_label(story)
            eases_label = _timing_date_label(story_end) if story_end else "—"
            where_label = _timing_story_life_area(story)
            summary_text = (
                str(voice["story"])
                if voice else "Luna voice unavailable; the calculated transit and timing remain current."
            )
            headline = str(voice["headline"]) if voice else f"{story.transit_planet} {story.aspect} natal {story.natal_target}"
            remember_html = (
                f'<p><strong>REMEMBER ·</strong> {escape(str(voice["affirmation"]))}</p>'
                if voice else ""
            )
            move_html = (
                f'<div class="timing-move"><div class="timing-move-label">Your move</div>'
                f'<p>{escape(str(voice["your_move"]))}</p></div>'
                if voice else ""
            )

            article_html = (
                '<article class="timing-story">'
                f'<div class="timing-meta">{number:02d} / {escape(_timing_signal_type(story))} · '
                f'{escape(story.polarity)} · active {escape(periods_label)}</div>'
                f'<h2>{escape(headline)}</h2>'
                '<div class="timing-plain-grid">'
                f'<div><span>What is happening</span><p>{escape(summary_text)}</p></div>'
                f'<div><span>Where it lands</span><p>{escape(simplify_life_area(where_label))}</p></div>'
                '</div>'
                '<div class="timing-phase-grid">'
                f'<div><span>Starts</span><strong>{escape(starts_label)}</strong></div>'
                f'<div><span>Strongest</span><strong>{escape(strongest_label)}</strong></div>'
                f'<div><span>Eases</span><strong>{escape(eases_label)}</strong></div>'
                '</div>'
                f'{remember_html}'
                f'{move_html}'
                '</article>'
            )
            st.markdown(article_html, unsafe_allow_html=True)

            with _luna_evidence_panel():
                confidence = _timing_story_confidence(story)
                st.markdown(
                    f"**{story.transit_planet} {story.aspect} natal {story.natal_target}**"
                    + (f" · natal house {story.natal_house}" if story.natal_house else "")
                )
                st.markdown(
                    f'<span class="timing-confidence">Confidence · {escape(confidence)}</span>',
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"{story.transit_planet} {story.aspect} natal {story.natal_target} is the technical transit. "
                    "Luna translates that geometry into the life-area story shown above."
                )
                for pass_number, hit in enumerate(story.hits, start=1):
                    motion = "retrograde" if hit.retrograde else "direct"
                    st.markdown(
                        f"- Pass {pass_number}: **{_timing_date_label(hit.exact_date)}** · {motion} · daily minimum orb {hit.orb:.2f}°"
                    )
                st.markdown(f"**{LUNA_TRUST_STATEMENT}**")
                st.caption(LUNA_TRUST_DISCLOSURE)
                st.caption(
                    "Luna scans the selected 365-day window with Swiss Ephemeris positions, detects exact natal contacts, "
                    "groups repeated direct/retrograde passes, then ranks the result by transit planet, natal target, aspect and angular/house emphasis."
                )

    st.markdown(
        f'''<div class="timing-summary-grid">
  <div><span>Recurring themes</span><strong>{report.major_games}</strong></div>
  <div><span>Exact dates</span><strong>{report.turning_points}</strong></div>
  <div><span>Major shifts</span><strong>{report.rule_changes}</strong></div>
</div>''',
        unsafe_allow_html=True,
    )
    st.markdown("### Transit intensity")
    st.markdown(_timing_strip_html(report), unsafe_allow_html=True)
    st.markdown("### What kind of period is it?")
    st.markdown(_timing_signal_strip(report), unsafe_allow_html=True)

    # Keep the raw event/transit lists available as evidence, but do not let
    # them dominate the customer-facing Year Ahead reading.
    with _luna_evidence_panel("Why Luna sees this · calculations"):
        _render_major_sky_evidence(
            getattr(report, "major_sky_events", ()) or (),
            "timing",
            heading="Shared-sky milestones inside your year",
            limit=8,
        )
        if report.stories:
            st.markdown("### Calculated natal transits")
            for story in report.stories:
                periods_label = " · ".join(
                    _timing_range_label(item.start_date, item.end_date) for item in story.periods
                )
                st.markdown(
                    f"**{story.transit_planet} {story.aspect} natal {story.natal_target}**"
                    + (f" · house {story.natal_house}" if story.natal_house else "")
                    + f" · {periods_label}"
                )

    # The natal/activation chart is part of the customer product, not hidden evidence.
    if timing_snapshot is not None:
        _timing_chart_in_motion(
            report,
            timing_snapshot,
            include_legacy_interpretation=False,
        )

    st.markdown(
        "<div class=\"timing-test\"><strong>Was this Year Ahead useful?</strong><br>Judge the reading by one thing: did it make the timing and the next move clearer?</div>",
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
        st.success("Recorded. This feedback stores the response and product context — not your birth details.")

    st.markdown('</section>', unsafe_allow_html=True)

def solar_year_page() -> None:
    set_page_metadata(
        "The Solar Year | Luna Convergence",
        "Explore the twelve tropical solar phases, four equinox and solstice gates, local daylight movement and the activated whole-sign house.",
        "/solar-year",
    )
    _snapshot_page_heading(
        "Free · Solar Structure",
        "The Solar\nConvergence",
        "Use the Sun as the clock. Then make the timing practical. Your location changes the light around you while the tropical sequence stays the same. Use your sign to see which part of life needs the next move.",
    )
    st.markdown('<a class="lean-monthly-link" href="/natal-snapshot">Create your free Natal Snapshot →</a>', unsafe_allow_html=True)

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
            "What is your Sun sign (star sign)?",
            SIGNS,
            index=None,
            placeholder="Select your star sign",
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

    if sign not in SIGNS:
        st.info("Select your star sign to calculate the Solar Convergence.")
        return

    solar = daily_solar_convergence(
        sign,
        selected_date,
        timezone_name,
        nearest_city=nearest_city,
    )
    solar_facts = {
        "sign": sign,
        "date": selected_date.isoformat(),
        "timezone": timezone_name,
        "solar_sign": solar.solar_sign,
        "solar_quarter": solar.solar_quarter,
        "solar_process": solar.solar_process,
        "local_light_direction": solar.light_direction,
        "city": solar.city,
        "next_solar_gate": solar_gate_label(solar.next_solar_gate),
        "days_to_next_gate": solar.days_to_next_gate,
        "activated_house_name": solar.activated_house_name,
    }
    guided_solar = _guided_luna_copy("solar", solar_facts)
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
</div>
        """,
        unsafe_allow_html=True,
    )

    if guided_solar:
        _render_guided_luna_story(guided_solar, "Luna reads the Solar Convergence")
    else:
        _render_voice_unavailable(facts_label="Solar Convergence calculation")

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

The free Natal Snapshot and Your Year Ahead use birth details in the current app session to calculate the result.
Birth details are not placed in the page URL or analytics events by either feature. Year Ahead feedback records only the
response and whether an exact birth time was available; it does not record the birth date, time or place.
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
- Your Year Ahead generation and feedback response (without birth details);
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
<br><strong>Build:</strong> {escape(BUILD_LABEL)}
{"<br><strong>Preview mode enabled</strong>" if EDITOR_PREVIEW_ENABLED else ""}
<br><a href="/privacy">Privacy</a> · <a href="/natal-snapshot">Free Natal Snapshot</a> · <a href="/timing-map">Your Year Ahead</a>{f' · <a href="{escape(LUNA_YOUTUBE_CHANNEL_URL)}" target="_blank" rel="noopener">YouTube</a>' if LUNA_YOUTUBE_CHANNEL_URL else ''}
</div>
        """,
        unsafe_allow_html=True,
    )


install_css()
install_complete_report_print_support()

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
BIRTHDAY_CARD_REF = st.Page(
    birthday_card_page,
    title="Birthday Card",
    url_path="birthday-card",
)
MONTHLY_INDEX_REF = st.Page(
    monthly_index_page,
    title="Monthly",
    url_path="monthly",
)
LEGACY_MONTHLY_INDEX_REF = st.Page(
    legacy_monthly_index_page,
    title="Monthly",
    url_path="august-2026-horoscopes",
    visibility="hidden",
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
    title="Your Year Ahead",
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
        title=f"{sign} Monthly (legacy link)",
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
    BIRTHDAY_CARD_REF,
    MONTHLY_INDEX_REF,
    LEGACY_MONTHLY_INDEX_REF,
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




