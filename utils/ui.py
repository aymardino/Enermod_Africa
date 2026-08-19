"""Shared UI theme for the AISESA observatory.

THEME PHILOSOPHY (openmod / OET style)
--------------------------------------
Streamlit's NATIVE Light/Dark theme paints the page, so the built-in switcher in
the "⋮" menu flips everything instantly. There is intentionally NO config.toml
[theme] block: a single [theme] block turns the app into one fixed "Custom Theme"
and removes the Light/Dark switcher.

Text colours: the pages used to hard-code colours in inline HTML. Those inline
styles are now written with `var(--text-color)` (Streamlit's active-theme text
colour) directly in the page files, so all that text is readable in both themes
and switches instantly. We do NOT try to override them from here with attribute
selectors, because Streamlit reserialises inline styles and the match fails.

LOGO
----
A single green logo (assets/aisesa_logo.png) is used in both themes — a medium
green reads on white and on the dark charcoal alike, so there is no file swap, no
theme detection, and no refresh lag. Logo size is set in CSS below (edit `height`).
"""

# Brand palette kept for Plotly/charts use.
GREEN_DARK = "#3E9B47"
GREEN_DEEP = "#1E5631"
GREEN = "#2F7D4F"
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


THEME_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;500;600&display=swap');

  /* Fonts only — no colours, so Streamlit's theme controls light/dark text. */
  html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, system-ui, sans-serif;
    font-size: 15px;
  }
  h1, h2, h3, h4 {
    font-family: 'Source Serif 4', Georgia, serif !important;
    font-weight: 600 !important; letter-spacing: -0.01em;
  }
  h1 { font-size: 1.9rem !important; }
  h2 { font-size: 1.4rem !important; }
  h3 { font-size: 1.15rem !important; }

  .block-container { padding-top: 3.5rem !important; max-width: 1200px; }

  /* Logo: bigger mark + more room around it, and push the nav (Home...) down.
     EDIT the numbers below to taste:
       • logo size       -> `height` on the img rule
       • space around it  -> `padding` on stSidebarHeader
       • gap before nav   -> `margin-top` on stSidebarNav  */
  [data-testid="stSidebarHeader"] {
    padding: 2.9rem 1rem 1rem 1rem !important; overflow: visible !important;
  }
  [data-testid="stLogo"], [data-testid="stSidebarHeader"] img {
    height: 89px !important; width: auto !important; max-width: 98% !important;
    object-fit: contain !important; margin: 0 !important;
  }
  [data-testid="stSidebarNav"] { margin-top: 2.5rem !important; }

  /* Subtle metric cards; value uses the theme text colour (no green). */
  .stApp [data-testid="stMetric"] {
    background: rgba(128,128,128,0.08);
    border: 1px solid rgba(128,128,128,0.18);
    border-radius: 8px; padding: 0.6rem 0.8rem;
  }
  [data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    color: var(--text-color, inherit) !important;
    font-family: 'Source Serif 4', Georgia, serif !important;
  }
</style>
"""

SIDEBAR_CSS = THEME_CSS


import streamlit as st
from pathlib import Path

_LOGO_PATH = str(Path(__file__).parent.parent / "assets" / "aisesa_logo.png")


def render_logo():
    """Place the AISESA logo at the top of the sidebar (single green logo, used
    in both themes). Uses st.logo (Streamlit >= 1.35).
    """
    try:
        st.logo(_LOGO_PATH, size="large")
    except Exception:
        pass


def beta_banner() -> str:
    """Beta notice in a translucent amber that reads on both light and dark."""
    return (
        "<div style='background:rgba(214,150,40,0.16); color:#B5791A; "
        "border:1px solid rgba(214,150,40,0.30); border-radius:8px; "
        "padding:8px 16px; font-size:0.9rem; font-weight:600; font-family:Inter,sans-serif; "
        "display:flex; align-items:center; gap:8px; margin-top:0.5rem;'>"
        "&#128679; We're still in beta, data and features are evolving</div>"
    )


# ── Extraction-level filter (used on Gap, Readiness, Browse, Map) ────────────────
EXTRACTION_LEVELS = ["full", "light"]
LEVEL_LABELS = {
    "full": "Whole-system",
    "light": "Focused",
    "unspecified": "Unspecified",
}
LEVEL_DESCRIPTIONS = {
    "full": "Models that represent a complete energy system and its internal "
            "trade-offs (MESSAGE, OSeMOSYS, TIMES, LEAP, PLEXOS, Balmorel)",
    "light": "Models that address a delimited question — site sizing, electricity "
             "access, spatial analysis, scenario accounting (HOMER, OnSSET, GIS, calculators)",
}


def level_label(value: str) -> str:
    """Public-facing name for an internal extraction_level value."""
    return LEVEL_LABELS.get(str(value).strip().lower(), str(value))


def extraction_level_filter(df, default="full", key_suffix=""):
    """Render a selectbox to filter a studies DataFrame by extraction_level."""
    options = ["all"] + EXTRACTION_LEVELS
    counts = df["extraction_level"].fillna("").value_counts().to_dict()
    total = len(df)

    def fmt(opt):
        if opt == "all":
            return f"All models ({total} studies)"
        n = counts.get(opt, 0)
        return f"{level_label(opt)} — {n} studies"

    picked = st.selectbox(
        "Filter by model scope",
        options,
        index=options.index(default) if default in options else 0,
        format_func=fmt,
        key=f"el_filter{key_suffix}",
        help=(
            "Studies are grouped by the scope of the model they use. "
            "**Whole-system** models represent a complete energy system and its "
            "internal trade-offs. **Focused** models address a delimited question — "
            "site sizing, electricity access, spatial analysis or scenario accounting. "
            "Focused models leave methodological fields empty because those fields "
            "do not apply to them, not because less effort went into extraction."
        ),
    )
    if picked != "all":
        st.caption(f"Showing {counts.get(picked, 0)} **{level_label(picked)}** studies — "
                   f"{LEVEL_DESCRIPTIONS[picked]}")
        return df[df["extraction_level"] == picked].copy()
    else:
        st.caption(f"Showing all {total} studies. Statistics aggregate whole-system "
                   "and focused models together, which can be misleading.")
        return df.copy()


def inventory_breakdown(df):
    """Compact summary of the inventory by extraction level, for the home page."""
    counts = df["extraction_level"].fillna("(unclassified)").value_counts()
    total = len(df)
    parts = []
    for lvl in EXTRACTION_LEVELS:
        n = counts.get(lvl, 0)
        if n:
            parts.append(f"**{n}** {level_label(lvl).lower()}")
    unclassified = counts.get("(unclassified)", 0)
    if unclassified:
        parts.append(f"**{unclassified}** unclassified")
    return f"Inventory: **{total}** studies — " + ", ".join(parts)