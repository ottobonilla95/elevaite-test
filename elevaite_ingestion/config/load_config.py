import os
import json
from dotenv import load_dotenv
load_dotenv()

CONFIG_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "config.json")

def load_config():
    """Loads the config.json file."""
    print(f"🔍 Looking for config.json at: {CONFIG_PATH}")

    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as file:
            try:
                config = json.load(file)
                print("✅ Successfully loaded config.json")
                return config
            except json.JSONDecodeError as e:
                print(f"❌ Error decoding config.json: {e}")
                return {}
    else:
        print("❌ config.json NOT FOUND")
        return {}

config = load_config()

DEFAULT_LOADING_SOURCE = config.get("loading", {}).get("default_source", "local")

LOADING_CONFIG = {
    "default_source": DEFAULT_LOADING_SOURCE,
    "sources": config.get("loading", {}).get("sources", {})
}

