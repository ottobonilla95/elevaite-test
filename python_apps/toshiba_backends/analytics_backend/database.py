
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Tuple, List, Optional
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load .env file
load_dotenv()

def log_query(query, params=None):
    """Log SQL query and parameters"""
    if params:
        param_str = ", ".join(str(p) for p in params)
        logging.debug(f"Executing SQL: {query} with params: [{param_str}]")
    else:
        logging.debug(f"Executing SQL: {query}")

def get_db_connection():
    """Get a connection to the PostgreSQL database using DATABASE_URL from .env"""
    try:
        # Get DATABASE_URL from environment variables (using your connection string)
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
            
        # Log connection attempt (without exposing password)
        # WARNING: never log the raw database url as it countains the password
        logging.info(f"Connecting to database: {database_url.split('@')[-1]}")
            
        # Connect to the database
        conn = psycopg2.connect(database_url)
        
        # Set cursor to return dictionaries
        conn.cursor_factory = RealDictCursor
        
        # Log successful connection
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user")
            db_info = cur.fetchone()
            logging.info(f"Connected to database: {db_info['current_database']} as {db_info['current_user']}")
        
        return conn
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        raise

# ADD THIS NEW FUNCTION FOR CHATBOT DATA
def get_chatbot_db_connection():
    """
    Get connection to the chatbot database (same database, different tables)
    This connects to chat_data_final and agent_flow_data tables
    """
    try:
        # Use the same database connection since chatbot tables are in the same DB
        conn = get_db_connection()
        
        # Log that we're accessing chatbot tables
        logging.info("Connected to chatbot tables: chat_data_final, agent_flow_data")
        
        return conn
    except Exception as e:
        logging.error(f"Chatbot database connection error: {e}")
        raise

def log_chatbot_query(query, params=None):
    """Log chatbot SQL queries for debugging"""
    if params:
        param_str = ", ".join(str(p) for p in params)
        logging.debug(f"[CHATBOT] SQL: {query} | PARAMS: {param_str}")
    else:
        logging.debug(f"[CHATBOT] SQL: {query}")

def build_date_filter(table_alias: str = "") -> callable:
    """
    Build a consistent date filter SQL clause and parameters
    
    Args:
        table_alias: Optional table alias (e.g., "sr." for "sr.incident_date")
        
    Returns:
        Function that takes start_date and end_date and returns filter and params
    """
    def get_filter(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[str, List]:
        prefix = f"{table_alias}." if table_alias else ""
        date_field = f"{prefix}incident_date"
        
        if start_date and end_date:
            return f"WHERE {date_field} BETWEEN %s AND %s", [start_date, end_date]
        elif start_date:
            return f"WHERE {date_field} >= %s", [start_date]
        elif end_date:
            return f"WHERE {date_field} <= %s", [end_date]
        else:
            return "", []
    
    return get_filter

# ADD THIS NEW FUNCTION FOR CHATBOT DATE FILTERING
def build_chatbot_date_filter(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[str, List]:
    """
    Build date filter for chatbot queries using request_timestamp
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Tuple of (filter_clause, params_list)
    """
    date_filter = ""
    params = []
    
    if start_date and end_date:
        date_filter = "WHERE request_timestamp BETWEEN %s AND %s"
        params = [start_date, end_date]
    elif start_date:
        date_filter = "WHERE request_timestamp >= %s"
        params = [start_date]
    elif end_date:
        date_filter = "WHERE request_timestamp <= %s"
        params = [end_date]
    
    return date_filter, params

# ADD THIS FUNCTION TO TEST CHATBOT CONNECTION
def test_chatbot_connection():
    """Test if chatbot tables are accessible"""
    try:
        conn = get_chatbot_db_connection()
        cur = conn.cursor()
        
        # Test chat_data_final table
        cur.execute("SELECT COUNT(*) as count FROM chat_data_final")
        chat_count = cur.fetchone()
        
        # Test agent_flow_data table  
        cur.execute("SELECT COUNT(*) as count FROM agent_flow_data")
        agent_count = cur.fetchone()
        
        cur.close()
        conn.close()
        
        logging.info("✅ Chatbot connection test successful:")
        logging.info(f"   - chat_data_final: {chat_count['count']} records")
        logging.info(f"   - agent_flow_data: {agent_count['count']} records")
        
        return {
            "status": "success",
            "chat_data_final": chat_count['count'],
            "agent_flow_data": agent_count['count']
        }
        
    except Exception as e:
        logging.error(f"❌ Chatbot connection test failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# ADD THIS HELPER FUNCTION FOR PRODUCTION VERIFICATION
def verify_all_tables():
    """Verify all required tables exist (both SR and chatbot)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check for service request tables
        sr_tables = ['service_requests', 'customers', 'tasks', 'parts_used', 'sr_notes']
        
        # Check for chatbot tables
        chatbot_tables = ['chat_data_final', 'agent_flow_data']
        
        all_tables = sr_tables + chatbot_tables
        existing_tables = []
        missing_tables = []
        
        for table in all_tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()['count']
                existing_tables.append(f"{table} ({count:,} records)")
            except psycopg2.Error:
                missing_tables.append(table)
        
        cur.close()
        conn.close()
        
        logging.info("📋 Table verification complete:")
        for table in existing_tables:
            logging.info(f"   ✅ {table}")
        for table in missing_tables:
            logging.error(f"   ❌ {table} - NOT FOUND")
        
        return {
            "existing": existing_tables,
            "missing": missing_tables,
            "all_present": len(missing_tables) == 0
        }
        
    except Exception as e:
        logging.error(f"Table verification failed: {e}")
        return {
            "existing": [],
            "missing": all_tables,
            "all_present": False,
            "error": str(e)
        }