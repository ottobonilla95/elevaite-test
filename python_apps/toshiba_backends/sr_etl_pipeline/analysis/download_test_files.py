import json
import os
import sys

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(parent_dir)

from connectors.S3Connector import S3Connector
from utils.logger import logger

def download_failed_files_for_testing():
    """Download a few failed files from S3 for testing the robust parser"""
    
    # Load config
    with open("config/settings.json") as f:
        config = json.load(f)
    
    # Load failed files list
    with open('failed_files_log.json', 'r') as f:
        failed_files = json.load(f)
    
    # Filter for CSV format errors only (these should be fixable)
    csv_errors = [f for f in failed_files if f.get('error_type') == 'CSV_FORMAT_ERROR']
    
    logger.info(f"Found {len(csv_errors)} CSV format error files")
    
    # Select a few diverse examples to test
    test_files = []
    
    # Get files with different field count mismatches
    for target_fields in [30, 32, 35, 43, 61]:  # Different complexity levels
        for failed_file in csv_errors:
            if f"saw {target_fields}" in failed_file['error']:
                test_files.append(failed_file['filename'])
                break
        if len(test_files) >= 5:  # Limit to 5 test files
            break
    
    if not test_files:
        # Fallback: just take first 5
        test_files = [f['filename'] for f in csv_errors[:5]]
    
    logger.info(f"Selected {len(test_files)} files for testing:")
    for filename in test_files:
        logger.info(f"  - {filename}")
    
    # Initialize S3 connector
    connector = S3Connector(config)
    
    # Create test directory
    test_dir = "analysis/test_files"
    os.makedirs(test_dir, exist_ok=True)
    
    # Download test files
    downloaded_files = []
    for filename in test_files:
        try:
            logger.info(f"Downloading {filename}...")
            
            # Find the file in S3
            s3_files = connector.list_files()
            s3_key = None
            
            for s3_file in s3_files:
                if s3_file['name'] == filename:
                    s3_key = s3_file['Key']
                    break
            
            if s3_key:
                # Download to test directory
                local_path = connector.download_file(s3_key, filename, "test_files")
                downloaded_files.append(local_path)
                logger.info(f"✅ Downloaded: {filename}")
            else:
                logger.warning(f"❌ File not found in S3: {filename}")
                
        except Exception as e:
            logger.error(f"❌ Failed to download {filename}: {e}")
    
    logger.info(f"\n📁 Downloaded {len(downloaded_files)} test files to {test_dir}/")
    return downloaded_files

if __name__ == "__main__":
    download_failed_files_for_testing()