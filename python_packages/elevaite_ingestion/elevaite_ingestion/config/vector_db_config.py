import json
import os

CONFIG_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "config.json"
)

with open(CONFIG_PATH, "r") as config_file:
    config_data = json.load(config_file)

# Be resilient if config.json lacks a vector_db section
vector_db_section = config_data.get("vector_db", {}) or {}
databases = vector_db_section.get("databases", {}) or {}
DEFAULT_VECTOR_DB_TYPE = vector_db_section.get("default_db", "pinecone")

VECTOR_DB_CONFIG = {
    "vector_db": DEFAULT_VECTOR_DB_TYPE,
    "pinecone": databases.get("pinecone", {}),
    "chroma": databases.get("chroma", {}),
    "qdrant": databases.get("qdrant", {}),
}

# print(f"Selected VectorDB: {VECTOR_DB_CONFIG['vector_db']}")
# print(f"Configurations: {VECTOR_DB_CONFIG[VECTOR_DB_CONFIG['vector_db']]}")
