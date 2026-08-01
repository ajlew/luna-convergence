from __future__ import annotations

from datetime import date, timedelta
from calendar import month_name
import json

import streamlit as st

from astrology_engine import SIGNS
from order_capture import MONTHLY_FOCUS_CHOICES, QUESTION_MAX_CHARS, YEARLY_FOCUS_CHOICES
from solar_cycle import city_input_help, representative_city_name
from report_pdf import build_report_pdf, report_filename
from monthly_narrative_v1 import (
    build_monthly_narrative,
    monthly_narrative_markdown,
    normalise_personal_question,
)
from monthly_experience_v1 import (
    build_monthly_experience_html,
    render_monthly_experience,
)
from synthesis import daily_report, period_report
from ephemeris_upload import inspect_ephemeris_pdf, profile_to_dict, source_note
from ollama_client import list_models, server_status, enhance, DEFAULT_URL


st.set_page_config(
    page_title="Hybrid Horoscope Engine",
    page_icon="✦",
    layout="wide",
)

st.title("Hybrid Swiss Ephemeris Horoscope Engine")
st.caption(
    "Deterministic planetary calculations + convergence analysis + optional Ollama prose synthesis"
)

if "forecast_year" not in st.session_state:
    st.session_state.forecast_year = 2026
if "result" not in st.session_state:
    st.session_state.result = None
if "uploaded_profile" not in st.session_state:
    st.session_state.uploaded_profile = None

with st.sidebar:
    st.header("Ephemeris reference")

    uploaded_file = st.file_uploader(
        "Upload an Astrodienst ephemeris PDF",
        type=["pdf"],
        help=(
            "The app detects the year and verifies that the table is tropical and geocentric. "
            "It then regenerates the positions directly with Swiss Ephemeris."
        ),
    )

    if uploaded_file is not None:
        try:
            profile = inspect_ephemeris_pdf(uploaded_file.getvalue(), uploaded_file.name)
            st.session_state.uploaded_profile = profile
            st.success(
                f"Detected: {profile.year or 'unknown year'} • "
                f"{profile.zodiac or 'unknown zodiac'} • "
                f"{profile.perspective or 'unknown perspective'}"
            )
            if profile.warnings:
                for warning in profile.warnings:
                    st.warning(warning)
            if profile.year and st.button("Use uploaded year", use_container_width=True):
                st.session_state.forecast_year = profile.year
                st.rerun()
        except Exception as exc:
            st.error(f"The PDF could not be inspected: {exc}")

    st.divider()
    st.header("Forecast controls")

    sign = st.selectbox(
        "Star sign",
        SIGNS,
        index=SIGNS.index("Sagittarius"),
    )

    period = st.radio("Forecast type", ["Daily", "Monthly", "Yearly"])

    timezone_name = st.selectbox(
        "Timezone",
        [
            "Australia/Sydney",
            "Australia/Melbourne",
            "Australia/Brisbane",
            "Australia/Perth",
            "Pacific/Auckland",
            "Europe/London",
            "America/New_York",
            "America/Los_Angeles",
            "UTC",
        ],
        index=0,
    )

    nearest_city = st.text_input(
        "Nearest city",
        value=representative_city_name(timezone_name),
        help=city_input_help(timezone_name),
    )

    selected_date = None
    selected_month = None

    if period == "Daily":
        selected_date = st.date_input(
            "Date",
            value=date(st.session_state.forecast_year, 7, 26),
            min_value=date(1900, 1, 1),
            max_value=date(2100, 12, 31),
        )
        st.session_state.forecast_year = selected_date.year
    else:
        year = st.number_input(
            "Year",
            min_value=1900,
            max_value=2100,
            step=1,
            key="forecast_year",
        )
        if period == "Monthly":
            selected_month = st.selectbox(
                "Month",
                list(range(1, 13)),
                index=6,
                format_func=lambda number: month_name[number],
            )

    st.divider()
    st.header("Manual fulfilment")
    delivery_email = st.text_input(
        "Customer delivery email",
        placeholder="customer@example.com",
    )
    order_reference = st.text_input(
        "Luna / Stripe order reference",
        placeholder="LC-MONTHLY-...",
    )
    focus_options = (
        MONTHLY_FOCUS_CHOICES
        if period == "Monthly"
        else YEARLY_FOCUS_CHOICES
        if period == "Yearly"
        else ["General overview"]
    )
    main_focus = st.selectbox("Customer main focus", focus_options)
    personal_question = st.text_area(
        "Customer personal question",
        max_chars=QUESTION_MAX_CHARS,
        placeholder="Optional question captured before payment",
    )
    st.caption(
        "If the order summary says 'No optional question supplied', leave this field blank. "
        "The phrase will not appear in the customer webpage or printed report."
    )

    generate = st.button("Generate analysis", type="primary", use_container_width=True)

profile = st.session_state.uploaded_profile
reference_note = source_note(profile)

if generate:
    with st.spinner("Calculating positions, transitions, retrogrades and convergence points..."):
        if period == "Daily":
            result = daily_report(sign, selected_date, timezone_name, reference_note)
        elif period == "Monthly":
            start = date(int(st.session_state.forecast_year), selected_month, 1)
            if selected_month == 12:
                end = date(int(st.session_state.forecast_year), 12, 31)
            else:
                end = date(int(st.session_state.forecast_year), selected_month + 1, 1) - timedelta(days=1)
            result = period_report(
                sign,
                start,
                end,
                timezone_name,
                f"{month_name[selected_month]} {int(st.session_state.forecast_year)}",
                reference_note,
                transition_count=9,
                nearest_city=nearest_city,
                main_focus=main_focus,
            )
        else:
            year = int(st.session_state.forecast_year)
            result = period_report(
                sign,
                date(year, 1, 1),
                date(year, 12, 31),
                timezone_name,
                str(year),
                reference_note,
                transition_count=9,
                nearest_city=nearest_city,
                main_focus=main_focus,
            )
    st.session_state.result = result

result = st.session_state.result

if profile:
    with st.expander("Uploaded ephemeris inspection"):
        st.json(profile_to_dict(profile), expanded=False)
        st.caption(
            "The PDF is used as a year/system reference. Direct Swiss Ephemeris calculation avoids OCR errors in dense tables."
        )

if result:
    main_tab, convergence_tab, retrograde_tab, ollama_tab, technical_tab = st.tabs(
        ["Horoscope", "Convergence points", "Retrogrades", "Ollama enhancement", "Technical data"]
    )

    with main_tab:
        cleaned_question = normalise_personal_question(personal_question)

        if result.get("period") == "monthly":
            customer_narrative = build_monthly_narrative(
                result,
                main_focus=main_focus,
                personal_question=cleaned_question,
                order_reference=order_reference,
            )
            customer_markdown = monthly_narrative_markdown(
                customer_narrative
            )
            customer_html = build_monthly_experience_html(
                customer_narrative,
                result,
                show_print=True,
                preview=False,
                order_reference=order_reference,
            )
            standalone_html = (
                "<!doctype html><html><head><meta charset='utf-8'>"
                "<meta name='viewport' content='width=device-width,initial-scale=1'>"
                "<title>Luna Convergence Monthly Report</title></head><body>"
                + customer_html
                + "</body></html>"
            )

            st.caption(
                "Customer webpage preview — read it here, then use "
                "'Print or save report' inside the page. The browser creates the "
                "PDF from the same Luna layout and fonts."
            )
            render_monthly_experience(
                customer_narrative,
                result,
                show_print=True,
                preview=False,
                order_reference=order_reference,
            )

            st.download_button(
                "Download customer webpage",
                data=standalone_html,
                file_name=(
                    f"luna_{result['sign'].lower()}_"
                    f"{result.get('label', 'monthly').lower().replace(' ', '_')}.html"
                ),
                mime="text/html",
                use_container_width=True,
            )

            with st.expander(
                "Internal backup and calculation output",
                expanded=False,
            ):
                st.caption(
                    "These files are internal backups. They are not the primary "
                    "customer design."
                )
                st.download_button(
                    "Download narrative source",
                    data=customer_markdown,
                    file_name=(
                        f"{result['sign'].lower()}_monthly_"
                        f"{result.get('label', 'reading').lower().replace(' ', '_')}.md"
                    ),
                    mime="text/markdown",
                )
                st.markdown("### Raw calculation output")
                st.markdown(result["markdown"])

                try:
                    legacy_pdf = build_report_pdf(
                        result,
                        main_focus=main_focus,
                        personal_question=cleaned_question,
                        order_reference=order_reference,
                    )
                except Exception as exc:
                    st.warning(f"Legacy backup PDF was unavailable: {exc}")
                    legacy_pdf = None

                if legacy_pdf:
                    st.download_button(
                        "Download legacy backup PDF",
                        data=legacy_pdf,
                        file_name=report_filename(result),
                        mime="application/pdf",
                    )

            if delivery_email:
                st.caption(
                    f"Manual delivery target: {delivery_email}. Use the browser's "
                    "Print / Save as PDF command, inspect the saved file, then attach it."
                )
        else:
            st.markdown(result["markdown"])
            st.download_button(
                "Download deterministic reading",
                data=result["markdown"],
                file_name=f"{result['sign'].lower()}_{result['period']}_{result.get('date', result.get('label', 'reading'))}.md",
                mime="text/markdown",
            )

            try:
                pdf_bytes = build_report_pdf(
                    result,
                    main_focus=main_focus,
                    personal_question=cleaned_question,
                    order_reference=order_reference,
                )
            except Exception as exc:
                st.error(
                    "The customer PDF could not be generated. "
                    f"Details: {exc}"
                )
                pdf_bytes = None

            if pdf_bytes:
                st.download_button(
                    "Download print-ready personalised PDF",
                    data=pdf_bytes,
                    file_name=report_filename(result),
                    mime="application/pdf",
                    type="primary",
                )

    with convergence_tab:
        convergences = result.get("convergences")
        if convergences:
            for index, item in enumerate(convergences, 1):
                with st.expander(
                    f"{index}. {item['title']} — {item['start_date']} to {item['end_date']}"
                ):
                    st.write(f"Score: {item['score']:.1f}")
                    st.write(f"Planets: {', '.join(item['planets'])}")
                    st.write(f"Houses: {', '.join(map(str, item['houses']))}")
                    st.json(item["events"], expanded=False)
        elif result.get("active_year_convergence") or result.get("active_month_convergence"):
            st.subheader("Active context")
            if result.get("active_year_convergence"):
                st.json(result["active_year_convergence"], expanded=False)
            if result.get("active_month_convergence"):
                st.json(result["active_month_convergence"], expanded=False)
        else:
            st.info("No convergence cluster met the threshold.")

    with retrograde_tab:
        cycles = result.get("retrograde_cycles", [])
        if cycles:
            for cycle in cycles:
                with st.expander(
                    f"{cycle['planet']}: {cycle['retrograde_start']} to {cycle['direct_date']}"
                ):
                    st.json(cycle, expanded=False)
        else:
            st.info("The daily view carries monthly/yearly context. Generate a monthly or yearly reading for full retrograde cycles.")

    with ollama_tab:
        st.subheader("Optional local language-model synthesis")
        st.write(
            "Ollama rewrites the structured facts into more varied prose. "
            "It does not calculate planetary positions or dates."
        )

        base_url = st.text_input("Ollama URL", value=DEFAULT_URL)
        status_clicked = st.button("Check Ollama")
        if status_clicked:
            ok, message = server_status(base_url)
            st.success(message) if ok else st.error(message)

        try:
            models = list_models(base_url, timeout=1.5)
        except Exception:
            models = []

        if models:
            model = st.selectbox("Model", models)
        else:
            model = st.text_input("Model name", value="qwen2.5:7b")

        style = st.selectbox(
            "Writing style",
            ["strategic", "practical", "traditional", "psychological", "business-focused"],
        )
        temperature = st.slider("Temperature", 0.0, 1.0, 0.35, 0.05)

        if st.button("Enhance this reading with Ollama", type="primary"):
            with st.spinner("Ollama is synthesising the calculated facts..."):
                try:
                    enhanced = enhance(
                        result,
                        model=model,
                        base_url=base_url,
                        style=style,
                        temperature=temperature,
                    )
                    st.session_state.enhanced = enhanced
                except Exception as exc:
                    st.error(f"Ollama enhancement failed: {exc}")

        if st.session_state.get("enhanced"):
            st.markdown(st.session_state.enhanced)
            st.download_button(
                "Download Ollama-enhanced reading",
                data=st.session_state.enhanced,
                file_name=f"{result['sign'].lower()}_{result['period']}_ollama.md",
                mime="text/markdown",
            )

    with technical_tab:
        payload = {key: value for key, value in result.items() if key != "markdown"}
        st.json(payload, expanded=False)
        st.download_button(
            "Download technical JSON",
            data=json.dumps(payload, indent=2),
            file_name=f"{result['sign'].lower()}_{result['period']}_technical.json",
            mime="application/json",
        )
else:
    st.info(
        "Upload an ephemeris PDF or select a year, then generate a daily, monthly or yearly analysis."
    )
    st.markdown(
        """
### Hybrid method

1. Swiss Ephemeris calculates planetary positions.
2. The event detector identifies aspects, ingresses, stations, lunations and eclipses.
3. The retrograde engine reconstructs the full review cycle.
4. The convergence engine groups events that overlap in time.
5. The interpretation library converts those combinations into opportunity, risk and strategic response.
6. Ollama can optionally rewrite the verified facts into more fluid prose.
        """
    )

st.caption(
    "Astrology is presented as a symbolic interpretive framework, not scientifically established causal forecasting."
)
