from __future__ import annotations

from datetime import date, timedelta
from calendar import month_name
import json

import streamlit as st

from astrology_engine import SIGNS
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
        st.markdown(result["markdown"])
        st.download_button(
            "Download deterministic reading",
            data=result["markdown"],
            file_name=f"{result['sign'].lower()}_{result['period']}_{result.get('date', result.get('label', 'reading'))}.md",
            mime="text/markdown",
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
