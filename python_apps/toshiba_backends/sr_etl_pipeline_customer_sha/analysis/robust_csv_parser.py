import pandas as pd
import os
import sys
from typing import Dict

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(parent_dir)

from utils.logger import logger

# Define expected schema - these are the columns we actually need
EXPECTED_COLUMNS = [
    "SR Number", "SR Customer Account Number", "SR Incident Date", "SR Closed Date",
    "SR Severity", "SR Machine Type", "SR Machine Model", "SR Machine Serial Number",
    "SR Barrier Code", "SR Country", "Column1", "SR Address Line 1", "SR Address Line 4",
    "SR City", "SR State", "SR Postal Code", "Task Number", "Task Assignee ID",
    "Task Assignee", "Task Notes External", "Task Travel Time Hours", "Task Actual Time Hours",
    "Part Number", "Part Description", "Part Quantity", "Part Unit Cost", "Part Total Cost",
    "SR Customer Problem Summary", "SR Notes", "SR Resolution Summary", 
    "CONCAT Comments (Formula)", "Comments (TEXT)"
]

def read_csv_with_flexible_parsing(file_path: str) -> pd.DataFrame:
    """
    Read CSV with flexible parsing to handle variable field counts
    """
    filename = os.path.basename(file_path)
    logger.info(f"Attempting to parse: {filename}")
    
    # Strategy 1: Try standard pandas with flexible column handling
    try:
        logger.info("  Strategy 1: Standard pandas parsing...")
        
        # First, peek at the file to understand its structure
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline().strip()
            second_line = f.readline().strip()
        
        # Count fields in header and first data row
        header_fields = len(first_line.split(','))
        data_fields = len(second_line.split(','))
        
        logger.info(f"    Header has {header_fields} fields, first data row has {data_fields} fields")
        
        # Use the maximum field count we've seen
        max_fields = max(header_fields, data_fields)
        
        # Read with flexible column names
        df = pd.read_csv(
            file_path,
            low_memory=False,
            encoding='utf-8',
            on_bad_lines='skip',  # Skip problematic lines
            engine='python'       # More flexible than C engine
        )
        
        if not df.empty:
            logger.info(f"  ✅ Strategy 1 successful: {len(df)} rows, {len(df.columns)} columns")
            return df
            
    except Exception as e:
        logger.warning(f"  ❌ Strategy 1 failed: {str(e)}")
    
    # Strategy 2: Read with no header, then assign column names
    try:
        logger.info("  Strategy 2: No header parsing...")
        
        # Read without headers to avoid field count issues
        df = pd.read_csv(
            file_path,
            header=None,
            low_memory=False,
            encoding='utf-8',
            on_bad_lines='skip',
            engine='python'
        )
        
        if df.empty:
            raise ValueError("File resulted in empty DataFrame")
        
        # Use first row as headers if it looks like headers
        first_row = df.iloc[0].astype(str)
        if any(col.startswith('SR ') or col.startswith('Task ') or col.startswith('Part ') for col in first_row):
            # First row contains headers
            df.columns = first_row
            df = df.drop(0).reset_index(drop=True)
            logger.info(f"  ✅ Strategy 2 successful: {len(df)} rows, {len(df.columns)} columns")
            return df
        else:
            # Generate generic column names
            df.columns = [f'col_{i}' for i in range(len(df.columns))]
            logger.info(f"  ✅ Strategy 2 successful: {len(df)} rows, {len(df.columns)} columns (generic headers)")
            return df
            
    except Exception as e:
        logger.warning(f"  ❌ Strategy 2 failed: {str(e)}")
    
    # Strategy 3: Line-by-line parsing with error recovery
    try:
        logger.info("  Strategy 3: Line-by-line parsing...")
        
        rows = []
        headers = None
        max_cols = 0
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f):
                try:
                    fields = line.strip().split(',')
                    max_cols = max(max_cols, len(fields))
                    
                    if line_num == 0:
                        headers = fields
                    else:
                        rows.append(fields)
                        
                except Exception as line_error:
                    logger.warning(f"    Skipping line {line_num}: {line_error}")
                    continue
        
        if not rows:
            raise ValueError("No valid data rows found")
        
        # Pad all rows to have the same number of columns
        for row in rows:
            while len(row) < max_cols:
                row.append('')
        
        # Ensure headers match max_cols
        if headers and len(headers) < max_cols:
            for i in range(len(headers), max_cols):
                headers.append(f'extra_col_{i}')
        elif not headers:
            headers = [f'col_{i}' for i in range(max_cols)]
        
        df = pd.DataFrame(rows, columns=headers)
        logger.info(f"  ✅ Strategy 3 successful: {len(df)} rows, {len(df.columns)} columns")
        return df
        
    except Exception as e:
        logger.error(f"  ❌ Strategy 3 failed: {str(e)}")
    
    # If all strategies fail
    raise ValueError(f"All CSV parsing strategies failed for {filename}")

def map_columns_to_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map DataFrame columns to expected schema, handling column variations
    """
    logger.info(f"Mapping {len(df.columns)} columns to expected schema...")
    
    # Create mapping dictionary
    column_mapping = {}
    
    # Exact matches first
    for expected_col in EXPECTED_COLUMNS:
        if expected_col in df.columns:
            column_mapping[expected_col] = expected_col
    
    # Fuzzy matching for remaining columns
    unmapped_expected = [col for col in EXPECTED_COLUMNS if col not in column_mapping]
    unmapped_actual = [col for col in df.columns if col not in column_mapping.values()]
    
    # Simple fuzzy matching rules
    for expected_col in unmapped_expected:
        for actual_col in unmapped_actual:
            # Handle common variations
            if 'SR Number' in expected_col and ('sr' in actual_col.lower() and 'number' in actual_col.lower()):
                column_mapping[actual_col] = expected_col
                unmapped_actual.remove(actual_col)
                break
            elif 'Customer Account' in expected_col and ('customer' in actual_col.lower() and 'account' in actual_col.lower()):
                column_mapping[actual_col] = expected_col
                unmapped_actual.remove(actual_col)
                break
            # Add more fuzzy matching rules as needed
    
    # Rename columns
    df_mapped = df.rename(columns=column_mapping)
    
    # Add missing columns with None values
    for expected_col in EXPECTED_COLUMNS:
        if expected_col not in df_mapped.columns:
            df_mapped[expected_col] = None
            logger.info(f"  Added missing column: {expected_col}")
    
    # Keep only expected columns (drop extra ones)
    df_final = df_mapped[EXPECTED_COLUMNS].copy()
    
    logger.info(f"✅ Column mapping complete: {len(df_final.columns)} columns")
    return df_final

def robust_csv_transform(file_path: str) -> Dict[str, pd.DataFrame]:
    """
    Main function to robustly parse and transform CSV files
    """
    logger.info(f"🔧 Processing {os.path.basename(file_path)} with robust parser...")
    
    try:
        # Step 1: Read CSV with flexible parsing
        df = read_csv_with_flexible_parsing(file_path)
        
        # Step 2: Map columns to expected schema
        df_mapped = map_columns_to_schema(df)
        
        # Step 3: Use existing transformation logic
        from etl_transformers.normalize_excel import transform_excel_to_model
        
        # Save to temp file and process with existing logic
        temp_file = f"temp_robust_{os.path.basename(file_path)}"
        df_mapped.to_csv(temp_file, index=False)
        
        try:
            # Use existing transformation
            result = transform_excel_to_model(temp_file)
            logger.info(f"✅ Successfully processed {os.path.basename(file_path)}")
            return result
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
    except Exception as e:
        logger.error(f"❌ Robust parsing failed for {os.path.basename(file_path)}: {e}")
        raise

# Test function for failed files
def test_robust_parser_on_failed_files():
    """
    Test the robust parser on downloaded test files
    """
    test_dir = "temp/test_files"  # Files are downloaded to temp/test_files
    
    if not os.path.exists(test_dir):
        logger.error(f"Test directory not found: {test_dir}")
        logger.info("Run 'python analysis/download_test_files.py' first to download test files")
        return 0, 0
    
    # Find CSV files in test directory
    test_files = []
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.csv'):
                test_files.append(os.path.join(root, file))
    
    if not test_files:
        logger.error(f"No CSV files found in {test_dir}")
        return 0, 0
    
    logger.info(f"Testing robust parser on {len(test_files)} downloaded files...")
    
    successes = 0
    failures = 0
    
    for file_path in test_files:
        filename = os.path.basename(file_path)
        logger.info(f"\n🧪 Testing: {filename}")
        
        try:
            # Just test the parsing part first
            df = read_csv_with_flexible_parsing(file_path)
            logger.info(f"✅ PARSING SUCCESS: {filename} - {len(df)} rows, {len(df.columns)} columns")
            successes += 1
            
            # Show some column info
            logger.info(f"   Columns: {list(df.columns)[:10]}{'...' if len(df.columns) > 10 else ''}")
            
        except Exception as e:
            failures += 1
            logger.error(f"❌ PARSING FAILED: {filename} - {e}")
    
    logger.info(f"\n📊 Test Results: {successes} successes, {failures} failures")
    
    return successes, failures

if __name__ == "__main__":
    # Run test on failed files
    test_robust_parser_on_failed_files()