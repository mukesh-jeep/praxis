"""
Streamlit frontend for the Medical RAG Assistant.

Run:
    streamlit run frontend/app.py
"""

import os
import streamlit as st
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


# ── page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Medical RAG Assistant",
    page_icon="🏥",
    layout="centered",
)

# ── custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Dark premium look */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
        min-height: 100vh;
    }

    /* Header */
    .medical-header {
        text-align: center;
        padding: 2rem 0 1.5rem 0;
    }
    .medical-header h1 {
        font-size: 2.2rem;
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .medical-header p {
        color: #8892b0;
        font-size: 0.95rem;
    }

    /* Status badges */
    .status-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .status-online  { background: #0d3b27; color: #4ade80; border: 1px solid #16a34a; }
    .status-offline { background: #3b0d0d; color: #f87171; border: 1px solid #dc2626; }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        border-radius: 12px;
        margin-bottom: 0.75rem;
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 0.5rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(15,15,30,0.9);
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    /* Input box */
    [data-testid="stChatInputContainer"] {
        border-top: 1px solid rgba(255,255,255,0.08);
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.04);
        border-radius: 8px;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ── session state ─────────────────────────────────────────────────────────────

if "session_id" not in st.session_state:
    st.session_state.session_id = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_queries" not in st.session_state:
    st.session_state.total_queries = 0
if "files_uploaded" not in st.session_state:
    st.session_state.files_uploaded = 0

# ── check backend health ──────────────────────────────────────────────────────

def _check_backend() -> bool:
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

backend_ok = _check_backend()

# ── header ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="medical-header">
    <h1>🏥 Medical RAG Assistant</h1>
    <p>AI-powered assistant with document upload & knowledge-base retrieval</p>
</div>
""", unsafe_allow_html=True)

status_cls   = "status-online"  if backend_ok else "status-offline"
status_label = "● Backend online" if backend_ok else "● Backend offline"
st.markdown(f'<div style="text-align:center"><span class="status-pill {status_cls}">{status_label}</span></div>', unsafe_allow_html=True)

# ── sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Settings")

    st.markdown("### 📊 Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Queries", st.session_state.total_queries)
    with col2:
        st.metric("Files", st.session_state.files_uploaded)

    if st.session_state.session_id:
        st.markdown("### 🔑 Session ID")
        st.code(st.session_state.session_id[:8] + "...", language=None)

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = ""
        st.session_state.total_queries = 0
        st.session_state.files_uploaded = 0
        st.rerun()

    st.divider()
    st.markdown("### 📤 Ingest to Knowledge Base")
    kb_files = st.file_uploader(
        "Upload PDFs to knowledge base",
        type=["pdf"],
        accept_multiple_files=True,
        key="kb_uploader",
    )
    if st.button("Ingest Files", use_container_width=True, disabled=not kb_files):
        with st.spinner("Ingesting…"):
            try:
                files_payload = [
                    ("files", (f.name, f.getvalue(), f.type)) for f in kb_files
                ]
                r = requests.post(f"{BACKEND_URL}/ingest", files=files_payload, timeout=120)
                if r.ok:
                    result = r.json()
                    st.success(result.get("message", "Ingested!"))
                else:
                    st.error(f"Error {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"Could not reach backend: {e}")

    st.divider()
    st.markdown("""
<div style="color:#4a5568; font-size:0.8rem; text-align:center;">
Medical RAG Assistant v1.0<br>
Powered by Groq + Qdrant + LangGraph
</div>
""", unsafe_allow_html=True)


# ── chat history ──────────────────────────────────────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("attachment"):
            st.caption(f"📎 {msg['attachment']}")

# ── file uploader (per query) ─────────────────────────────────────────────────

uploaded_file = st.file_uploader(
    "📎 Attach a file to this query (optional)",
    type=["pdf", "docx", "png", "jpg", "jpeg"],
    key="query_uploader",
    help="The file is sent directly to the LLM for this query only — it is NOT added to the knowledge base.",
)

# ── chat input ────────────────────────────────────────────────────────────────

if not backend_ok:
    st.warning(
        "⚠️ Cannot reach the backend at `http://localhost:8000`. "
        "Start it with:\n```\nuvicorn backend.main:app --reload --port 8000\n```",
        icon="⚠️",
    )

if query := st.chat_input("Ask a medical question…"):
    if not backend_ok:
        st.error("Backend is offline. Please start it first.")
        st.stop()

    # Show user message immediately
    with st.chat_message("user"):
        st.markdown(query)
        if uploaded_file:
            st.caption(f"📎 {uploaded_file.name}")

    st.session_state.messages.append({
        "role": "user",
        "content": query,
        "attachment": uploaded_file.name if uploaded_file else None,
    })

    # Call backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                data = {
                    "query": query,
                    "session_id": st.session_state.session_id,
                }
                files_payload = {}
                if uploaded_file:
                    files_payload = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )
                    }
                    st.session_state.files_uploaded += 1

                resp = requests.post(
                    f"{BACKEND_URL}/chat",
                    data=data,
                    files=files_payload if files_payload else None,
                    timeout=60,
                )

                if resp.ok:
                    result = resp.json()
                    st.session_state.session_id = result["session_id"]
                    answer = result["answer"]
                    st.markdown(answer)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                    })
                    st.session_state.total_queries += 1
                else:
                    err = f"Backend error {resp.status_code}: {resp.text}"
                    st.error(err)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"❌ {err}",
                    })

            except requests.exceptions.ConnectionError:
                msg = (
                    "❌ Could not connect to the backend. "
                    "Make sure it's running on `http://localhost:8000`."
                )
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
            except Exception as e:
                st.error(f"Unexpected error: {e}")
