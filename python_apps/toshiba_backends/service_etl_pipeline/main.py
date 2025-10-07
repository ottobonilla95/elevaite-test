import json
import os
import pickle
from datetime import datetime
from connectors.S3Connector import S3Connector
from etl_transformers.normalize_excel import transform_excel_to_model
from utils.logger import logger  
import asyncio
import asyncpg
from urllib.parse import urlparse

# Safe import for data reconciliation - won't break if module doesn't exist
try:
    from data_reconciliation_tracker import run_data_reconciliation_safe
    RECONCILIATION_AVAILABLE = True
except ImportError:
    RECONCILIATION_AVAILABLE = False
    logger.info("Data reconciliation module not available - skipping reconciliation")

def parse_connection_string_for_verification(conn_string: str) -> dict:
    """Parse connection string for verification"""
    try:
        parsed = urlparse(conn_string)
        import urllib.parse
        password = urllib.parse.unquote(parsed.password) if parsed.password else None
        
        return {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 5432,
            'user': parsed.username or 'postgres',
            'password': password,
            'database': parsed.path.lstrip('/') if parsed.path else 'postgres'
        }
    except Exception as e:
        logger.error(f"Error parsing connection string: {e}")
        raise

async def check_tables_exist(config):
    """Check if tables exist, create them if they don't"""
    try:
        db_config = parse_connection_string_for_verification(config["pg_conn_string"])
        connection = await asyncpg.connect(**db_config)
        
        # Check if service_requests table exists
        table_exists = await connection.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'service_requests'
            )
        """)
        
        await connection.close()
        return table_exists
        
    except Exception as e:
        logger.error(f"Error checking tables: {e}")
        return False

async def get_latest_file_timestamp(config):
    """Get the latest file modification timestamp from the database"""
    try:
        db_config = parse_connection_string_for_verification(config["pg_conn_string"])
        connection = await asyncpg.connect(**db_config)
        
        # Get the latest created_at timestamp (when data was inserted)
        latest_timestamp = await connection.fetchval("""
            SELECT MAX(created_at) FROM service_requests
        """)
        
        await connection.close()
        return latest_timestamp
        
    except Exception as e:
        logger.warning(f"Could not get latest timestamp: {e}")
        return None

def get_processed_files_log():
    """Load the log of processed files with their modification times"""
    log_file = "processed_files_log.pkl"
    if os.path.exists(log_file):
        try:
            with open(log_file, 'rb') as f:
                return pickle.load(f)
        except:
            logger.warning("Could not load processed files log, starting fresh")
    return {}

def save_processed_files_log(processed_files):
    """Save the log of processed files"""
    log_file = "processed_files_log.pkl"
    with open(log_file, 'wb') as f:
        pickle.dump(processed_files, f)

def get_failed_files_log():
    """Load previously failed files log"""
    failed_log_file = "failed_files_log.json"
    if os.path.exists(failed_log_file):
        try:
            with open(failed_log_file, 'r') as f:
                return json.load(f)
        except:
            logger.warning("Could not load failed files log, starting fresh")
    return []

def save_failed_files_log(failed_files):
    """Save failed files log"""
    failed_log_file = "failed_files_log.json"
    try:
        with open(failed_log_file, 'w') as f:
            json.dump(failed_files, f, indent=2)
        logger.info(f"Failed files details saved to: {failed_log_file}")
    except Exception as e:
        logger.warning(f"Could not save failed files log: {e}")

def cleanup_temp_file(file_path):
    """Safely delete a temporary file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temp file: {os.path.basename(file_path)}")
        else:
            logger.warning(f"Temp file not found for cleanup: {file_path}")
    except Exception as e:
        logger.warning(f"Could not delete temp file {file_path}: {e}")

def cleanup_temp_directory():
    """Clean up entire temp directory if it exists"""
    temp_dir = "temp"
    try:
        if os.path.exists(temp_dir):
            # Count files before cleanup
            total_files = 0
            for root, dirs, files in os.walk(temp_dir):
                total_files += len(files)
            
            # Remove all files recursively
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"Could not remove {file_path}: {e}")
                # Remove empty directories
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    try:
                        os.rmdir(dir_path)
                    except OSError:
                        pass  # Directory not empty
            
            # Remove main temp directory
            try:
                os.rmdir(temp_dir)
                logger.info(f"Cleaned up temp directory ({total_files} files removed)")
            except OSError:
                remaining_files = 0
                for root, dirs, files in os.walk(temp_dir):
                    remaining_files += len(files)
                logger.info(f"Cleaned up most temp files ({remaining_files} files remain)")
        else:
            logger.info("No temp directory to clean up")
    except Exception as e:
        logger.warning(f"Error during temp directory cleanup: {e}")

def categorize_files_for_processing(files, s3_files_info):
    """Categorize all files into different processing buckets"""
    processed_files_log = get_processed_files_log()
    previously_failed = get_failed_files_log()
    
    # Create sets for faster lookups
    failed_filenames = {f['filename'] for f in previously_failed}
    
    categorized = {
        'new_files': [],           # Never processed
        'modified_files': [],      # Modified since last processing
        'retry_failed': [],        # Previously failed files to retry
        'skipped_files': [],       # Already processed, no changes
        'missing_s3_info': []      # Files without S3 metadata
    }
    
    for file_path in files:
        filename = os.path.basename(file_path)
        
        # Find the S3 file info for this file
        s3_file_info = None
        for s3_file in s3_files_info:
            if s3_file["name"] == filename:
                s3_file_info = s3_file
                break
        
        if not s3_file_info:
            categorized['missing_s3_info'].append({
                'filename': filename,
                'file_path': file_path,
                'reason': 'Could not find S3 metadata'
            })
            continue
            
        s3_modified_time = s3_file_info["LastModified"]
        
        # Check processing history
        if filename in failed_filenames:
            # Previously failed file - retry it
            categorized['retry_failed'].append((file_path, s3_modified_time, 'Previously failed, retrying'))
        elif filename in processed_files_log:
            last_processed_time = processed_files_log[filename]
            if s3_modified_time > last_processed_time:
                categorized['modified_files'].append((file_path, s3_modified_time, 'Modified since last processing'))
            else:
                categorized['skipped_files'].append((file_path, s3_modified_time, 'Already processed, no changes'))
        else:
            # Completely new file
            categorized['new_files'].append((file_path, s3_modified_time, 'New file'))
    
    return categorized

def generate_comprehensive_report(categorized_files, processing_results):
    """Generate comprehensive report of all file statuses"""
    report = {
        'summary': {
            'total_files_in_s3': len(categorized_files['new_files']) + 
                                len(categorized_files['modified_files']) + 
                                len(categorized_files['retry_failed']) + 
                                len(categorized_files['skipped_files']) + 
                                len(categorized_files['missing_s3_info']),
            'files_processed_successfully': processing_results['successful'],
            'files_failed': processing_results['failed'],
            'files_skipped': len(categorized_files['skipped_files']),
            'files_missing_metadata': len(categorized_files['missing_s3_info'])
        },
        'file_details': {
            'successful_files': processing_results['successful_files'],
            'failed_files': processing_results['failed_files'],
            'skipped_files': [{'filename': os.path.basename(f[0]), 'reason': f[2]} for f in categorized_files['skipped_files']],
            'missing_metadata': categorized_files['missing_s3_info']
        },
        'data_quality_issues': {
            'parsing_errors': len([f for f in processing_results['failed_files'] if 'tokenizing' in f['error']]),
            'schema_errors': len([f for f in processing_results['failed_files'] if 'too long' in f['error']]),
            'other_errors': len([f for f in processing_results['failed_files'] 
                               if 'tokenizing' not in f['error'] and 'too long' not in f['error']])
        }
    }
    
    return report

async def verify_database_connection(config):
    """Verify database connection and show table info"""
    try:
        db_config = parse_connection_string_for_verification(config["pg_conn_string"])
        connection = await asyncpg.connect(**db_config)
        
        db_name = await connection.fetchval("SELECT current_database()")
        table_names = await connection.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        print(f"Connected to database: {db_name}")
        print(f"Tables found: {[row['table_name'] for row in table_names]}")
        
        for table in table_names:
            table_name = table['table_name']
            count = await connection.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            print(f"{table_name}: {count} rows")
        
        await connection.close()
        
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        raise

def main():
    """Main ETL function with comprehensive file tracking and data reconciliation"""
    logger.info("Starting Comprehensive S3 ETL Pipeline...")

    # Clean up any leftover temp files from previous runs
    logger.info("Cleaning up any existing temp files...")
    cleanup_temp_directory()

    try:
        # Load configuration
        with open("config/settings.json") as f:
            config = json.load(f)

        # Initialize S3 connector
        connector = S3Connector(config)
        
        # STEP 1: PRE-PROCESSING DATA RECONCILIATION
        pre_processing_report = None
        if RECONCILIATION_AVAILABLE:
            try:
                logger.info("STEP 1: Running pre-processing data reconciliation...")
                pre_processing_report = asyncio.run(run_data_reconciliation_safe(config, connector))
                if pre_processing_report:
                    logger.info(f"Pre-processing data coverage: {pre_processing_report['summary']['data_coverage_percentage']}%")
                else:
                    logger.warning("Pre-processing reconciliation encountered issues")
            except Exception as e:
                logger.warning(f"Pre-processing reconciliation failed: {e} - continuing with ETL")
        
        # Check if database tables exist
        tables_exist = asyncio.run(check_tables_exist(config))
        
        if not tables_exist:
            logger.info("Tables don't exist, setting up database...")
            from loaders.postgres_loader import setup_database_tables_sync
            setup_database_tables_sync(config["pg_conn_string"])
        else:
            logger.info("Database tables already exist, proceeding with incremental load...")

        # Get all files from S3 (to check modification times)
        logger.info("Checking S3 for files...")
        s3_files_info = connector.list_files()
        
        # Download all CSV/Excel files (connector will handle filtering)
        files = connector.download_excel_files(
            modified_after=None,  # Don't filter by date here, we'll handle it
            filename_pattern="",
            file_count=None  # Get all files to check modification times
        )

        if not files:
            logger.warning("No files found in S3.")
            return

        # Categorize files for comprehensive tracking
        categorized_files = categorize_files_for_processing(files, s3_files_info)
        
        # Combine all files that need processing (new, modified, and retry failed)
        files_to_process = (categorized_files['new_files'] + 
                           categorized_files['modified_files'] + 
                           categorized_files['retry_failed'])
        
        logger.info(f"File Analysis:")
        logger.info(f"  New files: {len(categorized_files['new_files'])}")
        logger.info(f"  Modified files: {len(categorized_files['modified_files'])}")
        logger.info(f"  Retrying failed files: {len(categorized_files['retry_failed'])}")
        logger.info(f"  Skipped (unchanged): {len(categorized_files['skipped_files'])}")
        logger.info(f"  Missing S3 metadata: {len(categorized_files['missing_s3_info'])}")
        logger.info(f"  Total to process: {len(files_to_process)}")
        
        if not files_to_process:
            logger.info("No files need processing!")
            # Still clean up and generate report
            for file_path in files:
                cleanup_temp_file(file_path)
            cleanup_temp_directory()
            
            # Generate and save report
            processing_results = {'successful': 0, 'failed': 0, 'successful_files': [], 'failed_files': []}
            report = generate_comprehensive_report(categorized_files, processing_results)
            save_processing_report(report)
            
            # FINAL RECONCILIATION (even if no processing)
            if RECONCILIATION_AVAILABLE:
                try:
                    logger.info("Running final data reconciliation (no processing occurred)...")
                    final_report = asyncio.run(run_data_reconciliation_safe(config, connector))
                except Exception as e:
                    logger.warning(f"Final reconciliation failed: {e}")
            return

        # Load existing logs
        processed_files_log = get_processed_files_log()
        all_failed_files = get_failed_files_log()  # Keep historical failures
        
        # Keep track of all downloaded files for cleanup
        all_downloaded_files = files.copy()
        
        # Process each file that needs processing
        successfully_processed = 0
        current_run_failures = []
        successful_files = []
        
        for file_tuple in files_to_process:
            file_path, modification_time, reason = file_tuple
            filename = os.path.basename(file_path)
            logger.info(f"Processing: {filename} ({reason})")
            
            try:
                # Transform CSV/Excel data
                cleaned_data = transform_excel_to_model(file_path)
                
                # Load to PostgreSQL (append mode)
                from loaders.postgres_loader import append_to_postgres_sync
                append_to_postgres_sync(cleaned_data, config["pg_conn_string"])
                
                # Mark file as processed successfully
                processed_files_log[filename] = modification_time
                successfully_processed += 1
                successful_files.append({
                    'filename': filename,
                    'processing_reason': reason,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Remove from failed files if it was previously failed
                all_failed_files = [f for f in all_failed_files if f['filename'] != filename]
                
                logger.info(f"Successfully processed: {filename}")

            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                
                # Add to current run failures
                failure_record = {
                    "filename": filename,
                    "error": str(e),
                    "processing_reason": reason,
                    "error_type": classify_error(str(e)),
                    "timestamp": datetime.now().isoformat(),
                    "retry_count": get_retry_count(all_failed_files, filename) + 1
                }
                current_run_failures.append(failure_record)
                
                # Update the comprehensive failed files list
                # Remove old entries for this file and add new one
                all_failed_files = [f for f in all_failed_files if f['filename'] != filename]
                all_failed_files.append(failure_record)
                
                # Continue processing other files
                continue
            finally:
                # Clean up this file immediately after processing
                cleanup_temp_file(file_path)

        # Save updated logs
        save_processed_files_log(processed_files_log)
        save_failed_files_log(all_failed_files)
        
        # Prepare processing results
        processing_results = {
            'successful': successfully_processed,
            'failed': len(current_run_failures),
            'successful_files': successful_files,
            'failed_files': current_run_failures
        }
        
        # Generate comprehensive report
        report = generate_comprehensive_report(categorized_files, processing_results)
        save_processing_report(report)
        
        # Show final results
        logger.info(f"Processing Complete!")
        logger.info(f"  Successfully processed: {successfully_processed} files")
        logger.info(f"  Failed in this run: {len(current_run_failures)} files")
        logger.info(f"  Total historical failures: {len(all_failed_files)} files")
        
        # Show current run failures
        if current_run_failures:
            logger.warning(f"Files that failed in this run:")
            for failed_file in current_run_failures:
                logger.warning(f"  - {failed_file['filename']}: {failed_file['error_type']}")
        
        # Show persistent failures (files that have failed multiple times)
        persistent_failures = [f for f in all_failed_files if f.get('retry_count', 1) > 1]
        if persistent_failures:
            logger.warning(f"Persistent failures ({len(persistent_failures)} files):")
            for failed_file in persistent_failures:
                logger.warning(f"  - {failed_file['filename']}: {failed_file['error_type']} (attempt #{failed_file['retry_count']})")
        
        # Clean up any remaining downloaded files
        logger.info("Final cleanup of remaining temp files...")
        for file_path in all_downloaded_files:
            cleanup_temp_file(file_path)
        
        # Clean up temp directory
        cleanup_temp_directory()
        
        # STEP 2: POST-PROCESSING DATA RECONCILIATION
        if RECONCILIATION_AVAILABLE:
            try:
                logger.info("STEP 2: Running post-processing data reconciliation...")
                final_report = asyncio.run(run_data_reconciliation_safe(config, connector))
                
                if final_report and pre_processing_report:
                    # Compare before and after
                    logger.info("DATA RECONCILIATION COMPARISON:")
                    pre_coverage = pre_processing_report['summary']['data_coverage_percentage']
                    post_coverage = final_report['summary']['data_coverage_percentage']
                    logger.info(f"Before Processing - Coverage: {pre_coverage}%")
                    logger.info(f"After Processing  - Coverage: {post_coverage}%")
                    
                    coverage_improvement = post_coverage - pre_coverage
                    if coverage_improvement > 0:
                        logger.info(f"Data coverage improved by: {coverage_improvement:.2f}%")
                    elif coverage_improvement == 0:
                        logger.info("Data coverage remained the same")
                    else:
                        logger.warning(f"Data coverage decreased by: {abs(coverage_improvement):.2f}%")
                
            except Exception as e:
                logger.warning(f"Post-processing reconciliation failed: {e}")
        
        # Verify database contents
        logger.info("Final database verification:")
        asyncio.run(verify_database_connection(config))

    except Exception as e:
        logger.error(f"ETL Pipeline failed: {e}")
        # Clean up temp files even on failure
        try:
            logger.info("Emergency cleanup of temp files due to error...")
            cleanup_temp_directory()
        except:
            pass  # Don't let cleanup errors mask the original error
        raise

def classify_error(error_message):
    """Classify error types for better reporting"""
    error_lower = error_message.lower()
    
    if 'tokenizing' in error_lower or 'expected' in error_lower and 'fields' in error_lower:
        return 'CSV_FORMAT_ERROR'
    elif 'too long' in error_lower:
        return 'SCHEMA_LENGTH_ERROR'
    elif 'no columns to parse' in error_lower:
        return 'EMPTY_FILE_ERROR'
    elif 'connection' in error_lower or 'timeout' in error_lower:
        return 'DATABASE_CONNECTION_ERROR'
    elif 'permission' in error_lower or 'access' in error_lower:
        return 'FILE_ACCESS_ERROR'
    else:
        return 'OTHER_ERROR'

def get_retry_count(failed_files_list, filename):
    """Get the current retry count for a file"""
    for failed_file in failed_files_list:
        if failed_file['filename'] == filename:
            return failed_file.get('retry_count', 0)
    return 0

def save_processing_report(report):
    """Save comprehensive processing report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"etl_processing_report_{timestamp}.json"
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Comprehensive processing report saved to: {report_file}")
    except Exception as e:
        logger.warning(f"Could not save processing report: {e}")

if __name__ == "__main__":
    main()