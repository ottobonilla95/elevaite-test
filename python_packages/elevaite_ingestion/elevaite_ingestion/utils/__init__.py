from .logger import get_logger

# S3 utilities are optional (only import if boto3 is available)
try:
    from .s3_utils import list_s3_files, fetch_json_from_s3, save_json_to_s3

    __all__ = ["get_logger", "list_s3_files", "fetch_json_from_s3", "save_json_to_s3"]
except ImportError:
    __all__ = ["get_logger"]
