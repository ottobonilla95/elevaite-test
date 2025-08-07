import streamlit as st
import os
import sys
import json
import subprocess

path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(path)

CONFIG_PATH = os.path.join(path, "config.json")
EMBED_STATUS_JSON_PATH = os.path.join(path, "stage/embed_stage/stage_4_status.json")
EMBED_SCRIPT_PATH = os.path.join(path, "stage/embed_stage/embed_main.py")

# Initialize session states
if "embedder_status" not in st.session_state:
    st.session_state.embedder_status = None
if "embedder_config_saved" not in st.session_state:
    st.session_state.embedder_config_saved = False

def load_config():
    """Load the existing config.json file."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as file:
            return json.load(file)
    return {"embedding": {"providers": {}}}

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
            st.session_state.embedder_status = status
            return status
        else:
            return {"error": "Pipeline execution failed", "details": result.stderr}
    except Exception as e:
        return {"error": "Execution error", "details": str(e)}

# Page configuration
st.set_page_config(page_title="Stage 4: Embedding", layout="wide")
st.markdown("## STAGE 4: EMBEDDING")

config = load_config()

# Check if embedding section exists in config
if "embedding" not in config:
    config["embedding"] = {
        "providers": {
            "openai": {
                "models": {
                    "text-embedding-ada-002": {"dimension": 1536},
                    "text-embedding-3-small": {"dimension": 1536},
                    "text-embedding-3-large": {"dimension": 3072}
                }
            },
            "cohere": {
                "models": {
                    "embed-english-light-v3.0": {"dimension": 1024},
                    "embed-english-v3.0": {"dimension": 1024},
                    "embed-multilingual-v3.0": {"dimension": 1024}
                }
            },
            "local": {
                "models": {
                    "all-MiniLM-L6-v2": {"dimension": 384},
                    "all-mpnet-base-v2": {"dimension": 768}
                }
            }
        },
        "default_provider": "openai",
        "default_model": "text-embedding-ada-002"
    }
    save_config(config)

# Get embedding providers from config
embed_providers = list(config.get("embedding", {}).get("providers", {}).keys())
selected_provider = st.selectbox(
    "Select Embedding Provider:", 
    ["Select Provider"] + embed_providers, 
    index=0
)

if selected_provider != "Select Provider":
    st.sidebar.title("Current Configuration")
    st.sidebar.subheader(f"Embedder Settings ({selected_provider.capitalize()})")
    
    # Safety check for providers
    if selected_provider in config.get("embedding", {}).get("providers", {}):
        current_settings = {
            "provider": selected_provider,
            "model": config["embedding"]["default_model"] if config["embedding"].get("default_provider") == selected_provider else "Not set"
        }
        
        # Add API key info if applicable
        if "api_key" in config["embedding"]["providers"].get(selected_provider, {}):
            current_settings["api_key"] = "Set (hidden)" if config["embedding"]["providers"][selected_provider].get("api_key") else "Not set"
        
        st.sidebar.json(current_settings)

        # Get models for the selected provider
        embed_models = list(config["embedding"]["providers"][selected_provider].get("models", {}).keys())
        selected_model = st.selectbox(
            f"Select {selected_provider} Model:", 
            ["Select Model"] + embed_models, 
            index=0
        )

        if selected_model != "Select Model":
            # Show API key input field for providers that need it
            api_key = ""
            if selected_provider in ["openai", "cohere"]:  # Providers that need API keys
                api_key = st.text_input(
                    "API Key", 
                    type="password",
                    value=config["embedding"]["providers"][selected_provider].get("api_key", "")
                )

            if st.button("Save Embedder Configuration"):
                # Update config with selected provider and model
                config["embedding"]["default_provider"] = selected_provider
                config["embedding"]["default_model"] = selected_model
                
                # Update API key if provided and applicable
                if api_key and selected_provider in ["openai", "cohere"]:
                    if "api_key" not in config["embedding"]["providers"][selected_provider]:
                        config["embedding"]["providers"][selected_provider]["api_key"] = ""
                    config["embedding"]["providers"][selected_provider]["api_key"] = api_key
                
                save_config(config)
                st.success("✅ Embedder settings updated successfully!")
                st.session_state.embedder_config_saved = True

            # Show "Run Embedder Pipeline" button
            st.markdown("---")
            if st.button("🚀 Run Embedder Pipeline"):
                st.info("Executing embedder pipeline... Please wait.")
                embed_status = run_pipeline(EMBED_SCRIPT_PATH, EMBED_STATUS_JSON_PATH, "embedder")

if st.session_state.embedder_status:
    st.subheader("Embedder Pipeline Execution Status")
    status_data = st.session_state.embedder_status
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
    if st.button("⬅ Back to Chunking"):
        st.switch_page("pages/3_Chunking.py")
with col2:
    if st.button("Next to Vectorstore ➡"):
        st.switch_page("pages/5_Vectorstore.py")