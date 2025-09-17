import os
from .base_config import BASE_DIR

LOG_DIR = os.getenv("LOG_DIR", os.path.join(BASE_DIR, "logs"))
LOG_FILE = os.path.join(LOG_DIR, "pipeline.log")

os.makedirs(LOG_DIR, exist_ok=True)

LOGGING_CONFIG = {
    "log_dir": LOG_DIR,
    "log_file": LOG_FILE
}
