import os
import sys
path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(path)
import json
import time
from dotenv import load_dotenv
from utils.logger import get_logger
from embed_pipeline import execute_embedding_stage

load_dotenv()
logger = get_logger(__name__)

def execute_embedding_pipeline():
    """Runs STAGE_4: GET_EMBEDDING."""
    logger.info("🚀 Starting STAGE_4: GET_EMBEDDING...")
    
    stage_4_status = execute_embedding_stage()

    json_output = json.dumps(stage_4_status, indent=4)
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, "stage_4_status.json")
    with open(file_path, "w") as json_file:
        json_file.write(json_output)
    
    logger.info(f"📌 Final Pipeline Execution Summary:\n{json_output}")

if __name__ == "__main__":
    start_time = time.time()
    execute_embedding_pipeline()
    end_time = time.time()
    print(f"total embedding time: {end_time -start_time:.2f} seconds")
