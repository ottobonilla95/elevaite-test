from urllib.parse import quote_plus
import pandas as pd
import psycopg2
from datetime import datetime, time
from sqlalchemy import create_engine, text
import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.exc import SQLAlchemyError

def check_file_existence(file_path):
    if os.path.exists(file_path):
        print(f"File found: {file_path}")
        return True
    else:
        print(f"File not found: {file_path}")
        return False

def add_voting_columns_if_not_exist(engine):
    try:
        check_columns_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'sf_chat_transcript_summary' 
        AND column_name IN ('upvotes', 'downvotes', 'total_votes');
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(check_columns_sql))
            existing_columns = [row[0] for row in result]
            
            # Add any missing columns
            if 'upvotes' not in existing_columns:
                conn.execute(text("ALTER TABLE sf_chat_transcript_summary ADD COLUMN upvotes INTEGER DEFAULT 0"))
            if 'downvotes' not in existing_columns:
                conn.execute(text("ALTER TABLE sf_chat_transcript_summary ADD COLUMN downvotes INTEGER DEFAULT 0"))
            if 'total_votes' not in existing_columns:
                conn.execute(text("ALTER TABLE sf_chat_transcript_summary ADD COLUMN total_votes INTEGER DEFAULT 0"))
            conn.commit()
            
        print("Verified voting columns exist")
            
    except Exception as e:
        print(f"Error checking/adding voting columns: {str(e)}")
        raise

def recreate_table(engine):
    try:
        drop_table_sql = "DROP TABLE IF EXISTS sf_chat_transcript_summary"
        create_table_sql = """
        CREATE TABLE sf_chat_transcript_summary (
            chat_transcript_id INTEGER PRIMARY KEY,
            case_number INTEGER NOT NULL,
            created_date TIMESTAMP,
            last_modified_date TIMESTAMP,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            time_duration TIME,
            wait_time_seconds INTEGER,
            chat_duration INTEGER,
            number_of_transfers SMALLINT,
            query_count SMALLINT,
            owner_full_name VARCHAR(100),
            created_by_full_name VARCHAR(100),
            chat_queue_name VARCHAR(255),
            chat_transcript_ref_id VARCHAR(50),
            product VARCHAR(100),
            sub_product VARCHAR(100),
            support_organization VARCHAR(50),
            lob VARCHAR(50),
            ai_usage_id VARCHAR(12),
            problem VARCHAR(50),
            case_origin VARCHAR(50),
            status VARCHAR(50),
            symptoms TEXT,
            root_cause TEXT,
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            total_votes INTEGER DEFAULT 0
        )"""
        
        with engine.connect() as conn:
            conn.execute(text(drop_table_sql))
            conn.commit()
            
            conn.execute(text(create_table_sql))
            conn.commit()
            
            indexes = [
                "CREATE INDEX idx_chat_transcript_id ON sf_chat_transcript_summary(chat_transcript_id)",
                "CREATE INDEX idx_case_number ON sf_chat_transcript_summary(case_number)",
                "CREATE INDEX idx_created_date ON sf_chat_transcript_summary(created_date)",
                "CREATE INDEX idx_status ON sf_chat_transcript_summary(status)",
                "CREATE INDEX idx_product_subproduct ON sf_chat_transcript_summary(product, sub_product)",
                "CREATE INDEX idx_date_status ON sf_chat_transcript_summary(created_date, status)",
                "CREATE INDEX idx_support_org ON sf_chat_transcript_summary(support_organization)",
                "CREATE INDEX idx_lob ON sf_chat_transcript_summary(lob)",
                "CREATE INDEX idx_symptoms_gin ON sf_chat_transcript_summary USING gin(to_tsvector('english', symptoms))",
                "CREATE INDEX idx_root_cause_gin ON sf_chat_transcript_summary USING gin(to_tsvector('english', root_cause))"
            ]
            
            for index in indexes:
                conn.execute(text(index))
                conn.commit()
            print("Created table and indexes successfully")
            
    except Exception as e:
        print(f"Error in table recreation: {str(e)}")
        raise

def clean_and_transform_data(df):
    try:
        column_mapping = {
            'Month': None,
            'Duration': 'time_duration',
            'Chat Transcript Name': 'chat_transcript_ref_id', 
            'Wait Time': 'wait_time_seconds',
            'Status': 'status',
            'Chat Duration': 'chat_duration',
            'Owner: Full Name': 'owner_full_name',
            'Created Date': 'created_date',
            'Created By: Full Name': 'created_by_full_name',
            'Case: Case Number': 'case_number',
            'Start Time': 'start_time',
            'End Time': 'end_time',
            '# of Transferred': 'number_of_transfers',
            'Chat Button: Developer Name': 'chat_queue_name',
            'Chat Transcript ID': 'chat_transcript_id',
            'Last Modified Date': 'last_modified_date',
            'Products': 'product',
            'Sub Product': 'sub_product',
            'Staff': 'support_organization',
            'LOB': 'lob',
            'AI Usage ID': 'ai_usage_id',
            '# of Querry': 'query_count',
            'Symptoms': 'symptoms',
            'Root cause': 'root_cause',
            'Problem': 'problem',
            'Case Origin': 'case_origin'
        }

        # Drop Month column and rename
        df = df.drop('Month', axis=1, errors='ignore')
        df = df.rename(columns=column_mapping)
        
        # Handle voting columns
        voting_cols = ['upvotes', 'downvotes', 'total_votes']
        for col in voting_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            else:
                df[col] = 0
        
        # Handle time duration
        if 'Duration' in df.columns:
            try:
                df['time_duration'] = pd.to_datetime(df['Duration'], format='%H:%M:%S').dt.time
                df = df.drop('Duration', axis=1)
            except Exception as e:
                print(f"Error converting time_duration: {e}")
                raise
                
        # Handle datetime columns
        datetime_cols = ['created_date', 'last_modified_date', 'start_time', 'end_time']
        for col in datetime_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert numeric columns
        numeric_cols = {
            'chat_transcript_id': int,
            'case_number': int,
            'wait_time_seconds': int,
            'chat_duration': int,
            'number_of_transfers': int,
            'query_count': int
        }

        for col, dtype in numeric_cols.items():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(dtype)
        
        # Handle text columns
        text_columns = [
            'symptoms', 'root_cause', 'owner_full_name', 'created_by_full_name', 
            'chat_queue_name', 'chat_transcript_ref_id', 'product', 'sub_product',
            'support_organization', 'lob', 'ai_usage_id', 'problem', 'case_origin', 'status'
        ]
        
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['chat_transcript_id'], keep='first')
        
        return df
        
    except Exception as e:
        print(f"Error in data transformation: {str(e)}")
        raise

def import_excel_to_db(file_path, db_params):
    try:
        if not check_file_existence(file_path):
            return False
        
        print(f"\nReading file: {file_path}")
        df = pd.read_excel(file_path)
        print(f"Successfully read {len(df)} rows from Excel")
        
        conn_string = f"postgresql://{db_params['user']}:{quote_plus(db_params['password'])}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
        engine = create_engine(conn_string)
        
        print("\nRecreating table with optimized schema...")
        recreate_table(engine)
        
        print("\nStarting data transformation...")
        df = clean_and_transform_data(df)
        print("Data transformation completed")
        
        print("\nImporting data to database...")
        chunk_size = 500
        total_chunks = len(df) // chunk_size + (1 if len(df) % chunk_size else 0)
        
        for i in range(0, len(df), chunk_size):
            chunk = df[i:i + chunk_size]
            chunk.to_sql(
                'sf_chat_transcript_summary',
                engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=50
            )
            print(f"Imported chunk {i//chunk_size + 1} of {total_chunks}")
        
        print(f"Successfully imported {len(df)} records to database")
        return True
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print("\nDetailed error information:")
        import traceback
        print(traceback.format_exc())
        return False

def update_voting_info(file_path, db_params):
    try:
        if not check_file_existence(file_path):
            return False
            
        print(f"\nReading file: {file_path}")
        df = pd.read_excel(file_path)
        print(f"Successfully read {len(df)} rows from Excel")
        
        # Create database connection
        conn_string = f"postgresql://{db_params['user']}:{quote_plus(db_params['password'])}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
        engine = create_engine(conn_string)
        
        # Ensure voting columns exist
        print("\nChecking and adding voting columns if needed...")
        add_voting_columns_if_not_exist(engine)
        
        # Transform the data
        print("\nTransforming data...")
        df = clean_and_transform_data(df)
        
        # Update voting information
        print("\nUpdating voting information...")
        total_rows = len(df)
        for index, row in df.iterrows():
            update_sql = """
            UPDATE sf_chat_transcript_summary 
            SET upvotes = :upvotes,
                downvotes = :downvotes,
                total_votes = :total_votes
            WHERE chat_transcript_id = :chat_transcript_id
            """
            
            with engine.connect() as conn:
                conn.execute(text(update_sql), {
                    'upvotes': row['upvotes'],
                    'downvotes': row['downvotes'],
                    'total_votes': row['total_votes'],
                    'chat_transcript_id': row['chat_transcript_id']
                })
                conn.commit()
                print(f"Updated voting info for chat_transcript_id: {row['chat_transcript_id']} ({index + 1}/{total_rows})")
                
        print("Updated voting information successfully")
        return True
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print("\nDetailed error information:")
        import traceback
        print(traceback.format_exc())
        return False

# Database connection parameters
db_params = {
    'host': 'localhost',
    'database': 'arlo_dashboard',
    'user': 'postgres',
    'password': 'Vijaya@2210$',
    'port': '5432'
}

excel_file = '../src/Assets/Elevaite_arlo_report_december.xlsx'

if __name__ == "__main__":
    print("Choose operation:")
    print("1. Full import (recreate table and import all data)")
    print("2. Update voting information only")
    
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == "1":
        print("\n=== Starting Full Data Import Process ===")
        success = import_excel_to_db(excel_file, db_params)
    elif choice == "2":
        print("\n=== Starting Voting Information Update Process ===")
        success = update_voting_info(excel_file, db_params)
    else:
        print("Invalid choice!")
        success = False
    
    if success:
        print("\n=== Operation completed successfully ===")
    else:
        print("\n=== Operation failed ===")
        print("Please check the error messages above")