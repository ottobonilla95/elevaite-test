# scripts/setup_technician_filtering.py
import asyncpg
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.logger import logger
import json
from urllib.parse import urlparse

async def setup_technician_filtering():
    """Setup technician filtering tables for analytics dashboard"""
    
    # Load config (using your existing config structure)
    with open("config/settings.json") as f:
        config = json.load(f)
    
    # Parse connection string (using your existing connection pattern)
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
        logger.info("✅ Connected to database for technician filtering setup")
        
        # Check if tables exist and clear them to avoid conflicts
        existing_fst = await connection.fetchval("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'fst_technicians'")
        if existing_fst:
            logger.info("⚠️ Technician filtering tables exist. Clearing to avoid duplicates...")
            await connection.execute("TRUNCATE TABLE fst_manager_assignments, manager_groups, fst_technicians RESTART IDENTITY CASCADE")
            logger.info("✅ Tables cleared")
        
        # Create technician filtering tables
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS fst_technicians (
                id SERIAL PRIMARY KEY,
                fst_email VARCHAR(255) UNIQUE NOT NULL,
                fst_first_name VARCHAR(255),
                fst_last_name VARCHAR(255),
                full_name VARCHAR(255),
                region VARCHAR(100),
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS manager_groups (
                id SERIAL PRIMARY KEY,
                manager_name VARCHAR(255) UNIQUE NOT NULL,
                manager_email VARCHAR(255),
                region VARCHAR(100),
                group_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS fst_manager_assignments (
                id SERIAL PRIMARY KEY,
                fst_id INTEGER REFERENCES fst_technicians(id) ON DELETE CASCADE,
                manager_id INTEGER REFERENCES manager_groups(id) ON DELETE CASCADE,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(fst_id, manager_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_fst_email ON fst_technicians(fst_email);
            CREATE INDEX IF NOT EXISTS idx_manager_name ON manager_groups(manager_name);
            CREATE INDEX IF NOT EXISTS idx_fst_assignments ON fst_manager_assignments(manager_id);
        """)
        logger.info("✅ Technician filtering tables created/verified")
        
        # Import data from existing fst_manager_mapping table
        logger.info("📊 Importing FST data from existing table...")
        
        # Import FSTs (use ROW_NUMBER to handle duplicates by taking first occurrence)
        fst_result = await connection.execute("""
            INSERT INTO fst_technicians (fst_email, fst_first_name, fst_last_name, full_name, region)
            SELECT 
                fst_email,
                fst_first_name,
                fst_last_name,
                CONCAT(fst_first_name, ' ', fst_last_name) as full_name,
                COALESCE(region, 'Unknown') as region
            FROM (
                SELECT DISTINCT ON (fst_email)
                    fst_email,
                    fst_first_name,
                    fst_last_name,
                    region
                FROM fst_manager_mapping 
                WHERE fst_email IS NOT NULL AND fst_email != ''
                ORDER BY fst_email, id
            ) deduplicated_fsts
        """)
        
        # Import Managers (use DISTINCT ON to handle duplicates)
        manager_result = await connection.execute("""
            INSERT INTO manager_groups (manager_name, manager_email, region, group_description)
            SELECT 
                manager_name,
                manager_email,
                COALESCE(region, 'Unknown') as region,
                CONCAT('Team managed by ', manager_name) as group_description
            FROM (
                SELECT DISTINCT ON (manager_name)
                    manager_name,
                    manager_email,
                    region
                FROM fst_manager_mapping 
                WHERE manager_name IS NOT NULL AND manager_name != ''
                ORDER BY manager_name, id
            ) deduplicated_managers
        """)
        
        # Create assignments (handle potential duplicates in mapping)
        assignment_result = await connection.execute("""
            INSERT INTO fst_manager_assignments (fst_id, manager_id)
            SELECT DISTINCT f.id, m.id
            FROM fst_manager_mapping fmm
            JOIN fst_technicians f ON fmm.fst_email = f.fst_email
            JOIN manager_groups m ON fmm.manager_name = m.manager_name
        """)
        
        # Verify setup
        fst_count = await connection.fetchval("SELECT COUNT(*) FROM fst_technicians")
        manager_count = await connection.fetchval("SELECT COUNT(*) FROM manager_groups")
        assignment_count = await connection.fetchval("SELECT COUNT(*) FROM fst_manager_assignments")
        
        logger.info(f"✅ Technician filtering setup complete:")
        logger.info(f"   FSTs: {fst_count}")
        logger.info(f"   Managers: {manager_count}")
        logger.info(f"   Assignments: {assignment_count}")
        
        # Show region distribution for FSTs
        fst_regions = await connection.fetch("""
            SELECT region, COUNT(*) as count
            FROM fst_technicians
            GROUP BY region
            ORDER BY count DESC
        """)
        
        logger.info("🌍 FST Region Distribution:")
        for region in fst_regions:
            logger.info(f"   {region['region']}: {region['count']} FSTs")
        
        # Show manager summary
        managers = await connection.fetch("""
            SELECT m.manager_name, m.region, COUNT(fa.fst_id) as fst_count
            FROM manager_groups m
            LEFT JOIN fst_manager_assignments fa ON m.id = fa.manager_id
            GROUP BY m.id, m.manager_name, m.region
            ORDER BY fst_count DESC
            LIMIT 10
        """)
        
        logger.info("👥 Top Manager Groups:")
        for manager in managers:
            logger.info(f"   {manager['manager_name']} ({manager['region']}): {manager['fst_count']} FSTs")
        
        # Show sample assignments
        sample_assignments = await connection.fetch("""
            SELECT f.fst_email, f.full_name, f.region as fst_region,
                   m.manager_name, m.region as manager_region
            FROM fst_manager_assignments fa
            JOIN fst_technicians f ON fa.fst_id = f.id
            JOIN manager_groups m ON fa.manager_id = m.id
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        logger.info("📋 Sample FST-Manager Assignments:")
        for assignment in sample_assignments:
            logger.info(f"   {assignment['full_name']} ({assignment['fst_region']}) -> {assignment['manager_name']} ({assignment['manager_region']})")
        
        await connection.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Technician filtering setup error: {e}")
        return False

async def run_technician_setup():
    """Run technician filtering setup as part of ETL pipeline"""
    logger.info("🚀 Starting technician filtering setup...")
    
    success = await setup_technician_filtering()
    
    if success:
        logger.info("✅ Technician filtering setup completed successfully")
    else:
        logger.error("❌ Technician filtering setup failed")
        
    return success

if __name__ == "__main__":
    asyncio.run(run_technician_setup())