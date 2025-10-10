#!/usr/bin/env python3
"""
Debug script to check actual column names in CSV files
"""
import os
import json
import pandas as pd
import sys

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from connectors.S3Connector import S3Connector

def check_csv_columns():
    """Download and check column names from a few CSV files"""
    
    # Load config
    with open("config/settings.json") as f:
        config = json.load(f)
    
    connector = S3Connector(config)
    
    # Get a few files to check
    s3_files = connector.list_files()
    csv_files = [f for f in s3_files if f['name'].endswith('.csv')][:3]  # Just check first 3
    
    print("Checking column names in CSV files...")
    print("=" * 50)
    
    for i, file_info in enumerate(csv_files, 1):
        filename = file_info['name']
        print(f"\n{i}. File: {filename}")
        
        try:
            # Download file
            local_path = connector.download_file(file_info['Key'], filename)
            
            # Read just the header
            df = pd.read_csv(local_path, nrows=0)  # Read only header
            
            print(f"   Columns ({len(df.columns)}):")
            for j, col in enumerate(df.columns):
                if 'customer' in col.lower() or 'name' in col.lower():
                    print(f"   {j:2d}. '{col}' ← CUSTOMER/NAME RELATED")
                else:
                    print(f"   {j:2d}. '{col}'")
            
            # Clean up
            if os.path.exists(local_path):
                os.remove(local_path)
            
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("Look for customer name columns above!")
    
    # Also check what your pipeline logs showed
    print("\nFrom your pipeline logs, you had these columns:")
    print("Check the console output from your last pipeline run for:")
    print("'Columns found: [...]' messages")

if __name__ == "__main__":
    check_csv_columns()