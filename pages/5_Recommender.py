"""Model Recommender page.

Scores every publicly available tool in the inventory against the user's context.
The scoring reads the harmonised fields of the tools sheet (best_for, type, scale,
time_horizon, data_intensity, licence and dependency fields, support fields) and
is documented on the Methodology page. In-house models (licence: internal) are
listed in the inventory but never ranked, since they cannot be obtained.
"""

import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from utils.data import load_tools, db_cache_token
from utils.ui import SIDEBAR_CSS, render_logo

st.set_page_config(page_title="Recommender | AISESA", layout="wide", page_icon="assets/aisesa_logo.png")
st.html(SIDEBAR_CSS)
render_logo()


@st.cache_data(ttl=3600)
def get_tools(db_token):
    return load_tools()


tools = get_tools(db_cache_token())

with st.sidebar:
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:var(--text-color); text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>About the recommender</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='font-size:0.79rem; line-height:1.7;'>"
        "Scoring weights:<br>"
        "🎯 Objective match: +30 (+10 tool type)<br>"
        "📐 Scale fit: +12<br>"
        "💰 Budget fit: -25 to +15<br>"
        "👩‍💻 Capacity and support: -20 to +23<br>"
        "⏱ Time horizon: +10<br>"
        "📊 Data fit: -8 to +10<br>"
        "🌍 Africa track record: +5 to +10<br>"
        "➕ Optional requirements: -15 to +10 each, "
        "open-source code required acts as a filter</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.69rem; color:var(--text-color); font-style:italic; line-height:1.5;'>AISESA · MINES Paris-PSL<br/>Research Platform · 2026</p>",
        unsafe_allow_html=True,
    )

st.title("Which tool fits your context?")
st.markdown(
    "<p style='font-size:1rem; color:var(--text-color); font-family:Georgia,serif; line-height:1.7; max-width:1100px;text-align:justify; hyphens:auto;'>"
    "There is no single best energy model, only the one best suited to your question, your team and your "
    "data. Answer six questions about your context, add optional requirements if you have any, and the "
    "recommender ranks the publicly available tools in the inventory. "
    "The scoring logic is documented on the Methodology page.</p>",
    unsafe_allow_html=True)
st.divider()

# ── Question options ────────────────────────────────────────────────────────────
OBJECTIVES = [
    "National energy planning (supply mix, capacity expansion)",
    "Electrification / energy access planning (grid extension, off-grid, geospatial least-cost)",
    "Project or site pre-feasibility (mini-grid, hybrid system, plant design)",
    "Regional power trade (interconnections, power pools)",
    "Power system operation, dispatch and reliability",
    "Resource assessment (solar, wind, hydro potential)",
    "Climate-energy-water-land nexus",
    "Demand forecasting",
    "Emissions, air quality and climate impact assessment",
    "Buildings and thermal energy",
]
SCALES = {
    "Facility":     "Facility, project site or community",
    "Sub-national": "Sub-national / state / province",
    "National":     "National",
    "Regional":     "Regional / multi-country",
    "Continental":  "Continental / global",
}
HORIZONS = {
    "Long-term":   "Long-term (strategic planning to 2030-2060)",
    "Medium-term": "Medium-term (5 to 15 years)",
    "Short-term":  "Short-term (operational, sub-annual, project lifetime)",
}
# Scales and horizons that make sense for each objective. The lists follow the
# scales and horizons actually recorded for the tools serving each objective in
# the inventory, so impossible pairs (regional trade at sub-national scale,
# strategic planning for a plant design) are not offered in the first place.
ALLOWED = {
    "National energy planning":        (["Sub-national", "National", "Regional", "Continental"], ["Long-term", "Medium-term", "Short-term"]),
    "Electrification / energy access": (["Facility", "Sub-national", "National", "Regional", "Continental"], ["Long-term", "Medium-term", "Short-term"]),
    "Project or site pre-feasibility": (["Facility", "Sub-national"], ["Short-term"]),
    "Regional power trade":            (["Regional", "Continental"], ["Long-term", "Medium-term", "Short-term"]),
    "Power system operation":          (["Facility", "Sub-national", "National", "Regional"], ["Short-term", "Medium-term", "Long-term"]),
    "Resource assessment":             (["Facility", "Sub-national", "National", "Regional", "Continental"], ["Short-term"]),
    "Climate-energy-water-land nexus": (["Sub-national", "National", "Regional", "Continental"], ["Long-term", "Medium-term", "Short-term"]),
    "Demand forecasting":              (["Facility", "Sub-national", "National", "Regional", "Continental"], ["Long-term", "Medium-term", "Short-term"]),
    "Emissions, air quality":          (["Facility", "Sub-national", "National", "Regional", "Continental"], ["Long-term", "Medium-term", "Short-term"]),
    "Buildings and thermal":           (["Facility", "Sub-national"], ["Short-term"]),
}


def allowed_options(policy_q):
    """Scale and horizon options for the chosen objective (all options when none is chosen)."""
    if policy_q:
        for key, (scales, horizons) in ALLOWED.items():
            if key in policy_q:
                return [SCALES[k] for k in scales], [HORIZONS[k] for k in horizons]
    return list(SCALES.values()), list(HORIZONS.values())


col_q1, col_q2 = st.columns(2)

with col_q1:
    policy_q = st.selectbox("1. Primary objective", OBJECTIVES, index=None,
                            placeholder="Select your primary objective...")
    scale_opts, horizon_opts = allowed_options(policy_q)
    scale_q = st.selectbox("2. Scale of analysis", scale_opts, index=None, placeholder="Select scale...",
                           help="The scales offered follow the objective chosen in question 1.")
    budget_q = st.selectbox(
        "3. Budget for software licences",
        ["No budget (free tools, including free licences granted to African institutions)",
         "Limited budget (freemium or affordable licences)",
         "Any budget"],
        index=None, placeholder="Select budget...",
        help="Budget is about the cost of using the tool. If you need the source code itself to be open, "
             "tick the corresponding requirement in question 7.",
    )

with col_q2:
    capacity_q = st.selectbox(
        "4. Team technical capacity",
        ["Limited (no programming, GUI-only)",
         "Intermediate (spreadsheets, basic scripting)",
         "Advanced (Python, Julia, GAMS, full programming)"],
        index=None, placeholder="Select capacity level...",
    )
    horizon_q = st.selectbox("5. Time horizon of analysis", horizon_opts, index=None,
                             placeholder="Select time horizon...",
                             help="The horizons offered follow the objective chosen in question 1.")
    data_q = st.selectbox(
        "6. Data availability in your context",
        ["Good (detailed national statistics available)",
         "Moderate (some gaps, proxy data needed)",
         "Limited (data-scarce context)"],
        index=None, placeholder="Select data situation...",
    )

extras = st.multiselect(
    "7. Additional requirements (optional)",
    ["Open-source code required (transparent, auditable, modifiable)",
     "Clean cooking / household energy must be represented",
     "Investment and financing analysis (LCOE, NPV, cost of capital)",
     "Team works on macOS / Linux (no Windows machines)",
     "A formal helpdesk or vendor support is required"],
    default=[], placeholder="None",
)

run = st.button("Get Recommendations", type="primary")
st.divider()

# ── Scoring ─────────────────────────────────────────────────────────────────────
# Each objective maps to the best_for tokens (primary signal, +30) and to the
# tool types that typically serve it (secondary signal, +10).
BEST_FOR = {
    "National energy planning":        (["national_planning"], ["capacity_expansion", "accounting"]),
    "Electrification / energy access": (["electrification_planning", "geospatial_analysis"], ["geospatial_electrification"]),
    "Project or site pre-feasibility": (["project_prefeasibility", "minigrid_hybrid_design"], ["hybrid_optimization"]),
    "Regional power trade":            (["regional_trade"], ["capacity_expansion"]),
    "Power system operation":          (["power_system_operation", "grid_reliability"], ["production_cost", "reliability"]),
    "Resource assessment":             (["resource_assessment"], ["simulation"]),
    "Climate-energy-water-land nexus": (["nexus_water_land"], ["nexus", "hydrological"]),
    "Demand forecasting":              (["demand_forecasting"], ["demand_forecast"]),
    "Emissions, air quality":          (["emissions_air_quality"], []),
    "Buildings and thermal":           (["buildings_thermal"], []),
}
SCALE_TOKENS = {
    "Facility": ["facility", "community"], "Sub-national": ["subnational"], "National": ["national"],
    "Regional": ["regional"], "Continental": ["continental", "global"],
}
# Dependencies that cost money even when the tool itself is open source (TIMES needs GAMS and VEDA, etc.)
PAID_DEPENDENCIES = ("gams", "matlab", "arcgis", "vensim", "stella", "powersim", "anylogic")


def _s(v):
    """Field value as a clean string; empty cells and pandas NaN become ''."""
    v = "" if v is None else str(v).strip()
    return "" if v in ("nan", "NaN", "None") else v


def _tokens(v):
    """Split a multi-valued cell ('a, b; c') into a set of tokens."""
    return {x.strip() for x in _s(v).replace(";", ",").split(",") if x.strip()}


def score_tool(tool, policy_q, scale_q, budget_q, capacity_q, horizon_q, data_q, extras=()):
    s = 0
    bf   = _tokens(tool.get("best_for"))
    typ  = _s(tool.get("type"))
    lic  = _s(tool.get("license"))
    fd   = _s(tool.get("free_for_developing")) == "yes"
    paid_dep = any(k in _s(tool.get("proprietary_dependency")).lower() for k in PAID_DEPENDENCIES)
    prog = _s(tool.get("programming_required"))
    tr   = _s(tool.get("training_available")) == "yes"
    hd   = _s(tool.get("helpdesk")) == "yes"
    com  = _s(tool.get("community")) == "yes"
    doc  = _s(tool.get("doc_quality"))
    hz   = _tokens(tool.get("time_horizon"))
    sc   = {x.lower() for x in _tokens(tool.get("scale"))}
    di   = _s(tool.get("data_intensity"))
    cc   = _s(tool.get("clean_cooking_capable"))
    fin  = _s(tool.get("financing_modelling"))
    os_  = _s(tool.get("os"))
    studies = int(tool.get("nb_studies_in_inventory", 0) or 0)

    # 1. objective: best_for is the primary signal, tool type the secondary one
    if policy_q:
        for key, (bf_keys, type_keys) in BEST_FOR.items():
            if key in policy_q:
                if bf & set(bf_keys): s += 30
                if typ in type_keys: s += 10

    # 2. scale, read from the tools sheet
    if scale_q:
        for key, vals in SCALE_TOKENS.items():
            if key in scale_q:
                if sc & set(vals): s += 12
                elif "varies" in sc: s += 6

    # 3. budget: what it costs to use the tool (licence, free access for African
    #    institutions, paid dependencies). Openness of the code is handled in 7.
    if budget_q:
        if "No budget" in budget_q:
            if lic in ("open_source", "free"): s += 15
            elif lic == "freemium": s += 12 if fd else 5
            elif lic == "proprietary": s += -5 if fd else -25
            if paid_dep: s -= 10
        elif "Limited" in budget_q:
            if lic in ("open_source", "free", "freemium"): s += 10
            elif lic == "proprietary" and not fd: s -= 10
            if paid_dep: s -= 5

    # 4. team capacity, support fields weighted by how much the team depends on them
    if capacity_q:
        if "Limited" in capacity_q:
            if prog == "none": s += 15
            elif prog == "advanced": s -= 20
            if tr: s += 5
            if hd: s += 5
            if doc == "high": s += 3
        elif "Intermediate" in capacity_q:
            if prog in ("none", "basic"): s += 8
            if tr: s += 3
            if com: s += 3
            if doc == "high": s += 2
        elif "Advanced" in capacity_q:
            if prog == "advanced": s += 10
            elif prog == "basic": s += 5
            if com: s += 3
            if doc == "high": s += 2

    # 5. time horizon, read from the tools sheet
    if horizon_q:
        if "Long-term" in horizon_q and "long_term" in hz: s += 10
        elif "Medium-term" in horizon_q:
            if "medium_term" in hz: s += 10
            elif "long_term" in hz: s += 5
        elif "Short-term" in horizon_q and "short_term" in hz: s += 10

    # 6. data availability against data intensity
    if data_q:
        if "Good" in data_q and di == "high": s += 5
        elif "Moderate" in data_q:
            if di == "medium": s += 5
            elif di == "low": s += 3
        elif "Limited" in data_q:
            if di == "low": s += 10
            elif di == "medium": s += 5
            elif di == "high": s -= 8

    # 7. optional requirements (the open-source requirement is a filter, see below)
    ex = " | ".join(extras)
    if "Clean cooking" in ex: s += {"yes": 10, "partial": 5}.get(cc, -10)
    if "financing" in ex:     s += {"advanced": 10, "basic": 6}.get(fin, -5)
    if "macOS" in ex and os_ == "windows": s -= 15
    if "helpdesk" in ex:      s += 8 if hd else -5

    # African track record
    if studies >= 10: s += 10
    elif studies >= 5: s += 5
    return s


# ── Display helpers ─────────────────────────────────────────────────────────────
_URL_RE = re.compile(r"https?://[^\s;,)\]]+")
_LABELS = {"official": "official site", "officials": "official site", "repository": "repository",
           "documentation": "documentation", "pricing": "pricing page", "study": "published study"}


def parse_sources(text):
    """Turn the free-text info_source cell into a list of (label, url).

    Cells look like 'repository: https://...; documentation: https://...'.
    The label is whatever precedes the URL in its segment; the domain is used
    when there is none. Segments without a URL are dropped.
    """
    out = []
    for seg in _s(text).split(";"):
        m = _URL_RE.search(seg)
        if not m:
            continue
        url = m.group(0).rstrip(".")
        label = seg[:m.start()].strip(" :,-")
        if label.startswith("(") and label.endswith(")"):
            label = label[1:-1].strip()
        if not label:
            label = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
        out.append((label, url))
    return out


def source_basis(row):
    """Short description of where the tool's characteristics come from."""
    sources = parse_sources(row.get("info_source"))
    n = int(row.get("nb_studies_in_inventory", 0) or 0)
    if sources:
        head = sources[0][0].lower()
        for key, nice in _LABELS.items():
            if head.startswith(key):
                return nice
        return sources[0][0][:30]
    text = _s(row.get("info_source"))
    if text:                                   # a source is named but no URL was recorded
        head = text.split(":")[0].strip().lower()
        return _LABELS.get(head, "external source") + " (no link)"
    return f"{n} inventory {'study' if n == 1 else 'studies'}"


def first_url(text):
    m = _URL_RE.search(_s(text))
    return m.group(0).rstrip(".") if m else None


def fmt(v):
    """Human-readable version of a harmonised cell ('long_term,short_term' -> 'long term · short term')."""
    return _s(v).replace("_", " ").replace(";", " · ").replace(",", " · ").replace(" ·  ", " · ") or "n/a"


def licence_text(row):
    lic = fmt(row.get("license"))
    if _s(row.get("free_for_developing")) == "yes" and _s(row.get("license")) != "open_source":
        lic += " (free licences for low- and middle-income countries)"
    dep = _s(row.get("proprietary_dependency"))
    if dep and dep.lower() != "none":
        lic += f", requires {dep}"
    return lic


def add_source_columns(df):
    """Add 'source_basis' and 'source_url' columns used by the tables."""
    df = df.copy()
    df["source_basis"] = df.apply(lambda r: source_basis(r.to_dict()), axis=1)
    df["source_url"] = df["info_source"].map(first_url) if "info_source" in df.columns else None
    return df


# Column labels and configuration shared by the two tables. Only columns present
# in the database are shown, so the page also runs before the schema is extended.
TABLE_LABELS = {
    "tool_name": "Tool", "full_name": "Full name", "match_score": "Score", "license": "License",
    "programming_required": "Programming", "learning_curve": "Learning", "time_horizon": "Time horizon",
    "scale": "Scale", "data_intensity": "Data intensity", "training_available": "Training",
    "free_for_developing": "Free LICs", "nb_studies_in_inventory": "Africa studies",
    "best_for": "Best for", "source_basis": "Sourced from", "source_url": "Link",
}
LINK_COL = st.column_config.LinkColumn("Link", display_text=r"^https?://(?:www\.)?([^/]+)",
                                       help="First external source recorded for this tool")
BASIS_COL = st.column_config.TextColumn("Sourced from", help="Where the tool's characteristics were taken from: "
                                        "an external source when one is recorded, otherwise the studies of the inventory.")


def build_table(df, cols):
    cols = [c for c in cols if c in df.columns]
    out = df[cols].copy()
    for c in ("time_horizon", "scale", "best_for"):
        if c in out.columns:
            out[c] = out[c].map(fmt)
    return out.rename(columns=TABLE_LABELS).reset_index(drop=True)


def tool_detail(df, key):
    """Inspection panel: strengths, weaknesses and sources of one tool."""
    st.markdown("#### Tool detail")
    names = df.sort_values("tool_name")["tool_name"].tolist()
    chosen = st.selectbox("Select a tool", names, index=None, placeholder="Choose a tool to inspect...", key=key)
    if not chosen:
        return
    r = df[df["tool_name"] == chosen].iloc[0].to_dict()
    st.markdown(f"### {chosen}")
    st.caption(f"{_s(r.get('full_name')) or chosen} · {fmt(r.get('type'))} · "
               f"{_s(r.get('origin_institution')) or 'origin not recorded'} · "
               f"{int(r.get('nb_studies_in_inventory', 0) or 0)} studies in the inventory")
    c1, c2, c3 = st.columns(3)
    c1.metric("License", fmt(r.get("license")))
    c2.metric("Programming", fmt(r.get("programming_required")))
    c3.metric("Learning curve", fmt(r.get("learning_curve")))
    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Strengths**")
        st.markdown(_s(r.get("strengths")) or "_not recorded_")
    with colB:
        st.markdown("**Weaknesses**")
        st.markdown(_s(r.get("weaknesses")) or "_not recorded_")
    st.markdown(f"**Time horizon:** {fmt(r.get('time_horizon'))} · **Scale:** {fmt(r.get('scale'))} · "
                f"**Data intensity:** {fmt(r.get('data_intensity'))} · **OS:** {fmt(r.get('os'))}")
    st.markdown(f"**Best for:** {fmt(r.get('best_for'))}")
    if _s(r.get("typical_results")):
        st.markdown(f"**Typical results:** {fmt(r.get('typical_results'))}")
    if _s(r.get("often_linked")):
        st.markdown(f"**Often linked with:** {_s(r.get('often_linked'))}")
    sources = parse_sources(r.get("info_source"))
    if sources:
        links = " · ".join(f"[{label}]({url})" for label, url in sources)
        checked = _s(r.get("info_date"))
        st.markdown("**Sources:** " + links + (f" (information checked: {checked})" if checked else ""))
    else:
        st.markdown(f"**Sources:** characteristics derived from the {source_basis(r)} of the inventory"
                    if "inventory" in source_basis(r) else f"**Sources:** {source_basis(r)}")


# Public tools only: in-house models cannot be adopted by another team.
rankable = tools[tools["license"].map(_s) != "internal"]
n_internal = len(tools) - len(rankable)
open_only = any("Open-source" in e for e in extras)
if open_only:
    rankable = rankable[rankable["license"].map(_s) == "open_source"]

# ── Results ─────────────────────────────────────────────────────────────────────
if run:
    scored = []
    for _, t in rankable.iterrows():
        sc = score_tool(t.to_dict(), policy_q, scale_q, budget_q, capacity_q, horizon_q, data_q, extras)
        scored.append({**t.to_dict(), "match_score": sc})
    scored_df = pd.DataFrame(scored).sort_values("match_score", ascending=False).head(8)
    scored_df = add_source_columns(scored_df)

    st.subheader("Recommended Tools")
    notes = []
    if open_only:
        notes.append(f"Only the {len(rankable)} open-source tools are ranked, as requested.")
    if n_internal:
        notes.append(f"{n_internal} in-house models that are not publicly available (licence: internal) "
                     "are listed in the inventory but never ranked.")
    if notes:
        st.caption(" ".join(notes))

    top3 = scored_df.head(3).reset_index(drop=True)
    card_cols = st.columns(3)

    for i, (col, (_, row)) in enumerate(zip(card_cols, top3.iterrows())):
        with col:
            badge = "BEST MATCH" if i == 0 else f"#{i+1}"
            st.markdown(f"**{badge} · {row['tool_name']}**")
            st.caption(f"*{_s(row.get('full_name'))[:65]}*")
            sc1, sc2 = st.columns(2)
            sc1.metric("Match score", int(row["match_score"]))
            sc2.metric("Africa studies", int(row["nb_studies_in_inventory"]))
            st.caption(
                f"License: **{licence_text(row)}**  \n"
                f"Programming: {fmt(row.get('programming_required'))}  \n"
                f"Learning curve: {fmt(row.get('learning_curve'))}  \n"
                f"Time horizon: {fmt(row.get('time_horizon'))}  \n"
                f"Scale: {fmt(row.get('scale'))}  \n"
                f"Data intensity: {fmt(row.get('data_intensity'))}  \n"
                f"Best for: {fmt(row.get('best_for'))}"
            )
            if _s(row.get("strengths")) or _s(row.get("weaknesses")):
                with st.expander("Strengths and weaknesses"):
                    st.markdown(f"**Strengths.** {_s(row.get('strengths')) or '_not recorded_'}")
                    st.markdown(f"**Weaknesses.** {_s(row.get('weaknesses')) or '_not recorded_'}")
            sources = parse_sources(row.get("info_source"))
            if sources:
                links = " · ".join(f"[{label}]({url})" for label, url in sources)
                checked = _s(row.get("info_date"))
                st.caption("Sources: " + links + (f"  \n*Information checked: {checked}*" if checked else ""))
            else:
                st.caption(f"Sources: {source_basis(row.to_dict())}")
            st.markdown("---")

    st.divider()
    st.subheader("Full comparison")
    st.dataframe(
        build_table(scored_df, [
            "tool_name", "match_score", "license", "programming_required", "time_horizon", "scale",
            "data_intensity", "training_available", "free_for_developing", "nb_studies_in_inventory",
            "best_for", "source_basis", "source_url",
        ]),
        use_container_width=True, hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Score", min_value=0, max_value=max(100, int(scored_df["match_score"].max())), format="%d"),
            "Sourced from": BASIS_COL,
            "Link": LINK_COL,
        },
    )
    st.divider()
    tool_detail(scored_df, key="detail_ranked")
else:
    st.info("Select your context above and click **Get Recommendations** to see matched tools.")
    st.divider()
    st.subheader("All tools in inventory")
    ref_df = add_source_columns(tools).sort_values("nb_studies_in_inventory", ascending=False)
    st.dataframe(
        build_table(ref_df, [
            "tool_name", "full_name", "license", "programming_required", "time_horizon", "scale",
            "data_intensity", "free_for_developing", "nb_studies_in_inventory", "best_for",
            "source_basis", "source_url",
        ]),
        use_container_width=True, hide_index=True,
        column_config={
            "Africa studies": st.column_config.NumberColumn(),
            "Sourced from": BASIS_COL,
            "Link": LINK_COL,
        },
    )
    st.divider()
    tool_detail(tools, key="detail_all")