import streamlit as st
import os
import sys
import json
import subprocess

path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(path)

CONFIG_PATH = os.path.join(path, "config.json")
CHUNK_STATUS_JSON_PATH = os.path.join(path, "stage/chunk_stage/stage_3_status.json")
CHUNK_SCRIPT_PATH = os.path.join(path, "stage/chunk_stage/chunk_main.py")

# Initialize session states
if "chunker_status" not in st.session_state:
    st.session_state.chunker_status = None
if "chunker_config_saved" not in st.session_state:
    st.session_state.chunker_config_saved = False

def load_config():
    """Load the existing config.json file."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as file:
            return json.load(file)
    return {"chunking": {"strategies": {}}}

def save_config(updated_config):
    """Save updated settings to config.json."""
    with open(CONFIG_PATH, "w") as file:
        json.dump(updated_config, file, indent=4)

def load_status_json(status_path):
    """Load the pipeline status JSON."""
    if os.path.exists(status_path):
        with open(status_path, "r") as file:
            return json.load(file)
    return {"message": "No status available yet."}

def run_pipeline(script_path, status_path, stage):
    """Execute a pipeline script and return the status."""
    try:
        result = subprocess.run(["python3", script_path], capture_output=True, text=True)
        if result.returncode == 0:
            status = load_status_json(status_path)
            st.session_state.chunker_status = status
            return status
        else:
            return {"error": "Pipeline execution failed", "details": result.stderr}
    except Exception as e:
        return {"error": "Execution error", "details": str(e)}

# Page configuration
st.set_page_config(page_title="Stage 3: Chunking", layout="wide")
st.markdown("## STAGE 3: CHUNKING")

config = load_config()

# Check if chunking section exists in config
if "chunking" not in config:
    config["chunking"] = {"strategies": {}}
    # Add default chunking strategies
    config["chunking"]["strategies"] = {
        "semantic_chunking": {
            "breakpoint_threshold_type": "percentile",
            "breakpoint_threshold_amount": 80
        },
        "mdstructure": {
            "chunk_size": 1500
        },
        "recursive_chunking": {
            "chunk_size": 700,
            "chunk_overlap": 100
        },
        "sentence_chunking": {
            "max_chunk_size": 1000
        }
    }
    save_config(config)

# Get chunking strategies from config
chunking_strategies = list(config.get("chunking", {}).get("strategies", {}).keys())
selected_chunker = st.selectbox(
    "Select Chunking Strategy:", 
    ["Select Chunking Strategy"] + chunking_strategies, 
    index=0
)

if selected_chunker != "Select Chunking Strategy":
    st.sidebar.title("Current Configuration")
    st.sidebar.subheader(f"Chunker Settings ({selected_chunker.capitalize()})")
    st.sidebar.json(config["chunking"]["strategies"].get(selected_chunker, {}))

    chunker_config_values = {}

    # Display input fields based on selected chunking strategy
    if selected_chunker == "semantic_chunking":
        chunker_config_values["breakpoint_threshold_type"] = st.selectbox(
            "Breakpoint Threshold Type",
            ["fixed", "percentile"],
            index=0 if config["chunking"]["strategies"]["semantic_chunking"].get("breakpoint_threshold_type", "percentile") == "fixed" else 1
        )
        chunker_config_values["breakpoint_threshold_amount"] = st.number_input(
            "Breakpoint Threshold Amount",
            min_value=1, max_value=100,
            value=config["chunking"]["strategies"]["semantic_chunking"].get("breakpoint_threshold_amount", 80)
        )

    elif selected_chunker == "mdstructure":
        chunker_config_values["chunk_size"] = st.number_input(
            "Chunk Size",
            min_value=100, max_value=5000,
            value=config["chunking"]["strategies"]["mdstructure"].get("chunk_size", 1500)
        )

    elif selected_chunker == "recursive_chunking":
        chunker_config_values["chunk_size"] = st.number_input(
            "Chunk Size",
            min_value=100, max_value=5000,
            value=config["chunking"]["strategies"]["recursive_chunking"].get("chunk_size", 700)
        )
        chunker_config_values["chunk_overlap"] = st.number_input(
            "Chunk Overlap",
            min_value=0, max_value=500,
            value=config["chunking"]["strategies"]["recursive_chunking"].get("chunk_overlap", 100)
        )

    elif selected_chunker == "sentence_chunking":
        chunker_config_values["max_chunk_size"] = st.number_input(
            "Max Chunk Size",
            min_value=100, max_value=5000,
            value=config["chunking"]["strategies"]["sentence_chunking"].get("max_chunk_size", 1000)
        )

    # Show "Save Chunker Configuration" button only after setting values
    if chunker_config_values and st.button("Save Chunker Configuration"):
        config["chunking"]["default_strategy"] = selected_chunker
        config["chunking"]["strategies"][selected_chunker] = chunker_config_values

        save_config(config)
        st.success("✅ Chunker settings updated successfully!")
        st.session_state.chunker_config_saved = True  # Mark as saved

# Show "Run Chunking Pipeline" only after saving configuration
if st.session_state.chunker_config_saved:
    st.markdown("---")
    if st.button("🚀 Run Chunking Pipeline"):
        st.info("Executing chunking pipeline... Please wait.")
        chunk_status = run_pipeline(CHUNK_SCRIPT_PATH, CHUNK_STATUS_JSON_PATH, "chunker")

if st.session_state.chunker_status:
    st.subheader("Chunker Pipeline Execution Status")
    status_data = st.session_state.chunker_status
    summary_data = {key: value for key, value in status_data.items() if key != "EVENT_DETAILS"}
    st.json(summary_data)  # Show summary

    # Show detailed logs
    if "EVENT_DETAILS" in status_data:
        with st.expander("🔍 View Detailed Event Logs"):
            st.json(status_data["EVENT_DETAILS"])

st.markdown("---")

# Navigation buttons using Streamlit's built-in page navigation
col1, col2 = st.columns([0.5, 0.5])
with col1:
    if st.button("⬅ Back to Parsing"):
        st.switch_page("pages/2_Parsing.py")
with col2:
    if st.button("Next to Embedding ➡"):
        st.switch_page("pages/4_Embedding.py")