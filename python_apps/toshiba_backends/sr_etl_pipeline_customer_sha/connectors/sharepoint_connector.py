import requests
from msal import ConfidentialClientApplication
from datetime import datetime
from dateutil import parser
import os
import urllib3
import logging
import json

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Replace the missing utils.logger with basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SharePointConnector:
    def __init__(self, config):
        self.tenant_id = config["tenant_id"]
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.site_url = config["sharepoint_site"]
        self.folder_path = config["sharepoint_folder"]
        self.token = self.authenticate()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def authenticate(self):
        app = ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret
        )
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        return result["access_token"]

    def get_site_and_drive_ids(self):
        site_resp = requests.get(
            f"https://graph.microsoft.com/v1.0/sites/{self.site_url}",
            headers=self.headers,
            verify=False
        )
        site_resp.raise_for_status()
        site_id = site_resp.json()["id"]
        print("Site ID:", site_id)

        drive_resp = requests.get(
            f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive",
            headers=self.headers,
            verify=False
        )
        drive_resp.raise_for_status()
        drive_id = drive_resp.json()["id"]
        print("Drive ID:", drive_id)

        return site_id, drive_id

    def list_files_recursive(self, folder_path=None):
        """Recursively list all files in folder and subfolders"""
        if folder_path is None:
            folder_path = self.folder_path
            
        site_id, drive_id = self.get_site_and_drive_ids()
        all_files = []
        
        # Get items in current folder
        folder_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{folder_path}:/children"
        
        try:
            response = requests.get(folder_url, headers=self.headers, verify=False)
            print(f"Checking folder: {folder_path}")
            response.raise_for_status()
            items = response.json().get("value", [])
            
            for item in items:
                if "folder" in item:
                    # This is a folder - recursively search it
                    subfolder_path = f"{folder_path}/{item['name']}"
                    print(f"Found subfolder: {item['name']}")
                    subfolder_files = self.list_files_recursive(subfolder_path)
                    all_files.extend(subfolder_files)
                else:
                    # This is a file - add full path info
                    item['full_path'] = folder_path
                    item['relative_path'] = f"{folder_path}/{item['name']}"
                    all_files.append(item)
                    print(f"Found file: {item['name']} in {folder_path}")
                    
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Folder not found: {folder_path}")
            else:
                raise
                
        return all_files

    def list_files(self):
        """Original method - now calls recursive version"""
        return self.list_files_recursive()

    def download_file(self, site_id, drive_id, item_id, filename, subfolder=""):
        """Download file with support for subfolder organization"""
        download_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{item_id}/content"
        
        # Create subfolder structure in temp directory
        if subfolder:
            safe_subfolder = subfolder.replace("/", "_").replace("\\", "_")
            local_dir = f"temp/{safe_subfolder}"
        else:
            local_dir = "temp"
            
        os.makedirs(local_dir, exist_ok=True)
        local_path = f"{local_dir}/{filename}"

        with open(local_path, "wb") as f:
            resp = requests.get(download_url, headers=self.headers, verify=False)
            resp.raise_for_status()
            f.write(resp.content)

        return local_path

    def download_excel_files(self, modified_after=None, created_after=None, filename_pattern=None, file_count=None, include_subfolders=True):
        """Download Excel files with optional subfolder support"""
        logger.info("Listing files from SharePoint...")
        
        if include_subfolders:
            files = self.list_files_recursive()
            logger.info(f"Found {len(files)} total files (including subfolders)")
        else:
            # Use original method for just the main folder
            site_id, drive_id = self.get_site_and_drive_ids()
            folder_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{self.folder_path}:/children"
            response = requests.get(folder_url, headers=self.headers, verify=False)
            response.raise_for_status()
            files = response.json().get("value", [])
            logger.info(f"Found {len(files)} files in main folder only")
        
        site_id, drive_id = self.get_site_and_drive_ids()
        filtered_files = []

        for file in files:
            # Skip if not Excel file
            if not file["name"].endswith(".xlsx"):
                continue
                
            # Apply date filters
            file_modified = parser.isoparse(file["lastModifiedDateTime"]).replace(tzinfo=None)
            file_created = parser.isoparse(file["createdDateTime"]).replace(tzinfo=None)

            if modified_after:
                filter_time = datetime.fromisoformat(modified_after)
                if file_modified < filter_time:
                    continue

            if created_after:
                filter_time = datetime.fromisoformat(created_after)
                if file_created < filter_time:
                    continue

            # Apply filename pattern filter
            if filename_pattern and filename_pattern not in file["name"]:
                continue

            filtered_files.append(file)

        # Limit number of files if specified
        if file_count:
            filtered_files = filtered_files[:file_count]

        # Download files
        downloaded_files = []
        for f in filtered_files:
            subfolder_path = f.get('full_path', '').replace(self.folder_path, '').strip('/')
            logger.info(f"Downloading: {f['name']} from {f.get('full_path', 'main folder')} (Modified: {f['lastModifiedDateTime']})")
            local_path = self.download_file(site_id, drive_id, f["id"], f["name"], subfolder_path)
            downloaded_files.append(local_path)

        logger.info(f"Downloaded {len(downloaded_files)} Excel files")
        return downloaded_files


# Example usage
if __name__ == "__main__":
    # Debug: Check current directory and look for settings files
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in current directory: {os.listdir('.')}")
    
    # Look for settings.json in multiple locations
    settings_paths = [
        'settings.json',
        '../settings.json', 
        '../../settings.json',
        '../config/settings.json',
        '../../config/settings.json',
        os.path.join(os.path.dirname(__file__), 'settings.json'),
        os.path.join(os.path.dirname(__file__), '..', 'settings.json'),
        os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json')
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
        print("Could not find settings.json in any expected location!")
        print("Tried paths:", settings_paths)
        exit(1)
    
    print(f"Loaded config from: {settings_file_used}")
    print("Config keys found:", list(config.keys()))
    
    try:
        connector = SharePointConnector(config)
        
        # Test with subfolders enabled (default)
        print("\n=== Testing with subfolders ===")
        files = connector.download_excel_files(file_count=5, include_subfolders=True)
        print(f"Downloaded {len(files)} files: {files}")
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"\nUsing settings from: {settings_file_used}")
        print("Make sure your settings.json contains valid SharePoint credentials")