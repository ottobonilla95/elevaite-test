import os
import json
import subprocess
import streamlit as st
import elevaite_ingestion as _pkg

_BASE = os.path.dirname(_pkg.__file__)

CONFIG_PATH = os.path.join(_BASE, "config.json")
PARSE_STATUS_JSON_PATH = os.path.join(_BASE, "stage/parse_stage/stage_2_status.json")
PARSE_SCRIPT_PATH = os.path.join(_BASE, "stage/parse_stage/parse_main.py")

if "parser_status" not in st.session_state:
    st.session_state.parser_status = None
if "parser_config_saved" not in st.session_state:
    st.session_state.parser_config_saved = False


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as file:
            return json.load(file)
    return {"parsing": {"default_mode": "auto_parser", "custom_parser_selection": {}, "parsers": {}}}


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
            st.session_state.parser_status = status
            return status
        else:
            return {"error": "Pipeline execution failed", "details": result.stderr}
    except Exception as e:
        return {"error": "Execution error", "details": str(e)}


st.set_page_config(page_title="Stage 2: Parsing", layout="wide")
st.markdown("## STAGE 2: PARSING")

config = load_config()

default_mode = config.get("parsing", {}).get("default_mode", "auto_parser")

st.sidebar.title("Current Configuration - Parsing")
st.sidebar.subheader(f"Parsing Mode: {default_mode.capitalize()}")
st.sidebar.json(config.get("parsing", {}))

parsing_modes = ["auto_parser", "custom_parser"]
selected_mode = st.radio("Select Parsing Mode:", parsing_modes, index=parsing_modes.index(default_mode))

if selected_mode:
    config.setdefault("parsing", {})["default_mode"] = selected_mode

    if selected_mode == "custom_parser":
        st.sidebar.subheader("Custom Parser Settings")
        parser_options = list(config.get("parsing", {}).get("parsers", {}).keys())
        selected_parser = st.selectbox("Select Parser:", ["Select Parser"] + parser_options, index=0)

        if selected_parser != "Select Parser":
            available_tools = config["parsing"]["parsers"].get(selected_parser, {}).get("available_tools", [])
            selected_tool = st.selectbox("Select Tool:", available_tools) if available_tools else None

            if st.button("Save Custom Parser Configuration"):
                config["parsing"]["custom_parser_selection"] = {"parser": selected_parser, "tool": selected_tool or None}
                save_config(config)
                st.success("Custom parser settings saved successfully!")
                st.session_state.parser_config_saved = True
                st.sidebar.json(config.get("parsing", {}))

    elif selected_mode == "auto_parser":
        if st.button("Save Auto Parser Mode"):
            save_config(config)
            st.success("Auto parser mode saved successfully!")
            st.session_state.parser_config_saved = True
            st.sidebar.json(config.get("parsing", {}))

if st.session_state.parser_config_saved:
    st.markdown("---")
    if st.button("Run Parser Pipeline"):
        st.info("Executing parser pipeline... Please wait.")
        run_pipeline(PARSE_SCRIPT_PATH, PARSE_STATUS_JSON_PATH)
        st.success("Parser pipeline executed.")

if st.session_state.parser_status:
    st.subheader("Parser Pipeline Execution Status")
    st.json({key: value for key, value in st.session_state.parser_status.items() if key != "EVENT_DETAILS"})

    stage_key = "STAGE_2: PARSING"
    if stage_key in st.session_state.parser_status and "EVENT_DETAILS" in st.session_state.parser_status[stage_key]:
        with st.expander("View Detailed Event Logs"):
            st.json(st.session_state.parser_status[stage_key]["EVENT_DETAILS"])

st.markdown("---")

col1, col2 = st.columns([0.5, 0.5])
with col1:
    if st.button("Back to Loading"):
        st.switch_page("pages/1_Loading.py")
with col2:
    if st.button("Next to Chunking"):
        st.switch_page("pages/3_Chunking.py")
