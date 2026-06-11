"""Chapter 3 of the narrative: what do the models leave out?

Coverage percentages are computed only over studies where each dimension was
actually assessed (see utils.data.coverage) — blank cells mean "not assessed",
not "no". This matters because many light/narrative extractions leave fields empty.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data import load_countries, load_studies, enrich_countries, coverage, ISO2_TO_ISO3, db_cache_token
from utils.ui import SIDEBAR_CSS, render_logo, extraction_level_filter

st.set_page_config(page_title="Gap Analysis | AISESA", layout="wide", page_icon="assets/aisesa_logo.png")
st.html(SIDEBAR_CSS)
render_logo()

AFRICAN_ISOS = set(ISO2_TO_ISO3)


@st.cache_data(ttl=3600)
def get_data(_db_token: int):
    c = load_countries()
    s = load_studies()
    return enrich_countries(c, s), s


countries, studies = get_data(db_cache_token())
n = len(studies)


def classify_origin(dev):
    """African-led / Non-African / Mixed from a list of author-origin ISO codes."""
    dev = str(dev).strip()
    if not dev:
        return None
    codes = [x.strip()[:2].upper() for x in dev.replace(",", ";").split(";") if x.strip()]
    has_a = any(c in AFRICAN_ISOS for c in codes)
    has_n = any(c not in AFRICAN_ISOS for c in codes)
    return "Mixed" if has_a and has_n else ("African-led" if has_a else "Non-African")


# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:#1E5631; text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>Region filter</p>",
        unsafe_allow_html=True)
    region_filter = st.multiselect(
        "Regions", sorted(countries["region"].unique().tolist()),
        default=[], placeholder="All regions", label_visibility="collapsed")
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:#1E5631; text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>How to read this</p>",
        unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.79rem; line-height:1.7;'>Percentages count only studies where "
        "a dimension was assessed. Blank cells mean <i>not assessed</i>, not <i>no</i>. "
        "The gap score is documented on the Methodology page.</br><br>"
        "The region filter applies to the map and the supporting table, but not the headline KPIs or charts 1-2, which summarise the full dataset.</p>",
        unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.69rem; color:#5A645E; font-style:italic; line-height:1.5;'>AISESA · MINES Paris-PSL<br/>Research Platform · 2026</p>",
        unsafe_allow_html=True)

countries_view = countries[countries["region"].isin(region_filter)] if region_filter else countries

# ── Narrative header ─────────────────────────────────────────────────────────────
st.title("What do the models leave out?")
st.markdown(
    "<p style='font-size:1rem; color:#444; font-family:Georgia,serif; line-height:1.7; max-width:820px;'>"
    "Having seen <i>where</i> modelling happens and <i>who</i> does it, the next question is what it "
    "misses. African energy systems have features like large informal economies, charcoal and biomass use, "
    "unreliable supply, rapid urbanisation that many global models were not built to capture. "
    "This chapter quantifies those silences.</p>",
    unsafe_allow_html=True)

# CRITICAL: filter by extraction_level. Mixing planning models (MESSAGE/LEAP),
# techno-economic studies (HOMER/GIS), and policy documents (NDCs) in the same
# coverage statistics distorts the picture — light/narrative extractions leave
# most methodological fields blank by design. Default to 'full' for this page.
studies = extraction_level_filter(studies, default="full")
n = len(studies)

_lv = studies["extraction_level"].value_counts()
st.caption(
    f"Based on {n} studies ({int(_lv.get('full',0))} full · {int(_lv.get('light',0))} light · "
    f"{int(_lv.get('narrative',0))} narrative · {int(_lv.get('unspecified',0))} unspecified).")

# ── Headline KPIs (replace several former pie charts) ────────────────────────────
_inf = coverage(studies, "informal_economy", positive=("yes",))
_loc = coverage(studies, "local_ownership", positive=("no",))
_freq = coverage(studies, "frequency", positive=("ad_hoc", "occasional"))
_sdg7 = coverage(studies, "sdg_7", positive=("yes",))
k1, k2, k3, k4 = st.columns(4)
k1.metric("Cover informal economy", f"{_inf['pct']}%",
          delta=f"{_inf['positive']} of {_inf['assessed']} assessed", delta_color="off")
k2.metric("No local ownership", f"{_loc['pct']}%",
          delta=f"{_loc['positive']} of {_loc['assessed']} assessed", delta_color="inverse")
k3.metric("Ad hoc / occasional use", f"{_freq['pct']}%",
          delta="not embedded in routine planning", delta_color="inverse")
k4.metric("Average gap score", f"{int(countries_view['gap_score'].mean())}/100",
          delta="higher = more under-served", delta_color="inverse")

st.divider()

# ── Chart 1 of 4 : African-specific feature coverage ─────────────────────────────
st.subheader("1 · African-specific features are rarely modelled")
st.caption("Four features critical to realistic African energy modelling,  each assessed only where the study reported on it.")
features = [
    ("Informal economy", coverage(studies, "informal_economy")),
    ("Biomass / charcoal", coverage(studies, "biomass_charcoal")),
    ("Power reliability", coverage(studies, "power_reliability")),
    ("Urbanisation", coverage(studies, "urbanization")),
]
feat_df = pd.DataFrame(
    [(name, c["positive"], c["pct"], c["assessed"]) for name, c in features],
    columns=["Feature", "Count", "Percentage", "Assessed"])

threshold = feat_df["Percentage"].median()

fig_feat = px.bar(feat_df, x="Feature", y="Percentage", color_discrete_sequence=["#C62828"],
                  text=feat_df["Percentage"].apply(lambda v: f"{v}%"),
                  hover_data=["Count", "Assessed"])
fig_feat.add_hline(y=threshold, line_dash="dot", line_color="#888", annotation_text=f"Average: {threshold:.0f}%")
fig_feat.update_traces(textposition="outside")
max=feat_df["Percentage"].max() * 1.2
fig_feat.update_layout(yaxis=dict(range=[0, max], title="% of assessed studies"),
                       xaxis_title="", height=320, margin={"t": 20, "b": 0})
st.plotly_chart(fig_feat, use_container_width=True)

st.divider()

# ── Chart 2 of 4 : who develops the models ───────────────────────────────────────
st.subheader("2 · Most studies are not African-led")
st.caption("Origin inferred from author affiliations. A study is 'Mixed' when it combines African and non-African institutions.")
origins = studies["developer_origin"].map(classify_origin).dropna()
dev_df = origins.value_counts().reset_index()
dev_df.columns = ["Origin", "Count"]
order = [o for o in ["African-led", "Mixed", "Non-African"] if o in dev_df["Origin"].values]
fig_dev = px.bar(dev_df, x="Count", y="Origin", orientation="h", text="Count",
                 category_orders={"Origin": order[::-1]},
                 color="Origin",
                 color_discrete_map={"African-led": "#2E7D32", "Mixed": "#1565C0", "Non-African": "#9E9E9E"})
fig_dev.update_layout(showlegend=False, height=220, margin={"t": 10, "b": 0},
                      xaxis_title=f"Studies (of {len(origins)} with stated affiliation)", yaxis_title="")
st.plotly_chart(fig_dev, use_container_width=True)

st.divider()

# ── Chart 3 of 4 : the gap map ───────────────────────────────────────────────────
st.subheader("3 · Where the gaps concentrate")
st.caption("Gap score combines feature coverage, institutional capacity, data availability and model density. See Methodology.")
fig_map = px.choropleth(
    countries_view, locations="iso3", color="gap_score",
    color_continuous_scale=["#1B5E20", "#FDD835", "#B71C1C"],
    hover_name="country_name",
    hover_data={"gap_score": True, "nb_models_applied": True, "iso3": False},
    scope="africa", labels={"gap_score": "Gap score"})
fig_map.update_geos(showframe=False, showcoastlines=True, coastlinecolor="#ccc",
                    showland=True, landcolor="#F0F4F0", showocean=True, oceancolor="#E3EEF9",
                    showcountries=True, countrycolor="#ccc")
fig_map.update_layout(margin={"r": 0, "t": 10, "l": 0, "b": 0}, height=420)
st.plotly_chart(fig_map, use_container_width=True)

st.divider()

# ── Chart 4 of 4 : do models account for financing? (AISESA R5) ──────────────────
st.subheader("4 · Do the models account for how projects are financed?")
st.caption("Capital cost and financing assumptions shape every investment result, yet are often left implicit or uniform.")

# cost_of_capital holds actual rates (e.g. 0.1 = 10%), "not_stated", or free text — not yes/no.
import re as _re
def _parse_rate(v):
    v = str(v).strip().lower()
    if not v or v in ("nan", "not_stated", "none"):
        return None
    m = _re.search(r"(\d+(?:\.\d+)?)\s*%", v)        # e.g. "8% (BF)"
    if m:
        return float(m.group(1))
    try:
        x = float(v)
        return x * 100 if x <= 1 else x               # 0.1 -> 10%
    except ValueError:
        return None

_rates = studies["cost_of_capital"].map(_parse_rate).dropna()
_not_stated = (studies["cost_of_capital"].astype(str).str.strip().str.lower() == "not_stated").sum()
_fin = coverage(studies, "financing_modelling", positive=("yes",))
_mechs = studies["financing_mechanism"].astype(str).str.strip()
_mechs = _mechs[~_mechs.str.lower().isin(["", "nan", "none", "no"])]

fc1, fc2, fc3 = st.columns(3)
_mode_rate = _rates.mode().iloc[0] if len(_rates) else 0
_mode_share = round((_rates == _mode_rate).sum() / len(_rates) * 100) if len(_rates) else 0
fc1.metric("Most common discount rate", f"{_mode_rate:.0f}%",
           delta=f"used by {_mode_share}% of studies stating one", delta_color="off")
fc2.metric("Model financing explicitly", f"{_fin['pct']}%",
           delta=f"{_fin['positive']} of {_fin['assessed']} assessed", delta_color="off")
fc3.metric("Name a financing mechanism", f"{len(_mechs)}",
           delta=f"· {_not_stated} studies leave the rate unstated", delta_color="off")

if len(_rates) > 1:
    import pandas as _pd
    rate_df = _rates.round(0).astype(int).value_counts().sort_index().reset_index()
    rate_df.columns = ["Discount rate (%)", "Studies"]
    fig_rate = px.bar(rate_df, x="Discount rate (%)", y="Studies", text="Studies",
                      color_discrete_sequence=["#5E35B1"])
    fig_rate.update_traces(textposition="outside")
    fig_rate.update_layout(height=260, margin={"t": 10, "b": 0},
                           xaxis_title="Assumed cost of capital / discount rate (%)",
                           yaxis_title="Studies",
                           yaxis=dict(range=[0, rate_df["Studies"].max() * 1.15]))
    st.plotly_chart(fig_rate, use_container_width=True)
    st.caption(f"Of the studies that state a rate, most assume a uniform {_mode_rate:.0f}% — rarely "
               "differentiated by country risk, despite wide variation in real financing costs across Africa.")

st.divider()

# ── Emerging coverage : honest counters that grow with the data (R13, R2) ────────
st.subheader("Emerging dimensions")
st.caption("These dimensions are tracked from the start; the counts are low today and will rise as the "
           "systematic review and grey literature are integrated.")
_a63 = coverage(studies, "agenda_2063", positive=("yes",))
_grey = coverage(studies, "grey_literature", positive=("yes",))
ec1, ec2 = st.columns(2)
ec1.metric("Reference Agenda 2063", f"{_a63['positive']} of {_a63['assessed']}",
           delta=f"{_a63['pct']}% of assessed studies", delta_color="off")
ec2.metric("Grey literature", f"{_grey['positive']} of {_grey['assessed']}",
           delta=f"{_grey['pct']}% of assessed studies", delta_color="off")

st.divider()

# ── Supporting table : highest-gap countries ─────────────────────────────────────
st.subheader("Highest-gap countries")
top_gap = countries_view.nlargest(15, "gap_score")[
    ["country_name", "region", "power_pool", "nb_models_applied",
     "gap_score", "data_availability", "has_institutional_capacity", "electrification_rate"]].copy()
top_gap.columns = ["Country", "Region", "Power pool", "Studies", "Gap score",
                   "Data", "Capacity", "Electrification (%)"]
top_gap["Region"] = top_gap["Region"].str.capitalize()
st.dataframe(
    top_gap.reset_index(drop=True), use_container_width=True, hide_index=True,
    column_config={
        "Gap score": st.column_config.ProgressColumn("Gap score", min_value=0, max_value=100, format="%d"),
        "Electrification (%)": st.column_config.NumberColumn(format="%.0f%%"),
    })

st.caption("Secondary breakdowns (licence, scale, SDG, usage frequency) are available as filters "
           "on the Browse Studies page.")
