import os
import json
from dotenv import load_dotenv

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")

load_dotenv()

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

def save_config(updated_config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        json.dump(updated_config, file, indent=4)

config = load_config()

PARSING_MODE = config.get("parsing", {}).get("default_mode", "auto_parser")
DEFAULT_PARSER = config.get("parsing", {}).get("default_parser", "pdf")

if PARSING_MODE == "auto_parser":
    DEFAULT_TOOL = config.get("parsing", {}).get("parsers", {}).get(DEFAULT_PARSER, {}).get("default_tool")
    CUSTOM_PARSER_SELECTION = {} 
else: 
    CUSTOM_PARSER_SELECTION = config.get("parsing", {}).get("custom_parser_selection", {})
    DEFAULT_TOOL = CUSTOM_PARSER_SELECTION.get("tool", "markitdown")

if DEFAULT_TOOL is None and DEFAULT_PARSER != "pdf":
    DEFAULT_TOOL = "markitdown"

PARSER_CONFIG = {
    "parsing_mode": PARSING_MODE,
    "default_parser": DEFAULT_PARSER,
    "default_tool": DEFAULT_TOOL,
    "custom_parser_selection": CUSTOM_PARSER_SELECTION,
    "parsers": config.get("parsing", {}).get("parsers", {}),
}


if "parsing" not in config:
    config["parsing"] = PARSER_CONFIG
    save_config(config)

print("DEBUG: Loaded PARSER_CONFIG:", json.dumps(PARSER_CONFIG, indent=4))
