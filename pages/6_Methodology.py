"""Methodology and scores — documents how every indicator is computed.

This page exists for replicability (AISESA feedback item 12). It mirrors the
exact formulas in utils.data (compute_gap_score, compute_readiness, coverage)
so the numbers shown across the platform can be reproduced and challenged.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.data import load_studies
from utils.ui import SIDEBAR_CSS, render_logo

st.set_page_config(page_title="Methodology | AISESA", layout="wide", page_icon="assets/aisesa_logo.png")
st.html(SIDEBAR_CSS)
render_logo()

studies = load_studies()
n = len(studies)
lv = studies["extraction_level"].value_counts()

with st.sidebar:
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:#1E5631; text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>On this page</p>",
        unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.82rem; line-height:1.9;'>· Extraction levels<br>· Empty-cell rule<br>"
        "· Gap score<br>· Readiness score<br>· Recommender scoring<br>· Limitations</p>",
        unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.68rem; color:#5A645E; font-style:italic; line-height:1.5;'>AISESA · MINES Paris-PSL<br/>Research Platform · 2025</p>",
        unsafe_allow_html=True)

st.title("Methodology & scores")
st.markdown(
    "<p style='font-size:1.05rem; color:#444; font-family:Georgia,serif; line-height:1.7; max-width:820px;'>"
    "Every figure on this platform is reproducible. This page documents how studies are extracted, how "
    "empty data is treated, and exactly how each composite score is computed — so the indicators can be "
    "scrutinised and replicated.</p>",
    unsafe_allow_html=True)
st.divider()

# ── Extraction levels ────────────────────────────────────────────────────────────
st.header("Extraction levels")
st.markdown(
    "Each study is classified at one of three extraction depths, based on **what kind of "
    "document it is** and **what kind of model it uses**. Lighter levels intentionally "
    "leave methodological fields blank — this is recorded, not hidden.")
st.markdown(
    "- **Full** — long-term planning models (MESSAGE, OSeMOSYS, TIMES, LEAP, PLEXOS, "
    "Balmorel). These have a multi-decade horizon and model full energy systems. "
    "All 50+ structured fields extracted, including methodological details "
    "(mathematical approach, energy vectors, strengths/weaknesses, financing).\n"
    "- **Light** — techno-economic, GIS-based, electrification, mini-grid or simulation "
    "studies (HOMER, OnSSET, RETScreen, custom GIS code, site-specific analyses). "
    "About 34 core fields extracted (scale, countries, tool, objective, key result, "
    "AISESA themes, authorship). Detailed methodology fields are omitted by design.\n"
    "- **Narrative** — country-policy documents (NDCs, national energy plans, "
    "SE4All Action Agendas, World Bank or AfDB country reports). About 24 summary "
    "fields extracted, focused on identification, scope, and policy framing. "
    "Even if these documents use models internally (e.g. a NDC using GACMO), they "
    "remain classified as narrative because the *document type* is country-policy.\n"
    "- **Unspecified** — extraction depth not yet recorded.")
st.warning("⚠ Mixing levels in statistics can mislead. For example, "
           "'Top tools by usage' computed across all 3 levels will dilute MESSAGE/OSeMOSYS "
           "(typical of full) with HOMER (typical of light). Most analytical pages let "
           "you filter by level — use it to keep comparisons honest.")
st.info(f"Current inventory ({n} studies): {int(lv.get('full',0))} full · {int(lv.get('light',0))} light · "
        f"{int(lv.get('narrative',0))} narrative · {int(lv.get('unspecified',0))} unspecified.")

# ── Empty-cell rule ────────────────────────────────────────────────────────────
st.header("How empty cells are treated")
st.markdown(
    "A blank cell means **not assessed**, never **no**. Coverage percentages are therefore computed only "
    "over the studies where a dimension was actually evaluated:")
st.latex(r"\text{coverage}(\%) = \frac{\text{studies marked 'yes'}}{\text{studies where the field is non-empty}} \times 100")
st.markdown(
    "Example: if clean cooking is assessed in 29 studies and 4 of them model it, coverage is "
    "4 / 29 = 14% — not 4 / 65 = 6%. Counting blanks as 'no' would understate coverage as the inventory "
    "grows with lightly-extracted studies.")
st.divider()

# ── Gap score ────────────────────────────────────────────────────────────────────
st.header("Gap score (0–100)")
st.markdown(
    "A country-level measure of how under-served it is by current modelling. **Higher = more under-served.** "
    "Four components, each contributing a fixed share:")
st.markdown(
    "| Component | Weight | How it is measured |\n"
    "|---|---|---|\n"
    "| African feature coverage | 40% | Share of 4 features (informal economy, biomass/charcoal, power reliability, urbanisation) covered by at least one study of that country |\n"
    "| Institutional capacity | 30% | yes = 2, partial = 1, no = 0 (scaled to the 30 points) |\n"
    "| Data availability | 20% | good = 2, moderate = 1, poor = 0 (scaled to the 20 points) |\n"
    "| Model density | 10% | Number of studies applied, capped at 10 |")
st.latex(r"\text{gap} = (1-\text{feat})\cdot 40 + \left(1-\tfrac{\text{cap}}{2}\right)\cdot 30 + \left(1-\tfrac{\text{dat}}{2}\right)\cdot 20 + \left(1-\tfrac{\min(n,10)}{10}\right)\cdot 10")
st.caption("feat = feature ratio (0–1); cap = capacity points (0–2); dat = data points (0–2); n = studies applied.")

# ── Readiness score ────────────────────────────────────────────────────────────
st.header("Readiness score (0–10)")
st.markdown(
    "A country-level measure of the conditions needed to use models in policy. **Higher = more ready.** "
    "Five additive components:")
st.markdown(
    "| Component | Max points | Scale |\n"
    "|---|---|---|\n"
    "| Institutional capacity | 3 | yes = 3, partial = 1.5, no = 0 |\n"
    "| Data availability | 3 | good = 3, moderate = 1.5, poor = 0 |\n"
    "| NDC commitment | 1 | present = 1 |\n"
    "| Long-term strategy | 1 | present = 1 |\n"
    "| Electrification rate | 2 | rate / 100 × 2 |")
st.latex(r"\text{readiness} = \text{cap} + \text{dat} + \text{ndc} + \text{lts} + \min\!\left(\tfrac{\text{elec}}{100}\cdot 2,\; 2\right)")

# ── Recommender ────────────────────────────────────────────────────────────────
st.header("Recommender scoring")
st.markdown(
    "The tool recommender scores each tool against your six answers, adding points for policy match "
    "(+30), budget fit (±10–25), capacity fit (±15–20), time-horizon fit (+10), African track record "
    "(+5–10) and available training (+5). It is a transparent heuristic to shortlist candidates — not a "
    "substitute for expert judgement.")
st.divider()

# ── Limitations ────────────────────────────────────────────────────────────────
st.header("Limitations")
st.markdown(
    "- The weights above are deliberate but not empirically calibrated; they encode editorial judgement "
    "about what makes a country under-served or ready, and can be revised.\n"
    "- Scores are only as complete as the underlying extraction; lightly-extracted studies contribute "
    "less detail.\n"
    "- Country attributes (capacity, data availability) are coded from secondary sources and simplify a "
    "complex reality.\n"
    "- The inventory is a living document and figures change as studies are added or corrected.")