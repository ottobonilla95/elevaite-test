import os
import streamlit as st
import elevaite_ingestion as _pkg
from datetime import datetime

# Resolve package asset path (logo inside elevaite_ingestion)
_PKG_ROOT = os.path.dirname(_pkg.__file__)

# Initialize session state
if 'chat_open' not in st.session_state:
    st.session_state.chat_open = False
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'knowledge_bases' not in st.session_state:
    st.session_state.knowledge_bases = []

st.set_page_config(
    page_title="ELEVAITE INGESTION PIPE",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;500;700&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');

    :root { --primary: #ffffff; --secondary: #00c7ff; --card-bg: #2d2d2d; --stage-tab: #3d3d3d; }
    body { font-family: 'Roboto', sans-serif; background-color: #1a1a1a; }
    .pipeline-container { display: flex; justify-content: space-between; margin: 2rem 0; gap: 1rem; }
    .stage-card { flex: 1 1 0; background: var(--card-bg); border-radius: 8px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: all 0.3s ease; border-left: 4px solid var(--secondary); animation: slideUp 0.5s ease forwards; opacity: 0; min-height: 200px; display: flex; flex-direction: column; position: relative; margin-top: 40px; }
    .stage-tab { position: absolute; top: -35px; left: 50%; transform: translateX(-50%); background: var(--stage-tab); color: var(--secondary); padding: 8px 20px; border-radius: 5px 5px 0 0; font-size: 0.9rem; font-weight: 700; white-space: nowrap; box-shadow: 0 -2px 6px rgba(0,0,0,0.2); }
    .stage-card:hover { transform: translateY(-5px); box-shadow: 0 8px 12px rgba(0,0,0,0.5); }
    .stage-icon { font-size: 1.8rem; color: var(--primary); margin-bottom: 1rem; }
    .stage-title { font-size: 1.2rem; color: var(--primary); margin-bottom: 0.5rem; font-weight: 700; }
    .stage-description { color: #b3b3b3; font-size: 0.9rem; line-height: 1.5; flex-grow: 1; }
    @keyframes slideUp { from { opacity: 0; transform: translateY(20px);} to { opacity: 1; transform: translateY(0);} }
    [data-testid="column"] { display: flex; flex-direction: column; gap: 1rem; position: relative; }
    .kb-card { background: var(--card-bg); padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 3px solid var(--secondary); }
    .kb-date { color: #00c7ff; font-size: 0.8rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.image(os.path.join(_PKG_ROOT, "elevaite_logo.png"), width=250)

st.title("*elevAIte* INGESTION PIPELINE")
st.markdown("---")
st.markdown("### *End-to-End Pipeline for LLM-Ready Retrieval Systems* ###")
st.markdown("---")

# Pipeline stages data
stages = [
    {"icon": "fa-cloud-upload-alt", "title": "Loading", "description": "Upload and configure data sources from various formats and locations"},
    {"icon": "fa-cogs", "title": "Parsing", "description": "Configure and execute document parsing with format-specific processors"},
    {"icon": "fa-shapes", "title": "Chunking", "description": "Apply optimal chunking strategies for text segmentation"},
    {"icon": "fa-project-diagram", "title": "Embedding", "description": "Transform text chunks into vector embeddings using AI models"},
    {"icon": "fa-database", "title": "Vectorstore", "description": "Store and manage vector embeddings with metadata in database"},
]

# Create pipeline cards
cols = st.columns(5)
for idx, (col, stage) in enumerate(zip(cols, stages), start=1):
    with col:
        st.markdown(
            f"""
            <div class=\"stage-card\" style=\"animation-delay: {idx * 0.5}s;\">
                <div class=\"stage-tab\">Stage {idx}: {stage['title']}</div>
                <i class=\"{stage['icon']} stage-icon\"></i>
                <div class=\"stage-description\">{stage['description']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")
if st.button("Begin Pipeline ➡", type="primary", use_container_width=True):
    st.session_state.knowledge_bases.insert(
        0,
        {
            "name": "Arlo Knowledge Base",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "doc_count": 1,
            "chunk_count": 1567,
        },
    )
    st.switch_page("pages/1_Loading.py")

st.markdown("---")

st.markdown("### Existing Knowledge Bases")
if st.session_state.knowledge_bases:
    for kb in st.session_state.knowledge_bases:
        st.markdown(
            f"""
            <div class=\"kb-card\">
                <div class=\"kb-date\">{kb['created']}</div>
                <h4>{kb['name']}</h4>
                <p>Documents: {kb['doc_count']} | Chunks: {kb['chunk_count']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.markdown("No knowledge bases created yet. Start a pipeline to create one!")

st.markdown("---")

