import pandas as pd
import os
from utils.logger import logger

# Define CRITICAL columns that must exist (will reject CSV if missing)
CRITICAL_COLUMNS = {
    "service_requests": ["SR Number"],  # Absolute minimum - primary key
    "customers": ["SR Customer Account Number"],  # Customer link
    "tasks": ["SR Number"],  # Link back to service request
    "parts_used": ["Task Number"],  # Link to task
    "sr_notes": ["SR Number"]  # Link to service request
}

# Define the FULL expected schema (nice-to-have columns)
FULL_SCHEMA = {
    "service_requests": [
        "SR Number", "SR Customer Account Number", "SR Address Line 1", "SR City", 
        "SR State", "SR Postal Code", "SR Incident Date", "SR Closed Date",
        "SR Severity", "SR Machine Type", "SR Machine Model", "SR Machine Serial Number",
        "SR Barrier Code", "SR Country"
    ],
    "customers": [
        "SR Customer Account Number", "SR Customer Name", "SR Address Line 4", "SR Country"
    ],
    "tasks": [
        "Task Number", "SR Number", "Task Assignee ID", "Task Assignee", "Task Notes External",
        "Task Travel Time Hours", "Task Actual Time Hours"
    ],
    "parts_used": [
        "Task Number", "Part Number", "Part Description", "Part Quantity", "Part Unit Cost", "Part Total Cost"
    ],
    "sr_notes": [
        "SR Number", "SR Customer Problem Summary", "SR Notes",
        "SR Resolution Summary", "CONCAT Comments (Formula)", "Comments (TEXT)"
    ]
}

def clean_numeric_strings(df, columns):
    """
    Remove .0 from string columns that look like '12345.0'
    This fixes the issue where SR Numbers like '2215208' become '2215208.0'
    """
    for col in columns:
        if col in df.columns:
            # Convert to string and remove trailing .0
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True)
            # Also handle 'nan' strings
            df[col] = df[col].replace('nan', None)
    return df

def read_csv_robust(file_path):
    """Enhanced robust CSV reading that handles variable field counts"""
    filename = os.path.basename(file_path)
    
    # Strategy 1: Standard parsing
    try:
        logger.info(f"Trying standard CSV parsing for {filename}")
        df = pd.read_csv(file_path, low_memory=False)
        if not df.empty:
            logger.info(f"Standard parsing successful for {filename}")
            return df
    except Exception as e:
        logger.warning(f"Standard parsing failed for {filename}: {str(e)}")
    
    # Strategy 2: Skip bad lines with python engine (FIXED)
    try:
        logger.info(f"Trying robust parsing (skip bad lines) for {filename}")
        df = pd.read_csv(file_path, 
                        engine='python', 
                        on_bad_lines='skip')  # Removed low_memory for python engine
        if not df.empty:
            logger.info(f"Robust parsing successful for {filename}")
            return df
    except Exception as e:
        logger.warning(f"Robust parsing failed for {filename}: {str(e)}")
    
    # Strategy 3: Line-by-line parsing with dynamic field count handling
    try:
        logger.info(f"Trying line-by-line parsing for {filename}")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            raise ValueError("File has insufficient data")
        
        # Parse header and determine expected columns
        header_line = lines[0].strip()
        headers = [col.strip('"') for col in header_line.split(',')]
        expected_cols = len(headers)
        
        logger.info(f"Header has {expected_cols} columns: {headers[:5]}...")
        
        # Parse data rows with field count adaptation
        data_rows = []
        field_count_issues = 0
        
        for line_num, line in enumerate(lines[1:], 2):
            try:
                # Split and clean fields
                fields = [field.strip().strip('"') for field in line.strip().split(',')]
                
                # Handle variable field counts
                if len(fields) != expected_cols:
                    field_count_issues += 1
                    
                    if len(fields) > expected_cols:
                        # Too many fields - truncate extra ones
                        fields = fields[:expected_cols]
                    else:
                        # Too few fields - pad with empty strings
                        while len(fields) < expected_cols:
                            fields.append('')
                
                data_rows.append(fields)
                
            except Exception as line_error:
                logger.warning(f"Skipping line {line_num}: {line_error}")
                continue
        
        if field_count_issues > 0:
            logger.info(f"Handled {field_count_issues} lines with field count mismatches")
        
        if not data_rows:
            raise ValueError("No valid data rows found")
        
        df = pd.DataFrame(data_rows, columns=headers)
        logger.info(f"Line-by-line parsing successful: {len(df)} rows, {len(df.columns)} columns")
        return df
            
    except Exception as e:
        logger.warning(f"Line-by-line parsing failed for {filename}: {str(e)}")
    
    # Strategy 4: Maximum columns approach (IMPROVED)
    try:
        logger.info(f"Trying max columns approach for {filename}")
        
        # Scan file to find maximum number of columns
        max_cols = 0
        header_cols = 0
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
            if lines:
                # Count header columns
                header_cols = len(lines[0].split(','))
                
                # Scan first 1000 lines for max columns
                for line_num, line in enumerate(lines[:1000]):
                    cols = len(line.split(','))
                    max_cols = max(max_cols, cols)
        
        logger.info(f"Header: {header_cols} cols, Max found: {max_cols} cols")
        
        # Use the larger of header or max found
        col_count = max(header_cols, max_cols)
        
        # Try reading with pandas using max columns
        df = pd.read_csv(file_path, 
                        engine='python',
                        on_bad_lines='skip',
                        names=range(col_count),  # Use numeric column names
                        header=0)
        
        if not df.empty:
            # Rename columns to use original headers where available
            if lines:
                original_headers = [col.strip().strip('"') for col in lines[0].split(',')]
                
                # Create final column names
                final_columns = []
                for i in range(col_count):
                    if i < len(original_headers):
                        final_columns.append(original_headers[i])
                    else:
                        final_columns.append(f"extra_col_{i}")
                
                df.columns = final_columns
            
            logger.info(f"Max columns approach successful: {len(df)} rows, {len(df.columns)} columns")
            return df
            
    except Exception as e:
        logger.warning(f"Max columns approach failed for {filename}: {str(e)}")
    
    raise ValueError(f"All CSV parsing strategies failed for {file_path}")

def validate_critical_columns(df: pd.DataFrame, table_name: str) -> tuple[bool, list]:
    """
    Check if critical columns exist. Only reject CSV if these are missing.
    Returns: (is_valid, missing_critical_columns)
    """
    critical_cols = CRITICAL_COLUMNS.get(table_name, [])
    missing_critical = [col for col in critical_cols if col not in df.columns]
    
    if missing_critical:
        return False, missing_critical
    return True, []

def fill_missing_columns_relaxed(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """
    Fill missing columns, but only add columns that exist in the CSV or are critical.
    This prevents creating tons of empty columns.
    """
    full_schema = FULL_SCHEMA.get(table_name, [])
    
    # Only include columns that either:
    # 1. Already exist in the CSV, OR  
    # 2. Are critical columns (fill with None if missing)
    columns_to_include = []
    
    for col in full_schema:
        if col in df.columns:
            columns_to_include.append(col)
        elif col in CRITICAL_COLUMNS.get(table_name, []):
            # Critical column missing - fill with None but keep it
            df[col] = None
            columns_to_include.append(col)
            logger.warning(f"Critical column '{col}' missing in {table_name}, filled with None")
    
    return df[columns_to_include] if columns_to_include else df

def truncate_long_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Truncate fields that are too long for database schema - works with original CSV column names"""
    
    # Map original CSV column names to their ACTUAL database length limits
    field_limits = {
        # These are the fields causing varchar(100) errors - set to 99 to be safe
        'SR Machine Type': 99,
        'SR Machine Model': 99,
        'SR Machine Serial Number': 99,
        'SR Barrier Code': 99,
        'Part Number': 99,
        'SR City': 99,
        'SR State': 99,              # Changed from 50 to 99
        'SR Country': 99,            # Changed from 100 to 99
        'SR Postal Code': 99,        # Add this - it's likely causing errors too
        'Task Assignee ID': 99,      # Add this - it's likely causing errors too
        
        # Longer text fields (these are probably TEXT or larger VARCHAR)
        'SR Notes': 1000,
        'SR Resolution Summary': 1000,
        'SR Customer Problem Summary': 1000,
        'Task Notes External': 500,
        'Part Description': 500,
        'Comments (TEXT)': 1000,
        'CONCAT Comments (Formula)': 1000,
        'Task Assignee': 200,
        'SR Customer Name': 200,  # Fixed: was 'Column1', now correct column name
        'SR Address Line 1': 200,
        'SR Address Line 4': 200
    }
    
    for column, max_length in field_limits.items():
        if column in df.columns:
            # Convert to string, handle NaN values, and truncate
            df[column] = df[column].astype(str).apply(
                lambda x: x[:max_length] if x != 'nan' and len(str(x)) > max_length else x
            )
            truncated_count = df[df[column].str.len() == max_length].shape[0]
            if truncated_count > 0:
                logger.warning(f"Truncated {truncated_count} values in column '{column}' to {max_length} characters")
    
    return df

def transform_excel_to_model(file_path):
    """
    Enhanced version that handles malformed CSVs and field count mismatches
    """
    # Check file extension and read accordingly
    try:
        if file_path.endswith('.csv'):
            df = read_csv_robust(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, engine="openpyxl")
        elif file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
    except Exception as e:
        raise ValueError(f"Could not read file {file_path}: {str(e)}")
    
    # Check if file is completely empty
    if df.empty:
        raise ValueError("CSV file is empty - no data to process")
    
    df = clean_numeric_strings(df, ['SR Number', 'Task Number', 'SR Customer Account Number'])

    logger.info(f"Processing file with {len(df)} rows and {len(df.columns)} columns")
    logger.info(f"Columns found: {list(df.columns)[:10]}{'...' if len(df.columns) > 10 else ''}")
    
    # Validate critical columns for service_requests (main entity)
    is_valid, missing_critical = validate_critical_columns(df, "service_requests")
    if not is_valid:
        raise ValueError(f"CRITICAL COLUMNS MISSING for service_requests: {missing_critical}. Cannot process this CSV.")
    
    # Log what columns we found vs expected
    for table_name, expected_cols in FULL_SCHEMA.items():
        present_cols = [col for col in expected_cols if col in df.columns]
        missing_cols = [col for col in expected_cols if col not in df.columns]
        
        if missing_cols:
            critical_missing = [col for col in missing_cols if col in CRITICAL_COLUMNS.get(table_name, [])]
            optional_missing = [col for col in missing_cols if col not in CRITICAL_COLUMNS.get(table_name, [])]
            
            if critical_missing:
                logger.warning(f"{table_name}: Missing CRITICAL columns: {critical_missing}")
            if optional_missing:
                logger.info(f"{table_name}: Missing optional columns: {optional_missing}")
    
    # Process each table with relaxed validation
    try:
        # Process and truncate long fields
        service_requests_df = fill_missing_columns_relaxed(df.copy(), "service_requests")
        service_requests_df = truncate_long_fields(service_requests_df)
        
        customers_df = fill_missing_columns_relaxed(df.copy(), "customers")
        customers_df = truncate_long_fields(customers_df)
        
        tasks_df = fill_missing_columns_relaxed(df.copy(), "tasks")
        tasks_df = truncate_long_fields(tasks_df)
        
        parts_used_df = fill_missing_columns_relaxed(df.copy(), "parts_used")
        parts_used_df = truncate_long_fields(parts_used_df)
        
        sr_notes_df = fill_missing_columns_relaxed(df.copy(), "sr_notes")
        sr_notes_df = truncate_long_fields(sr_notes_df)
        
        data = {
        "service_requests": service_requests_df.rename(columns={
        "SR Number": "sr_number",
        "SR Customer Account Number": "customer_account_number",
        "SR Address Line 1": "service_address",
        "SR City": "service_city",
        "SR State": "service_state",
        "SR Postal Code": "service_postal_code",
        "SR Incident Date": "incident_date",
        "SR Closed Date": "closed_date",
        "SR Severity": "severity",
        "SR Machine Type": "machine_type",
        "SR Machine Model": "machine_model", 
        "SR Machine Serial Number": "machine_serial_number",
        "SR Barrier Code": "barrier_code",
        "SR Country": "country"
    }).drop_duplicates(subset=['sr_number']),  # ADD THIS LINE
            
            "customers": customers_df.rename(columns={
                "SR Customer Account Number": "customer_account_number",
                "SR Customer Name": "customer_name",
                "SR Address Line 4": "address_line2",  # Corporate address only
                "SR Country": "country"
            }).drop_duplicates(),
            
            "tasks": tasks_df.rename(columns={
                "Task Number": "task_number",
                "SR Number": "sr_number",
                "Task Assignee ID": "task_assignee_id",
                "Task Assignee": "assignee_name", 
                "Task Notes External": "task_notes",
                "Task Travel Time Hours": "travel_time_hours",
                "Task Actual Time Hours": "actual_time_hours"
            }),
            
            "parts_used": parts_used_df.rename(columns={
                "Task Number": "task_number",
                "Part Number": "part_number", 
                "Part Description": "description",
                "Part Quantity": "quantity",
                "Part Unit Cost": "unit_cost",
                "Part Total Cost": "total_cost"
            }),
            
            "sr_notes": sr_notes_df.rename(columns={
                "SR Number": "sr_number",
                "SR Customer Problem Summary": "customer_problem_summary",
                "SR Notes": "sr_notes",
                "SR Resolution Summary": "resolution_summary", 
                "CONCAT Comments (Formula)": "concat_comments",
                "Comments (TEXT)": "comments"
            })
        }
        
        # Log successful processing stats
        for table_name, table_df in data.items():
            if not table_df.empty:
                logger.info(f"SUCCESS {table_name}: {len(table_df)} rows processed")
        
        return data
        
    except Exception as e:
        logger.error(f"Error during data transformation: {str(e)}")
        raise