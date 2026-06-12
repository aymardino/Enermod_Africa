"""Readiness Indicators page."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data import load_countries, load_studies, enrich_countries, db_cache_token
from utils.ui import SIDEBAR_CSS, render_logo

st.set_page_config(page_title="Readiness | AISESA", layout="wide", page_icon="assets/aisesa_logo.png")
st.html(SIDEBAR_CSS)
render_logo()

REGION_COLORS = {"north":"#1565C0","west":"#2E7D32","east":"#6A1B9A","central":"#E65100","southern":"#37474F"}

@st.cache_data(ttl=3600)
def get_data(db_token):
    c = load_countries()
    s = load_studies()
    return enrich_countries(c, s), s

countries, studies = get_data(db_cache_token())

with st.sidebar:
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:var(--text-color); text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>Readiness score</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='font-size:0.79rem; line-height:1.8;'>"
        "Score 0–10:<br>"
        "• Institutional capacity: 0/1.5/3<br>"
        "• Data availability: 0/1.5/3<br>"
        "• NDC commitment: +1<br>"
        "• Long-term strategy: +1<br>"
        "• Electrification rate: 0–2</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:var(--text-color); text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>Filters</p>",
        unsafe_allow_html=True,
    )
    region_filter = st.multiselect("Region", sorted(countries["region"].unique()), default=[], placeholder="All regions", label_visibility="visible")
    cap_filter = st.multiselect("Institutional capacity", ["yes","partial","no"], default=[], placeholder="All", label_visibility="visible")
    dat_filter = st.multiselect("Data availability", ["good","moderate","poor"], default=[], placeholder="All", label_visibility="visible")
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.69rem; color:var(--text-color); font-style:italic; line-height:1.5;'>AISESA · MINES Paris-PSL<br/>Research Platform · 2026</p>",
        unsafe_allow_html=True,
    )

st.title("Which countries are ready to use models?")
st.markdown(
    "<p style='font-size:1rem; color:var(--text-color); font-family:Georgia,serif; line-height:1.7; max-width:820px;'>"
    "A model is only as useful as a country's ability to run, maintain and trust it. Readiness combines "
    "institutional capacity, data availability, climate commitments and electrification. These are the conditions "
    "that let modelling translate into policy. The score (0–10) is documented on the Methodology page.</p>",
    unsafe_allow_html=True)

nc = len(countries)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Avg readiness score", f"{countries['readiness_score'].mean():.1f}/10")
k2.metric("Good data availability", int(countries["data_availability"].eq("good").sum()), delta=f"of {nc} countries", delta_color="off")
k3.metric("Full institutional capacity", int(countries["has_institutional_capacity"].eq("yes").sum()), delta=f"of {nc} countries", delta_color="off")
k4.metric("Have long-term strategy", int(countries["has_lts"].eq("yes").sum()), delta=f"of {nc} countries", delta_color="off")

st.divider()

fig_map = px.choropleth(
    countries, locations="iso3", color="readiness_score",
    color_continuous_scale=["#B71C1C","#FDD835","#1B5E20"],
    hover_name="country_name",
    hover_data={"readiness_score":True,"electrification_rate":True,"data_availability":True,
                "has_institutional_capacity":True,"iso3":False},
    scope="africa", labels={"readiness_score":"Readiness"}, title="Readiness Score Map",
)
fig_map.update_geos(showframe=False, showcoastlines=True, coastlinecolor="#ccc",
                    showland=True, landcolor="#F0F4F0", showocean=True, oceancolor="#E3EEF9",
                    showcountries=True, countrycolor="#ccc")
fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, height=400,
                      coloraxis_colorbar=dict(title="Score", len=0.8))
st.plotly_chart(fig_map, use_container_width=True)

st.divider()

col1, col2 = st.columns(2)
with col1:
    scatter_df = countries.copy()
    scatter_df["Region"] = scatter_df["region"].str.capitalize()
    fig_sc = px.scatter(
        scatter_df, x="electrification_rate", y="nb_models_applied",
        color="Region",
        color_discrete_map={r.capitalize():c for r,c in REGION_COLORS.items()},
        hover_name="country_name",
        hover_data={"electrification_rate":True,"nb_models_applied":True,"Region":False},
        labels={"electrification_rate":"Electrification Rate (%)","nb_models_applied":"Models Applied"},
        title="Electrification Rate vs. Models Applied",
    )
    fig_sc.update_traces(marker=dict(size=9, opacity=0.85))
    fig_sc.update_layout(height=320, margin={"t":40,"b":0,"l":0,"r":0}, yaxis=dict(range=[-0.5, scatter_df["nb_models_applied"].max() + 1.15]))
    st.plotly_chart(fig_sc, use_container_width=True)

with col2:
    bins = [0,2,4,6,8,10.1]
    labels = ["0–2","2–4","4–6","6–8","8–10"]
    countries["readiness_bin"] = pd.cut(countries["readiness_score"], bins=bins, labels=labels, right=False)
    dist = countries["readiness_bin"].value_counts().reindex(labels).reset_index()
    dist.columns = ["Range","Count"]
    fig_dist = px.bar(dist, x="Range", y="Count",
                      color_discrete_sequence=["#2E7D32"], text="Count",
                      title="Readiness Score Distribution",
                      labels={"Range":"Score Range","Count":"Countries"})
    fig_dist.update_traces(textposition="outside")
    fig_dist.update_layout(height=320, margin={"t":40,"b":0,"l":0,"r":0}, yaxis=dict(range=[0, dist["Count"].max() + 1.15]))
    st.plotly_chart(fig_dist, use_container_width=True)

st.divider()

st.subheader("Country comparison table")
col_f1, col_f2, col_f3, col_f4 = st.columns([2,1,1,1])
with col_f1:
    search = st.text_input("Search country", placeholder="Type country name...")
with col_f2:
    region_opts = ["All"] + sorted(countries["region"].str.capitalize().unique().tolist())
    region_sel = st.selectbox("Region", region_opts)
with col_f3:
    sort_by = st.selectbox("Sort by", ["readiness_score","gap_score","nb_models_applied","electrification_rate"])
with col_f4:
    cap_sel = st.selectbox("Capacity", ["All","yes","partial","no"])

filtered = countries.copy()
if search:
    filtered = filtered[filtered["country_name"].str.lower().str.contains(search.lower())]
if region_sel != "All":
    filtered = filtered[filtered["region"].str.capitalize() == region_sel]
if cap_sel != "All":
    filtered = filtered[filtered["has_institutional_capacity"] == cap_sel]
if region_filter:
    filtered = filtered[filtered["region"].isin(region_filter)]
if cap_filter:
    filtered = filtered[filtered["has_institutional_capacity"].isin(cap_filter)]
if dat_filter:
    filtered = filtered[filtered["data_availability"].isin(dat_filter)]
filtered = filtered.sort_values(sort_by, ascending=False)

display = filtered[["country_name","region","power_pool","nb_models_applied",
                     "readiness_score","gap_score","electrification_rate",
                     "data_availability","has_institutional_capacity","has_ndc","has_lts"]].copy()
display.columns = ["Country","Region","Pool","Studies","Readiness","Gap","Electrification %","Data","Capacity","NDC","LTS"]
display["Region"] = display["Region"].str.capitalize()

st.dataframe(
    display.reset_index(drop=True), use_container_width=True, hide_index=True,
    column_config={
        "Readiness": st.column_config.ProgressColumn("Readiness", min_value=0, max_value=10, format="%.1f"),
        "Gap": st.column_config.ProgressColumn("Gap", min_value=0, max_value=100, format="%d"),
        "Electrification %": st.column_config.NumberColumn(format="%.0f%%"),
    },
)
st.caption(f"Showing {len(display)} of {len(countries)} countries")
