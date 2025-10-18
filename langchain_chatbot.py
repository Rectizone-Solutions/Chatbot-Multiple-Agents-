import os
import time
import uuid
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
# Session init (multi-chat + Explore + Theme)
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

if "show_explore" not in st.session_state:
    st.session_state.show_explore = False   # False = Chat view, True = Explore tabs

if "theme" not in st.session_state:
    st.session_state.theme = "Light"        # Light / Dark Neon / Pastel

if "reduce_motion" not in st.session_state:
    st.session_state.reduce_motion = False

def current_chat():
    return st.session_state.chats[st.session_state.current_chat_id]

def chat_messages():
    return current_chat()["messages"]  # list of {"user","bot","ts"}

def set_chat_title_if_empty(first_user_msg: str):
    chat = current_chat()
    if chat["title"] in ("New chat", "Getting started") and first_user_msg.strip():
        t = first_user_msg.strip()
        chat["title"] = (t[:30] + "…") if len(t) > 30 else t

# =============================
# THEME CSS
# =============================
def theme_css(theme: str, reduce_motion: bool) -> str:
    # Defaults (Light)
    bg = "linear-gradient(120deg, #0ea5e9, #a78bfa, #f472b6, #22d3ee, #34d399)"
    title_grad = "linear-gradient(90deg, #ff6b6b, #ffd93d, #6ad6ff, #b794f4, #34d399, #ff6b6b)"
    btn_grad = "linear-gradient(135deg, #6366f1, #22d3ee)"
    card_blur = "2px"
    text_input_bg = "rgba(255,255,255,0.65)"
    text_input_border = "rgba(255,255,255,0.35)"
    subtitle_opacity = ".85"
    chat_shadow = "0 8px 24px rgba(0,0,0,.06)"
    app_text_color = "inherit"

    if theme == "Dark Neon":
        bg = ("radial-gradient(1200px circle at 10% 10%, #0ea5e933, transparent 40%),"
              "radial-gradient(1200px circle at 90% 20%, #f472b633, transparent 45%),"
              "radial-gradient(1200px circle at 20% 90%, #22d3ee33, transparent 45%), #0b1020")
        title_grad = "linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6, #22d3ee, #34d399, #60a5fa)"
        btn_grad = "linear-gradient(135deg, #22d3ee, #6366f1)"
        card_blur = "3px"
        text_input_bg = "rgba(15,23,42,0.75)"
        text_input_border = "rgba(99,102,241,0.55)"
        subtitle_opacity = ".9"
        chat_shadow = "0 12px 28px rgba(0,0,0,.35)"
        app_text_color = "#e5e7eb"
    elif theme == "Pastel":
        bg = "linear-gradient(120deg, #ffe0e0, #e6f3ff, #eaf5ff, #f7e8ff, #e7fff5)"
        title_grad = "linear-gradient(90deg, #fb7185, #fbbf24, #60a5fa, #a78bfa, #34d399, #fb7185)"
        btn_grad = "linear-gradient(135deg, #60a5fa, #a78bfa)"
        card_blur = "0px"
        text_input_bg = "rgba(255,255,255,0.85)"
        text_input_border = "rgba(0,0,0,0.1)"
        subtitle_opacity = ".85"
        chat_shadow = "0 8px 20px rgba(0,0,0,.04)"
        app_text_color = "#111827"

    # Motion control
    bg_anim = "bgShift 28s ease infinite"
    title_anim = "hue 12s linear infinite, floaty 6s ease-in-out infinite"
    chat_anim = "fadeInUp .55s ease both"
    if reduce_motion:
        bg_anim = "none"
        title_anim = "none"
        chat_anim = "fadeInUp .3s ease both"

    return f"""
    <style>
    .stApp {{
      background: {bg};
      background-size: 400% 400%;
      animation: {bg_anim};
      color: {app_text_color};
    }}
    .block-container {{ padding-top: 1rem; padding-bottom: 2rem; }}
    section.main > div {{ backdrop-filter: blur({card_blur}); }}
    .rainbow-title {{
      font-size: 2.2rem; font-weight: 800; line-height: 1.15;
      background: {title_grad};
      background-size: 300% 300%;
      -webkit-background-clip: text; background-clip: text;
      color: transparent; animation: {title_anim}; margin: 0 0 .25rem 0;
    }}
    .subtitle {{ margin-top: .1rem; opacity: {subtitle_opacity}; }}
    [data-testid="stChatMessage"] {{ animation: {chat_anim}; }}
    .stTextInput > div > div > input,
    .stTextArea textarea {{
      border-radius: 12px !important;
      border: 1px solid {text_input_border} !important;
      background: {text_input_bg} !important;
      box-shadow: {chat_shadow};
      color: inherit !important;
    }}
    .stTextArea textarea::placeholder,
    .stTextInput > div > div > input::placeholder {{ color: rgba(0,0,0,0.45); }}
    .stButton > button {{
      border-radius: 12px; background: {btn_grad}; border: none; color: white; font-weight: 600;
      box-shadow: 0 10px 20px rgba(34,211,238,.25);
      transition: transform .08s ease, filter .2s ease, box-shadow .2s ease;
    }}
    .stButton > button:hover {{ transform: translateY(-1px); filter: brightness(1.04); }}
    .stButton > button:active {{ transform: translateY(0); }}
    @keyframes bgShift {{
      0%{{background-position:0% 50%}} 50%{{background-position:100% 50%}} 100%{{background-position:0% 50%}}
    }}
    @keyframes hue {{ 0%{{background-position:0% 50%}} 100%{{background-position:100% 50%}} }}
    @keyframes floaty {{ 0%,100%{{transform: translateY(0)}} 50%{{transform: translateY(-6px)}} }}
    @keyframes fadeInUp {{ from {{opacity:0; transform: translateY(10px)}} to {{opacity:1; transform: translateY(0)}} }}
    </style>
    """

# Inject theme CSS
st.markdown(theme_css(st.session_state.theme, st.session_state.reduce_motion), unsafe_allow_html=True)

# ======= Extra CSS to remove top gap & improve mobile =======
st.markdown("""
<style>
html, body, .stApp { height: 100%; min-height: 100vh; }
header[data-testid="stHeader"] { height: 0px; min-height: 0px; background: transparent; }
header[data-testid="stHeader"] * { display: none; }
div[data-testid="stDecoration"] { display: none; }
.block-container { padding-top: 0.5rem !important; padding-bottom: 2.25rem; }
[data-testid="stForm"] {
  margin-top: .25rem; padding: 14px 16px; border-radius: 14px;
  border: 1px solid rgba(255,255,255,.25); background: rgba(255,255,255,.22);
  box-shadow: 0 8px 22px rgba(0,0,0,.08);
}
.streamlit-expanderHeader { font-size: 0.98rem; padding: 10px 12px; }
.streamlit-expanderContent { padding: 8px 12px 12px 12px; }
.stButton > button { padding: .6rem 1rem; }
.stTextInput > div > div > input, .stTextArea textarea { padding: .7rem .85rem; }
.stApp { padding-top: max(env(safe-area-inset-top), 0px); }
@media (max-width: 640px) {
  .rainbow-title { font-size: 1.6rem; }
  .subtitle { font-size: 0.95rem; }
  .stButton > button { width: 100%; }
  [data-testid="stForm"] { padding: 12px; }
  .block-container { padding-top: 0.35rem !important; padding-bottom: 2rem; }
}
@media (min-width: 1400px) { .block-container { max-width: 1200px; } }
</style>
""", unsafe_allow_html=True)

# =============================
# Sidebar (Theme + Explore + Projects/Chats)
# =============================
with st.sidebar:
    st.title("⚙️ Settings")
    st.caption("LangChain + Gemini")

    # Theme controls
    st.markdown("### 🎨 Theme")
    st.session_state.theme = st.selectbox(
        "Theme",
        ["Light", "Dark Neon", "Pastel"],
        index=["Light", "Dark Neon", "Pastel"].index(st.session_state.theme),
    )
    st.session_state.reduce_motion = st.checkbox("Reduce motion", value=st.session_state.reduce_motion)
    # Re-apply CSS if changed
    st.markdown(theme_css(st.session_state.theme, st.session_state.reduce_motion), unsafe_allow_html=True)

    st.markdown("---")
    # Explore launcher
    st.markdown("### 🧪 Explore")
    if not st.session_state.show_explore:
        if st.button("Open Explore", use_container_width=True):
            st.session_state.show_explore = True
            st.rerun()
    else:
        if st.button("← Back to Chat", use_container_width=True):
            st.session_state.show_explore = False
            st.rerun()

    st.markdown("---")
    st.session_state.mode = st.selectbox(
        "Chatbot Mode",
        ["Default", "Math Tutor", "Doctor", "Travel Guide", "Grammar Fixer", "Summarizer", "Quiz Generator"],
        index=["Default", "Math Tutor", "Doctor", "Travel Guide", "Grammar Fixer", "Summarizer", "Quiz Generator"].index(st.session_state.mode)
    )

    st.markdown("---")
    st.subheader("💼 Projects / Chats")

    # New chat (sidebar)
    if st.button("➕ New chat", key="new_chat_sidebar"):
        new_id, new_chat = _new_chat("New chat")
        st.session_state.chats[new_id] = new_chat
        st.session_state.current_chat_id = new_id
        st.rerun()

    # List chats (most recent first)
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
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GOOGLE_API_KEY
)
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
# Header (animated)
# =============================
st.markdown(f"""
<div class="header-row">
  <h1 class="rainbow-title">🌐 AI Chat Assistant</h1>
  <p class="subtitle">Mode: <b>{st.session_state.mode}</b> • Powered by LangChain + Gemini</p>
</div>
""", unsafe_allow_html=True)

# =============================
# EXPLORE VIEW (tabs)
# =============================
if st.session_state.show_explore:
    # Back button in MAIN content
    bc1, bc2 = st.columns([1, 8])
    with bc1:
        if st.button("← Back to Chat", key="back_to_chat_main"):
            st.session_state.show_explore = False
            st.rerun()
    with bc2:
        st.subheader("🧪 Explore")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🧭 Career Counselor",
        "📄 Cover Letter",
        "🧘 Wellness Tip",
        "🎲 Random Fact",
        "🍽️ Recipe"
    ])

    with tab1:
        with st.form("career_form", clear_on_submit=True):
            career_input = st.text_input("Describe your interests, skills, or goals", key="career_input")
            submitted = st.form_submit_button("🎯 Get Career Advice")
        if submitted and career_input:
            st.success(ask_llm(f"Suggest suitable careers for someone with these interests or skills: {career_input}"))

    with tab2:
        with st.form("cover_form", clear_on_submit=True):
            job_info = st.text_area("Enter job title and your background", key="cover_input")
            submitted = st.form_submit_button("✍️ Generate Cover Letter")
        if submitted and job_info:
            st.success(ask_llm(f"Write a professional cover letter for this: {job_info}"))

    with tab3:
        with st.form("wellness_form", clear_on_submit=True):
            feeling = st.text_input("How are you feeling today?", key="wellness_input")
            submitted = st.form_submit_button("💡 Get Tip")
        if submitted and feeling:
            st.success(ask_llm(f"""I'm feeling {feeling}. Give a positive, supportive tip (not medical advice)."""))

    with tab4:
        with st.form("fact_form", clear_on_submit=True):
            submitted = st.form_submit_button("🎉 Surprise Me")
        if submitted:
            st.success(ask_llm("Give me a surprising fact"))

    with tab5:
        with st.form("recipe_form", clear_on_submit=True):
            ingredients = st.text_input("Enter available ingredients or a craving", key="recipe_input")
            submitted = st.form_submit_button("👨‍🍳 Get Recipe")
        if submitted and ingredients:
            st.success(ask_llm(f"Suggest a recipe using: {ingredients}"))

    st.markdown('<p class="small-muted">Tip: Click “← Back to Chat” above or in the sidebar to return.</p>', unsafe_allow_html=True)
    st.stop()  # don't render chat view when Explore is open

# =============================
# CHAT VIEW (single search bar + latest exchange only)
# =============================
# Quick action under title
t1, t2 = st.columns([1, 6])
with t1:
    if st.button("➕ New chat", key="new_chat_header"):
        new_id, new_chat = _new_chat("New chat")
        st.session_state.chats[new_id] = new_chat
        st.session_state.current_chat_id = new_id
        st.rerun()
with t2:
    st.caption("Create a fresh conversation.")

# Search bar
with st.form("top_search", clear_on_submit=True):
    top_query = st.text_input(
        label="",
        placeholder="Type your question and press Enter…",
        label_visibility="collapsed",
        key="top_query",
    )
    submitted_top = st.form_submit_button("Ask")

if submitted_top and top_query:
    reply = ask_llm(top_query)
    add_message(top_query, reply)
    st.balloons()  # 🎈 small celebration on new reply
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
# Chat History (oldest → newest)
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
    '<p class="small-muted">Tip: Switch Theme from the sidebar. Reduce motion if you prefer a calmer UI.</p>',
    unsafe_allow_html=True,
)
