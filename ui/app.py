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
# STYLES
# =========================================================
st.markdown("""
<style>
.main .block-container { max-width: 100%; padding: 1.2rem; }
.stApp { background: linear-gradient(180deg,#eef2ff,#ffffff); }

.casia-header {
    background: linear-gradient(135deg,#020617,#1e293b);
    padding: 18px;
    border-radius: 20px;
    color: white;
    margin-bottom: 14px;
}

.chat-box {
    background: #f8fafc;
    border-radius: 20px;
    padding: 18px;
    min-height: 520px;
    box-shadow: 0 12px 30px rgba(2,6,23,.12);
}

.input-panel {
    background: white;
    border-radius: 18px;
    padding: 16px;
    box-shadow: 0 10px 28px rgba(2,6,23,.12);
}
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
    dot.attr(rankdir="LR")

    dot.node("Q", "Query")
    dot.node("I", "Intent")
    dot.node("K", "Knowledge")
    dot.node("S", "Safety")
    dot.node("E", "Explain")

    dot.edge("Q", "I")
    dot.edge("I", "K")

    last = "K"
    if metrics.get("rag_used"):
        dot.node("R", "RAG")
        dot.edge(last, "R")
        last = "R"
    elif metrics.get("web_used"):
        dot.node("W", "Web")
        dot.edge(last, "W")
        last = "W"

    dot.edge(last, "S")
    dot.edge("S", "E")
    return dot

def explainability_pie(metrics, uid):
    fig = go.Figure(data=[go.Pie(
        labels=[
            "Confidence",
            "Explainability",
            "RAG Usage",
            "Web Usage",
            "Safety",
            "Traceability"
        ],
        values=[
            float(metrics.get("confidence", 0.0)),
            float(metrics.get("explainability_score", 0.0)),
            1.0 if metrics.get("rag_used") else 0.0,
            1.0 if metrics.get("web_used") else 0.0,
            float(metrics.get("safety_score", 0.0)),
            float(metrics.get("trace_score", 0.0)),
        ],
        hole=0.45
    )])

    # 🔑 makes every chart unique (prevents Streamlit crash)
    fig.update_layout(
        height=330,
        title=f"Explainability Metrics – {uid}"
    )
    return fig

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("💬 Chats")

    if st.button("➕ New Chat", use_container_width=True):
        cid = str(uuid.uuid4())
        st.session_state.chats[cid] = {"title": "New Chat", "messages": []}
        st.session_state.active_chat = cid
        st.rerun()

    st.markdown("---")

    for cid, chat in list(st.session_state.chats.items()):
        c1, c2 = st.columns([0.82, 0.18])

        with c1:
            if st.button(chat["title"], key=f"open_{cid}", use_container_width=True):
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

# =========================================================
# HEADER
# =========================================================
st.markdown("""
<div class="casia-header">
<h2>🤖 CASIA – Neuro-Symbolic AI Assistant</h2>
<p>Explainable • Safe • RAG-Powered • Self-Learning</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# CHAT WINDOW
# =========================================================
st.markdown('<div class="chat-box">', unsafe_allow_html=True)

chat_id = st.session_state.active_chat
msgs = st.session_state.chats[chat_id]["messages"]

for m in msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["text"])

        if m.get("image"):
            st.image(m["image"], width=420)

        # 🔍 Explainability (SAFE)
        if m["role"] == "assistant" and m.get("metrics"):
            with st.container():
                with st.expander(
                    f"🔍 Explainability & Transparency ({time_fmt(m['time'])})"
                ):
                    st.graphviz_chart(flow_graph(m["metrics"]))
                    st.plotly_chart(
                        explainability_pie(m["metrics"], uid=m["time"]),
                        use_container_width=True
                    )

        # ✍️ Feedback
        if m["role"] == "assistant":
            with st.form(key=f"feedback_{chat_id}_{m['time']}"):
                feedback = st.text_input(
                    "✍️ Feedback (optional)",
                    placeholder="e.g. explain in exam point-wise format"
                )
                submit = st.form_submit_button("Submit")

                if submit and feedback.strip():
                    requests.post(API_URL, json={
                        "user_id": st.session_state.user_id,
                        "message": "",
                        "feedback": feedback
                    })
                    st.success("✅ Feedback saved. CASIA will adapt.")

        st.caption(time_fmt(m["time"]))

st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# INPUT PANEL
# =========================================================
st.markdown('<div class="input-panel">', unsafe_allow_html=True)

user_text = st.text_area("Ask CASIA or query documents", height=90)

files = st.file_uploader(
    "📎 Upload documents (PDF, DOCX, TXT)",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True
)

c1, c2 = st.columns([0.7, 0.3])

with c1:
    if st.button("🚀 Send", use_container_width=True):
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



st.markdown("</div>", unsafe_allow_html=True)
st.caption("CASIA behaves according to user needs")
