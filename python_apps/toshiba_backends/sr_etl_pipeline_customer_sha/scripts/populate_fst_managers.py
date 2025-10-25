import pandas as pd
import asyncpg
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.logger import logger
import json
from urllib.parse import urlparse

async def populate_fst_managers():
    """Populate FST manager mapping table from Excel file with proper header handling"""
    
    # Load config
    with open("config/settings.json") as f:
        config = json.load(f)
    
    # Parse connection string
    parsed = urlparse(config["pg_conn_string"])
    db_config = {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'user': parsed.username or 'postgres',
        'password': parsed.password,
        'database': parsed.path.lstrip('/') if parsed.path else 'postgres'
    }
    
    try:
        connection = await asyncpg.connect(**db_config)
        logger.info("✅ Connected to database")
        
        # Create table with proper handling for duplicates
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS fst_manager_mapping (
                id SERIAL PRIMARY KEY,
                fst_email VARCHAR(255),
                fst_first_name VARCHAR(255),
                fst_last_name VARCHAR(255),
                manager_name VARCHAR(255),
                manager_email VARCHAR(255),
                region VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(fst_email, manager_name)
            );
            
            CREATE INDEX IF NOT EXISTS idx_fst_email ON fst_manager_mapping(fst_email);
            CREATE INDEX IF NOT EXISTS idx_manager_name ON fst_manager_mapping(manager_name);
        """)
        logger.info("✅ FST Manager mapping table created/verified")
        
        # Check if data already exists
        existing_count = await connection.fetchval("SELECT COUNT(*) FROM fst_manager_mapping")
        if existing_count > 0:
            logger.info(f"⚠️ Found {existing_count} existing records. Clearing table to avoid duplicates...")
            await connection.execute("TRUNCATE TABLE fst_manager_mapping RESTART IDENTITY")
            logger.info("✅ Table cleared")
        
        # Read Excel file with correct header handling
        excel_path = "temp/IOPEX FST User List 071825.xlsx"
        if not os.path.exists(excel_path):
            logger.error(f"❌ Excel file not found: {excel_path}")
            return
        
        try:
            # Read Excel skipping the first 140 empty rows
            df = pd.read_excel(excel_path, skiprows=140)
            
            # Set correct column names
            df.columns = [
                'Person Full Name',
                'Person E-mail', 
                'Person Last Name',
                'Person First Name',
                'Manager Full Name',
                'Manager E-mail',
                'Region'
            ]
            
            logger.info(f"📊 Found {len(df)} FST records in Excel file (after skipping headers)")
            logger.info(f"📋 Columns in file: {list(df.columns)}")
            logger.info(f"📋 Region distribution: {df['Region'].value_counts().to_dict()}")
            
        except Exception as e:
            logger.error(f"❌ Error reading Excel: {e}")
            return
        
        # Clean and validate data
        df = df.dropna(subset=['Person E-mail', 'Manager Full Name'], how='any')
        df['Region'] = df['Region'].fillna('Unknown')
        
        logger.info(f"📊 Valid records after cleaning: {len(df)}")
        
        # Insert data
        insert_count = 0
        skip_count = 0
        
        for index, row in df.iterrows():
            try:
                await connection.execute("""
                    INSERT INTO fst_manager_mapping (
                        fst_email, fst_first_name, fst_last_name, 
                        manager_name, manager_email, region
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                    str(row['Person E-mail']).strip(),
                    str(row['Person First Name']).strip(),
                    str(row['Person Last Name']).strip(),
                    str(row['Manager Full Name']).strip(),
                    str(row['Manager E-mail']).strip(),
                    str(row['Region']).strip()
                )
                insert_count += 1
                
                if insert_count % 100 == 0:
                    logger.info(f"📝 Processed {insert_count} records...")
                    
            except Exception as e:
                skip_count += 1
                logger.warning(f"⚠️ Skipped row {index} due to error: {e}")
                if skip_count <= 5:  # Only show first 5 errors to avoid spam
                    logger.warning(f"Row data: {row.to_dict()}")
        
        logger.info(f"✅ Successfully inserted {insert_count} FST-Manager mappings")
        if skip_count > 0:
            logger.warning(f"⚠️ Skipped {skip_count} records due to errors")
        
        # Show sample data
        sample_data = await connection.fetch("""
            SELECT fst_email, manager_name, region 
            FROM fst_manager_mapping 
            ORDER BY RANDOM() 
            LIMIT 5
        """)
        
        logger.info("📋 Sample FST data:")
        for record in sample_data:
            logger.info(f"  {record['fst_email']} -> {record['manager_name']} ({record['region']})")
        
        # Show manager summary
        manager_summary = await connection.fetch("""
            SELECT manager_name, region, COUNT(*) as fst_count
            FROM fst_manager_mapping 
            GROUP BY manager_name, region
            ORDER BY fst_count DESC
            LIMIT 15
        """)
        
        logger.info("👥 Manager Summary:")
        for manager in manager_summary:
            logger.info(f"  {manager['manager_name']} ({manager['region']}): {manager['fst_count']} FSTs")
        
        # Show region distribution
        region_summary = await connection.fetch("""
            SELECT region, COUNT(*) as count
            FROM fst_manager_mapping 
            GROUP BY region
            ORDER BY count DESC
        """)
        
        logger.info("🌍 Region Distribution:")
        for region in region_summary:
            logger.info(f"  {region['region']}: {region['count']} FSTs")
        
        await connection.close()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(populate_fst_managers())