import streamlit as st
import requests
import uuid
import time
from datetime import datetime
from graphviz import Digraph
import plotly.graph_objects as go
import base64
from io import BytesIO
from PIL import Image

# =========================================================
# CONFIG
# =========================================================
API_URL = "http://127.0.0.1:8000/chat"
IMG_API_URL = "http://127.0.0.1:8000/generate-image"

st.set_page_config(
    page_title="CASIA – Neuro-Symbolic AI",
    page_icon="🤖",
    layout="wide",
)

# =========================================================
# STYLES — Bright, Professional, Attractive Theme
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

.main .block-container {
    max-width: 100%;
    padding: 1.4rem 2rem;
}

.stApp {
    background: #f0f4ff;
}

/* ── HEADER ── */
.casia-header {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #a855f7 100%);
    padding: 22px 28px;
    border-radius: 20px;
    color: white;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 18px;
    box-shadow: 0 8px 32px rgba(79, 70, 229, 0.30);
    border: 1px solid rgba(255,255,255,0.18);
}

.casia-header-icon {
    font-size: 2.6rem;
    background: rgba(255,255,255,0.18);
    border-radius: 16px;
    width: 64px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.casia-header h2 {
    margin: 0 0 4px 0;
    font-size: 1.55rem;
    font-weight: 700;
    letter-spacing: -0.3px;
}

.casia-header p {
    margin: 0;
    font-size: 0.85rem;
    opacity: 0.82;
    letter-spacing: 0.3px;
}

.casia-badge {
    display: inline-block;
    background: rgba(255,255,255,0.22);
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-right: 6px;
    margin-top: 6px;
    border: 1px solid rgba(255,255,255,0.28);
}

/* ── CHAT BOX ── */
.chat-box {
    background: white;
    border-radius: 22px;
    padding: 22px;
    min-height: 520px;
    box-shadow: 0 4px 24px rgba(79, 70, 229, 0.10);
    border: 1.5px solid #e0e7ff;
}

/* ── INPUT PANEL ── */
.input-panel {
    background: white;
    border-radius: 20px;
    padding: 20px 22px;
    box-shadow: 0 4px 24px rgba(79, 70, 229, 0.10);
    border: 1.5px solid #e0e7ff;
    margin-top: 16px;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%) !important;
}

section[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.08) !important;
    color: #c7d2fe !important;
    border: 1px solid rgba(165, 180, 252, 0.25) !important;
    border-radius: 10px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}

section[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(165, 180, 252, 0.18) !important;
    color: white !important;
    border-color: rgba(165, 180, 252, 0.5) !important;
    transform: translateX(2px);
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label {
    color: #c7d2fe !important;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(165, 180, 252, 0.2) !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 1.2rem !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.30) !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.2px !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(79, 70, 229, 0.42) !important;
}

.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ── TEXT AREA ── */
.stTextArea textarea {
    border: 1.5px solid #c7d2fe !important;
    border-radius: 14px !important;
    font-size: 0.95rem !important;
    padding: 12px 16px !important;
    color: #1e1b4b !important;
    background: #f8f7ff !important;
    transition: border 0.2s ease !important;
}

.stTextArea textarea:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.12) !important;
}

/* ── TEXT INPUT ── */
.stTextInput input {
    border: 1.5px solid #c7d2fe !important;
    border-radius: 10px !important;
    color: #1e1b4b !important;
    background: #f8f7ff !important;
}

.stTextInput input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.12) !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    border: 2px dashed #a5b4fc !important;
    border-radius: 14px !important;
    background: #f5f3ff !important;
    padding: 10px !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: #7c3aed !important;
    background: #ede9fe !important;
}

/* ── CHAT MESSAGES ── */
[data-testid="stChatMessage"] {
    border-radius: 16px !important;
    margin-bottom: 6px !important;
}

/* ── EXPANDER ── */
.streamlit-expanderHeader {
    background: #f5f3ff !important;
    border-radius: 10px !important;
    color: #4f46e5 !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
}

/* ── CAPTION ── */
.stCaption {
    color: #a5b4fc !important;
    font-size: 0.76rem !important;
}

/* ── SUCCESS/ERROR ── */
.stSuccess {
    background: #ecfdf5 !important;
    border: 1px solid #6ee7b7 !important;
    border-radius: 10px !important;
    color: #065f46 !important;
}

/* ── FORM ── */
[data-testid="stForm"] {
    background: #f8f7ff !important;
    border: 1.5px solid #e0e7ff !important;
    border-radius: 14px !important;
    padding: 10px !important;
}

/* ── PLOTLY CHART ── */
.js-plotly-plot {
    border-radius: 14px !important;
    overflow: hidden;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #f0f4ff; }
::-webkit-scrollbar-thumb { background: #c7d2fe; border-radius: 6px; }
::-webkit-scrollbar-thumb:hover { background: #818cf8; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION
# =========================================================
if "user_id" not in st.session_state:
    st.session_state.user_id = "casia_user"

if "chats" not in st.session_state:
    cid = str(uuid.uuid4())
    st.session_state.chats = {cid: {"title": "New Chat", "messages": []}}
    st.session_state.active_chat = cid

# =========================================================
# HELPERS
# =========================================================
def add_message(role, text, metrics=None, image=None):
    st.session_state.chats[st.session_state.active_chat]["messages"].append({
        "role": role,
        "text": text,
        "metrics": metrics or {},
        "image": image,
        "time": time.time()
    })

def time_fmt(ts):
    return datetime.fromtimestamp(ts).strftime("%I:%M %p")

def read_file(file):
    from pypdf import PdfReader
    from docx import Document

    if file.type == "application/pdf":
        return "\n".join(p.extract_text() or "" for p in PdfReader(file).pages)
    if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "\n".join(p.text for p in Document(file).paragraphs)
    if file.type == "text/plain":
        return file.read().decode("utf-8", errors="ignore")
    return ""

# =========================================================
# EXPLAINABILITY VISUALS
# =========================================================
def flow_graph(metrics):
    dot = Digraph()
    dot.attr(rankdir="LR", bgcolor="transparent")
    dot.attr("node", style="filled", fontname="Inter", fontsize="11",
             fillcolor="#ede9fe", fontcolor="#3730a3", color="#818cf8", shape="roundedbox")
    dot.attr("edge", color="#7c3aed", arrowsize="0.7")

    dot.node("Q", "Query")
    dot.node("I", "Intent")
    dot.node("K", "Knowledge")
    dot.node("S", "Safety")
    dot.node("E", "Explain")

    dot.edge("Q", "I")
    dot.edge("I", "K")

    last = "K"

    if metrics.get("rag_used"):
        dot.node("R", "RAG", fillcolor="#dbeafe", fontcolor="#1e40af", color="#60a5fa")
        dot.edge(last, "R")
        last = "R"

    if metrics.get("web_used"):
        dot.node("W", "Web", fillcolor="#d1fae5", fontcolor="#065f46", color="#34d399")
        dot.edge(last, "W")
        last = "W"

    dot.edge(last, "S")
    dot.edge("S", "E")

    return dot


def explainability_pie(metrics, uid):
    rag = 1.0 if metrics.get("rag_used") else 0.0
    web = 1.0 if metrics.get("web_used") else 0.0

    confidence = float(metrics.get("confidence", 0.1))
    explain = float(metrics.get("explainability_score", 0.1))
    safety = float(metrics.get("safety_score", 0.1))
    trace = float(metrics.get("trace_score", 0.1))

    total = rag + web + confidence + explain + safety + trace
    if total == 0:
        total = 1

    values = [
        (confidence / total) * 100,
        (explain / total) * 100,
        (rag / total) * 100,
        (web / total) * 100,
        (safety / total) * 100,
        (trace / total) * 100,
    ]

    colors = ["#7c3aed", "#a855f7", "#6366f1", "#38bdf8", "#34d399", "#fb923c"]

    fig = go.Figure(data=[go.Pie(
        labels=["Confidence", "Explainability", "RAG Usage", "Web Usage", "Safety", "Traceability"],
        values=values,
        hole=0.50,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        textfont=dict(family="Inter", size=12),
    )])

    fig.update_layout(
        height=310,
        margin=dict(l=20, r=20, t=36, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#374151"),
        title=dict(
            text=f"Explainability Breakdown",
            font=dict(size=14, color="#4f46e5", family="Inter"),
            x=0.5
        ),
        legend=dict(
            font=dict(size=11, family="Inter"),
            orientation="v",
            x=1.0,
            y=0.5
        )
    )

    return fig

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("### 💬 Conversations")

    if st.button("➕  New Chat", use_container_width=True):
        cid = str(uuid.uuid4())
        st.session_state.chats[cid] = {"title": "New Chat", "messages": []}
        st.session_state.active_chat = cid
        st.rerun()

    st.markdown("---")

    for cid, chat in list(st.session_state.chats.items()):
        c1, c2 = st.columns([0.82, 0.18])

        with c1:
            label = ("▶ " if cid == st.session_state.active_chat else "") + chat["title"]
            if st.button(label, key=f"open_{cid}", use_container_width=True):
                st.session_state.active_chat = cid
                st.rerun()

        with c2:
            if st.button("🗑", key=f"del_{cid}"):
                del st.session_state.chats[cid]
                if st.session_state.chats:
                    st.session_state.active_chat = next(iter(st.session_state.chats))
                else:
                    nid = str(uuid.uuid4())
                    st.session_state.chats[nid] = {"title": "New Chat", "messages": []}
                    st.session_state.active_chat = nid
                st.rerun()

    st.markdown("---")
    st.markdown(
        "<p style='color:#818cf8; font-size:0.78rem; text-align:center;'>CASIA v1.0 · Neuro-Symbolic AI</p>",
        unsafe_allow_html=True
    )

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div class="casia-header">
    <div class="casia-header-icon">🤖</div>
    <div>
        <h2>CASIA – Neuro-Symbolic AI Assistant</h2>
        <div>
            <span class="casia-badge">✦ Explainable</span>
            <span class="casia-badge">🛡 Safe</span>
            <span class="casia-badge">🔍 RAG + Web Hybrid</span>
            <span class="casia-badge">⚡ Self-Learning</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# CHAT WINDOW
# =========================================================
st.markdown('<div class="chat-box">', unsafe_allow_html=True)

msgs = st.session_state.chats[st.session_state.active_chat]["messages"]

if not msgs:
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px; color: #a5b4fc;">
        <div style="font-size: 3rem; margin-bottom: 14px;">✨</div>
        <p style="font-size: 1.1rem; font-weight: 600; color: #6366f1; margin-bottom: 6px;">Start a conversation</p>
        <p style="font-size: 0.88rem; color: #a5b4fc;">Ask CASIA anything — or upload a document to get started.</p>
    </div>
    """, unsafe_allow_html=True)

for m in msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["text"])

        if m["role"] == "assistant" and m.get("metrics"):
            with st.expander(f"🔍 Explainability — {time_fmt(m['time'])}"):
                col_g, col_p = st.columns([1, 1])
                with col_g:
                    st.graphviz_chart(flow_graph(m["metrics"]))
                with col_p:
                    st.plotly_chart(explainability_pie(m["metrics"], m["time"]), use_container_width=True)

        if m["role"] == "assistant":
            with st.form(key=f"fb_{m['time']}"):
                feedback = st.text_input("✍️ Suggest an improvement for this response:")
                submit = st.form_submit_button("Submit Feedback")

                if submit and feedback.strip():
                    requests.post(API_URL, json={
                        "user_id": st.session_state.user_id,
                        "message": "",
                        "feedback": feedback
                    })
                    st.success("✅ Feedback submitted — thank you!")

        st.caption(f"🕐 {time_fmt(m['time'])}")

st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# INPUT PANEL
# =========================================================
st.markdown('<div class="input-panel">', unsafe_allow_html=True)

st.markdown(
    "<p style='font-size:0.82rem; color:#6366f1; font-weight:600; margin-bottom:6px; text-transform:uppercase; letter-spacing:0.6px;'>Your Message</p>",
    unsafe_allow_html=True
)

user_text = st.text_area(
    label="message_input",
    label_visibility="collapsed",
    placeholder="Ask CASIA anything, or describe what you'd like to explore...",
    height=96
)

files = st.file_uploader(
    "📎 Attach documents — PDF, DOCX, or TXT",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True
)

col_send, col_clear = st.columns([5, 1])

with col_send:
    if st.button("🚀  Send to CASIA", use_container_width=True):
        doc_text = ""
        for f in files or []:
            doc_text += "\n\n" + read_file(f)

        if user_text.strip() or doc_text:
            add_message("user", user_text or "📎 Document Query")

            r = requests.post(API_URL, json={
                "user_id": st.session_state.user_id,
                "message": user_text,
                "document_text": doc_text
            }).json()

            add_message("assistant", r["reply"], metrics=r.get("metrics", {}))
            st.rerun()

with col_clear:
    if st.button("🗑 Clear", use_container_width=True):
        st.session_state.chats[st.session_state.active_chat]["messages"] = []
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    "<p style='text-align:center; color:#c7d2fe; font-size:0.76rem; margin-top:10px;'>CASIA responds intelligently and adapts to your needs · Powered by Neuro-Symbolic AI</p>",
    unsafe_allow_html=True
)