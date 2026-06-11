"""Shared UI theme for the AISESA observatory.

Design direction inspired by openmod-tracker.org: clean white content area,
AISESA green sidebar, compact editorial typography (Source Serif 4 headings +
Inter body). The AISESA logo is injected at the very top of the sidebar
navigation on every page via CSS. Single source of truth for the look.
"""


# AISESA green family (sidebar matched to the logo's own green so it blends)
GREEN_DARK = "#3E9B47"      # sidebar (matches logo background)
GREEN_DEEP = "#1E5631"      # deep green for text/accents on white
GREEN = "#2F7D4F"           # primary accent / charts
GREEN_LIGHT = "#5AA877"
SAND = "#F7F5EF"
INK = "#1F2A24"
CORAL = "#D8642F"
AMBER_BG = "#FBE4C9"
AMBER_TX = "#8A5A0B"

CHART_SEQUENCE = ["#2F7D4F", "#C9A227", "#3E7CB1", "#D8642F", "#7A6F9B", "#5AA877", "#9E9E9E"]
CHART_GREEN_SCALE = ["#E5F0E8", "#1E5631"]
GAP_SCALE = ["#1E5631", "#E8C547", "#C0392B"]
READINESS_SCALE = ["#C0392B", "#E8C547", "#1E5631"]


THEME_CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;500;600&display=swap');

  html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, system-ui, sans-serif;
    font-size: 15px; color: {INK};
  }}
  .stApp {{ background: #ffffff; }}
  .block-container {{ padding-top: 3.5rem !important; max-width: 1200px; }}

  h1, h2, h3, h4 {{
    font-family: 'Source Serif 4', Georgia, serif !important;
    color: {INK} !important; font-weight: 600 !important; letter-spacing: -0.01em;
  }}
  h1 {{ font-size: 1.9rem !important; }}
  h2 {{ font-size: 1.4rem !important; }}
  h3 {{ font-size: 1.15rem !important; }}

  /* Sidebar: light grey with green accents (logo + dark text stay legible) */
  [data-testid="stSidebarContent"] {{ background: #EEF1ED !important; }}
  [data-testid="stSidebarContent"], [data-testid="stSidebarContent"] p,
  [data-testid="stSidebarContent"] span, [data-testid="stSidebarContent"] div,
  [data-testid="stSidebarContent"] label {{ color: #2C352F !important; }}

  /* Section sub-headers in green */
  [data-testid="stSidebarContent"] p strong {{ color: {GREEN_DEEP} !important; }}

  /* Logo. The CONTAINER must be tall enough or the image gets clipped at the top.
     EDIT --logo-h below to resize; the container grows with it. */
  [data-testid="stSidebarHeader"] {{
    height: auto !important; min-height: 0 !important;
    padding: 1rem 1rem 1.4rem 1rem !important; overflow: visible !important;
  }}
  [data-testid="stSidebarHeader"] > div,
  [data-testid="stSidebarHeader"] a {{ height: auto !important; }}
  [data-testid="stSidebarHeader"] img,
  [data-testid="stLogo"] {{
    height: 90px !important; width: auto !important; max-width: 100% !important;
    object-fit: contain; margin: 0 !important;
  }}
  [data-testid="stSidebarNav"] {{ margin-top: 0.4rem !important; }}

  /* Nav links: dark text, green when active */
  [data-testid="stSidebarNav"] a span {{ color: #2C352F !important; font-size: 0.95rem; }}
  [data-testid="stSidebarNav"] [aria-current="page"] span {{ color: {GREEN_DARK} !important; font-weight: 700; }}
  [data-testid="stSidebarNav"] [aria-current="page"] {{ background: #E3EDE4 !important; border-radius: 6px; }}

  /* Form fields in sidebar: white with dark text */
  [data-testid="stSidebarContent"] .stSelectbox > div > div,
  [data-testid="stSidebarContent"] .stMultiSelect > div {{
    background: #ffffff !important; border: 1px solid #C9D1C7 !important; color: #2C352F !important;
  }}
  [data-testid="stSidebarContent"] .stSelectbox label,
  [data-testid="stSidebarContent"] .stMultiSelect label,
  [data-testid="stSidebarContent"] [data-baseweb="select"] * {{ color: #2C352F !important; }}
  [data-testid="stSidebarContent"] input {{ color: #2C352F !important; }}
  [data-testid="stSidebarContent"] hr {{ border-color: #D5DBD3 !important; }}

  /* Sidebar metric cards: white with green value */
  [data-testid="stSidebarContent"] [data-testid="stMetric"] {{
    background: #ffffff !important; border: 1px solid #C9D1C7 !important;
    border-radius: 8px; padding: 0.5rem 0.7rem;
  }}
  [data-testid="stSidebarContent"] [data-testid="stMetricValue"] {{
    color: {GREEN_DEEP} !important; font-size: 1.2rem !important;
    font-family: 'Source Serif 4', Georgia, serif !important;
  }}
  [data-testid="stSidebarContent"] [data-testid="stMetricLabel"],
  [data-testid="stSidebarContent"] [data-testid="stMetricLabel"] * {{ color: #5A645E !important; }}

  /* Metrics on white pages */
  [data-testid="stMetricValue"] {{ font-size: 1.5rem !important; color: {GREEN_DEEP} !important;
    font-family: 'Source Serif 4', Georgia, serif !important; }}
  .stApp [data-testid="stMetric"] {{ background: {SAND}; border-radius: 8px; padding: 0.6rem 0.8rem; }}

  a {{ color: {GREEN}; }}
</style>
"""

SIDEBAR_CSS = THEME_CSS


import streamlit as st
from pathlib import Path

_LOGO_PATH = str(Path(__file__).parent.parent / "assets" / "aisesa_logo.png")


def render_logo():
    """Place the AISESA logo at the top of the sidebar on every page.

    Uses st.logo (Streamlit >= 1.35). Edit assets/aisesa_logo.png to change it —
    no re-encoding needed.
    """
    try:
        st.logo(_LOGO_PATH, size="large")
    except Exception:
        pass


def beta_banner() -> str:
    """Visible amber beta notice (OET style)."""
    return (
        f"<div style='background:{AMBER_BG}; color:{AMBER_TX}; border-radius:8px; "
        f"padding:8px 16px; font-size:0.9rem; font-weight:600; font-family:Inter,sans-serif; "
        f"display:flex; align-items:center; gap:8px; margin-top:0.5rem;'>"
        f"&#128679; We're still in beta, data and features are evolving</div>"
    )


# ── Extraction-level filter (used on Gap, Readiness, Browse, Map) ────────────────
EXTRACTION_LEVELS = ["full", "light", "narrative"]
LEVEL_DESCRIPTIONS = {
    "full": "Long-term planning models (MESSAGE, OSeMOSYS, TIMES, LEAP)",
    "light": "Techno-economic / GIS / electrification studies (HOMER, OnSSET, custom)",
    "narrative": "Country-policy documents (NDCs, World Bank country reports)",
}


def extraction_level_filter(df, default="full", key_suffix=""):
    """Render a selectbox to filter a studies DataFrame by extraction_level.

    Returns the filtered DataFrame. Uses 'full' as the default for analytical
    pages (Gap, Readiness, Methodology) where mixing levels distorts statistics;
    pages that need the full overview (Map, Browse) should pass default='all'.

    A short caption below the selector tells the visitor what they're looking
    at, so the figures cannot be misread.
    """
    options = ["all"] + EXTRACTION_LEVELS
    counts = df["extraction_level"].fillna("").value_counts().to_dict()
    total = len(df)

    def fmt(opt):
        if opt == "all":
            return f"All levels ({total} studies)"
        n = counts.get(opt, 0)
        return f"{opt} — {n} studies"

    picked = st.selectbox(
        "Filter by extraction level",
        options,
        index=options.index(default) if default in options else 0,
        format_func=fmt,
        key=f"el_filter{key_suffix}",
        help=(
            "Studies are categorised by depth of analysis. "
            "**Full** = long-term planning models. **Light** = techno-economic, "
            "GIS, mini-grid or simulation studies. **Narrative** = country-policy "
            "documents (NDCs, World Bank country reports). Mixing levels in "
            "statistics can be misleading."
        ),
    )
    if picked != "all":
        st.caption(f"Showing {counts.get(picked, 0)} **{picked}** studies — "
                   f"{LEVEL_DESCRIPTIONS[picked]}")
        return df[df["extraction_level"] == picked].copy()
    else:
        st.caption(f"Showing all {total} studies across levels. "
                   "Statistics aggregate full, light and narrative studies together.")
        return df.copy()


def inventory_breakdown(df):
    """Compact summary of the inventory by extraction level, for the home page."""
    counts = df["extraction_level"].fillna("(unclassified)").value_counts()
    total = len(df)
    parts = []
    for lvl in EXTRACTION_LEVELS:
        n = counts.get(lvl, 0)
        if n:
            parts.append(f"**{n}** {lvl}")
    unclassified = counts.get("(unclassified)", 0)
    if unclassified:
        parts.append(f"**{unclassified}** unclassified")
    return f"Inventory: **{total}** studies — " + ", ".join(parts)
