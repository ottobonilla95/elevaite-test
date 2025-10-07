import asyncio
import json
import os
import pickle
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def investigate_unprocessed_files():
    """Deep dive into why 131 files were never processed"""
    
    print("="*80)
    print("INVESTIGATING UNPROCESSED FILES")
    print("="*80)
    
    # Load config
    config_paths = ['config/settings.json', 'settings.json']
    config = None
    for path in config_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                config = json.load(f)
            break
    
    if not config:
        print("ERROR: No configuration file found")
        return
    
    # Initialize S3 connector
    from connectors.S3Connector import S3Connector
    connector = S3Connector(config)
    
    # Get all files
    all_files = connector.list_files()
    data_files = [f for f in all_files if f['name'].endswith(('.csv', '.xlsx', '.xls'))]
    
    # Load processing logs
    processed_files = {}
    failed_files = []
    
    if os.path.exists('processed_files_log.pkl'):
        with open('processed_files_log.pkl', 'rb') as f:
            processed_files = pickle.load(f)
    
    if os.path.exists('failed_files_log.json'):
        with open('failed_files_log.json', 'r') as f:
            failed_files = json.load(f)
    
    # Identify unprocessed files
    processed_filenames = set(processed_files.keys())
    failed_filenames = {f['filename'] for f in failed_files}
    data_filenames = {f['name'] for f in data_files}
    
    unprocessed = data_filenames - processed_filenames - failed_filenames
    
    print(f"\n1. UNPROCESSED FILES COUNT: {len(unprocessed)}")
    
    # Get details for unprocessed files
    unprocessed_details = []
    for filename in unprocessed:
        file_info = next((f for f in data_files if f['name'] == filename), None)
        if file_info:
            unprocessed_details.append({
                'filename': filename,
                'size_bytes': file_info.get('Size', 0),
                'size_mb': file_info.get('Size', 0) / (1024 * 1024),
                'last_modified': file_info.get('LastModified'),
                'full_path': file_info.get('Key', '')
            })
    
    # Sort by upload date
    unprocessed_details.sort(key=lambda x: x['last_modified'] if x['last_modified'] else datetime.min)
    
    print(f"\n2. UPLOAD DATE DISTRIBUTION")
    print(f"   Earliest unprocessed file: {unprocessed_details[0]['last_modified'] if unprocessed_details else 'N/A'}")
    print(f"   Latest unprocessed file: {unprocessed_details[-1]['last_modified'] if unprocessed_details else 'N/A'}")
    
    # Group by date
    date_groups = {}
    for file_info in unprocessed_details:
        if file_info['last_modified']:
            date_key = file_info['last_modified'].strftime('%Y-%m-%d')
            if date_key not in date_groups:
                date_groups[date_key] = []
            date_groups[date_key].append(file_info)
    
    print(f"\n3. UNPROCESSED FILES BY UPLOAD DATE")
    for date_key in sorted(date_groups.keys()):
        files = date_groups[date_key]
        total_mb = sum(f['size_mb'] for f in files)
        print(f"   {date_key}: {len(files)} files ({total_mb:.2f} MB)")
    
    # Check if these files have any common patterns
    print(f"\n4. FILE NAME PATTERN ANALYSIS")
    
    # Check for common prefixes
    prefixes = {}
    for file_info in unprocessed_details:
        prefix = file_info['filename'].split('-')[0] if '-' in file_info['filename'] else 'other'
        prefixes[prefix] = prefixes.get(prefix, 0) + 1
    
    print(f"   Filename prefixes:")
    for prefix, count in sorted(prefixes.items(), key=lambda x: x[1], reverse=True):
        print(f"     {prefix}: {count} files")
    
    # Check folder paths
    print(f"\n5. FOLDER PATH ANALYSIS")
    folder_paths = {}
    for file_info in unprocessed_details:
        path_parts = file_info['full_path'].split('/')
        folder = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else 'root'
        folder_paths[folder] = folder_paths.get(folder, 0) + 1
    
    print(f"   Unprocessed files by folder:")
    for folder, count in sorted(folder_paths.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"     {folder}: {count} files")
    
    # Now test if we can actually read these files
    print(f"\n6. FILE READABILITY TEST (Testing first 5 unprocessed files)")
    
    test_results = []
    for i, file_info in enumerate(unprocessed_details[:5]):
        filename = file_info['filename']
        full_path = file_info['full_path']
        
        print(f"\n   Testing file {i+1}: {filename}")
        
        try:
            # Try to download and read the file
            file_data = connector.download_file(full_path)
            
            if file_data:
                # Try to parse as CSV
                import io
                if filename.endswith('.csv'):
                    try:
                        df = pd.read_csv(io.BytesIO(file_data), nrows=5)
                        test_results.append({
                            'filename': filename,
                            'status': 'READABLE',
                            'rows_sample': len(df),
                            'columns': len(df.columns),
                            'column_names': list(df.columns),
                            'error': None
                        })
                        print(f"      ✓ Successfully read CSV")
                        print(f"      - Columns: {len(df.columns)}")
                        print(f"      - Column names: {', '.join(list(df.columns)[:5])}...")
                    except Exception as csv_error:
                        test_results.append({
                            'filename': filename,
                            'status': 'CSV_ERROR',
                            'error': str(csv_error)
                        })
                        print(f"      ✗ CSV parsing error: {csv_error}")
                else:
                    test_results.append({
                        'filename': filename,
                        'status': 'NON_CSV',
                        'error': 'Not a CSV file'
                    })
                    print(f"      - Non-CSV file type")
            else:
                test_results.append({
                    'filename': filename,
                    'status': 'DOWNLOAD_FAILED',
                    'error': 'Could not download file'
                })
                print(f"      ✗ Could not download file")
                
        except Exception as e:
            test_results.append({
                'filename': filename,
                'status': 'ERROR',
                'error': str(e)
            })
            print(f"      ✗ Error: {e}")
    
    # Compare with processed files - timing analysis
    print(f"\n7. TIMING ANALYSIS")
    
    # Get last processed file date
    if processed_files:
        last_processed_time = max([v.get('processed_at', datetime.min) if isinstance(v, dict) else datetime.min 
                                   for v in processed_files.values()])
        print(f"   Last ETL run (last processed file): {last_processed_time}")
        
        # Count unprocessed files uploaded before/after last run
        if unprocessed_details:
            before_last_run = [f for f in unprocessed_details 
                             if f['last_modified'] and f['last_modified'] < last_processed_time]
            after_last_run = [f for f in unprocessed_details 
                            if f['last_modified'] and f['last_modified'] >= last_processed_time]
            
            print(f"   Unprocessed files uploaded BEFORE last ETL run: {len(before_last_run)}")
            print(f"   Unprocessed files uploaded AFTER last ETL run: {len(after_last_run)}")
            
            if before_last_run:
                print(f"\n   ⚠️ WARNING: {len(before_last_run)} files were in S3 BEFORE last run but weren't processed!")
                print(f"   This suggests the ETL script may have skipped them for a reason.")
                print(f"\n   Sample of files that should have been processed:")
                for f in before_last_run[:5]:
                    print(f"     - {f['filename']} (uploaded {f['last_modified']})")
    
    # Generate recommendations
    print(f"\n" + "="*80)
    print("FINDINGS & RECOMMENDATIONS")
    print("="*80)
    
    findings = []
    
    # Check if files are readable
    readable_count = sum(1 for r in test_results if r['status'] == 'READABLE')
    error_count = sum(1 for r in test_results if r['status'] not in ['READABLE', 'NON_CSV'])
    
    if readable_count > 0:
        findings.append({
            'finding': f'{readable_count} of {len(test_results)} tested files are readable and parseable',
            'recommendation': 'Files appear valid - investigate why ETL script skipped them'
        })
    
    if error_count > 0:
        findings.append({
            'finding': f'{error_count} of {len(test_results)} tested files have parsing errors',
            'recommendation': 'These files may have data quality issues similar to the 104 failed files'
        })
    
    # Check folder patterns
    unique_folders = len(folder_paths)
    if unique_folders > 10:
        findings.append({
            'finding': f'Unprocessed files spread across {unique_folders} different folders',
            'recommendation': 'ETL script may not be scanning all folder paths correctly'
        })
    
    for i, finding in enumerate(findings, 1):
        print(f"\n{i}. {finding['finding']}")
        print(f"   → {finding['recommendation']}")
    
    # Export detailed results
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_unprocessed': len(unprocessed),
            'date_range': {
                'earliest': unprocessed_details[0]['last_modified'].isoformat() if unprocessed_details else None,
                'latest': unprocessed_details[-1]['last_modified'].isoformat() if unprocessed_details else None
            },
            'total_size_mb': sum(f['size_mb'] for f in unprocessed_details)
        },
        'unprocessed_files': unprocessed_details,
        'test_results': test_results,
        'date_distribution': {k: len(v) for k, v in date_groups.items()},
        'folder_distribution': folder_paths,
        'findings': findings
    }
    
    output_file = 'unprocessed_files_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)
    
    print(f"\nDetailed analysis exported to: {output_file}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(investigate_unprocessed_files())