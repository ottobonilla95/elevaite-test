import boto3
from datetime import datetime
from dateutil import parser
import os
import logging
import urllib3

# Disable SSL warnings for corporate networks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class S3Connector:
    def __init__(self, config):
        self.bucket_name = config["s3_bucket"]
        self.folder_path = config.get("s3_folder", "")  # Optional folder prefix
        
        # Initialize S3 client with SSL verification disabled
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config["aws_access_key_id"],
            aws_secret_access_key=config["aws_secret_access_key"],
            region_name=config.get("aws_region", "us-west-1"),
            verify=False  # Disable SSL verification for corporate networks
        )
        
        logger.info(f"Connected to S3 bucket: {self.bucket_name}")
        if self.folder_path:
            logger.info(f"Folder prefix: {self.folder_path}")

    def list_files_recursive(self, folder_prefix=None):
        """Recursively list all files in S3 bucket/folder"""
        if folder_prefix is None:
            folder_prefix = self.folder_path
            
        all_files = []
        
        try:
            # Use paginator to handle large numbers of files
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=folder_prefix
            )
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        # Add path information
                        obj['full_path'] = os.path.dirname(obj['Key'])
                        obj['name'] = os.path.basename(obj['Key'])
                        all_files.append(obj)
                        
            logger.info(f"Found {len(all_files)} total objects in S3")
            
        except Exception as e:
            logger.error(f"Error listing S3 objects: {e}")
            raise
            
        return all_files

    def list_files(self):
        """Compatibility method - calls recursive version"""
        return self.list_files_recursive()

    def download_file(self, s3_key, filename, subfolder=""):
        """Download file from S3 with subfolder organization"""
        try:
            # Create local directory structure
            if subfolder:
                safe_subfolder = subfolder.replace("/", "_").replace("\\", "_")
                local_dir = f"temp/{safe_subfolder}"
            else:
                local_dir = "temp"
                
            os.makedirs(local_dir, exist_ok=True)
            local_path = f"{local_dir}/{filename}"
            
            # Download file from S3
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            logger.info(f"Downloaded: {filename} -> {local_path}")
            
            return local_path
            
        except Exception as e:
            logger.error(f"Error downloading {s3_key}: {e}")
            raise

    def download_excel_files(self, modified_after=None, created_after=None, filename_pattern=None, file_count=None, include_subfolders=True):
        """Download Excel files from S3 with filtering options"""
        logger.info("Listing files from S3...")
        
        # Get all files
        if include_subfolders:
            files = self.list_files_recursive()
            logger.info(f"Found {len(files)} total files (including subfolders)")
        else:
            # Just files in the main folder (no recursion)
            files = []
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=self.folder_path,
                    Delimiter='/'  # This prevents recursion
                )
                if 'Contents' in response:
                    for obj in response['Contents']:
                        obj['full_path'] = os.path.dirname(obj['Key'])
                        obj['name'] = os.path.basename(obj['Key'])
                        files.append(obj)
                logger.info(f"Found {len(files)} files in main folder only")
            except Exception as e:
                logger.error(f"Error listing main folder: {e}")
                raise
        
        filtered_files = []

        for file_obj in files:
            # Skip if not CSV or Excel file
            if not (file_obj["name"].endswith(".csv") or file_obj["name"].endswith(".xlsx")):
                continue
                
            # Skip if it's just a folder (ends with /)
            if file_obj["Key"].endswith("/"):
                continue
            
            # Apply date filters
            file_modified = file_obj["LastModified"].replace(tzinfo=None)

            if modified_after:
                filter_time = datetime.fromisoformat(modified_after)
                if file_modified < filter_time:
                    continue

            if created_after:
                filter_time = datetime.fromisoformat(created_after)
                if file_modified < filter_time:
                    continue

            # Apply filename pattern filter
            if filename_pattern and filename_pattern not in file_obj["name"]:
                continue

            filtered_files.append(file_obj)

        # Limit number of files if specified
        if file_count:
            filtered_files = filtered_files[:file_count]

        # Download files
        downloaded_files = []
        for f in filtered_files:
            subfolder_path = f.get('full_path', '').replace(self.folder_path, '').strip('/')
            logger.info(f"Downloading: {f['name']} from s3://{self.bucket_name}/{f['Key']} (Modified: {f['LastModified']})")
            local_path = self.download_file(f["Key"], f["name"], subfolder_path)
            downloaded_files.append(local_path)

        logger.info(f"Downloaded {len(downloaded_files)} Excel files")
        return downloaded_files

    def get_file_info(self, s3_key):
        """Get metadata for a specific S3 object"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return {
                'name': os.path.basename(s3_key),
                'Key': s3_key,
                'LastModified': response['LastModified'],
                'Size': response['ContentLength'],
                'full_path': os.path.dirname(s3_key)
            }
        except Exception as e:
            logger.error(f"Error getting file info for {s3_key}: {e}")
            return None


# Example usage and testing
if __name__ == "__main__":
    import json
    
    # Look for settings.json
    settings_paths = [
        'settings.json',
        'config/settings.json',
        '../config/settings.json'
    ]
    
    config = None
    settings_file_used = None
    
    for path in settings_paths:
        try:
            if os.path.exists(path):
                print(f"Found settings file at: {path}")
                with open(path, 'r') as f:
                    config = json.load(f)
                settings_file_used = path
                break
        except Exception as e:
            print(f"Could not read {path}: {e}")
            continue
    
    if config is None:
        print("Could not find settings.json!")
        print("Create a config/settings.json file with S3 credentials")
        exit(1)
    
    print(f"Loaded config from: {settings_file_used}")
    print("Config keys found:", list(config.keys()))
    
    try:
        connector = S3Connector(config)
        
        # Test listing files
        print("\n=== Testing S3 file listing ===")
        files = connector.list_files()
        print(f"Found {len(files)} total files")
        
        # Show first few files
        for i, file_obj in enumerate(files[:5]):
            print(f"  {file_obj['name']} (Modified: {file_obj['LastModified']})")
        
        # Test downloading Excel files
        print("\n=== Testing Excel file download ===")
        excel_files = connector.download_excel_files(file_count=2, include_subfolders=True)
        print(f"Downloaded {len(excel_files)} Excel files: {excel_files}")
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"\nUsing settings from: {settings_file_used}")
        print("Make sure your settings.json contains valid S3 credentials")