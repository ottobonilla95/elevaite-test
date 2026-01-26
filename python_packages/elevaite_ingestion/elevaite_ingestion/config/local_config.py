import os
from .base_config import BASE_DIR

INPUT_DIR = os.getenv("INPUT_DIR", os.path.join(BASE_DIR, "input_data"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(BASE_DIR, "output_data"))

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

LOCAL_CONFIG = {
    "input_directory": "data/raw",
    "output_parsed_directory": "data/processed",
}
