"""AISESA African Energy Modelling Observatory — Home page (live narrative)."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.data import (load_countries, load_studies, load_tools,
                        enrich_countries, coverage, ISO2_TO_ISO3, db_cache_token)
from utils.ui import SIDEBAR_CSS, beta_banner, GREEN, render_logo, inventory_breakdown, render_partner_logos
import pandas as pd
import pycountry
from utils.origin_map import build_origin_map_df, author_origin_choropleth

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

    _LO = {"yes": "African-led", "partial": "Mixed", "no": "Non-African"}
    _lo = studies["local_ownership"].astype(str).str.strip().str.lower().map(_LO)
    origins = _lo.dropna()
    nonafr = round((origins == "Non-African").sum() / len(origins) * 100) if len(origins) else 0
    african_led = round((origins == "African-led").sum() / len(origins) * 100) if len(origins) else 0
    mixed_origin = round((origins == "Mixed").sum() / len(origins) * 100) if len(origins) else 0
    origins_full = _lo[studies["extraction_level"] == "full"].dropna()
    origins_light = _lo[studies["extraction_level"] == "light"].dropna()
    afr_led_full = round((origins_full == "African-led").sum() / len(origins_full) * 100) if len(origins_full) else 0
    afr_led_light = round((origins_light == "African-led").sum() / len(origins_light) * 100) if len(origins_light) else 0

    opensrc = coverage(studies, "open_source", positive=("open", "mixed"))["pct"]

    by_year = years.astype(int).value_counts().sort_index().reset_index()
    by_year.columns = ["Year", "Studies"]

    # Author-origin counts (each country counted once per study) -> world map df
    origin_map = build_origin_map_df(studies, countries)

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
    import os, datetime as dt
    _db_path = "data/enermod.db"
    if os.path.exists(_db_path):
        _mtime = dt.datetime.fromtimestamp(os.path.getmtime(_db_path))
        st.markdown(
            f"<p style='font-size:0.68rem; color:var(--text-color); opacity:0.6;'>"
            f"DB updated: {_mtime.strftime('%Y-%m-%d %H:%M')}</p>",
            unsafe_allow_html=True)
        
    render_partner_logos()
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
      {S['afr_led_full']}% whole energy-system · · {S['afr_led_light']}% focused</div></div>
  <div class="kpi-box"><div class="kpi-lbl">Open / mixed licence</div>
    <div class="kpi-val">{S['opensrc']}%</div></div>
</div>
""", unsafe_allow_html=True)
st.caption("Every figure updates automatically as new studies are added. "
           "Full methodology and sources on the Methodology page.")

st.markdown(
    "<div style='font-family:Georgia,serif; font-weight:600; font-size:0.98rem; "
    "margin:0 0 0.3rem 0;'>Where the authors are based (for all studies)</div>",
    unsafe_allow_html=True)
st.plotly_chart(author_origin_choropleth(S["origin_map"]), use_container_width=True)
st.caption("Author institutions by country, counted once per study ")

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
        f"<b>whole energy-system studies</b></p>"
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

fig = px.bar(S["by_year"], x="Year", y="Studies",
                color_discrete_sequence=[GREEN],
                title="Studies by publication year")
fig.update_layout(height=300, margin={"t": 40, "b": 0, "l": 0, "r": 0},
                    paper_bgcolor="rgba(0,0,0,0)", xaxis=dict(dtick=2),
                    yaxis_title="Studies", xaxis_title="")
st.plotly_chart(fig, use_container_width=True)


st.divider()

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

st.markdown(
    "<p style='text-align:center; font-size:0.9rem; color:var(--text-color); margin-top:24px;'>"
    "<b>AISESA &nbsp;·&nbsp; MINES Paris-PSL &nbsp;·&nbsp; Research Platform</b></p>",
    unsafe_allow_html=True)