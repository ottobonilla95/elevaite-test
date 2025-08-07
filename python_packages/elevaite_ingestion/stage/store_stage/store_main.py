import os
import sys
path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(path)
import json
import time
from dotenv import load_dotenv
from utils.logger import get_logger
from store_pipeline import execute_store_stage

load_dotenv()
logger = get_logger(__name__)

def execute_store_pipeline():
    """Runs STAGE_5: STORE_VECTORS."""
    logger.info("🚀 Starting STAGE_5: STORE_VECTORS...")
    
    stage_5_status = execute_store_stage()

    json_output = json.dumps(stage_5_status, indent=4)
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, "stage_5_status.json")
    with open(file_path, "w") as json_file:
        json_file.write(json_output)
    
    logger.info(f"📌 Final Pipeline Execution Summary:\n{json_output}")
    
    return stage_5_status

if __name__ == "__main__":
    start_time = time.time()
    result = execute_store_pipeline()
    end_time = time.time()
    print(f"total store time: {end_time - start_time:.2f} seconds")
    
    # Exit with appropriate code based on result
    if result.get("STAGE_5: STORE_VECTORS", {}).get("STATUS") == "Completed":
        sys.exit(0)
    else:
        sys.exit(1)
