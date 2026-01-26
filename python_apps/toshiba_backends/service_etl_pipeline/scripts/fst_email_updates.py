import asyncpg
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.logger import logger
import json
from urllib.parse import urlparse

async def process_fst_email_updates():
    """Process FST additions and deletions from email updates"""
    
    # ===== MODIFY THESE LISTS EACH TIME YOU GET EMAIL UPDATES =====
    
    # TECHNICIANS TO ADD (copy from email)
    technicians_to_add = [
        {
            'date': '2025-07-28',
            'region': 'Central',
            'first_name': 'Gavin',
            'last_name': 'Cushman',
            'email': 'gavin.cushman@toshibagcs.com',
            'manager_first': 'Angela',
            'manager_last': 'Smith',
            'manager_email': 'Angela.Smith@toshibagcs.com'
        },
        {
            'date': '2025-07-28',
            'region': 'Central',
            'first_name': 'Terry',
            'last_name': 'Pate',
            'email': 'terry.pate@toshibagcs.com',
            'manager_first': 'Angela',
            'manager_last': 'Smith',
            'manager_email': 'Angela.Smith@toshibagcs.com'
        },
        {
            'date': '2025-07-28',
            'region': 'East',
            'first_name': 'Anthony',
            'last_name': 'Campbell',
            'email': 'anthony.campbell@toshibagcs.com',
            'manager_first': 'John',
            'manager_last': 'Francis',
            'manager_email': 'John.Francis@toshibagcs.com'
        },
        {
            'date': '2025-08-04',
            'region': 'West',
            'first_name': 'Emiliano',
            'last_name': 'Esquivel',
            'email': 'emi.esquivel@toshibagcs.com',
            'manager_first': 'Daniel',
            'manager_last': 'Reynolds',
            'manager_email': 'Daniel.Reynolds@toshibagcs.com'
        },
        {
            'date': '2025-08-04',
            'region': 'Central',
            'first_name': 'Zachary',
            'last_name': 'Whiteman',
            'email': 'zach.whiteman@toshibagcs.com',
            'manager_first': 'Angela',
            'manager_last': 'Smith',
            'manager_email': 'Angela.Smith@toshibagcs.com'
        },
        {
            'date': '2025-08-11',
            'region': 'Central',
            'first_name': 'Colin',
            'last_name': 'Myers',
            'email': 'colin.myers@toshibagcs.com',
            'manager_first': 'Phillip',
            'manager_last': 'Toto',
            'manager_email': 'phillip.toto@toshibagcs.com'
        },
        {
            'date': '2025-08-18',
            'region': 'West',
            'first_name': 'Naoufel',
            'last_name': 'Boulaksout',
            'email': 'naoufel.boulaksout@toshibagcs.com',
            'manager_first': 'William',
            'manager_last': 'Krause',
            'manager_email': 'William.Krause@toshibagcs.com'
        },
        {
            'date': '2025-08-18',
            'region': 'East',
            'first_name': 'Thomas',
            'last_name': 'Kerfien',
            'email': 'thomas.kerfien@toshibagcs.com',
            'manager_first': 'John',
            'manager_last': 'Francis',
            'manager_email': 'John.Francis@toshibagcs.com'
        }
    ]
    
    # TECHNICIANS TO REMOVE (copy from email) 
    technicians_to_remove = [
        {
            'date': '2025-07-28',
            'region': 'West',
            'first_name': 'Thomas',
            'last_name': 'Brown',
            'email': 'Tom.Brown@toshibagcs.com'
        },
        {
            'date': '2025-07-28',
            'region': 'Central',
            'first_name': 'Aloysius',
            'last_name': 'Keaton',
            'email': 'Aloysius.Keaton@toshibagcs.com'
        },
        {
            'date': '2025-08-04',
            'region': 'Central',
            'first_name': 'Ampon',
            'last_name': 'Chanthavong',
            'email': 'ampon.chanthavong@toshibagcs.com'
        },
        {
            'date': '2025-08-18',
            'region': 'West',
            'first_name': 'Steven',
            'last_name': 'Eisenman',
            'email': 'Steven.Eisenman@toshibagcs.com'
        },
        {
            'date': '2025-08-18',
            'region': 'West',
            'first_name': 'Cory',
            'last_name': 'Smith',
            'email': 'Cory.Smith@toshibagcs.com'
        },
        {
            'date': '2025-08-18',
            'region': 'East',
            'first_name': 'Jaime',
            'last_name': 'Munguia',
            'email': 'Jimmy.Munguia@toshibagcs.com'
        }
    ]
    
    # ===== DO NOT MODIFY BELOW THIS LINE =====
    
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
        logger.info("✅ Connected to database for FST email updates")
        
        # ===== PROCESS DELETIONS FIRST =====
        logger.info(f"🗑️ Processing {len(technicians_to_remove)} deletions...")
        deleted_count = 0
        
        for tech in technicians_to_remove:
            try:
                # Find technician
                fst_record = await connection.fetchrow(
                    "SELECT id, full_name FROM fst_technicians WHERE fst_email = $1",
                    tech['email']
                )
                
                if fst_record:
                    # Delete assignments first (foreign key constraint)
                    assignments_deleted = await connection.execute(
                        "DELETE FROM fst_manager_assignments WHERE fst_id = $1",
                        fst_record['id']
                    )
                    
                    # Delete technician
                    await connection.execute(
                        "DELETE FROM fst_technicians WHERE fst_email = $1",
                        tech['email']
                    )
                    
                    logger.info(f"   ❌ DELETED: {fst_record['full_name']} ({tech['email']})")
                    deleted_count += 1
                    
                else:
                    logger.info(f"   ⚠️ NOT FOUND: {tech['email']} (may already be deleted)")
                    
            except Exception as e:
                logger.error(f"   ❌ Error deleting {tech['email']}: {e}")
        
        # ===== PROCESS ADDITIONS =====
        logger.info(f"➕ Processing {len(technicians_to_add)} additions...")
        added_count = 0
        updated_count = 0
        
        for tech in technicians_to_add:
            try:
                # Create manager name
                manager_name = f"{tech['manager_first']} {tech['manager_last']}"
                
                # Ensure manager exists
                manager_id = await connection.fetchval(
                    "SELECT id FROM manager_groups WHERE manager_name = $1",
                    manager_name
                )
                
                if not manager_id:
                    # Create new manager
                    manager_id = await connection.fetchval("""
                        INSERT INTO manager_groups (manager_name, manager_email, region, group_description)
                        VALUES ($1, $2, $3, $4)
                        RETURNING id
                    """, manager_name, tech['manager_email'], tech['region'], 
                        f"Team managed by {manager_name}")
                    
                    logger.info(f"   📝 Created new manager: {manager_name}")
                
                # Check if technician already exists
                existing_fst = await connection.fetchrow(
                    "SELECT id, full_name FROM fst_technicians WHERE fst_email = $1",
                    tech['email']
                )
                
                if existing_fst:
                    # Update existing technician
                    await connection.execute("""
                        UPDATE fst_technicians 
                        SET fst_first_name = $2, fst_last_name = $3, full_name = $4, 
                            region = $5, status = 'active'
                        WHERE fst_email = $1
                    """, tech['email'], tech['first_name'], tech['last_name'],
                        f"{tech['first_name']} {tech['last_name']}", tech['region'])
                    
                    fst_id = existing_fst['id']
                    updated_count += 1
                    logger.info(f"   🔄 UPDATED: {tech['first_name']} {tech['last_name']} ({tech['email']})")
                    
                else:
                    # Create new technician
                    fst_id = await connection.fetchval("""
                        INSERT INTO fst_technicians (fst_email, fst_first_name, fst_last_name, full_name, region, status)
                        VALUES ($1, $2, $3, $4, $5, 'active')
                        RETURNING id
                    """, tech['email'], tech['first_name'], tech['last_name'],
                        f"{tech['first_name']} {tech['last_name']}", tech['region'])
                    
                    added_count += 1
                    logger.info(f"   ✅ ADDED: {tech['first_name']} {tech['last_name']} ({tech['email']})")
                
                # Ensure assignment exists
                assignment_exists = await connection.fetchval(
                    "SELECT id FROM fst_manager_assignments WHERE fst_id = $1 AND manager_id = $2",
                    fst_id, manager_id
                )
                
                if not assignment_exists:
                    await connection.execute(
                        "INSERT INTO fst_manager_assignments (fst_id, manager_id) VALUES ($1, $2)",
                        fst_id, manager_id
                    )
                    logger.info(f"      🔗 Assigned to {manager_name}")
                else:
                    logger.info(f"      ℹ️ Already assigned to {manager_name}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error adding {tech['email']}: {e}")
        
        # ===== FINAL SUMMARY =====
        final_stats = await connection.fetchrow("""
            SELECT 
                COUNT(*) as total_fsts,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_fsts,
                (SELECT COUNT(*) FROM manager_groups) as managers,
                (SELECT COUNT(*) FROM fst_manager_assignments) as assignments
            FROM fst_technicians
        """)
        
        logger.info("=" * 50)
        logger.info("🎯 EMAIL UPDATE PROCESSING COMPLETE!")
        logger.info("   📊 SUMMARY:")
        logger.info(f"      Deleted: {deleted_count} technicians")
        logger.info(f"      Added: {added_count} new technicians")
        logger.info(f"      Updated: {updated_count} existing technicians")
        logger.info("   📈 FINAL DATABASE STATE:")
        logger.info(f"      Total FSTs: {final_stats['total_fsts']}")
        logger.info(f"      Active FSTs: {final_stats['active_fsts']}")
        logger.info(f"      Managers: {final_stats['managers']}")
        logger.info(f"      Assignments: {final_stats['assignments']}")
        logger.info("✅ Dashboard filtering will automatically reflect these changes!")
        logger.info("=" * 50)
        
        await connection.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database update failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(process_fst_email_updates())