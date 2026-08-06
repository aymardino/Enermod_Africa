"""AISESA African Energy Modelling Observatory — Home page (live narrative)."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.data import (load_countries, load_studies, load_tools,
                        enrich_countries, coverage, ISO2_TO_ISO3, db_cache_token)
from utils.ui import SIDEBAR_CSS, beta_banner, GREEN, render_logo, inventory_breakdown
import pandas as pd

# ISO-2 -> ISO-3 for NON-African author origins (African codes come from
# ISO2_TO_ISO3). Add any new origin country here if it ever shows up unmapped.
_WORLD_ISO3 = {
    "US": "USA", "CA": "CAN", "MX": "MEX", "BR": "BRA", "AR": "ARG", "CL": "CHL",
    "CO": "COL", "PE": "PER", "GB": "GBR", "IE": "IRL", "FR": "FRA", "DE": "DEU",
    "IT": "ITA", "ES": "ESP", "PT": "PRT", "NL": "NLD", "BE": "BEL", "LU": "LUX",
    "CH": "CHE", "AT": "AUT", "SE": "SWE", "NO": "NOR", "DK": "DNK", "FI": "FIN",
    "IS": "ISL", "PL": "POL", "CZ": "CZE", "SK": "SVK", "HU": "HUN", "GR": "GRC",
    "RO": "ROU", "BG": "BGR", "HR": "HRV", "RS": "SRB", "EE": "EST", "LV": "LVA",
    "LT": "LTU", "RU": "RUS", "UA": "UKR", "TR": "TUR", "IL": "ISR", "SA": "SAU",
    "AE": "ARE", "QA": "QAT", "IR": "IRN", "IN": "IND", "PK": "PAK", "BD": "BGD",
    "CN": "CHN", "JP": "JPN", "KR": "KOR", "TW": "TWN", "HK": "HKG", "SG": "SGP",
    "MY": "MYS", "ID": "IDN", "TH": "THA", "VN": "VNM", "PH": "PHL", "AU": "AUS",
    "NZ": "NZL", "RE": "REU",
}
# African entries win on any overlap.
ISO2_TO_ISO3_WORLD = {**_WORLD_ISO3, **ISO2_TO_ISO3}

# Names for non-African origins (African names come from the countries table).
_WORLD_NAMES = {
    "US": "United States", "CA": "Canada", "MX": "Mexico", "BR": "Brazil",
    "AR": "Argentina", "CL": "Chile", "CO": "Colombia", "PE": "Peru",
    "GB": "United Kingdom", "IE": "Ireland", "FR": "France", "DE": "Germany",
    "IT": "Italy", "ES": "Spain", "PT": "Portugal", "NL": "Netherlands",
    "BE": "Belgium", "LU": "Luxembourg", "CH": "Switzerland", "AT": "Austria",
    "SE": "Sweden", "NO": "Norway", "DK": "Denmark", "FI": "Finland",
    "IS": "Iceland", "PL": "Poland", "CZ": "Czechia", "SK": "Slovakia",
    "HU": "Hungary", "GR": "Greece", "RO": "Romania", "BG": "Bulgaria",
    "HR": "Croatia", "RS": "Serbia", "EE": "Estonia", "LV": "Latvia",
    "LT": "Lithuania", "RU": "Russia", "UA": "Ukraine", "TR": "Turkey",
    "IL": "Israel", "SA": "Saudi Arabia", "AE": "United Arab Emirates",
    "QA": "Qatar", "IR": "Iran", "IN": "India", "PK": "Pakistan",
    "BD": "Bangladesh", "CN": "China", "JP": "Japan", "KR": "South Korea",
    "TW": "Taiwan", "HK": "Hong Kong", "SG": "Singapore", "MY": "Malaysia",
    "ID": "Indonesia", "TH": "Thailand", "VN": "Vietnam", "PH": "Philippines",
    "AU": "Australia", "NZ": "New Zealand", "RE": "Réunion",
}

# Colours for the two origin groups.
_AFR_COLOR = "#2F7D4F"       # African-based authors (brand green)
_NONAFR_COLOR = "#D98A29"    # authors based outside the continent (amber)

# ── Choose which map style to keep once you've decided: "bubbles" | "choropleth"
MAP_STYLE = "choropleth"

_GEO = dict(
    projection_type="natural earth",
    showframe=False, showcoastlines=False,
    showland=True, landcolor="rgba(128,128,128,0.10)",
    showcountries=True, countrycolor="rgba(128,128,128,0.20)",
    bgcolor="rgba(0,0,0,0)",
)


def author_origin_bubbles(df):
    """VERSION A — one bubble per country: size = number of studies,
    colour = African-based (green) vs outside Africa (amber). Best for
    *comparing counts* (Sweden 13 is a big circle, Belgium 1 a tiny one)."""
    fig = px.scatter_geo(
        df, locations="iso3", size="n", color="group", hover_name="name",
        hover_data={"n": True, "iso3": False, "group": False},
        color_discrete_map={"African-based": _AFR_COLOR,
                            "Based outside Africa": _NONAFR_COLOR},
        category_orders={"group": ["African-based", "Based outside Africa"]},
        size_max=34, labels={"n": "Studies"},
    )
    fig.update_traces(marker=dict(line=dict(width=0.6, color="rgba(255,255,255,0.65)"),
                                  opacity=0.9))
    fig.update_geos(**_GEO)
    fig.update_layout(
        height=380, margin={"t": 0, "b": 0, "l": 0, "r": 0},
        paper_bgcolor="rgba(0,0,0,0)", geo_bgcolor="rgba(0,0,0,0)",
        legend=dict(title="", orientation="h", yanchor="bottom", y=-0.02,
                    xanchor="center", x=0.5),
    )
    return fig


def author_origin_choropleth(df):
    """VERSION B — two shaded layers: African countries in a green scale and
    non-African countries in an amber scale, each darker with more studies.
    Two small colour bars on the right show the intensity per group."""
    afr = df[df["group"] == "African-based"]
    non = df[df["group"] == "Based outside Africa"]
    fig = go.Figure()
    fig.add_choropleth(
        locations=afr["iso3"], z=afr["n"], text=afr["name"],
        colorscale=[[0, "#CFE6D6"], [1, "#12402A"]],
        marker_line_color="rgba(128,128,128,0.30)", marker_line_width=0.3,
        colorbar=dict(title=dict(text="Africa", side="top"), x=1.00, y=0.76,
                      len=0.46, thickness=8),
        hovertemplate="<b>%{text}</b><br>%{z} studies<extra>African-based</extra>",
    )
    fig.add_choropleth(
        locations=non["iso3"], z=non["n"], text=non["name"],
        colorscale=[[0, "#F6D9BC"], [1, "#7E430E"]],
        marker_line_color="rgba(128,128,128,0.30)", marker_line_width=0.3,
        colorbar=dict(title=dict(text="Outside", side="top"), x=1.08, y=0.24,
                      len=0.46, thickness=8),
        hovertemplate="<b>%{text}</b><br>%{z} studies<extra>Outside Africa</extra>",
    )
    fig.update_geos(**_GEO)
    fig.update_layout(
        height=380, margin={"t": 0, "b": 0, "l": 0, "r": 60},
        paper_bgcolor="rgba(0,0,0,0)", geo_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def author_origin_map(df):
    """Dispatch to the chosen style (set MAP_STYLE above)."""
    return (author_origin_bubbles(df) if MAP_STYLE == "bubbles"
            else author_origin_choropleth(df))

st.set_page_config(
    page_title="AISESA | African Energy Modelling Observatory",
    page_icon="assets/aisesa_logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.html(SIDEBAR_CSS)
render_logo()

AFRICAN_ISOS = set(ISO2_TO_ISO3)


def _origin(d):
    d = str(d).strip()
    if not d:
        return None
    codes = [x.strip()[:2].upper() for x in d.replace(",", ";").split(";") if x.strip()]
    has_a = any(c in AFRICAN_ISOS for c in codes)
    has_n = any(c not in AFRICAN_ISOS for c in codes)
    return "Mixed" if has_a and has_n else ("African-led" if has_a else "Non-African")


@st.cache_data(ttl=3600)
def get_stats(db_token: int):
    studies = load_studies()
    countries = load_countries()
    tools = load_tools()
    enriched = enrich_countries(countries, studies)

    n = len(studies)
    years = studies["year"].dropna()
    y0, y1 = (int(years.min()), int(years.max())) if len(years) else (0, 0)
    covered = int((enriched["n_studies_actual"] > 0).sum())

    origins = studies["developer_origin"].map(_origin).dropna()
    nonafr = round((origins == "Non-African").sum() / len(origins) * 100) if len(origins) else 0
    african_led = round((origins == "African-led").sum() / len(origins) * 100) if len(origins) else 0

    adhoc = coverage(studies, "frequency", positive=("ad_hoc", "occasional"))["pct"]
    informal = coverage(studies, "informal_economy", positive=("yes",))["pct"]
    opensrc = coverage(studies, "open_source", positive=("open", "mixed"))["pct"]

    by_year = years.astype(int).value_counts().sort_index().reset_index()
    by_year.columns = ["Year", "Studies"]

    # Author-origin counts (each country counted once per study) -> world map df
    from collections import Counter
    _oc = Counter()
    for d in studies["developer_origin"].dropna():
        for code in {x.strip()[:2].upper()
                     for x in str(d).replace(",", ";").split(";") if x.strip()}:
            _oc[code] += 1
    _afr_name = dict(zip(countries["iso_code"], countries["country_name"]))
    _rows = []
    for c, v in _oc.items():
        if c not in ISO2_TO_ISO3_WORLD:
            continue
        is_afr = c in AFRICAN_ISOS
        _rows.append({
            "iso3": ISO2_TO_ISO3_WORLD[c], "n": v,
            "group": "African-based" if is_afr else "Based outside Africa",
            "name": _afr_name.get(c) or _WORLD_NAMES.get(c, c),
        })
    origin_map = pd.DataFrame(_rows)

    return dict(n=n, n_tools=len(tools), n_countries=len(countries), covered=covered,
                y0=y0, y1=y1, nonafr=nonafr, african_led=african_led, adhoc=adhoc,
                informal=informal, opensrc=opensrc, by_year=by_year,
                origin_map=origin_map)


S = get_stats(db_cache_token())

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<p style='font-size:0.78rem; color:var(--text-color); text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>Platform</p>",
        unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.82rem; line-height:1.6;'>A living inventory of energy modelling "
        "studies and tools applied across Africa.</p>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:var(--text-color); text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>Quick stats</p>",
        unsafe_allow_html=True)
    cs1, cs2 = st.columns(2)
    cs1.metric("Countries", S["n_countries"])
    cs1.metric("Studies", S["n"])
    cs2.metric("Tools", S["n_tools"])
    cs2.metric("Period", f"{S['y0']}–{S['y1']}")
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:var(--text-color); text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>Views</p>",
        unsafe_allow_html=True)
    st.markdown(
        """<ul style='font-size:0.82rem; line-height:2; padding-left:1rem;'>
        <li>🗺 <b>Map</b> — where modelling happens</li>
        <li>📊 <b>Gap Analysis</b> — who models, what's missing</li>
        <li>📈 <b>Readiness</b> — country readiness scores</li>
        <li>🔍 <b>Browse Studies</b> — explore the inventory</li>
        <li>🛠 <b>Recommender</b> — find the right tool</li>
        <li>📖 <b>Methodology</b> — how scores are built</li>
        </ul>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.69rem; color:var(--text-color); font-style:italic; line-height:1.5;'>AISESA · MINES Paris-PSL<br/>Research Platform · 2026</p>",
        unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────────
st.markdown(beta_banner(), unsafe_allow_html=True)
st.markdown(
    "<h1 style='margin-top:0.4rem; margin-bottom:0;'>African Energy Modelling Observatory</h1>",
    unsafe_allow_html=True)
st.markdown(
    "<p style='color:var(--text-color); margin-top:2px; font-size:1.09rem; font-family:\"Source Serif 4\",Georgia,serif; font-style:italic;'>"
    "How is Africa's energy future being modelled? by whom, with what tools, and where are the silences?</p>",
    unsafe_allow_html=True)


# ── Narrative framing (live figures) ─────────────────────────────────────────────
st.markdown(f"""
<div style='font-family:Georgia,serif; font-size:1rem; line-height:1.7; color:var(--text-color); max-width:1200px; margin:0; text-align:justify; hyphens:auto;'>

<p>The <i>African Energy Modelling Observatory</i> is a living synthesis of how energy systems
across the continent are represented in quantitative models. It currently documents
<i>{S['n']} modelling studies</i> published between <i>{S['y0']} and {S['y1']}</i>,
applied across African countries</b> and drawing on
<i>{S['n_tools']} distinct modelling tools</i>.</p>

<p>What emerges from the inventory is that <i>{S['nonafr']}%</i> of studies are led by
institutions based outside the continent. Only <i>{S['african_led']}%</i> are African-led and <i>{S['adhoc']}%</i> are produced on an <i>ad hoc</i> or occasional basis rather than embedded in routine national planning. African-specific realities remain under-represented: just
<i>{S['informal']}%</i> of assessed studies explicitly model the informal economy. Yet
<i>{S['opensrc']}%</i> already rely on open or mixed-licence tools, an opening for locally-owned,
reproducible modelling capacity.</p>

<p>This observatory is intended less as a catalogue than as a <i>starting point for dialogue</i>: to make visible where modelling effort concentrates, where it is absent, and how the community
might close those gaps. Every figure on this platform updates automatically as new studies are added.</p>

</div>
""", unsafe_allow_html=True)

st.markdown(
    "<div style='font-family:Georgia,serif; font-weight:600; font-size:0.98rem; "
    "margin:0 0 0.3rem 0;'>Where the authors are based</div>",
    unsafe_allow_html=True)
st.plotly_chart(author_origin_map(S["origin_map"]), use_container_width=True)
st.caption("Author institutions by country, counted once per study — "
            "most modelling effort is still based outside Africa.")

st.divider()

# ── Live key figures ─────────────────────────────────────────────────────────────
st.markdown("<h3 style='font-family:Georgia,serif;'>The inventory at a glance</h3>", unsafe_allow_html=True)
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Studies", S["n"])
m2.metric("Countries covered", f"{S['covered']}/{S['n_countries']}")
m3.metric("Modelling tools", S["n_tools"])
m4.metric("Non-African-led", f"{S['nonafr']}%")
m5.metric("Open / mixed licence", f"{S['opensrc']}%")
st.caption("Percentages are computed only over studies where the dimension was assessed, "
           "blank cells mean *not assessed*, not *no*.")

col_chart, col_nav = st.columns([3, 2])
with col_chart:
    fig = px.bar(S["by_year"], x="Year", y="Studies",
                 color_discrete_sequence=[GREEN],
                 title="Studies by publication year")
    fig.update_layout(height=300, margin={"t": 40, "b": 0, "l": 0, "r": 0},
                      paper_bgcolor="rgba(0,0,0,0)", xaxis=dict(dtick=2),
                      yaxis_title="Studies", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

with col_nav:
    st.markdown("<h4 style='font-family:Georgia,serif; margin-bottom:0;'>Follow the storyline</h4>",
                unsafe_allow_html=True)
    st.markdown("""
1. **🗺 Map** — where is Africa being modelled?
2. **📊 Gap Analysis** — who models, and what do they leave out?
3. **📈 Readiness** — which countries are ready to use models?
4. **🔍 Browse Studies** — explore the full evidence
5. **🛠 Recommender** — which tool fits your context?
6. **📖 Methodology** — how every score is computed
""")

st.divider()

# ── What's in this inventory (transparency block, visible to lambda visitors) ──
_studies_for_breakdown = load_studies()
_lvl_counts = _studies_for_breakdown["extraction_level"].fillna("(unclassified)").value_counts().to_dict()
_n_full = _lvl_counts.get("full", 0)
_n_light = _lvl_counts.get("light", 0)

st.markdown(f"""
<div style='background:rgba(128,128,128,0.06); padding:18px 22px;
            border-radius:4px; margin:18px 0 24px 0; font-family:Inter,sans-serif;'>
  <p style='margin:0 0 12px 0; font-size:1.1rem; color:var(--text-color);
            text-transform:uppercase; letter-spacing:0.08em; font-weight:800;'>
    <b>What's in this inventory</b>
  </p>
  <p style='margin:0 0 14px 0; font-size:0.88rem; color:var(--text-color); line-height:1.4;'>
    Studies are classified by <b>extraction depth</b>: how detailed the data we extracted is.
    This depends on the type of model used. Statistics computed on a mix of these two
    categories can be misleading, so most analytical pages let you filter by level.
  </p>
  <div style='display:grid; grid-template-columns:repeat(2, 1fr); gap:14px;'>
    <div style='background:rgba(128,128,128,0.12); padding:12px 14px; border-radius:6px;'>
      <div style='font-size:1.1rem; font-weight:700; color:var(--text-color);'>{_n_full}</div>
      <div style='font-size:0.88rem; color:var(--text-color); text-transform:uppercase;
                  letter-spacing:0.05em; font-weight:700; margin:2px 0 6px 0;'><b>full</b></div>
      <div style='font-size:0.82rem; color:var(--text-color); line-height:1.4;'>
        Long-term planning models (MESSAGE, OSeMOSYS, TIMES, LEAP, PLEXOS, Balmorel).
        All 50+ fields extracted, whether the document is a paper, a technical report,
        or a country-policy document using one of these tools.
      </div>
    </div>
    <div style='background:rgba(128,128,128,0.12); padding:12px 14px; border-radius:6px;'>
      <div style='font-size:1.1rem; font-weight:700; color:var(--text-color);'>{_n_light}</div>
      <div style='font-size:0.88rem; color:var(--text-color); text-transform:uppercase;
                  letter-spacing:0.05em; font-weight:700; margin:2px 0 6px 0;'><b>light</b></div>
      <div style='font-size:0.82rem; color:var(--text-color); line-height:1.4;'>
        Techno-economic, GIS, mini-grid, electrification, calculators (HOMER, OnSSET,
        GACMO), and country-policy documents without a full planning model. Core
        fields only.
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
st.divider()

st.markdown(
    "<p style='text-align:center; font-size:0.92rem; color:var(--text-color); margin-top:24px;'>"
    "<b>AISESA &nbsp;·&nbsp; MINES Paris-PSL &nbsp;·&nbsp; Research Platform</b></p>",
    unsafe_allow_html=True)