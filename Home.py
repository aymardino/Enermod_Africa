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
import pycountry

# ISO-2 -> ISO-3 and names for ALL countries in the world.
# Uses pycountry (see requirements.txt) which contains the official ISO 3166 list
# of 249 countries, kept in sync with the standard.
def _build_world_maps():
    iso3, names = {}, {}
    for c in pycountry.countries:
        iso2 = c.alpha_2
        iso3[iso2] = c.alpha_3
        # Use the common short name when available (e.g. "Iran" instead of
        # "Iran, Islamic Republic of"); fall back to the official name otherwise.
        names[iso2] = getattr(c, "common_name", c.name)
    return iso3, names

_WORLD_ISO3, _WORLD_NAMES = _build_world_maps()

# African entries win on any overlap (already defined above).
ISO2_TO_ISO3_WORLD = {**_WORLD_ISO3, **ISO2_TO_ISO3}

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
    mixed_origin = round((origins == "Mixed").sum() / len(origins) * 100) if len(origins) else 0
    origins_full = studies.loc[studies["extraction_level"]=="full", "developer_origin"].map(_origin).dropna()
    origins_light = studies.loc[studies["extraction_level"]=="light", "developer_origin"].map(_origin).dropna()
    afr_led_full = round((origins_full=="African-led").sum()/len(origins_full)*100) if len(origins_full) else 0
    afr_led_light = round((origins_light=="African-led").sum()/len(origins_light)*100) if len(origins_light) else 0

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
                y0=y0, y1=y1, nonafr=nonafr, african_led=african_led, mixed=mixed_origin,
                afr_led_full=afr_led_full, afr_led_light=afr_led_light, opensrc=opensrc, 
                by_year=by_year, origin_map=origin_map)


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
    import os, datetime as dt
    _db_path = "data/enermod.db"
    if os.path.exists(_db_path):
        _mtime = dt.datetime.fromtimestamp(os.path.getmtime(_db_path))
        st.markdown(
            f"<p style='font-size:0.68rem; color:var(--text-color); opacity:0.6;'>"
            f"DB updated: {_mtime.strftime('%Y-%m-%d %H:%M')}</p>",
            unsafe_allow_html=True)
        
    st.markdown(
        "<p style='font-size:0.69rem; color:var(--text-color); font-style:italic; line-height:1.5;'>AISESA · MINES Paris-PSL<br/>Research Platform · 2026</p>",
        unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────────
st.markdown(beta_banner(), unsafe_allow_html=True)
st.markdown(
    "<h1 style='margin-top:0.4rem; margin-bottom:0;'>African Energy Modelling Observatory</h1>",
    unsafe_allow_html=True)


# ── Narrative framing (live figures) ─────────────────────────────────────────────
st.markdown(f"""
<p>Africa's energy future is being modelled, but by whom, with which tools, and with what
blind spots? Individual studies exist in abundance; a synthesis of what they collectively
show, and collectively miss, does not.</p>

<p>This observatory maps <b>{S['n']} modelling studies</b> published between {S['y0']} and
{S['y1']}, covering all 54 African countries and drawing on <b>{S['n_tools']} distinct
modelling tools</b>. Every study is manually verified, and every figure updates as the
inventory grows.</p>

<p>It is built to answer questions such as:</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
- Which countries are heavily modelled, and which are barely studied at all?
- Which tools dominate ? and are they open, or locked behind licences?
- How much of this research is led by African institutions?
- Do the models capture what actually shapes African energy systems: informal economies,
  charcoal and biomass, unreliable supply, rapid urbanisation?
- Which countries have the institutions and data to put models to work?
""")

st.markdown(f"""
<style>
  .kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr));
               gap:10px; margin:16px 0 8px 0; }}
  .kpi-box {{ background:rgba(128,128,128,0.08); border-radius:8px; padding:12px 14px; }}
  .kpi-lbl {{ font-size:0.78rem; opacity:0.7; margin-bottom:2px; }}
  .kpi-val {{ font-size:1.5rem; font-weight:700; line-height:1.15; }}
</style>
<div class="kpi-grid">
  <div class="kpi-box"><div class="kpi-lbl">Studies</div>
    <div class="kpi-val">{S['n']}</div></div>
  <div class="kpi-box"><div class="kpi-lbl">Countries covered</div>
    <div class="kpi-val">{S['covered']}/{S['n_countries']}</div></div>
  <div class="kpi-box"><div class="kpi-lbl">Energy modelling tools</div>
    <div class="kpi-val">{S['n_tools']}</div></div>
  <div class="kpi-box"><div class="kpi-lbl">African-led</div>
    <div class="kpi-val">{S['african_led']}%</div>
    <div style="font-size:0.58rem; opacity:0.6; margin-top:3px;">
      {S['afr_led_full']}% whole-system · {S['afr_led_light']}% focused</div></div>
  <div class="kpi-box"><div class="kpi-lbl">Open / mixed licence</div>
    <div class="kpi-val">{S['opensrc']}%</div></div>
</div>
""", unsafe_allow_html=True)
st.caption("Every figure updates automatically as new studies are added. "
           "Full methodology and sources on the Methodology page.")

st.markdown(
    "<div style='font-family:Georgia,serif; font-weight:600; font-size:0.98rem; "
    "margin:0 0 0.3rem 0;'>Where the authors are based</div>",
    unsafe_allow_html=True)
st.plotly_chart(author_origin_map(S["origin_map"]), use_container_width=True)
st.caption("Author institutions by country, counted once per study — "
            "most modelling effort is still based outside Africa.")

st.divider()

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

st.markdown("#### What's in this inventory")
st.markdown(
    "<p style='font-family:Georgia,serif; font-size:0.95rem; line-height:1.7; "
    "color:var(--text-color); max-width:900px;'>"
    "Studies are grouped by the <i>scope of the model</i> they use. Statistics mixing the two "
    "can mislead, so most analytical pages let you filter by scope.</p>",
    unsafe_allow_html=True)

sc1, sc2 = st.columns(2)
with sc1:
    st.markdown(
        f"<p style='font-family:Georgia,serif; margin-bottom:2px;'>"
        f"<b style='font-size:1.1rem; color:{GREEN};'>{_n_full}</b> "
        f"<b>whole-system studies</b></p>"
        f"<p style='font-size:0.85rem; line-height:1.6; opacity:0.8; max-width:420px;'>"
        f"Long-term planning models — MESSAGE, OSeMOSYS, TIMES, LEAP, PLEXOS, Balmorel. "
        f"All 50+ fields extracted.</p>",
        unsafe_allow_html=True)
with sc2:
    st.markdown(
        f"<p style='font-family:Georgia,serif; margin-bottom:2px;'>"
        f"<b style='font-size:1.1rem; color:#B8860B;'>{_n_light}</b> "
        f"<b>focused studies</b></p>"
        f"<p style='font-size:0.85rem; line-height:1.6; opacity:0.8; max-width:420px;'>"
        f"Techno-economic, GIS, mini-grid, electrification and calculators — HOMER, OnSSET, "
        f"GACMO. Core fields only.</p>",
        unsafe_allow_html=True)
st.divider()

st.markdown(
    "<p style='text-align:center; font-size:0.9rem; color:var(--text-color); margin-top:24px;'>"
    "<b>AISESA &nbsp;·&nbsp; MINES Paris-PSL &nbsp;·&nbsp; Research Platform</b></p>",
    unsafe_allow_html=True)