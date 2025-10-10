import json
import sys
sys.path.append('connectors')

from sharepoint_connector import SharePointConnector
import requests

def find_sharepoint_libraries():
    """Find available document libraries in SharePoint"""
    
    # Load config
    with open('config/settings.json', 'r') as f:
        config = json.load(f)
    
    try:
        connector = SharePointConnector(config)
        site_id, drive_id = connector.get_site_and_drive_ids()
        
        print("✅ Connected to SharePoint successfully!")
        print(f"Site ID: {site_id}")
        print(f"Drive ID: {drive_id}")
        
        # Try to list root items to see what's available
        root_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root/children"
        
        response = requests.get(root_url, headers=connector.headers, verify=False)
        print(f"\n📂 Root folder contents:")
        print("="*50)
        
        if response.status_code == 200:
            items = response.json().get("value", [])
            for item in items:
                item_type = "📁 Folder" if "folder" in item else "📄 File"
                print(f"{item_type}: {item['name']}")
                
                # If it's a folder, try to peek inside
                if "folder" in item:
                    folder_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{item['id']}/children"
                    folder_response = requests.get(folder_url, headers=connector.headers, verify=False)
                    if folder_response.status_code == 200:
                        folder_items = folder_response.json().get("value", [])
                        print(f"   └── Contains {len(folder_items)} items")
                        # Show first few items
                        for sub_item in folder_items[:3]:
                            sub_type = "📁" if "folder" in sub_item else "📄"
                            print(f"       {sub_type} {sub_item['name']}")
                        if len(folder_items) > 3:
                            print(f"       ... and {len(folder_items) - 3} more")
        else:
            print(f"❌ Error accessing root: {response.status_code}")
            print(response.text)
            
        # Also try to get all drives/libraries
        print(f"\n📚 All document libraries:")
        print("="*50)
        drives_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
        drives_response = requests.get(drives_url, headers=connector.headers, verify=False)
        
        if drives_response.status_code == 200:
            drives = drives_response.json().get("value", [])
            for drive in drives:
                print(f"📚 Library: {drive.get('name', 'Unknown')}")
                print(f"   ID: {drive.get('id', 'Unknown')}")
                print(f"   Description: {drive.get('description', 'No description')}")
                print()
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_sharepoint_libraries()