from __future__ import annotations

"""Streamlit admin UI for Luna's durable ephemeris registry.

Keep this file independent of app.py so monthly/narrator updates do not overwrite
or re-implement the upload contract.
"""

from calendar import month_name
from datetime import date, datetime
import hmac

import streamlit as st

from astrology_engine import SIGNS
from monthly_report_pipeline import (
    MONTHLY_PIPELINE_VERSION,
    build_production_monthly_report,
    render_production_monthly_report,
)
from solar_cycle import representative_city_name
from ephemeris_repository import (
    EPHEMERIS_FEATURE_VERSION,
    ephemeris_data_dir,
    list_registered_ephemerides,
    persist_ephemeris_to_github,
    registered_years,
    registry_summary,
    store_ephemeris_pdf,
)
from historical_ephemeris import (
    ASPECTS as HISTORICAL_ASPECTS,
    archive_stats as historical_archive_stats,
    aspect_events as historical_aspect_events,
    positions_on as historical_positions_on,
)


def _secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default) or default)
    except Exception:
        return default


def _admin_authorised(editor_preview_enabled: bool) -> bool:
    expected = _secret("LUNA_ADMIN_KEY")
    if not expected:
        if editor_preview_enabled:
            st.warning(
                "LUNA_ADMIN_KEY is not configured. Access is allowed only because "
                "editor preview is enabled. Add LUNA_ADMIN_KEY to Streamlit Secrets "
                "before public launch."
            )
            return True
        st.error("Ephemeris Admin is locked. Configure LUNA_ADMIN_KEY in Streamlit Secrets.")
        return False

    if st.session_state.get("ephemeris-admin-authorised"):
        return True

    supplied = st.text_input("Admin key", type="password", key="ephemeris-admin-key-input")
    if st.button("Unlock ephemeris admin", type="primary"):
        if supplied and hmac.compare_digest(supplied, expected):
            st.session_state["ephemeris-admin-authorised"] = True
            st.rerun()
        st.error("Admin key not accepted.")
    return False


def _github_settings() -> tuple[str, str, str]:
    return (
        _secret("EPHEMERIS_GITHUB_REPO"),
        _secret("EPHEMERIS_GITHUB_BRANCH", "main"),
        _secret("EPHEMERIS_GITHUB_TOKEN"),
    )


def render_ephemeris_admin(
    *,
    editor_preview_enabled: bool,
    default_sign: str,
    default_timezone: str,
    timezones: list[str],
) -> None:
    if not _admin_authorised(editor_preview_enabled):
        return

    st.markdown('<div class="eyebrow">Admin · durable source registry</div>', unsafe_allow_html=True)
    st.markdown("# Ephemeris years")
    st.markdown(
        "Upload one or more **Astrodienst tropical geocentric** yearly ephemerides. "
        "Luna validates the header, records the year and keeps the PDF in a separate "
        "`data/ephemerides/` repository so monthly-engine updates do not touch it."
    )
    st.info(
        "The uploaded PDF is Luna's durable reference/validation source. Planetary "
        "positions are still calculated with Swiss Ephemeris rather than transcribed "
        "from the PDF, avoiding table-extraction errors."
    )

    repo, branch, token = _github_settings()
    cloud_durable = bool(repo and token)
    if cloud_durable:
        st.success(f"Durable GitHub persistence is configured: {repo} · branch {branch}.")
    else:
        st.warning(
            "Local storage is available, but Streamlit Cloud can discard runtime files "
            "after a restart/redeploy. For persistence across deployments, add "
            "EPHEMERIS_GITHUB_REPO and EPHEMERIS_GITHUB_TOKEN to Streamlit Secrets."
        )

    uploads = st.file_uploader(
        "Upload yearly ephemeris PDF(s)",
        type=["pdf"],
        accept_multiple_files=True,
        help="You can select several years at once, for example 2017, 2026 and 2027.",
    )
    allow_reference = st.checkbox(
        "Keep incompatible uploads as reference-only files",
        value=False,
        help="Heliocentric or non-tropical tables will never be enabled for Luna testing.",
    )

    if uploads and st.button("Validate and register ephemeris", type="primary", use_container_width=True):
        outcomes = []
        for upload in uploads:
            try:
                metadata, saved_path = store_ephemeris_pdf(
                    upload.getvalue(),
                    upload.name,
                    allow_reference_only=allow_reference,
                )
                row = metadata.to_dict()
                row["saved"] = bool(saved_path)
                row["github"] = False
                if saved_path and cloud_durable:
                    persist_ephemeris_to_github(
                        metadata=metadata,
                        local_path=saved_path,
                        repo=repo,
                        branch=branch,
                        token=token,
                    )
                    row["github"] = True
                outcomes.append(row)
            except Exception as exc:
                outcomes.append({"file": upload.name, "saved": False, "error": str(exc)})

        for row in outcomes:
            if row.get("error"):
                st.error(f"{row.get('file', 'Upload')}: {row['error']}")
                continue
            label = f"{row.get('year') or 'Unknown year'} · {row.get('original_name')}"
            if row.get("usable_by_luna") and row.get("saved"):
                persistence = " · committed to GitHub" if row.get("github") else " · stored locally"
                st.success(f"{label}: validated and registered{persistence}.")
            else:
                st.warning(f"{label}: {row.get('validation_message')}")
        st.session_state.pop("ephemeris-admin-test-result", None)

    # Structured 1950–2050 astronomy memory.  This database is generated directly
    # from Swiss Ephemeris; uploaded PDFs remain validation/reference artifacts.
    st.markdown("## Luna Astronomy Memory")
    archive = historical_archive_stats()
    if archive.get("available"):
        cols = st.columns(4, gap="small")
        cols[0].metric("Archive", f"{archive.get('start_year')}–{archive.get('end_year')}")
        cols[1].metric("Daily positions", f"{archive.get('positions', 0):,}")
        cols[2].metric("Events", "On demand")
        cols[3].metric("Bodies", str(archive.get('bodies', 0)))
        st.caption(
            f"{archive.get('frame', '').title()} · {archive.get('zodiac', '').title()} · "
            f"{archive.get('node', '')} · daily snapshot {archive.get('snapshot_utc', '')} UTC · "
            f"events {archive.get('event_mode', 'derived on demand')}. "
            "PDF ephemerides remain validation references rather than calculation tables."
        )

        with st.expander("Historical sky lookup", expanded=False):
            lookup_date = st.date_input(
                "UTC date",
                value=datetime.now().date(),
                min_value=datetime(archive.get('start_year', 1950), 1, 1).date(),
                max_value=datetime(archive.get('end_year', 2050), 12, 31).date(),
                key="historical-archive-date",
            )
            rows = historical_positions_on(lookup_date)
            if rows:
                st.dataframe(
                    [
                        {
                            "Body": row["body"],
                            "Sign": row["sign"],
                            "Degree": f"{row['degree_in_sign']:.2f}°",
                            "Longitude": f"{row['longitude']:.3f}°",
                            "Motion": "Rx" if row["retrograde"] else "Direct",
                        }
                        for row in rows
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

        with st.expander("Historical aspect recurrence", expanded=False):
            bodies = [
                "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
                "Uranus", "Neptune", "Pluto", "True Node"
            ]
            c1, c2, c3, c4 = st.columns(4, gap="small")
            with c1:
                body1 = st.selectbox("First body", bodies, index=bodies.index("Mercury"), key="hist-body1")
            with c2:
                body2_options = [body for body in bodies if body != body1]
                body2 = st.selectbox(
                    "Second body",
                    body2_options,
                    index=body2_options.index("Jupiter") if "Jupiter" in body2_options else 0,
                    key="hist-body2",
                )
            with c3:
                aspect = st.selectbox("Aspect", list(HISTORICAL_ASPECTS), key="hist-aspect")
            with c4:
                sign_filter = st.selectbox("First-body sign", ["Any"] + list(SIGNS), key="hist-sign")
            recurrence = historical_aspect_events(
                body1,
                body2,
                aspect,
                sign=None if sign_filter == "Any" else sign_filter,
                ascending=False,
                limit=30,
            )
            if recurrence:
                st.dataframe(
                    [
                        {
                            "Exact UTC": row["exact_utc"],
                            body1: f"{row['body1_sign'] if row['body1'] == body1 else row['body2_sign']} "
                                   f"{(row['body1_degree'] if row['body1'] == body1 else row['body2_degree']):.2f}°",
                            body2: f"{row['body2_sign'] if row['body2'] == body2 else row['body1_sign']} "
                                   f"{(row['body2_degree'] if row['body2'] == body2 else row['body1_degree']):.2f}°",
                            "Aspect": row["aspect"].title(),
                        }
                        for row in recurrence
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.caption("No matching precomputed event in the archive.")
    else:
        st.warning(
            "Structured historical archive is not present. Run build_historical_ephemeris.py "
            "and deploy data/luna_ephemeris_1950_2050.sqlite3."
        )

    entries = list_registered_ephemerides()
    st.markdown("## Registered years")
    if entries:
        st.dataframe(registry_summary(entries), use_container_width=True, hide_index=True)
        st.caption(
            f"Registry contract v{EPHEMERIS_FEATURE_VERSION} · local path: {ephemeris_data_dir()}"
        )
    else:
        st.caption("No ephemeris years have been registered yet.")

    years = registered_years(usable_only=True)
    st.markdown("## Historical monthly stress test")
    if not years:
        st.info("Register a tropical geocentric year first. The 2017 Astrodienst file should qualify.")
        return

    st.markdown(
        "This uses the **exact same full monthly production pipeline** as the selected Monthly Preview. "
        "The only extra rule is that a historical year must first pass the ephemeris registry gate. "
        "That makes the result a true like-for-like comparison: same calculation, same convergence logic, "
        "same narrator, same Love / Work / Money sections, same evidence appendix and same print renderer."
    )

    default_year_index = len(years) - 1
    cols = st.columns(4, gap="medium")
    with cols[0]:
        year = st.selectbox("Registered year", years, index=default_year_index)
    with cols[1]:
        sign_index = SIGNS.index(default_sign) if default_sign in SIGNS else 0
        sign = st.selectbox("Star sign", SIGNS, index=sign_index)
    with cols[2]:
        month = st.selectbox(
            "Month",
            list(range(1, 13)),
            index=date.today().month - 1,
            format_func=lambda value: month_name[value],
        )
    with cols[3]:
        tz_index = timezones.index(default_timezone) if default_timezone in timezones else 0
        timezone_name = st.selectbox("Timezone", timezones, index=tz_index)

    city = st.text_input(
        "Representative city",
        value=representative_city_name(timezone_name),
        key="ephemeris-admin-test-city",
    )

    if st.button("Generate full monthly like-for-like test", type="primary", use_container_width=True):
        with st.spinner("Running the full Luna monthly production pipeline..."):
            narrative, result = build_production_monthly_report(
                sign=sign,
                year=int(year),
                month=int(month),
                timezone_name=timezone_name,
                nearest_city=city,
                main_focus="General overview",
            )
        st.session_state["ephemeris-admin-test-result"] = (narrative, result)

    stored = st.session_state.get("ephemeris-admin-test-result")
    if stored:
        narrative, result = stored
        st.caption(
            f"Historical stress test · {result.get('sign')} · {result.get('label')} · "
            "registered ephemeris year"
        )
        st.caption(
            f"Full monthly production pipeline v{MONTHLY_PIPELINE_VERSION} · "
            "like-for-like with Monthly Preview"
        )
        render_production_monthly_report(
            narrative,
            result,
            show_print=True,
        )
