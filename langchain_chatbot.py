import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

# =============================
# Setup
# =============================
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
st.set_page_config(page_title="🧠 Langchain Gemini Chatbot", layout="wide")

# =============================
# Simple persistent storage for theme
# =============================
APP_DIR = Path.home() / ".appdata" / "ai-chat"
THEME_FILE = APP_DIR / "theme.json"
APP_DIR.mkdir(parents=True, exist_ok=True)

def load_theme_from_disk():
    if THEME_FILE.exists():
        try:
            data = json.loads(THEME_FILE.read_text(encoding="utf-8"))
            return data.get("theme", "Light"), bool(data.get("reduce_motion", False))
        except Exception:
            return "Light", False
    return "Light", False

def save_theme_to_disk(theme: str, reduce_motion: bool):
    try:
        THEME_FILE.write_text(
            json.dumps({"theme": theme, "reduce_motion": reduce_motion}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass

# =============================
# Session init (multi-chat + Tools + Theme)
# =============================
def _new_chat(title: str = "New chat"):
    cid = str(uuid.uuid4())[:8]
    return cid, {"title": title, "created": datetime.utcnow().isoformat(), "messages": []}

if "chats" not in st.session_state:
    cid, chat = _new_chat("Getting started")
    st.session_state.chats = {cid: chat}
    st.session_state.current_chat_id = cid

if "mode" not in st.session_state:
    st.session_state.mode = "Default"

TOOLS = ["Chat", "🧭 Career Counselor", "📄 Cover Letter", "🧘 Wellness Tip", "🎲 Random Fact", "🍽️ Recipe"]
if "selected_tool" not in st.session_state:
    st.session_state.selected_tool = "Chat"

def is_explore():
    return st.session_state.selected_tool != "Chat"

# Theme state + persistence
if "theme" not in st.session_state or "reduce_motion" not in st.session_state:
    t, rm = load_theme_from_disk()
    st.session_state.theme = t
    st.session_state.reduce_motion = rm

def current_chat():
    return st.session_state.chats[st.session_state.current_chat_id]

def chat_messages():
    return current_chat()["messages"]

def set_chat_title_if_empty(first_user_msg: str):
    chat = current_chat()
    if chat["title"] in ("New chat", "Getting started") and first_user_msg.strip():
        t = first_user_msg.strip()
        chat["title"] = (t[:30] + "…") if len(t) > 30 else t

# =============================
# THEME CSS (fixed search box layout; only colors change per theme)
# =============================
def theme_css(theme: str, reduce_motion: bool) -> str:
    # Light (clean)
    light_bg = (
        "radial-gradient(900px circle at 12% 8%, #eaf2ff, transparent 40%),"
        "radial-gradient(900px circle at 88% 16%, #ffe9f3, transparent 45%),"
        "linear-gradient(120deg, #f8fafc, #eef2ff)"
    )

    # Dark Neon
    dark_bg = (
        "linear-gradient(180deg, #0b0f19 0%, #0a0e16 60%, #090d14 100%),"
        "radial-gradient(900px 600px at 15% 10%, rgba(100,116,139,0.12), rgba(0,0,0,0) 60%),"
        "radial-gradient(900px 600px at 85% 20%, rgba(56,189,248,0.10), rgba(0,0,0,0) 60%),"
        "radial-gradient(900px 600px at 20% 85%, rgba(168,85,247,0.10), rgba(0,0,0,0) 60%)"
    )

    if theme == "Dark Neon":
        bg = dark_bg
        title_grad = "linear-gradient(90deg, #e2e8f0, #f1f5f9)"
        btn_grad = "linear-gradient(135deg, #3b82f6, #06b6d4)"  # generic buttons
        app_text_color = "#e5e7eb"
        border_col = "rgba(148,163,184,.32)"
        input_bg = "rgba(17,24,39,.92)"
        panel_bg = "rgba(17,24,39,.86)"
        code_bg = "#0b1220"
        code_border = "#334155"
        table_row = "rgba(15,23,42,.70)"
        table_head = "rgba(15,23,42,.92)"
        chat_shadow = "0 14px 28px rgba(0,0,0,.45)"
        placeholder_col = "rgba(229,231,235,.60)"
        link_col = "#93c5fd"
        subtitle_opacity = ".92"
        tab_underline = "#60a5fa"
        sidebar_bg = "rgba(15,23,42,.85)"
        sidebar_text = "#e5e7eb"
        sidebar_border = "rgba(148,163,184,.25)"
        select_bg = input_bg
        select_border = border_col
        select_text = app_text_color
        select_placeholder = "rgba(229,231,235,.70)"
        disabled_bg = "linear-gradient(135deg, #475569, #1f2937)"
        disabled_text = "#e5e7eb"
        disabled_border = "#64748b"
        quote_bg = "rgba(255,255,255,.03)"
        inline_code_bg = "rgba(148,163,184,.15)"
    else:
        bg = light_bg
        title_grad = "linear-gradient(90deg, #0f172a, #334155)"
        btn_grad = "linear-gradient(135deg, #6366f1, #22d3ee)"
        app_text_color = "#0f172a"
        border_col = "rgba(0,0,0,.12)"
        input_bg = "rgba(255,255,255,.98)"
        panel_bg = "rgba(255,255,255,.96)"
        code_bg = "#0f172a"
        code_border = "rgba(0,0,0,.12)"
        table_row = "rgba(241,245,249,.6)"
        table_head = "rgba(241,245,249,1)"
        chat_shadow = "0 10px 24px rgba(0,0,0,.08)"
        placeholder_col = "rgba(0,0,0,.45)"
        link_col = "#2563eb"
        subtitle_opacity = ".85"
        tab_underline = "#3b82f6"
        sidebar_bg = "rgba(255,255,255,.96)"
        sidebar_text = "#0f172a"
        sidebar_border = "rgba(0,0,0,.08)"
        select_bg = input_bg
        select_border = border_col
        select_text = app_text_color
        select_placeholder = "rgba(15,23,42,.55)"
        disabled_bg = "linear-gradient(135deg, #e5e7eb, #cbd5e1)"
        disabled_text = "#0f172a"
        disabled_border = "rgba(0,0,0,.15)"
        quote_bg = "rgba(0,0,0,.03)"
        inline_code_bg = "rgba(15,23,42,.07)"

    # Motion
    bg_anim = "bgShift 26s ease infinite"
    title_anim = "floaty 6s ease-in-out infinite"
    chat_anim = "fadeInUp .55s ease both"
    if reduce_motion:
        bg_anim = "none"; title_anim = "none"; chat_anim = "fadeInUp .3s ease both"

    css = f"""
    <style>
    html, body, .stApp {{ height: 100%; min-height: 100vh; }}
    .stApp {{
      background: {bg};
      background-size: 400% 400%;
      animation: {bg_anim};
      color: {app_text_color};
    }}
    header[data-testid="stHeader"] {{
      height: 40px; min-height: 40px; background: transparent; box-shadow: none;
      position: sticky; top: 0; z-index: 999;
    }}
    div[data-testid="stDecoration"] {{ display: none; }}
    .block-container {{ padding-top: 0.9rem !important; padding-bottom: 2rem; }}
    section.main > div {{ backdrop-filter: blur(2px); }}

    /* Sidebar */
    section[data-testid="stSidebar"] > div {{
      background: {sidebar_bg} !important;
      color: {sidebar_text} !important;
      border-right: 1px solid {sidebar_border};
      backdrop-filter: blur(4px);
    }}
    section[data-testid="stSidebar"] * {{ color: {sidebar_text} !important; }}
    section[data-testid="stSidebar"] .stSelectbox,
    section[data-testid="stSidebar"] .stButton {{ width: 100%; }}

    /* Headings */
    .rainbow-title {{
      font-size: 2.1rem; font-weight: 800; line-height: 1.15;
      background: {title_grad}; background-size: 200% 200%;
      -webkit-background-clip: text; background-clip: text; color: transparent;
      animation: {title_anim}; margin: 0 0 .25rem 0;
    }}
    .subtitle {{ margin-top: .1rem; opacity: {subtitle_opacity}; }}

    /* Chat text readability */
    [data-testid="stChatMessage"] .stMarkdown,
    [data-testid="stChatMessage"] .stMarkdown * {{ color: {app_text_color} !important; }}

    .stMarkdown blockquote {{
      border-left: 3px solid {tab_underline};
      background: {quote_bg};
      padding: .5rem .9rem; margin: .4rem 0 .6rem 0; border-radius: 8px;
    }}

    /* Inline code */
    .stMarkdown code:not(pre code) {{
      background: {inline_code_bg};
      padding: .12rem .3rem; border-radius: 6px; border: 1px solid {border_col};
    }}

    /* Panels / Expanders */
    [data-testid="stForm"],
    .streamlit-expanderContent {{
      background: {panel_bg} !important;
      border: 1px solid {border_col} !important;
      border-radius: 14px;
      box-shadow: {chat_shadow};
    }}

    /* ------- Generic controls ------- */
    .stButton > button, .stDownloadButton > button {{
      display: inline-flex; align-items: center; justify-content: center;
      min-height: 42px; min-width: 96px; padding: 0 .9rem;
      border-radius: 12px; background: {btn_grad}; border: 1px solid transparent;
      color: white; font-weight: 700;
      box-shadow: 0 10px 20px rgba(34,211,238,.25);
      transition: transform .08s ease, filter .2s ease, box-shadow .2s ease, border-color .2s ease;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover {{ transform: translateY(-1px); filter: brightness(1.06); }}
    .stButton > button:active, .stDownloadButton > button:active {{ transform: translateY(0); }}

    .stSelectbox > div > div {{
      width: 100% !important; min-height: 50px; padding: .4rem .75rem !important;
      background: {select_bg} !important; border: 1px solid {select_border} !important;
      border-radius: 12px !important; color: {select_text} !important; box-shadow: {chat_shadow};
    }}
    .stSelectbox div[role="combobox"] {{ display: flex; align-items: center; min-height: 44px; padding: 0; overflow: hidden; }}
    .stSelectbox div[role="listbox"] {{ background: {panel_bg} !important; border: 1px solid {select_border} !important; color: {select_text} !important; max-height: 320px; overflow-y: auto; }}
    .stSelectbox > div > div:hover, .stSelectbox > div > div:focus-within {{ border-color: {tab_underline} !important; }}

    .stTextInput > div > div > input,
    .stTextArea textarea {{
      min-height: 44px; border-radius: 12px !important; border: 1px solid {border_col} !important;
      background: {input_bg} !important; color: {app_text_color} !important; box-shadow: {chat_shadow}; padding: .72rem .9rem;
    }}
    .stTextArea textarea::placeholder,
    .stTextInput > div > div > input::placeholder {{ color: {placeholder_col}; }}

    /* Code blocks */
    .stMarkdown pre, .stCodeBlock, pre code {{
      background: {code_bg} !important; border: 1px solid {code_border} !important;
      color: {app_text_color} !important; border-radius: 12px !important; overflow-x: auto;
    }}

    /* Tables */
    .stMarkdown table {{ border-collapse: separate; border-spacing: 0; width: 100%; }}
    .stMarkdown th, .stMarkdown td {{ border: 1px solid {code_border}; padding: .5rem .6rem; }}
    .stMarkdown thead th {{ position: sticky; top: 0; background: {table_head}; }}
    .stMarkdown tbody tr:nth-child(odd) {{ background: {table_row}; }}

    /* Tabs */
    div[role="tablist"] > div > button {{ border-bottom: 2px solid transparent; }}
    div[role="tablist"] > div > button[aria-selected="true"] {{ border-bottom-color: {tab_underline}; font-weight: 700; }}

    /* Animations */
    @keyframes bgShift {{ 0%{{background-position:0% 50%}} 50%{{background-position:100% 50%}} 100%{{background-position:0% 50%}} }}
    @keyframes floaty {{ 0%,100%{{transform: translateY(0)}} 50%{{transform: translateY(-6px)}} }}
    @keyframes fadeInUp {{ from {{opacity:0; transform: translateY(10px)}} to {{opacity:1; transform: translateY(0)}} }}

    @media (max-width:640px){{
      .rainbow-title{{font-size:1.6rem;}}
      .subtitle{{font-size:.95rem;}}
      .stButton>button{{width:100%;}}
      [data-testid="stForm"]{{padding:12px;}}
      .block-container{{padding-top:.5rem !important; padding-bottom:2rem;}}
    }}
    @media (min-width:1400px){{ .block-container{{max-width:1200px;}} }}
    </style>
    """

    # ----- FIXED search box layout: sizes constant; colors swap per theme -----
    COMPOSER_WIDTH = "900px"     # one source of truth (width)
    PILL_MIN_HEIGHT = "56px"     # one source of truth (height)
    PILL_RADIUS = "12px"
    COMPOSER_RADIUS = "16px"
    PILL_TEXT_PAD_V = ".85rem"
    PILL_TEXT_PAD_H = "1rem"
    OUTER_PAD = "10px 12px 14px"  # wrapper padding

    # Ask button color policy:
    # Dark theme = dark button with white text
    # Light theme = light button with dark text
    if theme == "Dark Neon":
        comp_bg  = "linear-gradient(90deg, #334155, #4f46e5, #7c3aed)"
        comp_bd  = "rgba(148,163,184,.45)"
        pill_bg  = "#ffffff"
        pill_bd  = "rgba(0,0,0,.18)"
        ask_bg   = "#0f172a"        # dark button in dark theme
        ask_fg   = "#ffffff"
        ask_bd   = "#334155"
    else:
        comp_bg  = "linear-gradient(90deg, #93c5fd, #c4b5fd, #d8b4fe)"
        comp_bd  = "rgba(255,255,255,.55)"
        pill_bg  = "#ffffff"
        pill_bd  = "rgba(0,0,0,.08)"
        ask_bg   = "#ffffff"        # light button in light theme
        ask_fg   = "#111827"
        ask_bd   = "rgba(0,0,0,.12)"

    css += f"""
    <style>
    /* Centered gradient wrapper, fixed size */
    form#top_search .composer {{
      max-width: {COMPOSER_WIDTH};
      margin-left: auto !important; margin-right: auto !important;
      padding: {OUTER_PAD};
      border-radius: {COMPOSER_RADIUS};
      background: {comp_bg}; border: 1px solid {comp_bd};
      box-shadow: 0 12px 24px rgba(0,0,0,.08);
    }}

    /* White pill input container (fixed height) */
    form#top_search .composer .stTextInput > div > div {{
      width: 100% !important; min-height: {PILL_MIN_HEIGHT};
      background: {pill_bg} !important; border: 1px solid {pill_bd} !important;
      border-radius: {PILL_RADIUS} !important;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.6), 0 1px 3px rgba(0,0,0,.06);
      padding: .25rem .25rem !important;
    }}

    /* Focus ring on the pill */
    form#top_search .composer .stTextInput > div > div:focus-within {{
      border-color: {tab_underline} !important;
    }}

    /* Native input (transparent; no layout changes) */
    form#top_search .composer .stTextInput > div > div > input {{
      background: transparent !important; border: none !important; box-shadow: none !important;
      height: 100%; min-height: 0; padding: {PILL_TEXT_PAD_V} {PILL_TEXT_PAD_H};
      color: {app_text_color} !important;
    }}
    form#top_search .composer .stTextInput > div > div > input::placeholder {{ color: {placeholder_col}; }}

    /* Actions row under input */
    form#top_search .composer .composer-actions {{ display: flex; gap: 8px; padding-top: 8px; }}

    /* Ask button: sizes fixed; color only via variables above */
    form#top_search .composer .composer-actions .stButton > button {{
      background: {ask_bg} !important; color: {ask_fg} !important;
      border: 1px solid {ask_bd} !important; border-radius: 10px !important;
      min-height: 36px; min-width: 72px; padding: 0 .9rem;
      box-shadow: 0 2px 6px rgba(0,0,0,.08);
    }}
    </style>
    """

    # Remove hover/active effects on Ask button ONLY in Dark theme
    if theme == "Dark Neon":
        css += """
        <style>
        form#top_search .composer .composer-actions .stButton > button:hover,
        form#top_search .composer .composer-actions .stButton > button:active {
          filter: none !important;
          transform: none !important;
        }
        </style>
        """

    return css

# Inject CSS
st.markdown(theme_css(st.session_state.theme, st.session_state.reduce_motion), unsafe_allow_html=True)

# =============================
# Sidebar (Tools dropdown + Projects/Chats)
# =============================
with st.sidebar:
    st.title("⚙️ Settings")
    st.caption("LangChain + Gemini")

    st.markdown("### 🧰 Tools")
    st.session_state.selected_tool = st.selectbox(
        "Pick a tool",
        TOOLS,
        index=TOOLS.index(st.session_state.selected_tool),
        help="Choose a tool to open the Explore view, or select Chat to return to normal chat."
    )

    st.markdown("---")
    st.session_state.mode = st.selectbox(
        "Chatbot Mode",
        ["Default", "Math Tutor", "Doctor", "Travel Guide", "Grammar Fixer", "Summarizer", "Quiz Generator"],
        index=["Default", "Math Tutor", "Doctor", "Travel Guide", "Grammar Fixer", "Summarizer", "Quiz Generator"].index(st.session_state.mode)
    )

    st.markdown("---")
    new_rm = st.checkbox("Reduce motion", value=st.session_state.reduce_motion)
    if new_rm != st.session_state.reduce_motion:
        st.session_state.reduce_motion = new_rm
        save_theme_to_disk(st.session_state.theme, st.session_state.reduce_motion)
        st.markdown(theme_css(st.session_state.theme, st.session_state.reduce_motion), unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("💼 Projects / Chats")
    if st.button("➕ New chat", key="new_chat_sidebar"):
        new_id, new_chat = _new_chat("New chat")
        st.session_state.chats[new_id] = new_chat
        st.session_state.current_chat_id = new_id
        st.rerun()

    sorted_items = sorted(
        st.session_state.chats.items(),
        key=lambda kv: kv[1]["created"],
        reverse=True
    )
    ids = [cid for cid, _ in sorted_items]
    picked = st.radio(
        "Your chats",
        ids,
        format_func=lambda cid: st.session_state.chats[cid]["title"],
        label_visibility="visible",
    )
    if picked != st.session_state.current_chat_id:
        st.session_state.current_chat_id = picked
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧹 Clear this chat"):
            st.session_state.chats[st.session_state.current_chat_id]["messages"] = []
            st.rerun()
    with c2:
        if st.button("🗑️ Delete chat"):
            if len(st.session_state.chats) > 1:
                del st.session_state.chats[st.session_state.current_chat_id]
                new_current = sorted(
                    st.session_state.chats.items(),
                    key=lambda kv: kv[1]["created"],
                    reverse=True
                )[0][0]
                st.session_state.current_chat_id = new_current
            else:
                st.session_state.chats[st.session_state.current_chat_id]["messages"] = []
            st.rerun()

# =============================
# System prompts
# =============================
system_prompts = {
    "Default": "You are a helpful assistant.",
    "Math Tutor": "You are a math expert. Answer in a step-by-step logical way.",
    "Doctor": "You are a medical assistant. Always mention this is not medical advice.",
    "Travel Guide": "You are a travel expert helping people explore new places.",
    "Grammar Fixer": "You are a grammar expert. Correct the grammar of any input sentence and suggest improvements.",
    "Summarizer": "You summarize long text into concise points.",
    "Quiz Generator": "Generate a short multiple choice quiz on a given topic."
}

# =============================
# LLM pipeline
# =============================
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
prompt = ChatPromptTemplate.from_messages(
    [("system", system_prompts[st.session_state.mode]), ("human", "Question: {question}")]
)
output_parser = StrOutputParser()
chain = prompt | llm | output_parser

# =============================
# Helpers
# =============================
def ask_llm(question: str) -> str:
    with st.spinner("Thinking…"):
        try:
            return chain.invoke({"question": question})
        except Exception as e:
            return f"Sorry, I hit an error: `{e}`"

def add_message(user_text: str, bot_text: str):
    set_chat_title_if_empty(user_text)
    chat_messages().append({"user": user_text, "bot": bot_text, "ts": time.time()})

# =============================
# Header + Theme toggle icon
# =============================
left_h, right_h = st.columns([10,1], vertical_alignment="center")
with left_h:
    st.markdown(f"""
    <div class="header-row">
      <h1 class="rainbow-title">🌐 AI Chat Assistant</h1>
      <p class="subtitle">Mode: <b>{st.session_state.mode}</b> • Powered by LangChain + Gemini</p>
    </div>
    """, unsafe_allow_html=True)

with right_h:
    icon = "☀️" if st.session_state.theme == "Light" else "🌙"
    st.markdown('<div style="height:2px"></div>', unsafe_allow_html=True)
    if st.button(icon, key="theme_toggle", help="Toggle theme", use_container_width=True):
        st.session_state.theme = "Dark Neon" if st.session_state.theme == "Light" else "Light"
        save_theme_to_disk(st.session_state.theme, st.session_state.reduce_motion)
        st.markdown(theme_css(st.session_state.theme, st.session_state.reduce_motion), unsafe_allow_html=True)
        st.rerun()

# =============================
# EXPLORE VIEW (tabs)
# =============================
if is_explore():
    bc1, bc2 = st.columns([1, 8])
    with bc1:
        if st.button("← Back to Chat", key="back_to_chat_main"):
            st.session_state.selected_tool = "Chat"
            st.rerun()
    with bc2:
        st.subheader("🧪 Explore")

    tab_labels = ["🧭 Career Counselor", "📄 Cover Letter", "🧘 Wellness Tip", "🎲 Random Fact", "🍽️ Recipe"]
    tabs = st.tabs(tab_labels)
    st.caption(f"Selected tool: **{st.session_state.selected_tool}** (change from the sidebar)")

    with tabs[0]:
        with st.form("career_form", clear_on_submit=True):
            career_input = st.text_input("Describe your interests, skills, or goals", key="career_input")
            submitted = st.form_submit_button("🎯 Get Career Advice")
        if submitted and career_input:
            st.success(ask_llm(f"Suggest suitable careers for someone with these interests or skills: {career_input}"))

    with tabs[1]:
        with st.form("cover_form", clear_on_submit=True):
            job_info = st.text_area("Enter job title and your background", key="cover_input")
            submitted = st.form_submit_button("✍️ Generate Cover Letter")
        if submitted and job_info:
            st.success(ask_llm(f"Write a professional cover letter for this: {job_info}"))

    with tabs[2]:
        with st.form("wellness_form", clear_on_submit=True):
            feeling = st.text_input("How are you feeling today?", key="wellness_input")
            submitted = st.form_submit_button("💡 Get Tip")
        if submitted and feeling:
            st.success(ask_llm(f"I'm feeling {feeling}. Give a positive, supportive tip (not medical advice)."))

    with tabs[3]:
        with st.form("fact_form", clear_on_submit=True):
            submitted = st.form_submit_button("🎉 Surprise Me")
        if submitted:
            st.success(ask_llm("Give me a surprising fact"))

    with tabs[4]:
        with st.form("recipe_form", clear_on_submit=True):
            ingredients = st.text_input("Enter available ingredients or a craving", key="recipe_input")
            submitted = st.form_submit_button("👨‍🍳 Get Recipe")
        if submitted and ingredients:
            st.success(ask_llm(f"Suggest a recipe using: {ingredients}"))

    st.markdown("<script>window.scrollTo(0, 0);</script>", unsafe_allow_html=True)
    st.stop()

# =============================
# CHAT VIEW (composer search box + Ask)
# =============================
t1, t2 = st.columns([1, 6])
with t1:
    if st.button("➕ New chat", key="new_chat_header"):
        new_id, new_chat = _new_chat("New chat")
        st.session_state.chats[new_id] = new_chat
        st.session_state.current_chat_id = new_id
        st.rerun()
with t2:
    st.caption("Create a fresh conversation.")

# Input area styled like the screenshot: gradient wrapper, white pill input, Ask button
with st.form("top_search", clear_on_submit=True):
    st.markdown('<div class="composer">', unsafe_allow_html=True)

    top_query = st.text_input(
        label="",
        placeholder="Type your question and press Enter…",
        label_visibility="collapsed",
        key="top_query",
    )

    st.markdown('<div class="composer-actions">', unsafe_allow_html=True)
    submitted_top = st.form_submit_button("Ask")
    st.markdown('</div>', unsafe_allow_html=True)  # /composer-actions
    st.markdown('</div>', unsafe_allow_html=True)  # /composer

if submitted_top and top_query:
    reply = ask_llm(top_query)
    add_message(top_query, reply)
    st.balloons()
    st.rerun()

# Show only latest exchange (older saved below)
msgs = chat_messages()
if msgs:
    last = msgs[-1]
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(last["user"])
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(last["bot"])
else:
    st.caption("No messages yet. Ask something above!")

# =============================
# Chat History
# =============================
st.markdown("---")
st.subheader("📝 Chat History")

if not msgs:
    st.info("No messages yet in this chat.")
    if st.button("➕ Start a new chat", key="new_chat_empty"):
        new_id, new_chat = _new_chat("New chat")
        st.session_state.chats[new_id] = new_chat
        st.session_state.current_chat_id = new_id
        st.rerun()
else:
    for i, m in enumerate(msgs):
        with st.expander(f"👤 You: {m['user'][:60]}{'…' if len(m['user']) > 60 else ''}"):
            st.markdown("**🧠 Bot Response:**")
            st.code(m["bot"], language="markdown")
            st.download_button(
                "⬇️ Download Response",
                data=m["bot"],
                file_name=f"response_{i+1}.txt",
                key=f"download_{st.session_state.current_chat_id}_{i}"
            )

st.markdown(
    '<p class="small-muted">Tip: Pick a tool from the sidebar to open the Explore view, or stay in Chat.</p>',
    unsafe_allow_html=True,
)
