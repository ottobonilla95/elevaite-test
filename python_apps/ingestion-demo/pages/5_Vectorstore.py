import os
import json
import subprocess
import streamlit as st
import elevaite_ingestion as _pkg

_BASE = os.path.dirname(_pkg.__file__)

CONFIG_PATH = os.path.join(_BASE, "config.json")
VECTOR_STATUS_JSON_PATH = os.path.join(_BASE, "stage/vectorstore_stage/stage_5_status.json")
VECTOR_SCRIPT_PATH = os.path.join(_BASE, "stage/vectorstore_stage/vectordb_main.py")

if "vectorstore_status" not in st.session_state:
    st.session_state.vectorstore_status = None

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as file:
            return json.load(file)
    return {"vector_db": {"databases": {}}}

def save_config(updated_config):
    with open(CONFIG_PATH, "w") as file:
        json.dump(updated_config, file, indent=4)

def load_status_json(status_path):
    if os.path.exists(status_path):
        with open(status_path, "r") as file:
            return json.load(file)
    return {"message": "No status available yet."}

def run_pipeline(script_path, status_path):
    try:
        result = subprocess.run(["python3", script_path], capture_output=True, text=True)
        if result.returncode == 0:
            status = load_status_json(status_path)
            st.session_state.vectorstore_status = status
            return status
        else:
            return {"error": "Pipeline execution failed", "details": result.stderr}
    except Exception as e:
        return {"error": "Execution error", "details": str(e)}

st.set_page_config(page_title="Stage 5: Vectorstore", layout="wide")
st.markdown("## STAGE 5: VECTORSTORE")

config = load_config()

vector_db_options = list(config.get("vector_db", {}).get("databases", {}).keys())
selected_vector_db = st.selectbox("Select Vector Database:", ["Select a Vector DB"] + vector_db_options, index=0)

if selected_vector_db != "Select a Vector DB":
    st.sidebar.title("Current Configuration")
    st.sidebar.subheader(f"{selected_vector_db.capitalize()} Settings")
    st.sidebar.json(config["vector_db"]["databases"].get(selected_vector_db, {}))

    if selected_vector_db == "qdrant":
        st.subheader("Qdrant Configuration")
        host = st.text_input("Host", config["vector_db"]["databases"]["qdrant"].get("host", "localhost"))
        port = st.number_input("Port", min_value=1, max_value=65535, value=config["vector_db"]["databases"]["qdrant"].get("port", 5333))
        collection_name = st.text_input("Collection Name", config["vector_db"]["databases"]["qdrant"].get("collection_name", "kb-qdrant6"))
        if st.button("Save Qdrant Configuration"):
            config["vector_db"]["default_db"] = "qdrant"
            config["vector_db"]["databases"]["qdrant"] = {"host": host, "port": port, "collection_name": collection_name}
            save_config(config)
            st.success("Qdrant settings updated successfully!")

    elif selected_vector_db == "pinecone":
        st.subheader("Pinecone Configuration")
        api_key = st.text_input("API Key", config["vector_db"]["databases"]["pinecone"].get("api_key", ""))
        cloud = st.text_input("Cloud", config["vector_db"]["databases"]["pinecone"].get("cloud", "aws"))
        region = st.text_input("Region", config["vector_db"]["databases"]["pinecone"].get("region", "us-east-1"))
        index_name = st.text_input("Index Name", config["vector_db"]["databases"]["pinecone"].get("index_name", "kb-final-check"))
        dimension = st.number_input("Dimension", min_value=1, max_value=4096, value=config["vector_db"]["databases"]["pinecone"].get("dimension", 1536))
        if st.button("Save Pinecone Configuration"):
            config["vector_db"]["default_db"] = "pinecone"
            config["vector_db"]["databases"]["pinecone"] = {
                "api_key": api_key,
                "cloud": cloud,
                "region": region,
                "index_name": index_name,
                "dimension": dimension,
            }
            save_config(config)
            st.success("Pinecone settings updated successfully!")

    elif selected_vector_db == "chroma":
        st.subheader("Chroma Configuration")
        db_path = st.text_input("Database Path", config["vector_db"]["databases"]["chroma"].get("db_path", "data/chroma_db"))
        collection_name = st.text_input("Collection Name", config["vector_db"]["databases"]["chroma"].get("collection_name", "kb-chroma"))
        if st.button("Save Chroma Configuration"):
            config["vector_db"]["default_db"] = "chroma"
            config["vector_db"]["databases"]["chroma"] = {"db_path": db_path, "collection_name": collection_name}
            save_config(config)
            st.success("Chroma settings updated successfully!")

    st.markdown("---")
    if st.button("Run Vectorstore Pipeline"):
        st.info("Executing vectorstore pipeline... Please wait.")
        vector_status = run_pipeline(VECTOR_SCRIPT_PATH, VECTOR_STATUS_JSON_PATH)
        st.subheader("Vectorstore Pipeline Execution Status")
        st.json({key: value for key, value in vector_status.items() if key != "EVENT_DETAILS"})
        if "EVENT_DETAILS" in vector_status:
            with st.expander("View Detailed Event Logs"):
                st.json(vector_status["EVENT_DETAILS"])

    if selected_vector_db == "qdrant":
        st.markdown("##### Visualize your collection")
        qdrant_host = config["vector_db"]["databases"]["qdrant"].get("host", "http://localhost")
        qdrant_port = config["vector_db"]["databases"]["qdrant"].get("port", 6333)
        collection_name = config["vector_db"]["databases"]["qdrant"].get("collection_name", "kb-qdrant")
        qdrant_dashboard_url = f"{qdrant_host}:{qdrant_port}/dashboard#/collections/{collection_name}"
        st.markdown(f"Link: [{qdrant_dashboard_url}]({qdrant_dashboard_url})", unsafe_allow_html=True)

    if selected_vector_db == "pinecone":
        st.markdown("##### Visualize your Pinecone Index")
        pinecone_index_name = config["vector_db"]["databases"]["pinecone"].get("index_name", "kb-final")
        pinecone_dashboard_url = f"https://app.pinecone.io/projects/default/indexes/{pinecone_index_name}"
        st.markdown(f"Link: [{pinecone_dashboard_url}]({pinecone_dashboard_url})", unsafe_allow_html=True)

st.markdown("---")

col1, col2 = st.columns([0.5, 0.5])
with col1:
    if st.button("Back to Embedding"):
        st.switch_page("pages/4_Embedding.py")
with col2:
    if st.button("Back to Home"):
        st.switch_page("Home.py")

