"""Grounded assistant for the Observatory (Gemini through the google-genai SDK).

The assistant only sees the tools inventory (and, on the Recommender page, the
answers and ranking of the current session). It is instructed to answer from
that context, to say when the inventory does not cover a question, and never to
invent tools, figures, licences or links.

Setup
-----
- pip install google-genai (add it to requirements.txt)
- API key: environment variable GEMINI_API_KEY (Render: Environment tab) or
  .streamlit/secrets.toml locally with GEMINI_API_KEY = "..." (keep the file
  out of git).
"""

import os
import streamlit as st

MODEL = "gemini-2.5-flash"
MAX_TURNS = 15          # questions per browser session, to bound usage
HISTORY_TURNS = 8       # past exchanges sent back to the model
MAX_OUTPUT_TOKENS = 700

CONTEXT_FIELDS = [
    "tool_name", "full_name", "type", "license", "cost_usd", "free_for_developing",
    "proprietary_dependency", "programming_required", "learning_curve", "doc_quality",
    "training_available", "community", "helpdesk", "os", "time_horizon", "scale",
    "data_intensity", "clean_cooking_capable", "financing_modelling", "best_for",
    "nb_studies_in_inventory", "origin_institution", "strengths", "weaknesses",
    "typical_results", "often_linked", "info_source",
]

SYSTEM_PROMPT = """You are the assistant of EnerMod Africa, the African Energy Modelling Observatory built by AISESA and MINES Paris-PSL. It inventories the energy modelling tools and studies applied across the 54 African countries.

Rules:
- Answer only from the INVENTORY below and, when present, from the RECOMMENDATION CONTEXT. If the inventory does not contain what is asked, say so plainly instead of guessing.
- Never invent tools, figures, licences, prices or links. Name tools exactly as written in the inventory. Only give links that appear in the inventory.
- The recommender score is a transparent heuristic used to shortlist candidates, not a verdict. Say so when asked to compare tools, and explain rankings using the inventory fields (licence, programming required, scale, time horizon, data intensity, track record in Africa).
- Reply in the language of the user. Be concise, under 200 words unless more detail is requested. Do not use em dashes.
- If asked about the characteristics of an African energy system (informal economy, biomass and charcoal, unreliable supply, rapid urbanisation), remind the user that these are captured by the studies and their data more than by the tools themselves, and that the Gap Analysis page measures them at study level.
"""


def _s(v):
    v = "" if v is None else str(v).strip()
    return "" if v in ("nan", "NaN", "None") else v


def _api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        try:
            key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            key = None
    return key


@st.cache_data(ttl=3600)
def tools_context(tools):
    """One line per tool, field=value, for the system prompt."""
    lines = []
    for _, r in tools.iterrows():
        pairs = [f"{k}={_s(r.get(k))}" for k in CONTEXT_FIELDS if _s(r.get(k))]
        lines.append(" | ".join(pairs))
    return "\n".join(lines)


def render_chat(tools, recommendation_context=""):
    """Chat panel. Call it at the end of a page, after the content it should know about."""
    st.markdown("#### Ask the observatory (beta)")
    st.caption("An AI assistant that answers from the tools inventory of this observatory. "
               "It does not browse the web and it can be wrong; check the sources of the inventory.")

    key = _api_key()
    if not key:
        st.info("The assistant is not available on this deployment (no API key configured).")
        return
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        st.info("The assistant is not available on this deployment (google-genai is not installed).")
        return

    history = st.session_state.setdefault("chat_history", [])   # list of (role, text)

    box = st.container(border=True)
    with box:
        for role, text in history:
            with st.chat_message(role):
                st.markdown(text)
        this_turn = st.container()   # this turn's messages land here, above the input
        if len(history) >= 2 * MAX_TURNS:
            st.caption("Session limit reached. Reload the page to start a new conversation.")
            return
        prompt = st.chat_input("Ask about a tool, a licence, or why a tool ranked where it did...")

    if not prompt:
        return

    history.append(("user", prompt))
    system = SYSTEM_PROMPT + "\nINVENTORY (one tool per line, field=value):\n" + tools_context(tools)
    if recommendation_context:
        system += "\n\nRECOMMENDATION CONTEXT (current session):\n" + recommendation_context

    contents = [
        types.Content(role="user" if role == "user" else "model", parts=[types.Part(text=text)])
        for role, text in history[-2 * HISTORY_TURNS:]
    ]
    with this_turn:
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Reading the inventory..."):
                try:
                    client = genai.Client(api_key=key)
                    resp = client.models.generate_content(
                        model=MODEL, contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system, temperature=0.2,
                            max_output_tokens=MAX_OUTPUT_TOKENS),
                    )
                    answer = _s(resp.text) or "I could not produce an answer. Please rephrase the question."
                except Exception as exc:   # quota, network, invalid key: keep the page alive
                    answer = f"The assistant could not answer this time ({type(exc).__name__}). Please try again later."
            st.markdown(answer)
    history.append(("assistant", answer))
