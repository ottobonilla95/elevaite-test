import asyncio
import asyncpg
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from datetime import datetime
from dateutil import parser as date_parser
from utils.logger import logger  # Use your existing logger

# Define tables with natural primary keys (same as your original)
CONFLICT_KEYS = {
    "service_requests": "sr_number",
    "customers": "customer_account_number",
    "tasks": "task_number"
    # parts_used and sr_notes use SERIAL ids – no ON CONFLICT
}

def clean_dataframe(df):
    """Remove rows missing primary key and convert NaNs to None for asyncpg"""
    # Remove rows where the first column (primary key) is missing
    df = df.dropna(subset=[df.columns[0]])
    
    # Replace NaN values with None for PostgreSQL compatibility
    df = df.replace({np.nan: None})
    
    # Also handle other NaN-like values
    df = df.replace({'NaN': None, '': None, 'nan': None})
    
    return df

def convert_datetime_strings(value):
    """Convert string dates to datetime objects for AsyncPG"""
    if value is None or pd.isna(value):
        return None
    
    if isinstance(value, str):
        # Try to parse datetime strings
        try:
            # Common datetime formats in your data
            if value.strip() == '' or value.strip().lower() in ['nan', 'none', 'null']:
                return None
            
            # Parse the datetime string
            parsed_date = date_parser.parse(value)
            return parsed_date
        except (ValueError, TypeError, date_parser.ParserError):
            # If it's not a valid datetime string, return None
            return None
    
    elif isinstance(value, (datetime, pd.Timestamp)):
        # Already a datetime object
        return value
    
    else:
        # For other types, return None
        return None

def clean_value_for_asyncpg(key: str, value) -> Any:
    """Clean individual values for AsyncPG insertion"""
    # Handle None/NaN values
    if value is None or pd.isna(value):
        return None
    
    # Handle empty strings
    if isinstance(value, str) and value.strip() == '':
        return None
    
    # Handle datetime columns (based on column names)
    datetime_columns = ['incident_date', 'closed_date', 'created_at', 'updated_at']
    if any(col in key.lower() for col in datetime_columns):
        return convert_datetime_strings(value)
    
    # Handle integer columns (quantity should be integer)
    integer_columns = ['quantity']
    if any(col in key.lower() for col in integer_columns):
        try:
            if isinstance(value, str):
                # Handle string numbers like '2.0' -> 2
                if value.strip() == '' or value.strip().lower() in ['nan', 'none', 'null']:
                    return None
                # Convert float string to int
                float_val = float(value.strip())
                return int(float_val) if not np.isnan(float_val) else None
            elif isinstance(value, (np.integer, np.floating)):
                return int(value) if np.isfinite(value) else None
            elif isinstance(value, float):
                return int(value) if not np.isnan(value) and np.isfinite(value) else None
            else:
                return None
        except (ValueError, TypeError):
            logger.warning(f"Could not convert {key} value '{value}' to integer, setting to None")
            return None
    
    # Handle decimal/float columns (costs, hours)
    decimal_columns = ['unit_cost', 'total_cost', 'travel_time_hours', 'actual_time_hours']
    if any(col in key.lower() for col in decimal_columns):
        try:
            if isinstance(value, str):
                if value.strip() == '' or value.strip().lower() in ['nan', 'none', 'null']:
                    return None
                return float(value.strip())
            elif isinstance(value, (np.integer, np.floating)):
                return float(value) if np.isfinite(value) else None
            elif isinstance(value, (int, float)):
                return float(value) if not (isinstance(value, float) and np.isnan(value)) else None
            else:
                return None
        except (ValueError, TypeError):
            logger.warning(f"Could not convert {key} value '{value}' to decimal, setting to None")
            return None
    
    # Handle other numeric values
    if isinstance(value, (np.integer, np.floating)):
        if np.isfinite(value):
            # Convert to Python native types
            if isinstance(value, np.integer):
                return int(value)
            else:
                return float(value)
        else:
            return None
    
    # Handle string values
    if isinstance(value, str):
        # Clean up string values
        cleaned = value.strip()
        if cleaned.lower() in ['nan', 'none', 'null', '']:
            return None
        
        # Return full string without truncation - PostgreSQL TEXT fields can handle any length
        return cleaned
    
    # For other types, convert to string or return None
    try:
        result = str(value) if value is not None else None
        # Return full string without length restrictions
        return result
    except:
        return None

def parse_connection_string(conn_string: str) -> Dict[str, Any]:
    """Parse PostgreSQL connection string into components"""
    try:
        parsed = urlparse(conn_string)
        
        # Handle URL encoded passwords (like %40 for @, %24 for $)
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
        logger.error(f"❌ Error parsing connection string: {e}")
        raise

async def drop_and_create_tables(connection):
    """Drop existing tables and create fresh ones - ensures clean deployment"""
    
    # Order matters due to foreign key constraints - drop in reverse order
    drop_order = [
        "sr_notes",
        "parts_used", 
        "tasks",
        "customers",
        "service_requests"
    ]
    
    logger.info("🗑️ Dropping existing tables for clean deployment...")
    
    try:
        # Drop tables in correct order (reverse dependency order)
        for table_name in drop_order:
            await connection.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            logger.info(f"🗑️ Dropped table: {table_name}")
        
        logger.info("✅ All existing tables dropped successfully")
        
    except Exception as e:
        logger.error(f"❌ Error dropping tables: {e}")
        raise
    
    # Now create fresh tables
    table_schemas = {
        "service_requests": """
            CREATE TABLE service_requests (
                id SERIAL PRIMARY KEY,
                sr_number VARCHAR(255) UNIQUE NOT NULL,
                customer_account_number VARCHAR(255),
                incident_date TIMESTAMP,
                closed_date TIMESTAMP,
                severity VARCHAR(100),
                machine_type VARCHAR(255),
                machine_model VARCHAR(255),
                machine_serial_number VARCHAR(255),
                barrier_code VARCHAR(100),
                country VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        "customers": """
            CREATE TABLE customers (
                id SERIAL PRIMARY KEY,
                customer_account_number VARCHAR(255) UNIQUE NOT NULL,
                customer_name TEXT,
                address_line1 TEXT,
                address_line2 TEXT,
                city VARCHAR(255),
                state VARCHAR(255),
                postal_code VARCHAR(50),
                country VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        "tasks": """
            CREATE TABLE tasks (
                id SERIAL PRIMARY KEY,
                task_number VARCHAR(255) UNIQUE NOT NULL,
                sr_number VARCHAR(255),
                task_assignee_id VARCHAR(255),
                assignee_name TEXT,
                task_notes TEXT,
                travel_time_hours DECIMAL(10,2),
                actual_time_hours DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sr_number) REFERENCES service_requests(sr_number) ON DELETE CASCADE
            )
        """,
        
        "parts_used": """
            CREATE TABLE parts_used (
                id SERIAL PRIMARY KEY,
                task_number VARCHAR(255),
                part_number VARCHAR(255),
                description TEXT,
                quantity INTEGER,
                unit_cost DECIMAL(12,2),
                total_cost DECIMAL(12,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_number) REFERENCES tasks(task_number) ON DELETE CASCADE
            )
        """,
        
        "sr_notes": """
            CREATE TABLE sr_notes (
                id SERIAL PRIMARY KEY,
                sr_number VARCHAR(255),
                customer_problem_summary TEXT,
                sr_notes TEXT,
                resolution_summary TEXT,
                concat_comments TEXT,
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sr_number) REFERENCES service_requests(sr_number) ON DELETE CASCADE
            )
        """
    }
    
    # Create indexes for better performance
    index_queries = [
        "CREATE INDEX idx_sr_customer_account ON service_requests(customer_account_number)",
        "CREATE INDEX idx_sr_incident_date ON service_requests(incident_date)",
        "CREATE INDEX idx_sr_country ON service_requests(country)",
        "CREATE INDEX idx_tasks_sr_number ON tasks(sr_number)",
        "CREATE INDEX idx_tasks_assignee ON tasks(task_assignee_id)",
        "CREATE INDEX idx_parts_task_number ON parts_used(task_number)",
        "CREATE INDEX idx_notes_sr_number ON sr_notes(sr_number)"
    ]
    
    try:
        # Create tables in correct order
        creation_order = ["service_requests", "customers", "tasks", "parts_used", "sr_notes"]
        
        for table_name in creation_order:
            await connection.execute(table_schemas[table_name])
            logger.info(f"✅ Created table: {table_name}")
        
        # Create indexes
        for index_query in index_queries:
            await connection.execute(index_query)
        
        logger.info("🏗️ All tables and indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        raise

async def load_data_to_table(connection, table_name: str, df: pd.DataFrame):
    """Load data to a specific table with conflict resolution"""
    
    if df.empty:
        logger.info(f"⚠️ Skipping empty DataFrame for table: {table_name}")
        return 0
    
    # Clean the dataframe
    df = clean_dataframe(df)
    df = df.drop_duplicates(subset=[df.columns[0]])  # Remove duplicates based on first column
    
    logger.info(f"📥 Loading {len(df)} rows into '{table_name}'...")
    
    try:
        # Convert DataFrame to list of dictionaries for easier processing
        records = df.to_dict(orient="records")
        
        # Process in batches of 500 for better performance
        batch_size = 500
        total_inserted = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            for row in batch:
                # Clean the row data with proper type conversion
                cleaned_row = {}
                for key, value in row.items():
                    cleaned_row[key] = clean_value_for_asyncpg(key, value)
                
                # Build the SQL query
                columns = list(cleaned_row.keys())
                values = list(cleaned_row.values())
                placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
                columns_str = ', '.join(columns)
                
                if table_name in CONFLICT_KEYS:
                    pk = CONFLICT_KEYS[table_name]
                    # Use ON CONFLICT for tables with natural primary keys
                    sql = f"""
                        INSERT INTO {table_name} ({columns_str})
                        VALUES ({placeholders})
                        ON CONFLICT ({pk}) DO NOTHING
                    """
                else:
                    # Simple insert for tables without conflicts
                    sql = f"""
                        INSERT INTO {table_name} ({columns_str})
                        VALUES ({placeholders})
                    """
                
                await connection.execute(sql, *values)
            
            total_inserted += len(batch)
            logger.info(f"📤 Inserted batch {i//batch_size + 1}: {len(batch)} rows")
        
        # Post-insert check
        count = await connection.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        logger.info(f"✅ Total rows in '{table_name}': {count}")
        
        return total_inserted
        
    except Exception as e:
        logger.error(f"❌ Error loading table '{table_name}': {e}")
        raise

async def load_to_postgres(cleaned_data, conn_string):
    """
    Main function to load data to PostgreSQL using AsyncPG
    Replaces your original SQLAlchemy version - same function signature
    """
    logger.info(f"🔐 Connecting to DB with: {conn_string}")  # Match your original log message
    
    # Parse connection string
    db_config = parse_connection_string(conn_string)
    
    connection = None
    try:
        # Create connection
        connection = await asyncpg.connect(**db_config)
        
        # Get database info
        db_name = await connection.fetchval("SELECT current_database()")
        db_user = await connection.fetchval("SELECT current_user")
        logger.info(f"📌 Connected to PostgreSQL database: {db_name} as user: {db_user}")
        
        # Drop and create fresh tables
        await drop_and_create_tables(connection)
        
        # Verify tables exist
        tables = await connection.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        table_names = [row['table_name'] for row in tables]
        logger.info("📋 Tables in schema 'public': " + ", ".join(table_names))
        
        # Load data into each table
        for table_name, df in cleaned_data.items():
            await load_data_to_table(connection, table_name, df)
        
        logger.info("🎉 All data loaded successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database operation failed: {e}")
        raise
        
    finally:
        if connection:
            await connection.close()
            logger.info("🔒 Database connection closed")

async def setup_database_tables(conn_string):
    """
    One-time setup: Drop and create fresh tables
    Called once at the beginning of the pipeline
    """
    logger.info(f"🔐 Setting up database with: {conn_string}")
    
    # Parse connection string
    db_config = parse_connection_string(conn_string)
    
    connection = None
    try:
        # Create connection
        connection = await asyncpg.connect(**db_config)
        
        # Get database info
        db_name = await connection.fetchval("SELECT current_database()")
        db_user = await connection.fetchval("SELECT current_user")
        logger.info(f"📌 Connected to PostgreSQL database: {db_name} as user: {db_user}")
        
        # Drop and create fresh tables
        await drop_and_create_tables(connection)
        
        # Verify tables exist
        tables = await connection.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        table_names = [row['table_name'] for row in tables]
        logger.info("📋 Tables in schema 'public': " + ", ".join(table_names))
        
        logger.info("🏗️ Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise
        
    finally:
        if connection:
            await connection.close()

async def append_to_postgres(cleaned_data, conn_string):
    """
    Append data to existing tables (no dropping/recreating)
    Used for combining multiple files
    """
    logger.info(f"🔗 Appending data to existing tables...")
    
    # Parse connection string
    db_config = parse_connection_string(conn_string)
    
    connection = None
    try:
        # Create connection
        connection = await asyncpg.connect(**db_config)
        
        # Load data into each table (APPEND mode)
        for table_name, df in cleaned_data.items():
            await load_data_to_table(connection, table_name, df)
        
        logger.info("✅ Data appended successfully!")
        
    except Exception as e:
        logger.error(f"❌ Data append failed: {e}")
        raise
        
    finally:
        if connection:
            await connection.close()

# Wrapper functions for synchronous calls
def setup_database_tables_sync(conn_string):
    """Synchronous wrapper for setup_database_tables"""
    return asyncio.run(setup_database_tables(conn_string))

def append_to_postgres_sync(cleaned_data, conn_string):
    """Synchronous wrapper for append_to_postgres"""
    return asyncio.run(append_to_postgres(cleaned_data, conn_string))