import pandas as pd
import psycopg2
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
from urllib.parse import urlparse

def ingest_machine_types():
    """Ingest machine types from Excel into PostgreSQL"""
    
    # Load your existing database config
    with open("config/settings.json") as f:
        config = json.load(f)
    
    # Parse the connection string
    parsed = urlparse(config["pg_conn_string"])
    
    try:
        # Connect to your database
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/')
        )
        cur = conn.cursor()
        print("Connected to database successfully")
        
        # DROP and recreate the table to fix column structure
        cur.execute("DROP TABLE IF EXISTS toshiba_machine_types")
        print("Dropped existing table")
        
        cur.execute("""
            CREATE TABLE toshiba_machine_types (
                id SERIAL PRIMARY KEY,
                machine_number VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                classification VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX idx_toshiba_machine_number 
            ON toshiba_machine_types(machine_number);
        """)
        conn.commit()
        print("Created new toshiba_machine_types table with correct structure")
        
        # Read Excel file
        excel_path = "temp/MTMs For Dashboard.xlsx"
        df = pd.read_excel(excel_path)
        print(f"Read {len(df)} rows from Excel file")
        
        # Show type distribution
        type_counts = df['Type'].value_counts()
        print(f"\nType distribution:")
        for type_name, count in type_counts.items():
            print(f"  {type_name}: {count}")
        
        # Insert data in batches
        insert_count = 0
        batch_size = 100
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            batch_data = []
            
            for index, row in batch.iterrows():
                batch_data.append((
                    str(row['Number']).strip(),
                    str(row['Description']).strip(), 
                    str(row['Type']).strip()
                ))
            
            # Insert batch
            cur.executemany("""
                INSERT INTO toshiba_machine_types 
                (machine_number, description, classification)
                VALUES (%s, %s, %s)
            """, batch_data)
            
            insert_count += len(batch_data)
            if i % 500 == 0:
                print(f"Processed {insert_count} records...")
        
        conn.commit()
        print(f"Successfully inserted {insert_count} machine types")
        
        # Show summary by classification
        cur.execute("""
            SELECT classification, COUNT(*) 
            FROM toshiba_machine_types 
            GROUP BY classification
            ORDER BY COUNT(*) DESC
        """)
        summary = cur.fetchall()
        print("\nClassification summary:")
        for class_name, count in summary:
            print(f"  {class_name}: {count}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting machine type ingestion...")
    success = ingest_machine_types()
    if success:
        print("\nStep 1 completed successfully!")
        print("You now have:")
        print("- 154 TGCS - Active (Toshiba products)")
        print("- 2866 OEM (non-Toshiba products)")
        print("- Others: TGCS - Withdrawn, TGCS")
        print("\nNext: We'll test the classification with your existing data")
    else:
        print("Machine type ingestion failed!")