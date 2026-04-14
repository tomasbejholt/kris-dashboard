import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

from pipeline.normalize import run_pipeline
from pipeline.database import save_incidents, fetch_recent_incidents
from models.anomaly import score_incidents


st.set_page_config(
    page_title="Nationell Kris- och Incidentdashboard",
    page_icon="🚨",
    layout="wide",
)

st.title("🚨 Nationell Kris- och Incidentdashboard")
st.caption(f"Senast uppdaterad: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

st.sidebar.header("Inställningar")
hours = st.sidebar.slider("Visa händelser från senaste (timmar)", 1, 72, 24)
sources = st.sidebar.multiselect(
    "Filtrera källa",
    ["SMHI", "Trafikverket", "Krisinformation", "Polisen"],
    default=["SMHI", "Trafikverket", "Krisinformation", "Polisen"],
)
severity_filter = st.sidebar.multiselect(
    "Filtrera allvarlighetsgrad",
    ["Låg", "Måttlig", "Hög"],
    default=["Låg", "Måttlig", "Hög"],
)

if st.sidebar.button("Hämta ny data nu"):
    with st.spinner("Hämtar data från alla källor..."):
        incidents = run_pipeline()
        saved = save_incidents(incidents)
    st.sidebar.success(f"{saved} nya händelser sparades.")

raw = fetch_recent_incidents(hours=hours)
incidents = score_incidents(raw)

df = pd.DataFrame(incidents) if incidents else pd.DataFrame()

if not df.empty:
    df = df[df["source"].isin(sources)]
    df = df[df["severity"].isin(severity_filter)]


# --- LÄGESBILD ---
st.subheader("Lägesbild")

if df.empty:
    st.info("Inga händelser matchar valda filter.")
else:
    high = len(df[df["severity"] == "Hög"])
    moderate = len(df[df["severity"] == "Måttlig"])
    anomalies = len(df[df.get("is_anomaly", False) == True]) if "is_anomaly" in df.columns else 0
    top_county = df["county"].value_counts().idxmax() if "county" in df.columns else "okänt"

    summary = (
        f"Under de senaste {hours} timmarna har **{len(df)} händelser** registrerats. "
        f"Av dessa bedöms **{high} som allvarliga** och **{moderate} som måttliga**. "
        f"Mest aktiva område är **{top_county}**."
    )
    if anomalies > 0:
        summary += f" Modellen har flaggat **{anomalies} ovanliga händelser** som avviker från normalmönstret."

    st.markdown(summary)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Totalt", len(df))
    col2.metric("Allvarliga", high, delta=None)
    col3.metric("Måttliga", moderate)
    col4.metric("Anomalier", anomalies)


# --- KARTA ---
st.subheader("Karta")

if not df.empty:
    map_df = df.dropna(subset=["lat", "lon"])

    m = folium.Map(location=[62.0, 15.0], zoom_start=5, tiles="CartoDB dark_matter")

    color_map = {"Hög": "red", "Måttlig": "orange", "Låg": "blue", "Ingen": "gray"}

    for _, row in map_df.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=color_map.get(row["severity"], "gray"),
            fill=True,
            fill_opacity=0.8,
            popup=folium.Popup(
                f"<b>{row['title']}</b><br>"
                f"Källa: {row['source']}<br>"
                f"Allvarlighet: {row['severity']}<br>"
                f"Tid: {row['published']}",
                max_width=300,
            ),
        ).add_to(m)

    st_folium(m, width="100%", height=500)
else:
    st.info("Inga händelser med koordinater att visa.")


# --- TABELL ---
st.subheader("Händelser")

if not df.empty:
    display_cols = ["published", "source", "title", "severity", "county"]
    if "anomaly_score" in df.columns:
        display_cols.append("anomaly_score")

    st.dataframe(
        df[display_cols].rename(columns={
            "published": "Tid",
            "source": "Källa",
            "title": "Händelse",
            "severity": "Allvarlighet",
            "county": "Län",
            "anomaly_score": "Anomalipoäng",
        }),
        use_container_width=True,
        hide_index=True,
    )
