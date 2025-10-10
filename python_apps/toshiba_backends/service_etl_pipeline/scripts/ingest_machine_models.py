import pandas as pd
import psycopg2
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
from urllib.parse import urlparse

def ingest_machine_models():
    """Ingest machine models from Excel Sheet 2 into PostgreSQL"""
    
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
        
        # Create the machine models table
        cur.execute("DROP TABLE IF EXISTS machine_type_models")
        print("Dropped existing machine_type_models table")
        
        cur.execute("""
            CREATE TABLE machine_type_models (
                id SERIAL PRIMARY KEY,
                machine_number VARCHAR(255) NOT NULL,
                description TEXT,
                classification VARCHAR(100),
                machine_type VARCHAR(10),
                machine_model VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(machine_number)
            );
            
            CREATE INDEX idx_machine_type ON machine_type_models(machine_type);
            CREATE INDEX idx_machine_model ON machine_type_models(machine_model);
            CREATE INDEX idx_classification ON machine_type_models(classification);
        """)
        conn.commit()
        print("Created machine_type_models table with indexes")
        
        # Read Excel file - Sheet 2 (the detailed one with Machine Type and Model columns)
        excel_path = "temp/MTMs For Dashboard.xlsx"
        
        # Read the second sheet (index 1) - this should have the Machine Type and Model columns
        try:
            df = pd.read_excel(excel_path, sheet_name=1)  # Second sheet
            print(f"Successfully read Sheet 2 with {len(df)} rows")
        except Exception as e:
            print(f"Could not read Sheet 2, trying sheet name 'Sheet2'...")
            try:
                df = pd.read_excel(excel_path, sheet_name='Sheet2')
                print(f"Successfully read Sheet2 with {len(df)} rows")
            except:
                print("Listing all available sheets...")
                xl_file = pd.ExcelFile(excel_path)
                print("Available sheets:", xl_file.sheet_names)
                # Use the second available sheet
                if len(xl_file.sheet_names) > 1:
                    df = pd.read_excel(excel_path, sheet_name=xl_file.sheet_names[1])
                    print(f"Using sheet '{xl_file.sheet_names[1]}' with {len(df)} rows")
                else:
                    raise Exception("Only one sheet available in Excel file")
        
        # Show column names to verify structure
        print(f"Columns found: {list(df.columns)}")
        
        # Verify we have the required columns
        required_columns = ['Number', 'Description', 'Type', 'Machine Type', 'Model']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Warning: Missing columns: {missing_columns}")
            print("Available columns:", list(df.columns))
            return False
        
        # Show type distribution
        type_counts = df['Type'].value_counts()
        print(f"\nType distribution:")
        for type_name, count in type_counts.items():
            print(f"  {type_name}: {count}")
        
        # Show machine type distribution
        machine_type_counts = df['Machine Type'].value_counts()
        print(f"\nMachine Type distribution (top 10):")
        for machine_type, count in machine_type_counts.head(10).items():
            print(f"  {machine_type}: {count}")
        
        # Insert data in batches
        insert_count = 0
        error_count = 0
        batch_size = 100
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            batch_data = []
            
            for index, row in batch.iterrows():
                try:
                    # Clean and validate data
                    machine_number = str(row['Number']).strip()
                    description = str(row['Description']).strip()
                    classification = str(row['Type']).strip()
                    machine_type = str(row['Machine Type']).strip()
                    machine_model = str(row['Model']).strip()
                    
                    # Skip if any required field is empty/NaN
                    if any(val in ['nan', 'None', ''] for val in [machine_number, machine_type, machine_model]):
                        error_count += 1
                        continue
                    
                    batch_data.append((
                        machine_number,
                        description,
                        classification,
                        machine_type,
                        machine_model
                    ))
                    
                except Exception as e:
                    print(f"Error processing row {index}: {e}")
                    error_count += 1
                    continue
            
            # Insert batch
            if batch_data:
                try:
                    cur.executemany("""
                        INSERT INTO machine_type_models 
                        (machine_number, description, classification, machine_type, machine_model)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (machine_number) DO UPDATE SET
                            description = EXCLUDED.description,
                            classification = EXCLUDED.classification,
                            machine_type = EXCLUDED.machine_type,
                            machine_model = EXCLUDED.machine_model
                    """, batch_data)
                    
                    insert_count += len(batch_data)
                    if i % 500 == 0:
                        print(f"Processed {insert_count} records...")
                        
                except Exception as e:
                    print(f"Error inserting batch: {e}")
                    error_count += len(batch_data)
        
        conn.commit()
        print(f"Successfully inserted {insert_count} machine models")
        print(f"Errors encountered: {error_count}")
        
        # Show summary by classification and machine type
        cur.execute("""
            SELECT classification, COUNT(*) 
            FROM machine_type_models 
            GROUP BY classification
            ORDER BY COUNT(*) DESC
        """)
        summary = cur.fetchall()
        print("\nClassification summary:")
        for class_name, count in summary:
            print(f"  {class_name}: {count}")
        
        # Show machine type summary for Toshiba products
        cur.execute("""
            SELECT machine_type, COUNT(*), MIN(machine_model), MAX(machine_model)
            FROM machine_type_models 
            WHERE classification = 'TGCS - Active'
            GROUP BY machine_type
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        toshiba_summary = cur.fetchall()
        print("\nToshiba machine types (TGCS - Active):")
        for machine_type, count, min_model, max_model in toshiba_summary:
            print(f"  {machine_type}: {count} models ({min_model} to {max_model})")
        
        # Test the mapping - show what machine types would be used for filtering
        cur.execute("""
            SELECT DISTINCT machine_type 
            FROM machine_type_models 
            WHERE classification = 'TGCS - Active'
            ORDER BY machine_type
        """)
        toshiba_types = [row[0] for row in cur.fetchall()]
        print(f"\nToshiba machine types for filtering: {toshiba_types}")
        
        cur.execute("""
            SELECT DISTINCT machine_type 
            FROM machine_type_models 
            WHERE classification = 'OEM'
            ORDER BY machine_type
            LIMIT 20
        """)
        oem_types = [row[0] for row in cur.fetchall()]
        print(f"\nOEM machine types (first 20): {oem_types}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_product_filter():
    """Generate the updated product filter function code"""
    print("\n" + "="*50)
    print("UPDATED PRODUCT FILTER FUNCTION")
    print("="*50)
    print("""
Replace your build_product_type_filter function with this:

def build_product_type_filter(product_type: Optional[str]):
    \"\"\"Build product type filter using the ingested machine models table\"\"\"
    if not product_type or product_type == 'all':
        return ""
    elif product_type == 'toshiba':
        return \"\"\"AND sr.machine_type IN (
            SELECT DISTINCT machine_type 
            FROM machine_type_models 
            WHERE classification = 'TGCS - Active'
        )\"\"\"
    elif product_type == 'oem':
        return \"\"\"AND sr.machine_type IN (
            SELECT DISTINCT machine_type 
            FROM machine_type_models 
            WHERE classification = 'OEM'
        )\"\"\"
    else:
        return ""
""")

if __name__ == "__main__":
    print("Starting machine models ingestion from Sheet 2...")
    success = ingest_machine_models()
    if success:
        print("\nMachine models ingestion completed successfully!")
        print("\nWhat you now have:")
        print("- machine_type_models table with detailed mappings")
        print("- Machine Type and Model columns for proper filtering")
        print("- Indexes for fast lookups")
        
        update_product_filter()
        
        print("\nNext steps:")
        print("1. Update your build_product_type_filter function (code shown above)")
        print("2. Update main_machine_types list to include Toshiba machine types")
        print("3. Test your product type filtering")
    else:
        print("Machine models ingestion failed!")