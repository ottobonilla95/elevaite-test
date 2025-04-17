import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CHUNKER = os.getenv("CHUNKING_STRATEGY", "semantic_chunking")

CHUNKER_CONFIG = {
    "chunk_strategy": DEFAULT_CHUNKER,
    "available_chunkers": {
        "semantic_chunking": {
            "import_path": "chunk_strategy.custom_chunking.semantic_chunk_v1",
            "function_name": "chunk_text",
            "settings": {
                "breakpoint_threshold_type": "percentile",
                "breakpoint_threshold_amount": 90
            }
        },
        "mdstructure": {
            "import_path": "chunk_strategy.custom_chunking.mdstructure",
            "function_name": "chunk_text",
            "settings": {
                "chunk_size": 2000
            }
        },
        "recursive_chunking": {
            "import_path": "chunk_strategy.standard_chunking.recursive_chunking",
            "function_name": "chunk_text",
            "settings": {
                "chunk_size": 500,
                "chunk_overlap": 50
            }
        },
        "sentence_chunking": {
            "import_path": "chunk_strategy.custom_chunking.sentence_chunking",
            "function_name": "chunk_text",
            "settings": {
                "max_chunk_size": 500
            }
        }
    }
}
