"""what do the models leave out?

Coverage percentages are computed only over studies where each dimension was
actually assessed (see utils.data.coverage) — blank cells mean "not assessed",
not "no". This matters because many light extractions leave fields empty.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data import load_countries, load_studies, enrich_countries, coverage, ISO2_TO_ISO3, db_cache_token
from utils.ui import SIDEBAR_CSS, render_logo, extraction_level_filter, render_partner_logos
from utils.origin_map import build_origin_map_df, author_origin_choropleth


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
        "<p style='font-size:0.78rem; color:var(--text-color); text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>Region filter</p>",
        unsafe_allow_html=True)
    region_filter = st.multiselect(
        "Regions", sorted(countries["region"].unique().tolist()),
        default=[], placeholder="All regions", label_visibility="collapsed")
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:var(--text-color); text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>How to read this</p>",
        unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.79rem; line-height:1.7;'>Percentages count only studies where "
        "a dimension was assessed. Blank cells mean <i>not assessed</i>, not <i>no</i>. "
        "The gap score is documented on the Methodology page.</br><br>"
        "The region filter applies to the map and the supporting table, but not the headline KPIs or charts 1-2, which summarise the full dataset.</p>",
        unsafe_allow_html=True)
    st.markdown("---")

    render_partner_logos()
    st.markdown(
        "<p style='font-size:0.69rem; color:var(--text-color); font-style:italic; line-height:1.5;'>AISESA · MINES Paris-PSL<br/>Research Platform · 2026</p>",
        unsafe_allow_html=True)

countries_view = countries[countries["region"].isin(region_filter)] if region_filter else countries

# ── Narrative header ─────────────────────────────────────────────────────────────
st.title("What do the models leave out?")
st.markdown(
    "<p style='font-size:1rem; color:var(--text-color); font-family:Georgia,serif; line-height:1.7; max-width:1100px;text-align:justify; hyphens:auto;'>"
    "Having seen <i>where</i> modelling happens and <i>who</i> does it, the next question is what it "
    "misses. African energy systems have features like large informal economies, charcoal and biomass use, "
    "unreliable supply, rapid urbanisation that many global models were not built to capture. "
    "This chapter quantifies those silences.</p>",
    unsafe_allow_html=True)

# CRITICAL: filter by extraction_level. Mixing planning models (MESSAGE/LEAP),
# techno-economic studies (HOMER/GIS), and policy documents (NDCs) in the same
# most methodological fields blank by design. Default to 'full' for this page.
studies = extraction_level_filter(studies, default="full")
n = len(studies)

st.divider()

# ── Chart 1 of 4 : African-specific feature coverage ─────────────────────────────
st.subheader("African-specific features are rarely modelled")
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
st.subheader("Who leads the modelling?")
st.caption("Based on author affiliations. African-led: the first author, or all authors, "
           "are at African institutions. Mixed: the first author is at a non-African institution "
           "in a team that includes African institutions. Non-African: all authors are outside Africa.")
origins = (studies["local_ownership"].astype(str).str.strip().str.lower()
           .map({"yes": "African-led", "partial": "Mixed", "no": "Non-African"})
           .dropna())
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

st.markdown("<div style='font-family:Georgia,serif; font-weight:600; font-size:0.98rem; "
            "margin:14px 0 4px 0;'>Where the authors are based</div>", unsafe_allow_html=True)
_map_studies = studies
if region_filter:
    _isos = set(countries_view["iso_code"])
    _map_studies = studies[studies["countries"].apply(
        lambda s: any(c.strip() in _isos for c in str(s).split(",") if c.strip()))]
st.plotly_chart(author_origin_choropleth(build_origin_map_df(_map_studies, countries)),
                use_container_width=True)
st.caption(f"Author institutions by country, counted once per study, for the {len(_map_studies)} "
           "studies matching the current scope and region filters.")

st.divider()

# ── Chart 3 of 4 : the gap map ───────────────────────────────────────────────────
st.subheader("Where the gaps concentrate")
st.caption("Gap score combines coverage of Africa-specific dimensions, data availability, "
           "energy governance and model density. Higher = more under-served. See Methodology.")
fig_map = px.choropleth(
    countries_view, locations="iso3", color="gap_score",
    color_continuous_scale=["#EAF3EC", "#E8A24A", "#B71C1C"],
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
st.subheader("Do the models account for how projects are financed?")
st.caption("Capital cost and financing assumptions shape every investment result, yet are often left implicit or uniform.")

# cost_of_capital: raw text kept in `cost_of_capital`; parsed by Excel into
# coc_min / coc_max (%) and coc_type (single / range / multiple / not_stated).
_coc_type = studies["coc_type"].astype(str).str.strip().str.lower()
_coc_min = pd.to_numeric(studies["coc_min"], errors="coerce")
_coc_max = pd.to_numeric(studies["coc_max"], errors="coerce")
# Excel stores 8 % as 0.08: rescale when values are fractions
if _coc_min.dropna().max() <= 1:
    _coc_min = _coc_min * 100
    _coc_max = _coc_max * 100

_stated = _coc_type.isin(["single", "range", "multiple"]) & _coc_min.notna()
_rates = _coc_min[_stated]                       # base (lowest) rate per study
_n_varied = int(_coc_type.isin(["range", "multiple"]).sum())
_not_stated = int((_coc_type == "not_stated").sum())

_fin = coverage(studies, "financing_modelling", positive=("yes",))
_mechs = studies["financing_mechanism"].astype(str).str.strip()
_mechs = _mechs[~_mechs.str.lower().isin(["", "nan", "none", "no"])]

_mode_rate = _rates.round(0).mode().iloc[0] if len(_rates) else 0
_mode_share = round((_rates.round(0) == _mode_rate).sum() / len(_rates) * 100) if len(_rates) else 0

st.markdown(
    f"<div style='max-width:900px; margin:18px 0 24px 0;'>"
    f"<div style='font-size:0.95rem; line-height:1.5; color:var(--text-color);'>"
    f"<b style='font-size:1.35rem; color:#5E35B1;'>{_mode_rate:.0f}%</b> is the most common "
    f"discount rate, used by {_mode_share}% of the {len(_rates)} studies that state one</div>"
    f"<div style='font-size:0.85rem; line-height:1.7; opacity:0.75; margin-top:8px;'>"
    f"Only {_n_varied} studies test more than one rate (range or scenario-specific) "
    f"&nbsp;·&nbsp; {_fin['pct']}% model financing explicitly ({_fin['positive']} of {_fin['assessed']} assessed) "
    f"&nbsp;·&nbsp; {len(_mechs)} name a specific mechanism "
    f"&nbsp;·&nbsp; {_not_stated} leave the rate unstated entirely</div>"
    f"</div>", unsafe_allow_html=True)

if len(_rates) > 1:
    rate_df = _rates.round(0).astype(int).value_counts().sort_index().reset_index()
    rate_df.columns = ["Discount rate (%)", "Studies"]
    fig_rate = px.bar(rate_df, x="Discount rate (%)", y="Studies", text="Studies",
                      color_discrete_sequence=["#5E35B1"])
    fig_rate.update_traces(textposition="outside")
    fig_rate.update_layout(height=260, margin={"t": 10, "b": 0},
                           xaxis_title="Assumed cost of capital / discount rate (%, base case)",
                           yaxis_title="Studies",
                           yaxis=dict(range=[0, rate_df["Studies"].max() * 1.15]))
    st.plotly_chart(fig_rate, use_container_width=True)
    st.caption(f"Of the studies that state a rate, most assume a uniform {_mode_rate:.0f}% "
               f"and only {_n_varied} vary it across scenarios, despite wide differences "
               "in real financing costs across African countries.")

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
     "gap_score", "data_availability", "energy_governance", "electrification_rate"]].copy()
top_gap.columns = ["Country", "Region", "Power pool", "Studies", "Gap score",
                   "Data", "Capacity", "Electrification (%)"]
top_gap["Region"] = top_gap["Region"].str.capitalize()
st.dataframe(
    top_gap.reset_index(drop=True), use_container_width=True, hide_index=True,
    column_config={
        "Gap score": st.column_config.ProgressColumn("Gap score", min_value=0, max_value=100, format="%d"),
        "Electrification (%)": st.column_config.NumberColumn(format="%.0f%%"),
    })

st.caption("Secondary breakdowns (licence, scale, SDG) are available as filters "
           "on the Browse Studies page.")
