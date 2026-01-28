import asyncpg
import asyncio
import sys
import os
import json
from urllib.parse import urlparse
from datetime import datetime

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(parent_dir)
from utils.logger import logger

async def analyze_database_state():
    """Comprehensive analysis of current database state to identify issues"""
    
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
        logger.info("✅ Connected to database for analysis")
        
        analysis_results = {}
        
        # 1. BASIC TABLE INFORMATION
        logger.info("=" * 60)
        logger.info("1. BASIC TABLE INFORMATION")
        logger.info("=" * 60)
        
        tables = await connection.fetch("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name AND table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        table_info = {}
        for table in tables:
            table_name = table['table_name']
            row_count = await connection.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            
            table_info[table_name] = {
                'row_count': row_count,
                'column_count': table['column_count']
            }
            
            logger.info(f"📊 {table_name}: {row_count:,} rows, {table['column_count']} columns")
        
        analysis_results['table_info'] = table_info
        
        # 2. DUPLICATE ANALYSIS
        logger.info("\n" + "=" * 60)
        logger.info("2. DUPLICATE ANALYSIS")
        logger.info("=" * 60)
        
        # Check for duplicates in service_requests (main table)
        sr_duplicates = await connection.fetch("""
            SELECT sr_number, COUNT(*) as duplicate_count
            FROM service_requests
            GROUP BY sr_number
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 20
        """)
        
        total_duplicate_srs = len(sr_duplicates)
        if total_duplicate_srs > 0:
            total_duplicate_rows = sum([dup['duplicate_count'] - 1 for dup in sr_duplicates])
            logger.warning(f"🚨 Found {total_duplicate_srs} service requests with duplicates")
            logger.warning(f"🚨 Total duplicate rows: {total_duplicate_rows}")
            
            logger.info("Top 10 most duplicated SRs:")
            for dup in sr_duplicates[:10]:
                logger.info(f"   SR {dup['sr_number']}: {dup['duplicate_count']} copies")
        else:
            logger.info("✅ No duplicate service requests found")
        
        analysis_results['sr_duplicates'] = {
            'unique_duplicated_srs': total_duplicate_srs,
            'total_duplicate_rows': sum([dup['duplicate_count'] - 1 for dup in sr_duplicates]) if sr_duplicates else 0,
            'sample_duplicates': [dict(dup) for dup in sr_duplicates[:10]]
        }
        
        # Check customer duplicates
        customer_duplicates = await connection.fetch("""
            SELECT customer_account_number, COUNT(*) as duplicate_count
            FROM customers
            GROUP BY customer_account_number
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 10
        """)
        
        if customer_duplicates:
            logger.warning(f"🚨 Found {len(customer_duplicates)} customers with duplicates")
            for dup in customer_duplicates:
                logger.info(f"   Customer {dup['customer_account_number']}: {dup['duplicate_count']} copies")
        
        analysis_results['customer_duplicates'] = len(customer_duplicates)
        
        # 3. DATA QUALITY ISSUES
        logger.info("\n" + "=" * 60)
        logger.info("3. DATA QUALITY ANALYSIS")
        logger.info("=" * 60)
        
        # Check for NULL primary keys
        null_sr_numbers = await connection.fetchval("""
            SELECT COUNT(*) FROM service_requests WHERE sr_number IS NULL
        """)
        
        # Check for empty/invalid data
        empty_customer_accounts = await connection.fetchval("""
            SELECT COUNT(*) FROM service_requests 
            WHERE customer_account_number IS NULL OR customer_account_number = ''
        """)
        
        # Check date ranges
        date_stats = await connection.fetchrow("""
            SELECT 
                MIN(incident_date) as earliest_incident,
                MAX(incident_date) as latest_incident,
                MIN(closed_date) as earliest_closed,
                MAX(closed_date) as latest_closed,
                COUNT(CASE WHEN incident_date IS NULL THEN 1 END) as null_incident_dates,
                COUNT(CASE WHEN closed_date IS NULL THEN 1 END) as null_closed_dates
            FROM service_requests
        """)
        
        logger.info(f"📅 Date range: {date_stats['earliest_incident']} to {date_stats['latest_incident']}")
        logger.info(f"📅 Closed dates: {date_stats['earliest_closed']} to {date_stats['latest_closed']}")
        logger.info(f"⚠️  NULL incident dates: {date_stats['null_incident_dates']:,}")
        logger.info(f"⚠️  NULL closed dates: {date_stats['null_closed_dates']:,}")
        logger.info(f"⚠️  NULL SR numbers: {null_sr_numbers:,}")
        logger.info(f"⚠️  Empty customer accounts: {empty_customer_accounts:,}")
        
        analysis_results['data_quality'] = {
            'null_sr_numbers': null_sr_numbers,
            'empty_customer_accounts': empty_customer_accounts,
            'date_stats': dict(date_stats)
        }
        
        # 4. RELATIONSHIP INTEGRITY
        logger.info("\n" + "=" * 60)
        logger.info("4. RELATIONSHIP INTEGRITY")
        logger.info("=" * 60)
        
        # Check orphaned records
        orphaned_tasks = await connection.fetchval("""
            SELECT COUNT(*) FROM tasks t
            LEFT JOIN service_requests sr ON t.sr_number = sr.sr_number
            WHERE sr.sr_number IS NULL
        """)
        
        orphaned_parts = await connection.fetchval("""
            SELECT COUNT(*) FROM parts_used p
            LEFT JOIN tasks t ON p.task_number = t.task_number
            WHERE t.task_number IS NULL
        """)
        
        orphaned_notes = await connection.fetchval("""
            SELECT COUNT(*) FROM sr_notes n
            LEFT JOIN service_requests sr ON n.sr_number = sr.sr_number
            WHERE sr.sr_number IS NULL
        """)
        
        logger.info(f"🔗 Orphaned tasks: {orphaned_tasks:,}")
        logger.info(f"🔗 Orphaned parts: {orphaned_parts:,}")
        logger.info(f"🔗 Orphaned notes: {orphaned_notes:,}")
        
        analysis_results['orphaned_records'] = {
            'tasks': orphaned_tasks,
            'parts': orphaned_parts,
            'notes': orphaned_notes
        }
        
        # 5. SCHEMA ANALYSIS
        logger.info("\n" + "=" * 60)
        logger.info("5. SCHEMA ANALYSIS")
        logger.info("=" * 60)
        
        # Check for fields that might be too long
        long_fields_analysis = await connection.fetch("""
            SELECT 
                'machine_type' as field_name,
                MAX(LENGTH(machine_type)) as max_length,
                COUNT(CASE WHEN LENGTH(machine_type) > 100 THEN 1 END) as over_limit_count
            FROM service_requests
            WHERE machine_type IS NOT NULL
            
            UNION ALL
            
            SELECT 
                'machine_model' as field_name,
                MAX(LENGTH(machine_model)) as max_length,
                COUNT(CASE WHEN LENGTH(machine_model) > 100 THEN 1 END) as over_limit_count
            FROM service_requests
            WHERE machine_model IS NOT NULL
            
            UNION ALL
            
            SELECT 
                'machine_serial_number' as field_name,
                MAX(LENGTH(machine_serial_number)) as max_length,
                COUNT(CASE WHEN LENGTH(machine_serial_number) > 100 THEN 1 END) as over_limit_count
            FROM service_requests
            WHERE machine_serial_number IS NOT NULL
        """)
        
        logger.info("📏 Field length analysis:")
        for field in long_fields_analysis:
            logger.info(f"   {field['field_name']}: max {field['max_length']} chars, {field['over_limit_count']} over 100 limit")
        
        analysis_results['schema_issues'] = [dict(field) for field in long_fields_analysis]
        
        # 6. RECENT DATA ACTIVITY
        logger.info("\n" + "=" * 60)
        logger.info("6. RECENT DATA ACTIVITY")
        logger.info("=" * 60)
        
        recent_data = await connection.fetch("""
            SELECT 
                DATE(created_at) as load_date,
                COUNT(*) as records_loaded
            FROM service_requests
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY load_date DESC
            LIMIT 10
        """)
        
        if recent_data:
            logger.info("📈 Recent data loads (last 30 days):")
            for day in recent_data:
                logger.info(f"   {day['load_date']}: {day['records_loaded']:,} records")
        else:
            logger.warning("⚠️  No recent data loads found")
        
        analysis_results['recent_activity'] = [dict(day) for day in recent_data]
        
        # 7. SUMMARY RECOMMENDATIONS
        logger.info("\n" + "=" * 60)
        logger.info("7. SUMMARY & RECOMMENDATIONS")
        logger.info("=" * 60)
        
        recommendations = []
        
        if analysis_results['sr_duplicates']['total_duplicate_rows'] > 0:
            recommendations.append("🔧 CRITICAL: Remove duplicate service requests")
        
        if analysis_results['orphaned_records']['tasks'] > 0:
            recommendations.append("🔧 MEDIUM: Clean up orphaned task records")
        
        if any(field['over_limit_count'] > 0 for field in analysis_results['schema_issues']):
            recommendations.append("🔧 HIGH: Increase VARCHAR limits for schema fields")
        
        if analysis_results['data_quality']['null_sr_numbers'] > 0:
            recommendations.append("🔧 CRITICAL: Handle NULL SR numbers")
        
        recommendations.append("🔧 LOW: Implement incremental loading to prevent future duplicates")
        
        for rec in recommendations:
            logger.info(rec)
        
        analysis_results['recommendations'] = recommendations
        analysis_results['analysis_timestamp'] = datetime.now().isoformat()
        
        # Save analysis results
        os.makedirs('analysis', exist_ok=True)
        with open('analysis/analysis_results.json', 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        logger.info("\n✅ Analysis complete! Results saved to analysis/database_audit/analysis_results.json")
        
        await connection.close()
        return analysis_results
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(analyze_database_state())