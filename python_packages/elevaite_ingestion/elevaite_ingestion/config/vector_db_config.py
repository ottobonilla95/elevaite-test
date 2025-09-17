import json
import os

CONFIG_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),"config.json")

with open(CONFIG_PATH, "r") as config_file:
    config_data = json.load(config_file)

DEFAULT_VECTOR_DB_TYPE = config_data["vector_db"].get("default_db", "pinecone")

VECTOR_DB_CONFIG = {
    "vector_db": DEFAULT_VECTOR_DB_TYPE,
    "pinecone": config_data["vector_db"]["databases"].get("pinecone", {}),
    "chroma": config_data["vector_db"]["databases"].get("chroma", {}),
    "qdrant": config_data["vector_db"]["databases"].get("qdrant", {})
}

# print(f"Selected VectorDB: {VECTOR_DB_CONFIG['vector_db']}")
# print(f"Configurations: {VECTOR_DB_CONFIG[VECTOR_DB_CONFIG['vector_db']]}")

