import logging
import logging.handlers
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import threading

class ProductionMetrics:
    """Thread-safe metrics collection for production monitoring"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self.reset()
    
    def reset(self):
        with self._lock:
            self.start_time = datetime.now()
            self.files_processed = 0
            self.files_failed = 0
            self.files_skipped = 0
            self.total_rows = 0
            self.error_types = {}
            self.last_batch_time = datetime.now()
    
    def file_success(self, rows: int):
        with self._lock:
            self.files_processed += 1
            self.total_rows += rows
    
    def file_failed(self, error_type: str):
        with self._lock:
            self.files_failed += 1
            self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
    
    def file_skipped(self):
        with self._lock:
            self.files_skipped += 1
    
    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            duration = (datetime.now() - self.start_time).total_seconds()
            throughput = self.total_rows / duration if duration > 0 else 0
            
            return {
                'duration_seconds': duration,
                'files_processed': self.files_processed,
                'files_failed': self.files_failed,
                'files_skipped': self.files_skipped,
                'total_rows': self.total_rows,
                'throughput_rows_per_second': throughput,
                'error_breakdown': self.error_types.copy()
            }

class ProductionLogger:
    """Production-ready logger with structured logging and metrics"""
    
    def __init__(self, log_level: str = "INFO"):
        self.metrics = ProductionMetrics()
        self._setup_loggers(log_level)
        self._batch_counter = 0
        self._batch_size = 50  # Report progress every 50 files
    
    def _setup_loggers(self, log_level: str):
        """Setup production logging with rotation and structured output"""
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Main application logger
        self.logger = logging.getLogger('etl_pipeline')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler - only important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/etl_pipeline.log',
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        # Error-only handler
        error_handler = logging.handlers.RotatingFileHandler(
            'logs/etl_errors.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        self.logger.addHandler(error_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def pipeline_start(self, total_files: int):
        """Log pipeline start with high-level info"""
        self.metrics.reset()
        self.logger.info(f"ETL Pipeline Started - Processing {total_files} files")
    
    def file_processed(self, filename: str, rows: int, is_retry: bool = False):
        """Log successful file processing"""
        self.metrics.file_success(rows)
        self._batch_counter += 1
        
        # Only log individual files in debug mode
        retry_msg = " (retry)" if is_retry else ""
        self.logger.debug(f"Processed: {filename} - {rows:,} rows{retry_msg}")
        
        # Batch progress reporting
        if self._batch_counter % self._batch_size == 0:
            self._log_batch_progress()
    
    def file_failed(self, filename: str, error: str, error_type: str):
        """Log file failure"""
        self.metrics.file_failed(error_type)
        self.logger.error(f"FAILED: {filename} - {error_type}: {error}")
    
    def file_skipped(self, filename: str, reason: str):
        """Log skipped file"""
        self.metrics.file_skipped()
        self.logger.debug(f"Skipped: {filename} - {reason}")
    
    def _log_batch_progress(self):
        """Log batch progress summary"""
        summary = self.metrics.get_summary()
        self.logger.info(
            f"Progress: {summary['files_processed']} processed, "
            f"{summary['files_failed']} failed, "
            f"{summary['total_rows']:,} rows, "
            f"{summary['throughput_rows_per_second']:.0f} rows/sec"
        )
    
    def pipeline_complete(self):
        """Log pipeline completion with final summary"""
        summary = self.metrics.get_summary()
        
        self.logger.info("ETL Pipeline Completed")
        self.logger.info(f"Duration: {summary['duration_seconds']:.0f} seconds")
        self.logger.info(f"Files processed: {summary['files_processed']}")
        self.logger.info(f"Files failed: {summary['files_failed']}")
        self.logger.info(f"Total rows: {summary['total_rows']:,}")
        self.logger.info(f"Throughput: {summary['throughput_rows_per_second']:.0f} rows/second")
        
        if summary['error_breakdown']:
            self.logger.warning(f"Error breakdown: {summary['error_breakdown']}")
        
        # Save summary to JSON for monitoring systems
        self._save_pipeline_summary(summary)
    
    def _save_pipeline_summary(self, summary: Dict[str, Any]):
        """Save pipeline summary for monitoring"""
        summary_with_timestamp = {
            'timestamp': datetime.now().isoformat(),
            'pipeline_type': 'etl_data_processing',
            **summary
        }
        
        # Save to daily summary file
        date_str = datetime.now().strftime('%Y%m%d')
        summary_file = f'logs/pipeline_summary_{date_str}.json'
        
        # Append to daily file
        summaries = []
        if os.path.exists(summary_file):
            try:
                with open(summary_file, 'r') as f:
                    summaries = json.load(f)
            except:
                summaries = []
        
        summaries.append(summary_with_timestamp)
        
        with open(summary_file, 'w') as f:
            json.dump(summaries, f, indent=2)
    
    def database_operation(self, operation: str, details: str = ""):
        """Log database operations"""
        self.logger.info(f"Database: {operation} {details}")
    
    def s3_operation(self, operation: str, count: int = None):
        """Log S3 operations"""
        count_msg = f" ({count} objects)" if count else ""
        self.logger.info(f"S3: {operation}{count_msg}")
    
    def warning(self, message: str):
        """Log warnings"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log errors"""
        self.logger.error(message)
    
    def info(self, message: str):
        """Log info messages"""
        self.logger.info(message)
    
    def debug(self, message: str):
        """Log debug messages"""
        self.logger.debug(message)

# Global production logger instance
_production_logger = None

def get_production_logger(log_level: str = "INFO") -> ProductionLogger:
    """Get or create global production logger"""
    global _production_logger
    if _production_logger is None:
        _production_logger = ProductionLogger(log_level)
    return _production_logger

# Backward compatibility - existing code can still use 'logger'
logger = get_production_logger()

# Production usage examples:
"""
# In your main pipeline:
from utils.logger import get_production_logger

prod_logger = get_production_logger("INFO")  # "DEBUG" for development

# Pipeline lifecycle
prod_logger.pipeline_start(total_files=150)
prod_logger.s3_operation("Scanning files", 1484)
prod_logger.database_operation("Connection established")

# File processing (only logs batches, not individual files unless debug)
prod_logger.file_processed("file1.csv", 1000)
prod_logger.file_failed("file2.csv", "Parse error", "CSV_FORMAT_ERROR")

# Pipeline completion
prod_logger.pipeline_complete()

# Output:
# Console: High-level progress and summary only
# logs/etl_pipeline.log: Detailed logs with rotation
# logs/etl_errors.log: Errors only
# logs/pipeline_summary_YYYYMMDD.json: Daily summaries for monitoring
"""