import os
import json
import subprocess
import streamlit as st
import elevaite_ingestion as _pkg

# Resolve package root
_BASE = os.path.dirname(_pkg.__file__)

CONFIG_PATH = os.path.join(_BASE, "config.json")
LOAD_STATUS_JSON_PATH = os.path.join(_BASE, "stage/load_stage/stage_1_status.json")
LOAD_SCRIPT_PATH = os.path.join(_BASE, "stage/load_stage/load_main.py")

# Initialize session states for all stages
if "loading_status" not in st.session_state:
    st.session_state.loading_status = None
if "loading_config_saved" not in st.session_state:
    st.session_state.loading_config_saved = False

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as file:
            return json.load(file)
    return {"loading": {"sources": {"local": {}, "s3": {}}}}

def save_config(updated_config):
    with open(CONFIG_PATH, "w") as file:
        json.dump(updated_config, file, indent=4)

def load_status_json(status_path):
    if os.path.exists(status_path):
        with open(status_path, "r") as file:
            return json.load(file)
    return {"message": "No status available yet."}

def run_pipeline(script_path, status_path, stage):
    try:
        result = subprocess.run(["python3", script_path], capture_output=True, text=True)
        if result.returncode == 0:
            status = load_status_json(status_path)
            if stage == "load":
                st.session_state.loading_status = status
            return status
        else:
            return {"error": "Pipeline execution failed", "details": result.stderr}
    except Exception as e:
        return {"error": "Execution error", "details": str(e)}

# Page configuration
st.set_page_config(page_title="Stage 1: Loading", layout="wide")
st.markdown("## STAGE 1: LOADING")

# Load configuration
config = load_config()
input_directory = config.get("loading", {}).get("sources", {}).get("local", {}).get("input_directory", "INPUT")

# Select Data Source
data_sources = ["Select Data Source", "AWS S3 Bucket", "Local"]
selected_source = st.selectbox("Select Loading Data Source:", data_sources, index=0)

uploaded_files = None

if selected_source == "AWS S3 Bucket":
    st.sidebar.title("Current Configuration - AWS S3")

    bucket_name = st.text_input("S3 Bucket Name", config.get("loading", {}).get("sources", {}).get("s3", {}).get("bucket_name", ""))
    region = st.text_input("AWS Region", config.get("loading", {}).get("sources", {}).get("s3", {}).get("region", ""))

    st.sidebar.json(config.get("loading", {}).get("sources", {}).get("s3", {}))

    if st.button("Save Loading Configuration"):
        config.setdefault("loading", {}).setdefault("sources", {}).setdefault("s3", {})
        config["loading"]["default_source"] = "s3"
        config["loading"]["sources"]["s3"] = {"bucket_name": bucket_name, "region": region}
        save_config(config)
        st.success("✅ AWS S3 Configuration Saved!")
        st.session_state.loading_config_saved = True

elif selected_source == "Local":
    st.sidebar.title("Current Configuration - Local")

    input_directory = st.text_input("Input Directory", input_directory)
    output_directory = st.text_input(
        "Output Directory",
        config.get("loading", {}).get("sources", {}).get("local", {}).get("output_directory", "OUTPUT"),
    )

    st.sidebar.json(config.get("loading", {}).get("sources", {}).get("local", {}))

    if st.button("Save Loading Configuration"):
        config.setdefault("loading", {}).setdefault("sources", {}).setdefault("local", {})
        config["loading"]["default_source"] = "local"
        config["loading"]["sources"]["local"] = {"input_directory": input_directory, "output_directory": output_directory}
        save_config(config)
        st.success("✅ Local Configuration Saved!")
        st.session_state.loading_config_saved = True

uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)

if uploaded_files:
    os.makedirs(input_directory, exist_ok=True)
    for uploaded_file in uploaded_files:
        file_path = os.path.join(input_directory, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"✅ Uploaded `{uploaded_file.name}` to `{input_directory}`.")

if st.session_state.loading_config_saved:
    st.markdown("---")
    if st.button("🚀 Run Loading Pipeline"):
        st.info("Executing loading pipeline... Please wait.")
        run_pipeline(LOAD_SCRIPT_PATH, LOAD_STATUS_JSON_PATH, "load")
        st.success("✅ Loading pipeline executed.")

if st.session_state.loading_status:
    st.subheader("Loading Pipeline Execution Status")
    status_data = st.session_state.loading_status
    summary_data = {key: value for key, value in status_data.items() if key != "EVENT_DETAILS"}
    st.json(summary_data)

    stage_key = "STAGE_1: LOADING"
    if stage_key in status_data and "EVENT_DETAILS" in status_data[stage_key]:
        with st.expander("🔍 View Detailed Event Logs"):
            st.json(status_data[stage_key]["EVENT_DETAILS"])

st.markdown("---")

col1, col2 = st.columns([0.5, 0.5])
with col1:
    if st.button("⬅ Back to Home 🏠"):
        st.switch_page("Home.py")
with col2:
    if st.button("Next to Parsing ➡"):
        st.switch_page("pages/2_Parsing.py")

