#!/usr/bin/env python3
"""
Complete analysis runner for ETL pipeline investigation
Run this to get a full picture of current database and file processing state
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from utils.logger import logger

async def run_complete_analysis():
    """Run all analysis scripts and provide summary"""
    
    logger.info("🚀 Starting Complete ETL Pipeline Analysis")
    logger.info("=" * 80)
    
    try:
        # Import analysis modules
        sys.path.append('analysis')
        from database_audit import analyze_database_state
        from failed_files_investigation import analyze_failed_files, analyze_s3_vs_processed
        
        # 1. Analyze current database state
        logger.info("STEP 1: Analyzing database state...")
        db_analysis = await analyze_database_state()
        
        # 2. Analyze failed files
        logger.info("\nSTEP 2: Analyzing failed files...")
        failed_analysis = analyze_failed_files()
        
        # 3. Analyze processing gaps
        logger.info("\nSTEP 3: Analyzing processing gaps...")
        gap_analysis = analyze_s3_vs_processed()
        
        # 4. Generate summary report
        logger.info("\n" + "=" * 80)
        logger.info("EXECUTIVE SUMMARY")
        logger.info("=" * 80)
        
        total_db_rows = sum([info['row_count'] for info in db_analysis['table_info'].values()])
        duplicate_rows = db_analysis['sr_duplicates']['total_duplicate_rows']
        
        logger.info(f"📊 DATABASE STATE:")
        logger.info(f"   Total rows across all tables: {total_db_rows:,}")
        logger.info(f"   Service requests: {db_analysis['table_info']['service_requests']['row_count']:,}")
        logger.info(f"   Duplicate SR rows: {duplicate_rows:,}")
        
        if duplicate_rows > 0:
            duplicate_percentage = (duplicate_rows / db_analysis['table_info']['service_requests']['row_count']) * 100
            logger.warning(f"   Duplication rate: {duplicate_percentage:.1f}%")
        
        logger.info(f"\n📊 FILE PROCESSING STATE:")
        if gap_analysis:
            logger.info(f"   Successfully processed: {gap_analysis['processed_count']} files")
            logger.info(f"   Failed files: {gap_analysis['failed_count']} files")
            logger.info(f"   Estimated missing: {gap_analysis['estimated_missing']} files")
        
        logger.info(f"\n🎯 PRIORITY ACTION ITEMS:")
        
        priority_actions = []
        
        if duplicate_rows > 1000:
            priority_actions.append("🔴 CRITICAL: Remove database duplicates immediately")
        
        if failed_analysis and failed_analysis['total_failed_files'] > 50:
            priority_actions.append("🟠 HIGH: Fix CSV parsing for failed files")
        
        if db_analysis['data_quality']['null_sr_numbers'] > 0:
            priority_actions.append("🟠 HIGH: Handle NULL SR numbers")
        
        schema_issues = any(field['over_limit_count'] > 0 for field in db_analysis['schema_issues'])
        if schema_issues:
            priority_actions.append("🟡 MEDIUM: Update database schema for longer fields")
        
        priority_actions.append("🟢 LOW: Implement incremental loading system")
        
        for i, action in enumerate(priority_actions, 1):
            logger.info(f"   {i}. {action}")
        
        logger.info(f"\n📁 ANALYSIS FILES GENERATED:")
        logger.info(f"   - analysis/analysis_results.json")
        logger.info(f"   - analysis/failed_files_analysis.json")
        
        logger.info(f"\n✅ Analysis complete! Ready to proceed with fixes.")
        
        return {
            'database_analysis': db_analysis,
            'failed_files_analysis': failed_analysis,
            'gap_analysis': gap_analysis,
            'priority_actions': priority_actions
        }
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_complete_analysis())