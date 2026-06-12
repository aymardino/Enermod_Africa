"""Explore the evidence: filter the full inventory and inspect any single study.

The summary chart and table read from the live database. The per-study detail
panel surfaces the richer extracted fields; fields not yet extracted show
"not yet extracted" rather than a blank, so depth of coverage stays honest.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data import load_studies, load_countries, db_cache_token
from utils.ui import SIDEBAR_CSS, render_logo

st.set_page_config(page_title="Browse Studies | AISESA", layout="wide", page_icon="assets/aisesa_logo.png")
st.html(SIDEBAR_CSS)
render_logo()


@st.cache_data(ttl=3600)
def get_data(db_token):
    return load_studies(), load_countries()


studies, countries = get_data(db_cache_token())
TECH_COLS = ["solar", "wind", "hydro", "biomass", "nuclear", "geothermal", "fossil", "h2", "coal"]


def show(value):
    """Render a field value, flagging empties as not-yet-extracted."""
    v = str(value).strip() if value is not None else ""
    return v if v and v.lower() not in ("nan", "none") else "_not yet extracted_"


# ── Sidebar filters ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:var(--text-color); text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>Filters</p>",
        unsafe_allow_html=True)
    year_range = st.slider("Publication year", 2010, 2025, (2010, 2025))
    scales = st.multiselect("Scale", sorted([s for s in studies["scale"].dropna().unique() if s]),
                            default=[], placeholder="All")
    approaches = st.multiselect("Approach", sorted([a for a in studies["approach"].dropna().unique() if a]),
                                default=[], placeholder="All")
    methods = st.multiselect("Method", sorted([m for m in studies["method"].dropna().unique() if m]),
                             default=[], placeholder="All")
    freqs = st.multiselect("Usage frequency", sorted([f for f in studies["frequency"].dropna().unique() if f]),
                           default=[], placeholder="All")
    lics = st.multiselect("License", sorted([l for l in studies["open_source"].dropna().unique() if l]),
                          default=[], placeholder="All")

    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:var(--text-color); text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>African features</p>",
        unsafe_allow_html=True)
    f_informal = st.checkbox("Covers informal economy")
    f_biomass = st.checkbox("Covers biomass/charcoal")
    f_reliability = st.checkbox("Covers power reliability")
    f_urban = st.checkbox("Covers urbanization")

    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:var(--text-color); text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>SDG &amp; policy</p>",
        unsafe_allow_html=True)
    f_sdg7 = st.checkbox("SDG 7 aligned")
    f_sdg13 = st.checkbox("SDG 13 aligned")
    f_ndc = st.checkbox("Mentions NDC")
    f_local = st.checkbox("Local ownership (African-led)")

    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:var(--text-color); text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>Technology</p>",
        unsafe_allow_html=True)
    tech_avail = [t for t in TECH_COLS if t in studies.columns]
    selected_techs = st.multiselect("Must include technology", tech_avail, default=[], placeholder="Any")

    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.69rem; color:var(--text-color); font-style:italic; line-height:1.5;'>AISESA · MINES Paris-PSL<br/>Research Platform · 2026</p>",
        unsafe_allow_html=True)

# ── Apply filters ───────────────────────────────────────────────────────────────
filt = studies[studies["year"].between(year_range[0], year_range[1], inclusive="both")].copy()
if scales:        filt = filt[filt["scale"].isin(scales)]
if approaches:    filt = filt[filt["approach"].isin(approaches)]
if methods:       filt = filt[filt["method"].isin(methods)]
if freqs:         filt = filt[filt["frequency"].isin(freqs)]
if lics:          filt = filt[filt["open_source"].isin(lics)]
if f_informal:    filt = filt[filt["informal_economy"].eq("yes")]
if f_biomass:     filt = filt[filt["biomass_charcoal"].eq("yes")]
if f_reliability: filt = filt[filt["power_reliability"].eq("yes")]
if f_urban:       filt = filt[filt["urbanization"].eq("yes")]
if f_sdg7 and "sdg_7" in filt.columns:       filt = filt[filt["sdg_7"].eq("yes")]
if f_sdg13 and "sdg_13" in filt.columns:     filt = filt[filt["sdg_13"].eq("yes")]
if f_ndc and "ndc_mention" in filt.columns:  filt = filt[filt["ndc_mention"].eq("yes")]
if f_local:       filt = filt[filt["local_ownership"].eq("yes")]
for tech in selected_techs:
    if tech in filt.columns:
        filt = filt[filt[tech].eq("yes")]

# ── Narrative header ─────────────────────────────────────────────────────────────
st.title("Explore the evidence")
st.markdown(
    "<p style='font-size:1rem; color:var(--text-color); font-family:Georgia,serif; line-height:1.7; max-width:820px;'>"
    "The full inventory, open for inspection. Filter by approach, tool, technology or policy alignment, "
    "then open any study to see everything that was extracted from it.</p>",
    unsafe_allow_html=True)

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(f"Showing **{len(filt)}** of **{len(studies)}** studies matching your filters.")
with col_h2:
    search_text = st.text_input("Search model / author", placeholder="e.g. LEAP, OSeMOSYS...",
                                label_visibility="collapsed")
if search_text:
    mask = (filt["model_name"].str.lower().str.contains(search_text.lower(), na=False) |
            filt["authors"].str.lower().str.contains(search_text.lower(), na=False))
    filt = filt[mask]
    st.caption(f"After text search: {len(filt)} results")

st.divider()

if len(filt) == 0:
    st.warning("No studies match the current filters. Try relaxing some constraints.")
    st.stop()

# ── Single supporting chart: technology coverage ─────────────────────────────────
st.markdown("#### Technology coverage in the filtered set")

# Technology fields are only systematically extracted at 'full' level —
# including light/narrative studies would deflate the percentages.
tech_base = filt[filt["extraction_level"] == "full"]
st.caption(f"Computed on the {len(tech_base)} full-extraction studies in the filtered set "
           f"(of {len(filt)} shown below); technology fields are not extracted for lighter levels.")

tech_avail_full = [t for t in TECH_COLS if t in tech_base.columns]
if tech_avail_full and len(tech_base) > 0:
    tech_pct = {t: round(tech_base[t].eq("yes").sum() / len(tech_base) * 100, 1) for t in tech_avail_full}
    tech_df = pd.DataFrame(list(tech_pct.items()), columns=["Technology", "Coverage (%)"]).sort_values("Coverage (%)")
    fig_tech = px.bar(tech_df, x="Coverage (%)", y="Technology", orientation="h",
                      color="Coverage (%)", color_continuous_scale=["#C8E6C9", "#1B5E20"],
                      text=tech_df["Coverage (%)"].apply(lambda v: f"{v}%"), height=300)
    fig_tech.update_traces(textposition="outside")
    fig_tech.update_layout(margin={"t": 10, "b": 0, "l": 0, "r": 40}, showlegend=False,
                           coloraxis_showscale=False,
                           xaxis=dict(range=[0, tech_df["Coverage (%)"].max() * 1.15]))
    st.plotly_chart(fig_tech, use_container_width=True)
else:
    st.info("No full-extraction studies in the current selection — relax the filters to see technology coverage.")

st.divider()

# ── Studies table (compact) ──────────────────────────────────────────────────────
st.markdown("#### Studies")
display_cols = [c for c in [
    "id", "model_name", "authors", "year", "extraction_level", "scale", "approach",
    "method", "open_source", "frequency", "sdg_7", "local_ownership", "countries",
] if c in filt.columns]
rename = {
    "id": "ID", "model_name": "Model", "authors": "Authors", "year": "Year",
    "extraction_level": "Extraction", "scale": "Scale", "approach": "Approach",
    "method": "Method", "open_source": "License", "frequency": "Frequency",
    "sdg_7": "SDG 7", "local_ownership": "Local", "countries": "Countries",
}
disp = filt[display_cols].rename(columns=rename).reset_index(drop=True)
if "Authors" in disp.columns:
    disp["Authors"] = disp["Authors"].str.slice(0, 40)
if "Countries" in disp.columns:
    disp["Countries"] = disp["Countries"].str.slice(0, 50)
st.dataframe(disp, use_container_width=True, hide_index=True, height=380,
             column_config={"Year": st.column_config.NumberColumn(format="%d")})

# ── Per-study detail panel ───────────────────────────────────────────────────────
st.markdown("#### Study detail")
st.caption("Open a study to see the full extraction, including the richer fields not shown in the table.")

labels = {int(r["id"]): f"#{int(r['id'])} — {r['model_name']} ({r['year'] if pd.notna(r['year']) else 'n.d.'})"
          for _, r in filt.iterrows()}
chosen = st.selectbox("Select a study", options=list(labels.keys()),
                      format_func=lambda i: labels[i], index=None,
                      placeholder="Choose a study to inspect...")

if chosen is not None:
    s = filt[filt["id"] == chosen].iloc[0]
    title = show(s.get("full_title")) if show(s.get("full_title")).startswith("_") is False else s.get("model_name")
    st.markdown(f"### {title}")
    st.caption(f"Study #{int(s['id'])} · {show(s.get('authors'))} · "
               f"{s['year'] if pd.notna(s['year']) else 'n.d.'} · extraction level: {s.get('extraction_level','unspecified')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Scale", show(s.get("scale")).replace("_", " "))
    c2.metric("Approach", show(s.get("approach")).replace("_", " "))
    c3.metric("License", show(s.get("open_source")).replace("_", " "))
    c4.metric("Usage", show(s.get("frequency")).replace("_", " "))

    st.markdown("**Objective**")
    st.markdown(show(s.get("study_objective")))
    st.markdown("**Key result**")
    st.markdown(show(s.get("key_result")))

    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Strengths**")
        st.markdown(show(s.get("strengths")))
        st.markdown("**Time horizon**")
        st.markdown(show(s.get("time_horizon_start"))+ " to " + show(s.get("time_horizon_end")))
        st.markdown("**Financing mechanism**")
        st.markdown(show(s.get("financing_mechanism")))
    with colB:
        st.markdown("**Weaknesses**")
        st.markdown(show(s.get("weaknesses")))
        st.markdown("**Cost of capital modelled**")
        st.markdown(show(s.get("cost_of_capital")))
        st.markdown("**Clean cooking**")
        st.markdown(show(s.get("clean_cooking")))

    techs = [t.capitalize() for t in TECH_COLS if t in s.index and str(s.get(t)).strip().lower() == "yes"]
    st.markdown("**Technologies modelled:** " + (", ".join(techs) if techs else "_not yet extracted_"))

    pol = []
    if str(s.get("sdg_7")).strip().lower() == "yes": pol.append("SDG 7")
    if str(s.get("sdg_13")).strip().lower() == "yes": pol.append("SDG 13")
    if str(s.get("ndc_mention")).strip().lower() == "yes": pol.append("NDC")
    if show(s.get("agenda_2063")).lower() == "yes": pol.append("Agenda 2063")
    st.markdown("**Policy alignment:** " + (", ".join(pol) if pol else "_none recorded_"))

    st.markdown(f"**Countries:** {show(s.get('countries'))}")

    doi = show(s.get("link_doi"))
    if not doi.startswith("_"):
        st.markdown(f"**Source:** [{doi}]({doi})")
