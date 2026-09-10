from __future__ import annotations

from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from model.allocation import estimate_water_cost, load_default_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]
METHODOLOGY_PATH = PROJECT_ROOT / "docs" / "methodology.md"


def _estimate(payload: dict[str, Any]) -> dict[str, Any]:
    return estimate_water_cost(payload)


def _band_width(confidence: str) -> float:
    return 0.05 if confidence == "high" else 0.20


st.set_page_config(page_title="DC Water Attribution Audit", layout="wide")
st.title("DC Water Attribution Audit")
st.caption("Workload-level water attribution with source-linked confidence reporting")

tabs = st.tabs(["Estimator", "Methodology"])

with tabs[0]:
    data = load_default_data()
    facility_options = ["(none)"] + sorted(
        data.facilities["facility_id"].dropna().astype(str).unique().tolist()
    )
    region_options = sorted(data.facilities["region"].dropna().astype(str).unique().tolist())
    if not region_options:
        region_options = ["(no public data)"]

    with st.form("estimate_form"):
        col1, col2, col3 = st.columns(3)
        region = col1.selectbox("Region", region_options)
        hardware_type = col2.selectbox("Hardware type", ["h100", "a100", "l40s"])
        gpu_hours = col3.number_input("GPU-hours", min_value=1.0, value=1000.0, step=100.0)
        col4, col5 = st.columns(2)
        month = col4.slider("Month", min_value=1, max_value=12, value=7)
        facility_id = col5.selectbox("Facility (optional)", facility_options)
        submitted = st.form_submit_button("Estimate water usage")

    if submitted:
        payload: dict[str, Any] = {
            "region": region,
            "hardware_type": hardware_type,
            "gpu_hours": float(gpu_hours),
            "month": int(month),
        }
        if facility_id != "(none)":
            payload["facility_id"] = facility_id

        result = _estimate(payload)
        if result["estimate_liters"] is None:
            st.warning("No public data available for this selection.")
        else:
            st.metric("Estimated liters", f"{result['estimate_liters']:.2f}")
            st.metric("Confidence", result["confidence"])
            st.caption(f"Sample size: N={result['sample_size']}")

            st.subheader("Source URLs")
            if result["sources"]:
                for source in result["sources"]:
                    st.markdown(f"- [{source}]({source})")
            else:
                st.write("No public data")

    st.subheader("Water cost per 1000 GPU-hours by region")
    chart_rows: list[dict[str, Any]] = []
    for region_name in region_options:
        if region_name == "(no public data)":
            continue
        estimate = _estimate(
            {
                "region": region_name,
                "hardware_type": "h100",
                "gpu_hours": 1000.0,
                "month": 7,
            }
        )
        if estimate["estimate_liters"] is None:
            continue
        chart_rows.append(
            {
                "region": region_name,
                "estimate_liters": estimate["estimate_liters"],
                "confidence": estimate["confidence"],
            }
        )

    if chart_rows:
        bar_df = pd.DataFrame(chart_rows)
        st.altair_chart(
            alt.Chart(bar_df)
            .mark_bar()
            .encode(
                x=alt.X("region:N", title="Region"),
                y=alt.Y("estimate_liters:Q", title="Liters per 1000 GPU-hours"),
                color=alt.Color("confidence:N", scale=alt.Scale(domain=["high", "low"])),
            )
            .properties(height=320),
            use_container_width=True,
        )
    else:
        st.info("No public data")

    st.subheader("Seasonal variation by month")
    selected_region = st.selectbox("Seasonal region", region_options, key="seasonal_region")
    seasonal_rows: list[dict[str, Any]] = []
    for m in range(1, 13):
        estimate = _estimate(
            {
                "region": selected_region,
                "hardware_type": hardware_type,
                "gpu_hours": 1000.0,
                "month": m,
            }
        )
        liters = estimate["estimate_liters"]
        if liters is None:
            continue
        width = _band_width(estimate["confidence"])
        seasonal_rows.append(
            {
                "month": m,
                "estimate_liters": liters,
                "lower_liters": max(0.0, liters * (1 - width)),
                "upper_liters": liters * (1 + width),
                "confidence": estimate["confidence"],
            }
        )

    if seasonal_rows:
        seasonal_df = pd.DataFrame(seasonal_rows)
        band = (
            alt.Chart(seasonal_df)
            .mark_area(opacity=0.25)
            .encode(
                x=alt.X("month:O", title="Month"),
                y=alt.Y("lower_liters:Q", title="Liters per 1000 GPU-hours"),
                y2="upper_liters:Q",
                color=alt.Color("confidence:N", legend=None),
            )
        )
        line = (
            alt.Chart(seasonal_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("month:O", title="Month"),
                y=alt.Y("estimate_liters:Q", title="Liters per 1000 GPU-hours"),
                color=alt.Color("confidence:N", scale=alt.Scale(domain=["high", "low"])),
            )
        )
        st.altair_chart((band + line).properties(height=350), use_container_width=True)
    else:
        st.info("No public data")

with tabs[1]:
    st.header("Methodology")
    if METHODOLOGY_PATH.exists():
        st.markdown(METHODOLOGY_PATH.read_text(encoding="utf-8"))
    else:
        st.warning("Methodology file not found.")

    st.subheader("Facility citations")
    data = load_default_data()
    citation_rows = []
    for _, row in data.facilities.iterrows():
        source_url = str(row.get("source_url", "") or "").strip()
        citation_rows.append(
            {
                "facility_id": row.get("facility_id"),
                "company": row.get("company"),
                "region": row.get("region"),
                "source_url": source_url,
                "source_url": source_url,
            }
        )
    if citation_rows:
        citation_df = pd.DataFrame(citation_rows)
        for _, row in citation_df.iterrows():
            if row["source_url"]:
                st.markdown(
                    f"- `{row['facility_id']}` ({row['company']}, {row['region']}): "
                    f"[source]({row['source_url']})"
                )
            else:
                st.markdown(
                    f"- `{row['facility_id']}` ({row['company']}, {row['region']}): no public data"
                )
    else:
        st.info("No public data")
