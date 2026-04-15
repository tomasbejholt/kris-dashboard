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
    page_title="KRISCENTRAL — Nationell Incidentövervakning",
    page_icon="⚠",
    layout="wide",
)

if "table_filter" not in st.session_state:
    st.session_state.table_filter = "Alla"

st.markdown("""
<style>
/* Bakgrund med taktiskt rutnät */
.stApp {
    background-color: #090d18;
    background-image:
        radial-gradient(ellipse at 15% 10%, rgba(230,57,70,0.10) 0%, transparent 45%),
        radial-gradient(ellipse at 85% 90%, rgba(20,50,120,0.12) 0%, transparent 45%),
        linear-gradient(rgba(230,57,70,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(230,57,70,0.03) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 48px 48px, 48px 48px;
}

/* Dölj Streamlit-branding */
#MainMenu, footer, header { visibility: hidden; }

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* Sektionsrubriker */
h2, h3 {
    color: #e63946 !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-size: 0.75rem !important;
    border-left: 3px solid #e63946 !important;
    padding-left: 16px !important;
    margin-top: 2.2rem !important;
    margin-bottom: 0.8rem !important;
}

/* Metric-kort */
.metric-card {
    background: rgba(16,21,33,0.95);
    border: 1px solid rgba(230,57,70,0.2);
    border-radius: 3px;
    padding: 1rem 1.2rem;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #e63946, transparent);
}
.metric-label {
    font-size: 0.6rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #6e7681;
    margin-bottom: 0.4rem;
}
.metric-value {
    font-size: 2.2rem;
    font-weight: 700;
    color: #e6edf3;
    line-height: 1;
    font-family: monospace;
}
.metric-value.red    { color: #e63946; text-shadow: 0 0 12px rgba(230,57,70,0.5); }
.metric-value.orange { color: #f4845f; text-shadow: 0 0 12px rgba(244,132,95,0.4); }
.metric-value.yellow { color: #e3b341; text-shadow: 0 0 12px rgba(227,179,65,0.4); }

/* Statusrad */
.status-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    color: #6e7681;
    margin-bottom: 1.5rem;
    font-family: monospace;
}
.status-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #3fb950;
    box-shadow: 0 0 8px #3fb950;
    animation: blink 2s infinite;
    flex-shrink: 0;
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.3; }
}

/* Filteretikett */
.filter-label {
    font-size: 0.6rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #6e7681;
    margin-bottom: 4px;
    font-family: monospace;
}

/* Progress-bar (källfördelning) */
.src-bar-wrap {
    margin-bottom: 8px;
}
.src-bar-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.7rem;
    color: #8b949e;
    margin-bottom: 3px;
    font-family: monospace;
}
.src-bar-bg {
    background: rgba(230,57,70,0.08);
    border-radius: 2px;
    height: 3px;
}
.src-bar-fill {
    background: #e63946;
    height: 3px;
    border-radius: 2px;
}

/* Knapp */
.stButton > button {
    background: transparent !important;
    border: 1px solid rgba(230,57,70,0.6) !important;
    color: #e63946 !important;
    letter-spacing: 0.1em;
    font-size: 0.7rem;
    text-transform: uppercase;
    border-radius: 2px !important;
    font-family: monospace !important;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: rgba(230,57,70,0.12) !important;
    box-shadow: 0 0 14px rgba(230,57,70,0.25) !important;
    border-color: #e63946 !important;
}

/* Divider */
hr { border-color: rgba(230,57,70,0.12) !important; margin: 0.6rem 0 !important; }

/* Slider */
.stSlider [data-baseweb="slider"] { padding-top: 0.3rem; }

/* Info-box */
div[data-testid="stAlert"] {
    background: rgba(16,21,33,0.8) !important;
    border-left: 3px solid rgba(230,57,70,0.4) !important;
    font-size: 0.8rem;
}
</style>
""", unsafe_allow_html=True)


# ── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:1px solid rgba(230,57,70,0.25); padding-bottom:0.9rem; margin-bottom:0.3rem;">
    <div style="font-size:0.65rem; letter-spacing:0.25em; color:#e63946; text-transform:uppercase; margin-bottom:0.25rem; font-family:monospace;">
        ⚠ &nbsp;KRISCENTRAL &nbsp;/&nbsp; NATIONELL INCIDENTÖVERVAKNING
    </div>
    <div style="font-size:1.9rem; font-weight:800; color:#e6edf3; letter-spacing:0.06em; font-family:monospace;">
        REALTIDSÖVERVAKNING
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="status-bar">
    <div class="status-dot"></div>
    SYSTEM AKTIVT &nbsp;·&nbsp;
    UPPDATERAD {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &nbsp;·&nbsp;
    SMHI &nbsp;·&nbsp; TRAFIKVERKET &nbsp;·&nbsp; KRISINFORMATION &nbsp;·&nbsp; POLISEN
</div>
""", unsafe_allow_html=True)


# ── FILTERPANEL ──────────────────────────────────────────────────────────────
col_time, col_sources, col_severity, col_btn = st.columns([2, 2, 2, 1])

with col_time:
    st.markdown('<div class="filter-label">Tidsfönster (timmar)</div>', unsafe_allow_html=True)
    hours = st.slider("", 1, 72, 24, label_visibility="collapsed")

with col_sources:
    st.markdown('<div class="filter-label">Källor</div>', unsafe_allow_html=True)
    src_smhi   = st.toggle("SMHI", value=True)
    src_trafik = st.toggle("Trafikverket", value=True)
    src_kris   = st.toggle("Krisinformation", value=True)
    src_polis  = st.toggle("Polisen", value=True)

with col_severity:
    st.markdown('<div class="filter-label">Allvarlighetsgrad</div>', unsafe_allow_html=True)
    sev_hog     = st.toggle("Hög", value=True)
    sev_mattlig = st.toggle("Måttlig", value=True)
    sev_lag     = st.toggle("Låg", value=True)

with col_btn:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("⟳ Hämta data", use_container_width=True):
        with st.spinner(""):
            new_incidents = run_pipeline()
            saved = save_incidents(new_incidents)
        st.success(f"{saved} nya händelser sparades.")

st.divider()

# ── DATA ─────────────────────────────────────────────────────────────────────
sources = (
    (["SMHI"]            if src_smhi   else []) +
    (["Trafikverket"]    if src_trafik else []) +
    (["Krisinformation"] if src_kris   else []) +
    (["Polisen"]         if src_polis  else [])
)
severity_filter = (
    (["Hög"]    if sev_hog     else []) +
    (["Måttlig"] if sev_mattlig else []) +
    (["Låg"]    if sev_lag     else [])
)

raw       = fetch_recent_incidents(hours=hours)
incidents = score_incidents(raw)
df        = pd.DataFrame(incidents) if incidents else pd.DataFrame()

if not df.empty:
    df = df[df["source"].isin(sources)]
    df = df[df["severity"].isin(severity_filter)]

available_counties = sorted(df["county"].dropna().unique()) if not df.empty else []
selected_counties = st.multiselect(
    "Filtrera på län (lämna tomt för alla)",
    options=available_counties,
    default=[],
    placeholder="Välj ett eller flera län...",
)

if not df.empty and selected_counties:
    df = df[df["county"].isin(selected_counties)]

high      = len(df[df["severity"] == "Hög"])    if not df.empty else 0
moderate  = len(df[df["severity"] == "Måttlig"]) if not df.empty else 0
anomalies = (
    len(df[df["is_anomaly"] == True])
    if (not df.empty and "is_anomaly" in df.columns) else 0
)
top_county = (
    df["county"].value_counts().idxmax()
    if (not df.empty and "county" in df.columns) else "—"
)
total = len(df) if not df.empty else 0


# ── METRICS ──────────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Totalt aktiva</div>
        <div class="metric-value">{total}</div>
    </div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Allvarliga</div>
        <div class="metric-value red">{high}</div>
    </div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Måttliga</div>
        <div class="metric-value orange">{moderate}</div>
    </div>""", unsafe_allow_html=True)
with m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Avvikelser</div>
        <div class="metric-value yellow">{anomalies}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ── KARTA + LÄGESBILD ────────────────────────────────────────────────────────
col_map, col_summary = st.columns([3, 1])

with col_map:
    st.markdown("### Geografisk lägesbild")
    if not df.empty:
        map_df    = df.dropna(subset=["lat", "lon"])
        m         = folium.Map(location=[62.0, 15.0], zoom_start=5, min_zoom=4, tiles="CartoDB dark_matter")
        color_map = {"Hög": "#e63946", "Måttlig": "#f4845f", "Låg": "#e3b341", "Ingen": "#6e7681"}
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
        st_folium(m, width="100%", height=520)
    else:
        st.info("Inga händelser att visa på kartan.")

with col_summary:
    st.markdown("### Lägesbild")
    if df.empty:
        st.info("Inga aktiva händelser.")
    else:
        st.markdown(f"""
        <div style="font-size:0.78rem; line-height:1.9; color:#8b949e; font-family:monospace;">
            PERIOD<br>
            <span style="color:#e6edf3; font-size:1rem;">Senaste {hours}h</span><br><br>
            TOTALT<br>
            <span style="color:#e6edf3; font-size:1rem;">{total} händelser</span><br><br>
            ALLVARLIGA<br>
            <span style="color:#e63946; font-size:1rem;">{high} st</span><br><br>
            MÅTTLIGA<br>
            <span style="color:#f4845f; font-size:1rem;">{moderate} st</span><br><br>
            MEST AKTIVA LÄN<br>
            <span style="color:#e6edf3; font-size:0.85rem;">{top_county}</span>
            {f'<br><br><span style="color:#e3b341;">⚠ {anomalies} AVVIKELSE(R)</span>' if anomalies > 0 else ''}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="filter-label">Fördelning per källa</div>', unsafe_allow_html=True)

        for src, count in df["source"].value_counts().items():
            pct = int(count / total * 100)
            st.markdown(f"""
            <div class="src-bar-wrap">
                <div class="src-bar-row"><span>{src}</span><span>{count}</span></div>
                <div class="src-bar-bg"><div class="src-bar-fill" style="width:{pct}%"></div></div>
            </div>""", unsafe_allow_html=True)


# ── HÄNDELSELOGG ─────────────────────────────────────────────────────────────
st.markdown("### Händelselogg")

active_filter = st.session_state.table_filter

f1, f2, f3, f4, _ = st.columns([1, 1, 1, 1, 4])
for col, label, key in [
    (f1, "Alla",       "Alla"),
    (f2, "Allvarliga", "Allvarliga"),
    (f3, "Måttliga",   "Måttliga"),
    (f4, "Avvikelser", "Avvikelser"),
]:
    with col:
        if st.button(label, key=f"tbl_{key}", use_container_width=True):
            st.session_state.table_filter = key
            st.rerun()
        if active_filter == key:
            st.markdown('<div style="height:2px; background:#e63946; border-radius:1px; margin-top:-6px;"></div>', unsafe_allow_html=True)

SEVERITY_DISPLAY = {"Hög": "🔴 Hög", "Måttlig": "🟠 Måttlig", "Låg": "🟡 Låg"}

if not df.empty:
    table_df = df.copy()
    if active_filter == "Allvarliga":
        table_df = table_df[table_df["severity"] == "Hög"]
    elif active_filter == "Måttliga":
        table_df = table_df[table_df["severity"] == "Måttlig"]
    elif active_filter == "Avvikelser" and "is_anomaly" in table_df.columns:
        table_df = table_df[table_df["is_anomaly"] == True]

    table_df["severity"] = table_df["severity"].map(SEVERITY_DISPLAY).fillna(table_df["severity"])

    display_cols = ["published", "source", "title", "severity", "county"]

    st.dataframe(
        table_df[display_cols].rename(columns={
            "published": "Tid",
            "source":    "Källa",
            "title":     "Händelse",
            "severity":  "Allvarlighet",
            "county":    "Län",
        }),
        width="stretch",
        hide_index=True,
    )

    if active_filter == "Avvikelser":
        st.markdown("""
        <div style="margin-top:0.8rem; padding:0.8rem 1rem; background:rgba(227,179,65,0.07);
                    border-left:3px solid #e3b341; border-radius:2px;
                    font-size:0.78rem; color:#8b949e; font-family:monospace; line-height:1.7;">
            <span style="color:#e3b341;">⚠ OM AVVIKELSER</span><br>
            Händelserna ovan har flaggats av en Isolation Forest-modell som analyserar
            mönster i allvarlighetsgrad, källa och tidpunkt. En händelse klassas som
            avvikande om den kombinerar ovanliga värden — t.ex. ett rikslarm nattetid
            eller hög allvarlighet från en källa som sällan rapporterar sådant.
            Modellen tränas om vid varje datahämtning.
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Inga händelser matchar valda filter.")
