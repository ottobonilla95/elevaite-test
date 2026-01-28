import os
import json
import time
from typing import Optional

from elevaite_ingestion.config.pipeline_config import PipelineConfig
from elevaite_ingestion.utils.logger import get_logger
from elevaite_ingestion.stage.vectorstore_stage.vectordb_pipeline import (
    execute_vector_db_stage,
)

logger = get_logger(__name__)


def execute_vector_db_pipeline(config: Optional[PipelineConfig] = None) -> dict:
    """
    Runs STAGE_5: VECTORSTORE - Stores embeddings into the vector database.

    Args:
        config: Optional PipelineConfig object. Falls back to global config if not provided.

    Returns:
        Dictionary with pipeline execution status.
    """
    logger.info("🚀 Starting STAGE_5: VECTORSTORE...")

    stage_5_status = execute_vector_db_stage(config=config)

    # ✅ Save final execution summary
    json_output = json.dumps(stage_5_status, indent=4)
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, "stage_5_status.json")
    with open(file_path, "w") as json_file:
        json_file.write(json_output)

    logger.info(f"📌 Final Pipeline Execution Summary:\n{json_output}")

    return stage_5_status


if __name__ == "__main__":
    start_time = time.time()
    execute_vector_db_pipeline()
    end_time = time.time()
    print(f"total vectorstore stage time: {end_time - start_time:.2f} seconds")
