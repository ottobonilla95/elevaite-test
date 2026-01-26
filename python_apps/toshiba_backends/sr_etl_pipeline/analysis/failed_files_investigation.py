import json
import os
from collections import defaultdict, Counter
import sys
# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(parent_dir)
from utils.logger import logger

def analyze_failed_files():
    """Analyze the failed_files_log.json to understand failure patterns"""
    
    logger.info("=" * 60)
    logger.info("FAILED FILES ANALYSIS")
    logger.info("=" * 60)
    
    # Load failed files
    try:
        with open('failed_files_log.json', 'r') as f:
            failed_files = json.load(f)
    except FileNotFoundError:
        logger.error("failed_files_log.json not found!")
        return
    
    logger.info(f"Total failed files: {len(failed_files)}")
    
    # 1. ERROR TYPE ANALYSIS
    error_types = Counter()
    error_details = defaultdict(list)
    
    for file_data in failed_files:
        error_type = file_data.get('error_type', 'UNKNOWN')
        error_types[error_type] += 1
        error_details[error_type].append({
            'filename': file_data['filename'],
            'error': file_data['error'][:100] + '...' if len(file_data['error']) > 100 else file_data['error']
        })
    
    logger.info("\n📊 ERROR TYPE BREAKDOWN:")
    for error_type, count in error_types.most_common():
        percentage = (count / len(failed_files)) * 100
        logger.info(f"   {error_type}: {count} files ({percentage:.1f}%)")
    
    # 2. CSV FORMAT ERROR ANALYSIS
    csv_format_errors = [f for f in failed_files if f.get('error_type') == 'CSV_FORMAT_ERROR']
    if csv_format_errors:
        logger.info(f"\n🔍 CSV FORMAT ERROR DETAILS ({len(csv_format_errors)} files):")
        
        # Analyze field count mismatches
        field_mismatches = defaultdict(int)
        for error_file in csv_format_errors:
            error_msg = error_file['error']
            # Extract expected vs actual field counts
            if 'Expected' in error_msg and 'saw' in error_msg:
                try:
                    parts = error_msg.split('Expected ')[1].split(' fields')[0]
                    expected = int(parts)
                    actual = int(error_msg.split('saw ')[1].split('\n')[0])
                    mismatch_key = f"Expected {expected}, got {actual}"
                    field_mismatches[mismatch_key] += 1
                except:
                    pass
        
        logger.info("   Field count mismatches:")
        for mismatch, count in sorted(field_mismatches.items()):
            logger.info(f"      {mismatch}: {count} files")
    
    # 3. SCHEMA LENGTH ERROR ANALYSIS
    schema_errors = [f for f in failed_files if f.get('error_type') == 'SCHEMA_LENGTH_ERROR']
    if schema_errors:
        logger.info(f"\n📏 SCHEMA LENGTH ERRORS ({len(schema_errors)} files):")
        for error_file in schema_errors[:5]:  # Show first 5
            logger.info(f"   {error_file['filename']}: {error_file['error']}")
    
    # 4. EMPTY FILE ERRORS
    empty_errors = [f for f in failed_files if f.get('error_type') == 'EMPTY_FILE_ERROR']
    if empty_errors:
        logger.info(f"\n📄 EMPTY FILE ERRORS ({len(empty_errors)} files):")
        for error_file in empty_errors:
            logger.info(f"   {error_file['filename']}")
    
    # 5. RETRY COUNT ANALYSIS
    retry_counts = Counter([f.get('retry_count', 1) for f in failed_files])
    logger.info("\n🔄 RETRY ATTEMPTS:")
    for retry_count, count in sorted(retry_counts.items()):
        logger.info(f"   Attempt #{retry_count}: {count} files")
    
    # 6. FILENAME PATTERN ANALYSIS
    logger.info("\n📂 FILENAME PATTERNS:")
    
    patterns = {
        'part-files': len([f for f in failed_files if f['filename'].startswith('part-')]),
        'data-uuid-files': len([f for f in failed_files if 'data_' in f['filename'] and len(f['filename']) > 50]),
        'simple-names': len([f for f in failed_files if not f['filename'].startswith('part-') and 'data_' not in f['filename']]),
    }
    
    for pattern, count in patterns.items():
        logger.info(f"   {pattern}: {count} files")
    
    # 7. RECOMMENDATIONS
    logger.info("\n💡 RECOMMENDATIONS:")
    
    csv_error_percentage = (error_types['CSV_FORMAT_ERROR'] / len(failed_files)) * 100
    schema_error_percentage = (error_types.get('SCHEMA_LENGTH_ERROR', 0) / len(failed_files)) * 100
    
    if csv_error_percentage > 50:
        logger.info("   🔧 HIGH PRIORITY: Implement robust CSV parsing with dynamic field detection")
        logger.info("   🔧 Use pandas with error_bad_lines=False or implement custom parsing")
    
    if schema_error_percentage > 5:
        logger.info("   🔧 MEDIUM PRIORITY: Increase VARCHAR limits in database schema")
        logger.info("   🔧 Implement field truncation with logging")
    
    if empty_errors:
        logger.info("   🔧 LOW PRIORITY: Add file size validation before processing")
    
    logger.info("   🔧 GENERAL: Implement gradual retry with exponential backoff")
    logger.info("   🔧 GENERAL: Add file validation before processing (size, format, headers)")
    
    # Save detailed analysis
    analysis_output = {
        'total_failed_files': len(failed_files),
        'error_type_breakdown': dict(error_types),
        'field_mismatches': dict(field_mismatches) if 'field_mismatches' in locals() else {},
        'filename_patterns': patterns,
        'retry_distribution': dict(retry_counts),
        'sample_errors_by_type': {
            error_type: [
                {'filename': item['filename'], 'error': item['error']} 
                for item in error_details[error_type][:3]
            ]
            for error_type in error_types.keys()
        }
    }
    
    os.makedirs('analysis', exist_ok=True)
    with open('analysis/failed_files_analysis.json', 'w') as f:
        json.dump(analysis_output, f, indent=2)
    
    logger.info("\n✅ Failed files analysis saved to analysis/failed_files_investigation/failed_files_analysis.json")
    
    return analysis_output

def analyze_s3_vs_processed():
    """Compare S3 files vs processed files to find gaps"""
    
    logger.info("\n" + "=" * 60)
    logger.info("S3 vs PROCESSED FILES GAP ANALYSIS")
    logger.info("=" * 60)
    
    # This would need S3 connector to get full file list
    # For now, let's analyze what we can from existing logs
    
    try:
        # Load processed files log
        import pickle
        if os.path.exists('processed_files_log.pkl'):
            with open('processed_files_log.pkl', 'rb') as f:
                processed_files = pickle.load(f)
        else:
            processed_files = {}
        
        logger.info(f"📊 Total successfully processed files: {len(processed_files)}")
        
        # Load failed files
        with open('failed_files_log.json', 'r') as f:
            failed_files = json.load(f)
        
        failed_filenames = {f['filename'] for f in failed_files}
        
        logger.info(f"📊 Total failed files: {len(failed_filenames)}")
        logger.info(f"📊 Total files attempted: {len(processed_files) + len(failed_filenames)}")
        
        # Check for overlap (shouldn't exist)
        overlap = set(processed_files.keys()) & failed_filenames
        if overlap:
            logger.warning(f"⚠️  Found {len(overlap)} files in both processed and failed logs!")
            for filename in list(overlap)[:5]:
                logger.warning(f"      {filename}")
        
        # Based on your mention of 509 total files
        estimated_total_s3_files = 509
        estimated_missing = estimated_total_s3_files - len(processed_files) - len(failed_filenames)
        
        logger.info("\n📈 ESTIMATED COVERAGE:")
        logger.info(f"   Successfully processed: {len(processed_files)}/{estimated_total_s3_files} ({len(processed_files)/estimated_total_s3_files*100:.1f}%)")
        logger.info(f"   Failed: {len(failed_filenames)}/{estimated_total_s3_files} ({len(failed_filenames)/estimated_total_s3_files*100:.1f}%)")
        logger.info(f"   Potentially missing: {estimated_missing}/{estimated_total_s3_files} ({estimated_missing/estimated_total_s3_files*100:.1f}%)")
        
        return {
            'processed_count': len(processed_files),
            'failed_count': len(failed_filenames),
            'estimated_missing': estimated_missing,
            'overlap_count': len(overlap)
        }
        
    except Exception as e:
        logger.error(f"Error in gap analysis: {e}")
        return None

if __name__ == "__main__":
    # Run failed files analysis
    failed_analysis = analyze_failed_files()
    
    # Run gap analysis
    gap_analysis = analyze_s3_vs_processed()
    
    logger.info("\n" + "=" * 60)
    logger.info("ANALYSIS COMPLETE - Next Steps:")
    logger.info("=" * 60)
    logger.info("1. Run database_analysis.py to check current database state")
    logger.info("2. Review analysis results in analysis/ directory")
    logger.info("3. Plan fixes based on recommendations")
    logger.info("=" * 60)