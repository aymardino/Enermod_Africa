"""Methodology and scores — documents how every indicator is computed.

This page exists for replicability (AISESA feedback item 12). It mirrors the
exact formulas in utils.data (compute_gap_score, compute_readiness, coverage)
so the numbers shown across the platform can be reproduced and challenged.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.data import load_studies, load_countries
from utils.ui import SIDEBAR_CSS, render_logo

st.set_page_config(page_title="Methodology | AISESA", layout="wide", page_icon="assets/aisesa_logo.png")
st.html(SIDEBAR_CSS)
render_logo()

def callout(text, kind="warning"):
    """Readable long-form callout box (st.warning/st.info render poorly for
    multi-line methodology text under some themes — this uses explicit
    light colours that stay legible regardless of the active theme)."""
    styles = {
        "warning": ("#FFF8E1", "#7A5B00", "#F5C518"),   # bg, text, left-border
        "info":    ("#EAF3EC", "#1E5631", "#2E7D32"),
    }
    bg, tx, bd = styles.get(kind, styles["warning"])
    st.markdown(
        f"<div style='background:{bg}; color:{tx}; border-left:4px solid {bd}; "
        f"border-radius:6px; padding:14px 18px; margin:12px 0; "
        f"font-family:Inter,sans-serif; font-size:0.88rem; line-height:1.6;'>"
        f"{text}</div>", unsafe_allow_html=True)

studies = load_studies()
countries = load_countries()
n = len(studies)
lv = studies["extraction_level"].value_counts()
n_gov = int((countries["energy_governance"] != "").sum())
n_dat = int((countries["data_availability"] != "").sum())

with st.sidebar:
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:var(--text-color); text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>On this page</p>",
        unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:0.82rem; line-height:1.9;'>· Extraction levels<br>· Empty-cell rule<br>"
        "· Country indicators & sources<br>· Gap score<br>· Readiness score<br>"
        "· Recommender scoring<br>· Limitations</p>",
        unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.68rem; color:var(--text-color); font-style:italic; line-height:1.5;'>AISESA · MINES Paris-PSL<br/>Research Platform · 2026</p>",
        unsafe_allow_html=True)

st.title("Methodology & scores")
st.markdown(
    "<p style='font-size:1.05rem; color:var(--text-color); font-family:Georgia,serif; line-height:1.7; max-width:1100px;text-align:justify; hyphens:auto;'>"
    "Every figure on this platform is reproducible. This page documents how studies are extracted, how "
    "empty data is treated, where every country-level indicator comes from, and exactly how each "
    "composite score is computed — so the indicators can be scrutinised and replicated.</p>",
    unsafe_allow_html=True)
st.divider()

# ── Extraction levels ────────────────────────────────────────────────────────────
st.header("Extraction levels")
st.markdown(
    "Each study is classified at one of two extraction depths, based on the **type of "
    "model** used. The lighter level intentionally leaves methodological fields blank "
    "when they are not applicable — this is recorded, not hidden.")
st.markdown(
    "- **Full** — long-term planning models (MESSAGE, OSeMOSYS, TIMES, LEAP, PLEXOS, "
    "Balmorel). Multi-decade horizon, full energy systems. All 50+ structured fields "
    "extracted. This applies to peer-reviewed articles, technical reports, AND "
    "country-policy documents that use one of these tools (e.g. a NDC using LEAP).\n"
    "- **Light** — everything else: techno-economic studies, GIS-based analyses, "
    "electrification / mini-grid studies, calculators (HOMER, OnSSET, GACMO, CERC), "
    "and country-policy documents without a long-term planning model. Core fields "
    "extracted (~34 fields), methodological fields specific to system optimisation "
    "are omitted.\n"
    "- **Unspecified** — extraction depth not yet recorded.\n\n"
    "Whether a document is grey literature (NDC, WB report) or peer-reviewed is "
    "captured by the separate `grey_literature` field, not by the extraction level.")
callout("⚠ <b>Mixing levels in statistics can mislead.</b> For example, "
        "'Top tools by usage' computed across both levels will dilute MESSAGE/OSeMOSYS "
        "(typical of full) with HOMER (typical of light). Most analytical pages let "
        "you filter by level — use it to keep comparisons honest.")
st.info(f"Current inventory ({n} studies): {int(lv.get('full',0))} full · "
        f"{int(lv.get('light',0))} light · {int(lv.get('unspecified',0))} unspecified.")
st.divider()

# ── Empty-cell rule ────────────────────────────────────────────────────────────
st.header("How empty cells are treated")
st.markdown(
    "A blank cell means **not assessed**, never **no**. Coverage percentages are therefore computed only "
    "over the studies where a dimension was actually evaluated:")
st.latex(r"\text{coverage}(\%) = \frac{\text{studies marked 'yes'}}{\text{studies where the field is non-empty}} \times 100")
st.markdown(
    "Example: if clean cooking is assessed in 29 studies and 4 of them model it, coverage is "
    "4 / 29 = 14% — not 4 / 65 = 6%. Counting blanks as 'no' would understate coverage as the inventory "
    "grows with lightly-extracted studies.\n\n"
    "The same rule applies to country-level indicators below: a country not covered by a source is left "
    "blank and excluded from the corresponding ranking, never defaulted to the worst value.")
st.divider()

# ── Country indicators & sources ──────────────────────────────────────────────────
st.header("Country indicators & sources")
st.markdown(
    "Four country-level indicators feed the Gap and Readiness scores. Each has a public, citable "
    "source — no indicator on this platform is estimated or inferred without one.")

st.subheader("Energy governance")
st.markdown(
    "**Source:** World Bank / ESMAP, *Regulatory Indicators for Sustainable Energy* (RISE), 2023 edition. "
    "[rise.esmap.org](https://rise.esmap.org)\n\n"
    "**Computation:** mean of three RISE governance indicators — *Electrification Governance and "
    "Planning*, *Renewable Energy Governance*, *Energy Efficiency Governance* — each scored 0–100 by "
    "the World Bank. The mean is then classified into RISE's own three performance zones:")
st.markdown(
    "| RISE score | Category |\n"
    "|---|---|\n"
    "| ≥ 66.67 (green zone) | `strong` |\n"
    "| 33.33 – 66.66 (yellow zone) | `moderate` |\n"
    "| < 33.33 (red zone) | `weak` |")
callout(
    "<b>Caveat — read before interpreting this indicator.</b> RISE measures whether a formal regulatory "
    "and policy framework <i>exists</i> (a named regulator, a published national plan, a written incentive "
    "scheme) — it does <b>not</b> measure whether that framework is effectively implemented, nor does it "
    "measure a country's analytical or energy-modelling capacity directly. A country can score "
    "<code>strong</code> on paper while execution on the ground remains weak; conversely, informal or "
    "emerging capacity that isn't yet codified into regulation won't show up here. No public dataset "
    "measures modelling capacity directly. <code>energy_governance</code> is used as the best available "
    "public proxy for institutional readiness — a country with an established regulatory framework is "
    "more likely to have institutions able to commission, run or interpret an energy model. A corpus-based "
    "measure (e.g. share of African-led, nationally-scoped studies per country, now feasible with 261 "
    "national/subnational studies in the inventory) is a natural complement and may be added once "
    "validated against RISE.")
st.caption(f"Coverage: {n_gov}/{len(countries)} countries. The remaining countries — mostly small "
           "island states not covered by RISE — are shown as *not assessed*, not as `weak`.")
 
st.subheader("Data availability")
st.markdown(
    "**Source:** Ember, *African Electricity Data Transparency*, January 2022. "
    "[ember-energy.org](https://ember-energy.org/app/uploads/2024/10/African-Electricity-Data-Transparency.pdf)\n\n"
    "**Computation:** Ember scored each of the 54 African countries 0–5 on the availability and "
    "quality of *national* electricity production data sources, combining six criteria: publishing "
    "lag, time granularity, fuel-type disaggregation, sub-national/unit-level detail, additional data "
    "metrics (capacity, imports, etc.), and ease of download. The 0–5 score is grouped into three "
    "levels:")
st.markdown(
    "| Ember score | Category |\n"
    "|---|---|\n"
    "| 3 – 5 | `good` |\n"
    "| 1 – 2 | `limited` |\n"
    "| 0 | `none` |")
st.warning(
    "**Caveat.** This score measures the transparency of *electricity production* data specifically, "
    "not the full range of data an energy model may need (demand by sector, costs, resource "
    "potentials, energy balances). It is used as a proxy for broader data availability. The report "
    "dates from January 2022; several countries have since published new or updated data portals, so "
    "some scores are likely understated for 2026.")
st.caption(f"Coverage: {n_dat}/{len(countries)} countries — full coverage, all 54 African countries "
           "were assessed by Ember.")

st.subheader("Electrification rate")
st.markdown(
    "**Source:** World Bank, World Development Indicators, indicator `EG.ELC.ACCS.ZS` "
    "(Access to electricity, % of population), 2024 data release.\n\n"
    "Used directly as a percentage (0–100), each country's most recent available year is recorded "
    "alongside the value.")

st.subheader("NDC and Long-Term Strategy submission")
st.markdown(
    "**Source:** UNFCCC NDC Registry ([unfccc.int/NDCREG](https://unfccc.int/NDCREG)) and the UNFCCC "
    "Long-Term Strategies portal. Binary `yes`/`no` per country, verified against the official registry.")
st.divider()

# ── Gap score ────────────────────────────────────────────────────────────────────
st.header("Gap score (0–100)")
st.markdown(
    "A country-level measure of how under-served it is by current modelling. **Higher = more under-served.** "
    "Four components, each contributing a fixed share of the 100 points:")
st.markdown(
    "| Component | Weight | How it is measured |\n"
    "|---|---|---|\n"
    "| African feature coverage | 35% | Share of 4 features (informal economy, biomass/charcoal, power reliability, urbanisation) covered by at least one study of that country |\n"
    "| Data availability | 30% | Ember score: `good` = 2, `limited` = 1, `none` = 0 (scaled to 30 pts) |\n"
    "| Energy governance | 20% | RISE score: `strong` = 2, `moderate` = 1, `weak` = 0 (scaled to 20 pts); countries with no RISE coverage get the neutral mid-value (1), so missing data neither helps nor hurts |\n"
    "| Model density | 15% | Number of distinct modelling tools applied, capped at 10 |")
st.latex(
    r"\text{gap} = (1-\text{feat})\cdot 35 + \left(1-\tfrac{\text{dat}}{2}\right)\cdot 30 "
    r"+ \left(1-\tfrac{\text{gov}}{2}\right)\cdot 20 + \left(1-\tfrac{\min(n,10)}{10}\right)\cdot 15"
)
st.caption("feat = feature ratio (0–1); dat = data-availability points (0–2); "
           "gov = governance points (0–2, neutral = 1 if not assessed); n = distinct models applied.")
st.divider()

# ── Readiness score ────────────────────────────────────────────────────────────
st.header("Readiness score (0–10)")
st.markdown(
    "A country-level measure of the conditions needed to use models in policy. **Higher = more ready.** "
    "Five additive components, every one traceable to a cited public source:")
st.markdown(
    "| Component | Max points | Scale | Source |\n"
    "|---|---|---|---|\n"
    "| Energy governance | 3 | `strong` = 3, `moderate` = 1.5, `weak` = 0 | World Bank/ESMAP RISE 2023 |\n"
    "| Data availability | 3 | `good` = 3, `limited` = 1.5, `none` = 0 | Ember, Jan 2022 |\n"
    "| Electrification rate | 2 | rate / 100 × 2 | World Bank WDI, 2024 |\n"
    "| NDC commitment | 1 | present = 1 | UNFCCC NDC Registry |\n"
    "| Long-term strategy | 1 | present = 1 | UNFCCC LT-LEDS portal |")
st.latex(
    r"\text{readiness} = \text{gov} + \text{dat} + \min\!\left(\tfrac{\text{elec}}{100}\cdot 2,\; 2\right) "
    r"+ \text{ndc} + \text{lts}"
)
st.warning(
    f"**Countries without RISE coverage ({len(countries) - n_gov}/{len(countries)}, mostly small island "
    "states) have no readiness score at all** — they are excluded from rankings and averages rather "
    "than scored as unready. This follows the empty-cell rule above.")
st.divider()

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
    "- **Energy governance is a proxy, not a direct measure of modelling capacity** — see the caveat "
    "above. A high score reflects the existence of a regulatory framework, not its implementation.\n"
    "- The Ember data-transparency score dates from January 2022 and may understate progress made "
    "since then in some countries.\n"
    "- Scores are only as complete as the underlying extraction; lightly-extracted studies contribute "
    "less detail.\n"
    "- The inventory is a living document and figures change as studies are added or corrected.")