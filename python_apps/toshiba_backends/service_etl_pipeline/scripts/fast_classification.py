import psycopg2
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
from urllib.parse import urlparse

def create_fast_classification():
    """Create a fast lookup table for machine types"""
    
    # Load database config
    with open("config/settings.json") as f:
        config = json.load(f)
    
    parsed = urlparse(config["pg_conn_string"])
    
    try:
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/')
        )
        cur = conn.cursor()
        
        # Create fast lookup table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS machine_type_lookup (
                machine_type VARCHAR(50) PRIMARY KEY,
                product_category VARCHAR(20)
            );
        """)
        
        # Clear and populate with all machine types
        cur.execute("DELETE FROM machine_type_lookup")
        
        # Insert classifications for your known machine types
        classifications = [
            ('0335', 'OEM'), ('0344', 'OEM'), ('0368', 'OEM'), ('0343', 'OEM'),
            ('0363', 'OEM'), ('0364', 'OEM'), ('0336', 'OEM'), ('0346', 'OEM'),
            ('0365', 'OEM'), ('0347', 'OEM'), ('0369', 'OEM'), ('335', 'OEM'),
            ('368', 'OEM'), ('343', 'OEM'), ('344', 'OEM'), ('TGCS', 'OEM'),
            ('4900', 'Toshiba'), ('4136', 'Toshiba')
        ]
        
        # Get all machine types from your database
        cur.execute("SELECT DISTINCT machine_type FROM service_requests WHERE machine_type IS NOT NULL")
        all_types = [row[0] for row in cur.fetchall()]
        
        # Insert known classifications
        for machine_type, category in classifications:
            if machine_type in all_types:
                cur.execute("""
                    INSERT INTO machine_type_lookup (machine_type, product_category)
                    VALUES (%s, %s)
                    ON CONFLICT (machine_type) DO UPDATE SET product_category = EXCLUDED.product_category
                """, (machine_type, category))
        
        # Default unknown types to OEM
        for machine_type in all_types:
            cur.execute("""
                INSERT INTO machine_type_lookup (machine_type, product_category)
                VALUES (%s, %s)
                ON CONFLICT (machine_type) DO NOTHING
            """, (machine_type, 'OEM'))
        
        conn.commit()
        
        # Test the lookup
        cur.execute("""
            SELECT product_category, COUNT(*) 
            FROM machine_type_lookup 
            GROUP BY product_category
        """)
        
        results = cur.fetchall()
        print("Classification summary:")
        for category, count in results:
            print(f"  {category}: {count} machine types")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Creating fast lookup table...")
    success = create_fast_classification()
    if success:
        print("Fast lookup table created!")