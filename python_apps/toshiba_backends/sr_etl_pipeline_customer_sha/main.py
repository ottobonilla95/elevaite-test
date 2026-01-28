 #!/usr/bin/env python3
"""
Enhanced ETL Pipeline with Production Logging
- Incremental loading (only new/modified files)
- Robust CSV parsing for all files  
- Production-ready logging with proper rotation
- No data loss (preserves existing data)
- Handles all error types gracefully
"""

import json
import os
import pickle
from datetime import datetime
from typing import Dict, List, Tuple

from connectors.S3Connector import S3Connector
from etl_transformers.normalize_excel import transform_excel_to_model
from loaders.postgres_loader import append_to_postgres_sync, ensure_tables_exist_sync
from utils.logger import get_production_logger

class FileStateManager:
    """Manages file processing state with production logging"""
    
    def __init__(self, prod_logger):
        self.logger = prod_logger
        self.processed_files = self._load_processed_files()
        self.failed_files = self._load_failed_files()
    
    def _load_processed_files(self) -> Dict:
        """Load successfully processed files with their modification times"""
        try:
            if os.path.exists('processed_files_log.pkl'):
                with open('processed_files_log.pkl', 'rb') as f:
                    data = pickle.load(f)
                    self.logger.debug(f"Loaded {len(data)} previously processed files")
                    return data
        except Exception as e:
            self.logger.warning(f"Could not load processed files log: {e}")
        return {}
    
    def _load_failed_files(self) -> List:
        """Load failed files log"""
        try:
            if os.path.exists('failed_files_log.json'):
                with open('failed_files_log.json', 'r') as f:
                    data = json.load(f)
                    self.logger.debug(f"Loaded {len(data)} previously failed files")
                    return data
        except Exception as e:
            self.logger.warning(f"Could not load failed files log: {e}")
        return []
    
    def should_process_file(self, filename: str, modification_time) -> Tuple[bool, str]:
        """Determine if file should be processed and why"""
        
        # Check if successfully processed before
        if filename in self.processed_files:
            last_processed = self.processed_files[filename]
            if modification_time <= last_processed:
                return False, "already_current"
            else:
                return True, "modified"
        
        # Check if failed before (retry failed files)
        failed_filenames = {f['filename'] for f in self.failed_files}
        if filename in failed_filenames:
            return True, "retry"
        
        # New file never attempted
        return True, "new"
    
    def mark_success(self, filename: str, modification_time, rows_inserted: int, is_retry: bool = False):
        """Mark file as successfully processed"""
        self.processed_files[filename] = modification_time
        
        # Remove from failed files if it was there
        self.failed_files = [f for f in self.failed_files if f['filename'] != filename]
        
        # Log through production logger (handles batching)
        self.logger.file_processed(filename, rows_inserted, is_retry)
    
    def mark_failed(self, filename: str, error: str, error_type: str):
        """Mark file as failed with error details"""
        # Classify retry count
        existing_failures = [f for f in self.failed_files if f['filename'] == filename]
        retry_count = len(existing_failures) + 1
        
        failure_record = {
            'filename': filename,
            'error': str(error),
            'error_type': error_type,
            'retry_count': retry_count,
            'timestamp': datetime.now().isoformat()
        }
        
        # Remove old failures for this file
        self.failed_files = [f for f in self.failed_files if f['filename'] != filename]
        self.failed_files.append(failure_record)
        
        # Log through production logger
        self.logger.file_failed(filename, error, error_type)
    
    def mark_skipped(self, filename: str, reason: str):
        """Mark file as skipped"""
        self.logger.file_skipped(filename, reason)
    
    def save_state(self):
        """Save all file state to disk"""
        try:
            # Save processed files
            with open('processed_files_log.pkl', 'wb') as f:
                pickle.dump(self.processed_files, f)
            
            # Save failed files
            with open('failed_files_log.json', 'w') as f:
                json.dump(self.failed_files, f, indent=2)
            
            self.logger.debug("File state saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

def classify_error(error_message: str) -> str:
    """Classify error types for better handling and reporting"""
    error_lower = error_message.lower()
    
    if 'tokenizing' in error_lower or 'expected' in error_lower and 'fields' in error_lower:
        return 'CSV_FORMAT_ERROR'
    elif 'too long' in error_lower or 'character varying' in error_lower:
        return 'SCHEMA_LENGTH_ERROR'
    elif 'no columns to parse' in error_lower or 'empty' in error_lower:
        return 'EMPTY_FILE_ERROR'
    elif 'connection' in error_lower or 'timeout' in error_lower:
        return 'DATABASE_CONNECTION_ERROR'
    elif 'permission' in error_lower or 'access' in error_lower:
        return 'FILE_ACCESS_ERROR'
    elif 'critical columns missing' in error_lower:
        return 'MISSING_REQUIRED_COLUMNS'
    else:
        return 'OTHER_ERROR'

def process_single_file(file_info: Dict, connector: S3Connector, config: Dict) -> Tuple[bool, str, int]:
    """
    Process a single file with robust error handling
    Returns: (success, error_message, rows_inserted)
    """
    filename = file_info['name']
    s3_key = file_info['Key']
    local_path = None
    
    try:
        # Download file
        local_path = connector.download_file(s3_key, filename)
        
        # Transform data using enhanced parser
        cleaned_data = transform_excel_to_model(local_path)
        
        # Count total rows for reporting
        total_rows = sum(len(df) for df in cleaned_data.values() if not df.empty)
        
        # Load to database incrementally
        append_to_postgres_sync(cleaned_data, config["pg_conn_string"])
        
        return True, "", total_rows
        
    except Exception as e:
        error_msg = str(e)
        return False, error_msg, 0
        
    finally:
        # Always clean up downloaded file
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except:
                pass

def categorize_s3_files(s3_files: List[Dict], state_manager: FileStateManager) -> Dict[str, List]:
    """Categorize S3 files by processing status"""
    categories = {
        'new_files': [],
        'modified_files': [],
        'retry_failed': [],
        'already_current': []
    }
    
    for s3_file in s3_files:
        filename = s3_file['name']
        
        # Only process CSV and Excel files
        if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
            continue
            
        should_process, reason = state_manager.should_process_file(filename, s3_file['LastModified'])
        
        if not should_process:
            categories['already_current'].append(s3_file)
            state_manager.mark_skipped(filename, reason)
        elif reason == "new":
            categories['new_files'].append(s3_file)
        elif reason == "modified":
            categories['modified_files'].append(s3_file)
        elif reason == "retry":
            categories['retry_failed'].append(s3_file)
    
    return categories

def main():
    """Main ETL pipeline with production logging"""
    
    # Initialize production logger
    prod_logger = get_production_logger("INFO")  # Change to "DEBUG" for development
    
    try:
        # Load configuration
        with open("config/settings.json") as f:
            config = json.load(f)
        
        # Initialize components
        connector = S3Connector(config)
        state_manager = FileStateManager(prod_logger)
        
        # Ensure database tables exist
        prod_logger.database_operation("Ensuring tables exist")
        ensure_tables_exist_sync(config["pg_conn_string"])

        
        # Get all files from S3
        prod_logger.s3_operation("Scanning files")
        s3_files = connector.list_files()
        prod_logger.s3_operation("Scan complete", len(s3_files))
        
        # Categorize files by processing status
        categories = categorize_s3_files(s3_files, state_manager)
        
        # Calculate total work
        files_to_process = (categories['new_files'] + 
                           categories['modified_files'] + 
                           categories['retry_failed'])
        
        # Start pipeline
        prod_logger.pipeline_start(len(files_to_process))
        
        if not files_to_process:
            prod_logger.info("No files need processing")
            prod_logger.pipeline_complete()
            return
        
        # Log processing plan
        prod_logger.info(f"Processing plan: {len(categories['new_files'])} new, "
                        f"{len(categories['modified_files'])} modified, "
                        f"{len(categories['retry_failed'])} retry, "
                        f"{len(categories['already_current'])} current")
        
        # Process files in priority order
        all_processing_files = [
            ("NEW", categories['new_files']),
            ("MODIFIED", categories['modified_files']), 
            ("RETRY", categories['retry_failed'])
        ]
        
        for batch_name, file_list in all_processing_files:
            if not file_list:
                continue
                
            prod_logger.info(f"Processing {batch_name} files: {len(file_list)}")
            
            for file_info in file_list[:1]:
                filename = file_info['name']
                is_retry = batch_name == "RETRY"
                
                # Process the file
                success, error_msg, rows_inserted = process_single_file(file_info, connector, config)
                return

                
                if success:
                    state_manager.mark_success(filename, file_info['LastModified'], rows_inserted, is_retry)
                else:
                    error_type = classify_error(error_msg)
                    state_manager.mark_failed(filename, error_msg, error_type)
        
        # Final state save and completion
        state_manager.save_state()
        prod_logger.pipeline_complete()
        
    except Exception as e:
        prod_logger.error(f"Pipeline failed: {e}")
        try:
            if 'state_manager' in locals():
                state_manager.save_state()
        except:
            pass
        raise
    
    # finally:
        # Clean up temp files
        # try:
        #     temp_dir = "temp"
        #     if os.path.exists(temp_dir):
        #         for root, dirs, files in os.walk(temp_dir):
        #             for file in files:
        #                 try:
        #                     os.remove(os.path.join(root, file))
        #                 except:
        #                     pass
        # except:
        #     pass

if __name__ == "__main__":
    main()