import os
import json
import subprocess
import streamlit as st
import elevaite_ingestion as _pkg

_BASE = os.path.dirname(_pkg.__file__)

CONFIG_PATH = os.path.join(_BASE, "config.json")
EMBED_STATUS_JSON_PATH = os.path.join(_BASE, "stage/embed_stage/stage_4_status.json")
EMBED_SCRIPT_PATH = os.path.join(_BASE, "stage/embed_stage/embed_main.py")

if "embedder_status" not in st.session_state:
    st.session_state.embedder_status = None
if "embedder_config_saved" not in st.session_state:
    st.session_state.embedder_config_saved = False

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as file:
            return json.load(file)
    return {"embedding": {"providers": {}}}

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
            st.session_state.embedder_status = status
            return status
        else:
            return {"error": "Pipeline execution failed", "details": result.stderr}
    except Exception as e:
        return {"error": "Execution error", "details": str(e)}

st.set_page_config(page_title="Stage 4: Embedding", layout="wide")
st.markdown("## STAGE 4: EMBEDDING")

config = load_config()

if "embedding" not in config:
    config["embedding"] = {
        "providers": {
            "openai": {"models": {"text-embedding-ada-002": {"dimension": 1536}, "text-embedding-3-small": {"dimension": 1536}, "text-embedding-3-large": {"dimension": 3072}}},
            "cohere": {"models": {"embed-english-light-v3.0": {"dimension": 1024}, "embed-english-v3.0": {"dimension": 1024}, "embed-multilingual-v3.0": {"dimension": 1024}}},
            "local": {"models": {"all-MiniLM-L6-v2": {"dimension": 384}, "all-mpnet-base-v2": {"dimension": 768}}},
        },
        "default_provider": "openai",
        "default_model": "text-embedding-ada-002",
    }
    save_config(config)

embed_providers = list(config.get("embedding", {}).get("providers", {}).keys())
selected_provider = st.selectbox("Select Embedding Provider:", ["Select Provider"] + embed_providers, index=0)

if selected_provider != "Select Provider":
    st.sidebar.title("Current Configuration")
    st.sidebar.subheader(f"Embedder Settings ({selected_provider.capitalize()})")

    if selected_provider in config.get("embedding", {}).get("providers", {}):
        current_settings = {
            "provider": selected_provider,
            "model": config["embedding"]["default_model"] if config["embedding"].get("default_provider") == selected_provider else "Not set",
        }
        if "api_key" in config["embedding"]["providers"].get(selected_provider, {}):
            current_settings["api_key"] = "Set (hidden)" if config["embedding"]["providers"][selected_provider].get("api_key") else "Not set"
        st.sidebar.json(current_settings)

        embed_models = list(config["embedding"]["providers"][selected_provider].get("models", {}).keys())
        selected_model = st.selectbox(f"Select {selected_provider} Model:", ["Select Model"] + embed_models, index=0)

        if selected_model != "Select Model":
            api_key = ""
            if selected_provider in ["openai", "cohere"]:
                api_key = st.text_input("API Key", type="password", value=config["embedding"]["providers"][selected_provider].get("api_key", ""))

            if st.button("Save Embedder Configuration"):
                config["embedding"]["default_provider"] = selected_provider
                config["embedding"]["default_model"] = selected_model
                if api_key and selected_provider in ["openai", "cohere"]:
                    config["embedding"]["providers"].setdefault(selected_provider, {})
                    config["embedding"]["providers"][selected_provider]["api_key"] = api_key
                save_config(config)
                st.success("Embedder settings updated successfully!")
                st.session_state.embedder_config_saved = True

            st.markdown("---")
            if st.button("Run Embedder Pipeline"):
                st.info("Executing embedder pipeline... Please wait.")
                run_pipeline(EMBED_SCRIPT_PATH, EMBED_STATUS_JSON_PATH)

if st.session_state.embedder_status:
    st.subheader("Embedder Pipeline Execution Status")
    status_data = st.session_state.embedder_status
    summary_data = {key: value for key, value in status_data.items() if key != "EVENT_DETAILS"}
    st.json(summary_data)

    if "EVENT_DETAILS" in status_data:
        with st.expander("View Detailed Event Logs"):
            st.json(status_data["EVENT_DETAILS"])

st.markdown("---")

col1, col2 = st.columns([0.5, 0.5])
with col1:
    if st.button("Back to Chunking"):
        st.switch_page("pages/3_Chunking.py")
with col2:
    if st.button("Next to Vectorstore"):
        st.switch_page("pages/5_Vectorstore.py")

