import os
import json
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.getenv("INPUT_DIR", os.path.join(BASE_DIR, "input_data"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(BASE_DIR, "output_data"))

SUPPORTED_FORMATS = ["docx", "xlsx", "html", "pdf"]

# Logging settings
LOG_DIR = os.getenv("LOG_DIR", os.path.join(BASE_DIR, "logs"))
LOG_FILE = os.path.join(LOG_DIR, "pipeline.log")

DEFAULT_TOOL = "markitdown"
TOOL_CHOICES = ["markitdown", "docling", "llamaparse"]

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

# Ensure `config.json` exists before loading
if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"❌ config.json not found at {CONFIG_PATH}")

# Load JSON configuration
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

# Ensure essential keys exist
CONFIG.setdefault("data_source", "s3")
CONFIG.setdefault(
    "aws", {"input_bucket": "kb-check-pdf", "intermediate_bucket": "kb-check-docs"}
)
CONFIG.setdefault(
    "local",
    {"input_directory": "data/raw", "output_parsed_directory": "data/processed"},
)
CONFIG.setdefault("parsing", {"default_mode": "auto_parser"})
CONFIG.setdefault("vector_db", {})

# Directories setup
os.makedirs(CONFIG["local"]["input_directory"], exist_ok=True)
os.makedirs(CONFIG["local"]["output_parsed_directory"], exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
