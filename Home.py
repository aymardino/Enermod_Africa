"""AISESA African Energy Modelling Observatory — Home page (live narrative)."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import plotly.express as px
from utils.data import (load_countries, load_studies, load_tools,
                        enrich_countries, coverage, ISO2_TO_ISO3, db_cache_token)
from utils.ui import SIDEBAR_CSS, beta_banner, GREEN, render_logo, inventory_breakdown

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

    return dict(n=n, n_tools=len(tools), n_countries=len(countries), covered=covered,
                y0=y0, y1=y1, nonafr=nonafr, african_led=african_led, adhoc=adhoc,
                informal=informal, opensrc=opensrc, by_year=by_year)


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
<div style='font-family:Georgia,serif; font-size:1rem; line-height:1.7; color:var(--text-color); max-width:900px; margin:0;'>

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
_n_narr = _lvl_counts.get("narrative", 0)

st.markdown(f"""
<div style='background:rgba(128,128,128,0.06); padding:18px 22px;
            border-radius:4px; margin:18px 0 24px 0; font-family:Inter,sans-serif;'>
  <p style='margin:0 0 12px 0; font-size:1.1rem; color:var(--text-color);
            text-transform:uppercase; letter-spacing:0.08em; font-weight:800;'>
    <b>What's in this inventory</b>
  </p>
  <p style='margin:0 0 14px 0; font-size:0.88rem; color:var(--text-color); line-height:1.4;'>
    Studies are classified by <b>extraction depth</b>: how detailed the data we extracted is.
    This matters: statistics computed on a mix of these three categories can be misleading,
    so most analytical pages let you filter by level.
  </p>
  <div style='display:grid; grid-template-columns:repeat(3, 1fr); gap:14px;'>
    <div style='background:rgba(128,128,128,0.12); padding:12px 14px; border-radius:6px;'>
      <div style='font-size:1.1rem; font-weight:700; color:var(--text-color);'>{_n_full}</div>
      <div style='font-size:0.88rem; color:var(--text-color); text-transform:uppercase;
                  letter-spacing:0.05em; font-weight:700; margin:2px 0 6px 0;'><b>full</b></div>
      <div style='font-size:0.82rem; color:var(--text-color); line-height:1.4;'>
        Long-term planning models (MESSAGE, OSeMOSYS, TIMES, LEAP, PLEXOS).
        All 50+ fields extracted.
      </div>
    </div>
    <div style='background:rgba(128,128,128,0.12); padding:12px 14px; border-radius:6px;'>
      <div style='font-size:1.1rem; font-weight:700; color:var(--text-color);'>{_n_light}</div>
      <div style='font-size:0.88rem; color:var(--text-color); text-transform:uppercase;
                  letter-spacing:0.05em; font-weight:700; margin:2px 0 6px 0;'><b>light</b></div>
      <div style='font-size:0.82rem; color:var(--text-color); line-height:1.4;'>
        Techno-economic, GIS, mini-grid or simulation studies (HOMER, OnSSET, custom code).
        Core fields only.
      </div>
    </div>
    <div style='background:rgba(128,128,128,0.12); padding:12px 14px; border-radius:6px;'>
      <div style='font-size:1.1rem; font-weight:700; color:var(--text-color);'>{_n_narr}</div>
      <div style='font-size:0.88rem; color:var(--text-color); text-transform:uppercase;
                  letter-spacing:0.05em; font-weight:700; margin:2px 0 6px 0;'><b>narrative</b></div>
      <div style='font-size:0.82rem; color:var(--text-color); line-height:1.4;'>
        Country-policy documents (NDCs, national plans, World Bank country reports).
        Summary fields only.
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