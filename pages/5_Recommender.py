"""Model Recommender page."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from utils.data import load_tools
from utils.ui import SIDEBAR_CSS, render_logo

st.set_page_config(page_title="Recommender | AISESA", layout="wide", page_icon="assets/aisesa_logo.png")
st.html(SIDEBAR_CSS)
render_logo()

@st.cache_data(ttl=3600)
def get_tools():
    return load_tools()

tools = get_tools()

with st.sidebar:
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem; color:#1E5631; text-transform:uppercase; letter-spacing:0.08em; font-weight:700;'>About the recommender</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='font-size:0.79rem; line-height:1.7;'>"
        "Scoring weights:<br>"
        "🎯 Policy match: +30<br>"
        "💰 Budget fit: ±15–25<br>"
        "👩‍💻 Capacity match: ±15–20<br>"
        "🌍 Africa track record: +5–10<br>"
        "⏱ Time horizon: +10<br>"
        "📚 Training available: +5</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.69rem; color:#5A645E; font-style:italic; line-height:1.5;'>AISESA · MINES Paris-PSL<br/>Research Platform · 2026</p>",
        unsafe_allow_html=True,
    )

st.title("Which tool fits your context?")
st.markdown(
    "<p style='font-size:1rem; color:#444; font-family:Georgia,serif; line-height:1.7; max-width:820px;'>"
    "There is no single best energy model, only the one best suited to your question, your team and your "
    "data. Answer six questions about your context and the recommender ranks the tools in the inventory. "
    "The scoring logic is documented on the Methodology page.</p>",
    unsafe_allow_html=True)
st.divider()

col_q1, col_q2 = st.columns(2)

with col_q1:
    policy_q = st.selectbox(
        "1. Primary policy question / objective",
        ["National energy planning (supply mix, capacity expansion)",
         "Electrification / energy access (off-grid, mini-grid)",
         "Regional power trade (interconnections, power pools)",
         "Short-term dispatch and grid flexibility",
         "Climate-energy-water-land nexus",
         "Demand forecasting",
         "Environmental / climate impact assessment"],
        index=None, placeholder="Select your primary objective...",
    )
    scale_q = st.selectbox(
        "2. Scale of analysis",
        ["National","Sub-national / state / province","Regional / multi-country","Continental"],
        index=None, placeholder="Select scale...",
    )
    budget_q = st.selectbox(
        "3. Budget constraint",
        ["Zero budget (open source only)","Low / freemium acceptable","Any budget"],
        index=None, placeholder="Select budget...",
    )

with col_q2:
    capacity_q = st.selectbox(
        "4. Team technical capacity",
        ["Limited (no programming, GUI-only)",
         "Intermediate (scripting, some technical skills)",
         "Advanced (Python, Julia, full programming)"],
        index=None, placeholder="Select capacity level...",
    )
    horizon_q = st.selectbox(
        "5. Time horizon of analysis",
        ["Long-term (2030–2060, strategic planning)",
         "Medium-term (5–15 years)",
         "Short-term / sub-annual dispatch"],
        index=None, placeholder="Select time horizon...",
    )
    data_q = st.selectbox(
        "6. Data availability in your context",
        ["Good — detailed national statistics available",
         "Moderate — some gaps, proxy data needed",
         "Limited — data-scarce, low-income context"],
        index=None, placeholder="Select data situation...",
    )

run = st.button("Get Recommendations", type="primary")
st.divider()

def score_tool(tool, policy_q, scale_q, budget_q, capacity_q, horizon_q, data_q):
    s = 0
    bf  = str(tool.get("best_for",""))
    lc  = str(tool.get("learning_curve","medium"))
    prog= str(tool.get("programming_required","none"))
    lic = str(tool.get("license",""))
    fd  = tool.get("free_for_developing","no") == "yes"
    tr  = tool.get("training_available","no") == "yes"
    studies = int(tool.get("nb_studies_in_inventory",0))
    name = str(tool.get("tool_name",""))

    if policy_q:
        if "National energy planning" in policy_q and "national_planning" in bf: s += 30
        if "Electrification" in policy_q and "electrification" in bf: s += 30
        if "Regional power trade" in policy_q and "regional_trade" in bf: s += 30
        if "dispatch" in policy_q and "dispatch_flexibility" in bf: s += 30
        if "nexus" in policy_q and "nexus" in bf: s += 30
        if "Demand" in policy_q and "demand_forecasting" in bf: s += 30
        if "Environmental" in policy_q and "environmental" in bf: s += 30

    if budget_q:
        if "Zero budget" in budget_q:
            if lic == "open_source": s += 15
            elif lic == "proprietary": s -= 25
        elif "Low" in budget_q:
            if lic in ("open_source","freemium"): s += 10
            elif lic == "proprietary": s -= 10

    if capacity_q:
        if "Limited" in capacity_q:
            if prog == "none": s += 15
            elif prog == "advanced": s -= 20
        elif "Intermediate" in capacity_q:
            if prog in ("none","intermediate"): s += 8
        elif "Advanced" in capacity_q:
            if prog == "advanced": s += 10

    if horizon_q:
        long_tools  = ["OSeMOSYS","TIMES","MESSAGE","LEAP","TEMBA","CLEWs","Balmorel"]
        short_tools = ["FlexTool","PLEXOS","Dispa-SET","SWITCH","EnergyPLAN"]
        if "Long-term" in horizon_q and any(t in name for t in long_tools): s += 10
        if "Short-term" in horizon_q and any(t in name for t in short_tools): s += 10

    if scale_q:
        if "Sub-national" in scale_q and "electrification" in bf: s += 8
        if "Regional" in scale_q and "regional_trade" in bf: s += 8

    if data_q and "Limited" in data_q:
        if lc in ("low","medium"): s += 5

    if tr: s += 5
    if studies >= 10: s += 10
    elif studies >= 5: s += 5
    return s

if run:
    scored = []
    for _, t in tools.iterrows():
        sc = score_tool(t.to_dict(), policy_q, scale_q, budget_q, capacity_q, horizon_q, data_q)
        scored.append({**t.to_dict(), "match_score": sc})
    scored_df = pd.DataFrame(scored).sort_values("match_score", ascending=False).head(8)

    st.subheader("Recommended Tools")
    top3 = scored_df.head(3).reset_index(drop=True)
    card_cols = st.columns(3)
    lic_color = {"open_source":"green","freemium":"blue","proprietary":"orange"}

    for i, (col, (_, row)) in enumerate(zip(card_cols, top3.iterrows())):
        with col:
            badge = "BEST MATCH" if i == 0 else f"#{i+1}"
            st.markdown(f"**{badge} — {row['tool_name']}**")
            st.caption(f"*{str(row['full_name'])[:65]}*")
            sc1, sc2 = st.columns(2)
            sc1.metric("Match score", int(row["match_score"]))
            sc2.metric("Africa studies", int(row["nb_studies_in_inventory"]))
            st.caption(
                f"License: **{row['license'].replace('_',' ')}**  \n"
                f"Learning curve: {row['learning_curve']}  \n"
                f"Programming: {row['programming_required']}  \n"
                f"Best for: {str(row['best_for']).replace('_',' ').replace(',',' · ')}"
            )
            st.markdown("---")

    st.divider()
    st.subheader("Full comparison")
    display_df = scored_df[[
        "tool_name","license","learning_curve","programming_required",
        "training_available","free_for_developing","nb_studies_in_inventory","best_for","match_score"
    ]].copy()
    display_df.columns = ["Tool","License","Learning","Programming","Training","Free LICs","Africa Studies","Best For","Score"]
    display_df["Best For"] = display_df["Best For"].str.replace("_"," ").str.replace(","," · ")
    st.dataframe(
        display_df.reset_index(drop=True), use_container_width=True, hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=80, format="%d"),
        },
    )
else:
    st.info("Select your context above and click **Get Recommendations** to see matched tools.")
    st.divider()
    st.subheader("All tools in inventory")
    ref_df = tools[[
        "tool_name","full_name","license","learning_curve",
        "programming_required","free_for_developing","nb_studies_in_inventory","best_for"
    ]].copy()
    ref_df.columns = ["Tool","Full Name","License","Learning","Programming","Free LICs","Africa Studies","Best For"]
    ref_df["Best For"] = ref_df["Best For"].str.replace("_"," ").str.replace(","," · ")
    ref_df = ref_df.sort_values("Africa Studies", ascending=False)
    st.dataframe(
        ref_df.reset_index(drop=True), use_container_width=True, hide_index=True,
        column_config={"Africa Studies": st.column_config.NumberColumn()},
    )
