import pandas as pd
import json
import sys
import os
from datetime import datetime
import re
import logging
import zipfile
import requests
from io import BytesIO

# Add connectors to path
sys.path.append('connectors')

from sharepoint_connector import SharePointConnector
from qdrant_connector import QdrantConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SmartZipTracker:
    def __init__(self, config_path='config/settings.json', max_zip_size_mb=100):
        """Initialize tracker with ZIP size limit"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.sp_connector = SharePointConnector(self.config)
        self.qdrant_connector = QdrantConnector(self.config)
        self.max_zip_size = max_zip_size_mb * 1024 * 1024  # Convert to bytes
        
    def analyze_zip_file(self, zip_file_info):
        """Analyze ZIP file - extract only if small enough"""
        zip_size_mb = zip_file_info.get('size', 0) / (1024 * 1024)
        
        logger.info(f"ZIP Analysis: {zip_file_info['name']} ({zip_size_mb:.1f} MB)")
        
        if zip_file_info.get('size', 0) > self.max_zip_size:
            logger.warning(f"Skipping large ZIP: {zip_file_info['name']} ({zip_size_mb:.1f} MB)")
            return {
                'zip_name': zip_file_info['name'],
                'size_mb': zip_size_mb,
                'status': 'SKIPPED_TOO_LARGE',
                'contents': [],
                'estimated_files': 'Unknown (too large to extract)'
            }
        
        # Small enough - extract contents
        logger.info(f"Extracting small ZIP: {zip_file_info['name']}")
        try:
            site_id, drive_id = self.sp_connector.get_site_and_drive_ids()
            download_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{zip_file_info['id']}/content"
            
            response = requests.get(download_url, headers=self.sp_connector.headers, verify=False)
            response.raise_for_status()
            
            zip_contents = []
            with zipfile.ZipFile(BytesIO(response.content), 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if not file_info.is_dir():
                        zip_contents.append({
                            'file_name': os.path.basename(file_info.filename),
                            'full_path_in_zip': file_info.filename,
                            'file_size': file_info.file_size,
                            'file_type': os.path.splitext(file_info.filename)[1].lower()
                        })
            
            return {
                'zip_name': zip_file_info['name'],
                'size_mb': zip_size_mb,
                'status': 'EXTRACTED',
                'contents': zip_contents,
                'estimated_files': len(zip_contents)
            }
            
        except Exception as e:
            logger.error(f"Error extracting {zip_file_info['name']}: {e}")
            return {
                'zip_name': zip_file_info['name'],
                'size_mb': zip_size_mb,
                'status': 'EXTRACTION_FAILED',
                'contents': [],
                'estimated_files': 'Error during extraction'
            }
    
    def get_sharepoint_files_smart_zip(self):
        """Get SharePoint files with smart ZIP handling"""
        logger.info("Getting SharePoint files with smart ZIP analysis...")
        
        all_files = self.sp_connector.list_files_recursive()
        
        all_file_info = {}
        zip_analysis = {}
        total_zip_contents = 0
        
        for file in all_files:
            filename = file['name']
            
            # Regular file info
            file_info = {
                'file_name': filename,
                'full_path': file.get('relative_path', ''),
                'size': file.get('size', 0),
                'size_mb': file.get('size', 0) / (1024 * 1024),
                'modified_date': file.get('lastModifiedDateTime', ''),
                'created_date': file.get('createdDateTime', ''),
                'file_type': os.path.splitext(filename)[1].lower(),
                'folder': file.get('full_path', '').replace('/', ' > '),
                'source': 'SHAREPOINT_DIRECT'
            }
            
            all_file_info[filename] = file_info
            
            # Handle ZIP files smartly
            if filename.lower().endswith('.zip'):
                zip_result = self.analyze_zip_file(file)
                zip_analysis[filename] = zip_result
                
                # Only add contents if successfully extracted
                if zip_result['status'] == 'EXTRACTED':
                    for zip_content in zip_result['contents']:
                        zip_content_key = f"{filename}::{zip_content['file_name']}"
                        all_file_info[zip_content_key] = {
                            'file_name': zip_content['file_name'],
                            'full_path': f"{file_info['full_path']} (inside {filename})",
                            'size': zip_content['file_size'],
                            'size_mb': zip_content['file_size'] / (1024 * 1024),
                            'modified_date': file.get('lastModifiedDateTime', ''),
                            'created_date': file.get('createdDateTime', ''),
                            'file_type': zip_content['file_type'],
                            'folder': f"{file_info['folder']} > {filename}",
                            'source': 'ZIP_CONTENT',
                            'parent_zip': filename,
                            'path_in_zip': zip_content['full_path_in_zip']
                        }
                        total_zip_contents += 1
        
        logger.info("Smart ZIP analysis complete:")
        logger.info(f"  - Total files: {len(all_file_info)}")
        logger.info(f"  - ZIP contents extracted: {total_zip_contents}")
        logger.info(f"  - ZIP files analyzed: {len(zip_analysis)}")
        
        return all_file_info, zip_analysis
    
    def get_unique_files_from_qdrant(self):
        """Get unique files from Qdrant (same as before)"""
        logger.info("Getting all documents from Qdrant...")
        
        all_docs = []
        offset = None
        
        while True:
            try:
                result = self.qdrant_connector.client.scroll(
                    collection_name=self.config['collection_name'],
                    limit=1000,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                points, next_offset = result
                all_docs.extend(points)
                
                if next_offset is None:
                    break
                offset = next_offset
                
                if len(all_docs) % 1000 == 0:
                    logger.info(f"Retrieved {len(all_docs)} documents so far...")
                
            except Exception as e:
                logger.error(f"Error retrieving documents: {e}")
                break
        
        unique_files = set()
        filename_details = {}
        
        for doc in all_docs:
            if doc.payload:
                for field in ['filename', 'table_filename']:
                    if field in doc.payload and doc.payload[field]:
                        filename = doc.payload[field].strip()
                        if filename:
                            clean_filename = self.clean_filename(filename)
                            unique_files.add(clean_filename)
                            
                            if clean_filename not in filename_details:
                                filename_details[clean_filename] = {
                                    'original_filename': filename,
                                    'type': 'table' if field == 'table_filename' else 'document',
                                    'chunk_count': 0
                                }
                            filename_details[clean_filename]['chunk_count'] += 1
        
        logger.info(f"Found {len(unique_files)} unique files in Qdrant")
        return unique_files, filename_details
    
    def clean_filename(self, filename):
        """Clean filename for matching"""
        cleaned = re.sub(r'_page_\d+.*$', '', filename)
        cleaned = re.sub(r'\s*\(\d+\)(?=\.[^.]*$)', '', cleaned)
        
        if '.' in cleaned and not cleaned.endswith('.'):
            return cleaned
        
        if '.' not in cleaned:
            return cleaned + '.pdf'
        
        return cleaned
    
    def advanced_filename_matching(self, sp_filename, qdrant_filenames):
        """Advanced filename matching"""
        if sp_filename in qdrant_filenames:
            return sp_filename, "exact"
        
        sp_base = os.path.splitext(sp_filename)[0]
        for q_filename in qdrant_filenames:
            q_base = os.path.splitext(q_filename)[0]
            if sp_base.lower() == q_base.lower():
                return q_filename, "fuzzy_extension"
        
        sp_clean = re.sub(r'\s*\(\d+\)$', '', sp_base)
        for q_filename in qdrant_filenames:
            q_clean = re.sub(r'\s*\(\d+\)$', '', os.path.splitext(q_filename)[0])
            if sp_clean.lower() == q_clean.lower():
                return q_filename, "fuzzy_version"
        
        return None, "no_match"
    
    def compare_files_smart(self, sp_files, qdrant_files, qdrant_details):
        """Compare files with smart ZIP handling"""
        logger.info("Comparing files with smart ZIP analysis...")
        
        tracking_records = []
        qdrant_filenames = set(qdrant_files)
        matched_qdrant_files = set()
        
        for sp_key, sp_info in sp_files.items():
            sp_filename = sp_info['file_name']
            
            matched_qdrant_file, match_type = self.advanced_filename_matching(sp_filename, qdrant_filenames)
            
            in_qdrant = matched_qdrant_file is not None
            if in_qdrant:
                matched_qdrant_files.add(matched_qdrant_file)
            
            if match_type == "exact":
                status = "Ingested"
            elif match_type == "no_match":
                status = "Not Ingested"
            else:
                status = f"Ingested ({match_type})"
            
            record = {
                'file_name': sp_filename,
                'sharepoint_path': sp_info['full_path'],
                'folder': sp_info['folder'],
                'file_size_bytes': sp_info['size'],
                'file_size_mb': sp_info['size_mb'],
                'file_type': sp_info['file_type'],
                'modified_date': sp_info['modified_date'],
                'source_type': sp_info['source'],
                'parent_zip': sp_info.get('parent_zip', ''),
                'path_in_zip': sp_info.get('path_in_zip', ''),
                'in_sharepoint': True,
                'in_qdrant': in_qdrant,
                'status': status,
                'match_type': match_type,
                'matched_qdrant_file': matched_qdrant_file or '',
                'qdrant_chunks': qdrant_details.get(matched_qdrant_file, {}).get('chunk_count', 0) if in_qdrant else 0
            }
            tracking_records.append(record)
        
        # Add orphaned files
        orphaned_files = qdrant_filenames - matched_qdrant_files
        for qdrant_filename in orphaned_files:
            qdrant_info = qdrant_details.get(qdrant_filename, {})
            
            record = {
                'file_name': qdrant_filename,
                'sharepoint_path': 'NOT FOUND IN SHAREPOINT',
                'folder': 'N/A',
                'file_size_bytes': 0,
                'file_size_mb': 0,
                'file_type': os.path.splitext(qdrant_filename)[1].lower(),
                'modified_date': '',
                'source_type': 'QDRANT_ONLY',
                'parent_zip': '',
                'path_in_zip': '',
                'in_sharepoint': False,
                'in_qdrant': True,
                'status': 'Orphaned in Qdrant',
                'match_type': 'orphaned',
                'matched_qdrant_file': qdrant_filename,
                'qdrant_chunks': qdrant_info.get('chunk_count', 0)
            }
            tracking_records.append(record)
        
        return tracking_records
    
    def generate_smart_excel_report(self, tracking_data, zip_analysis):
        """Generate report with ZIP analysis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"kroger_smart_zip_tracking_report_{timestamp}.xlsx"
        
        logger.info(f"Generating smart ZIP report: {report_path}")
        
        df = pd.DataFrame(tracking_data)
        
        with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
            # Main tracking
            df.to_excel(writer, sheet_name='File_Tracking', index=False)
            
            # ZIP analysis summary
            zip_summary = []
            for zip_name, zip_info in zip_analysis.items():
                zip_summary.append({
                    'ZIP_Name': zip_name,
                    'Size_MB': f"{zip_info['size_mb']:.1f}",
                    'Status': zip_info['status'],
                    'Files_Inside': zip_info['estimated_files'],
                    'Extraction_Note': 'Too large - skipped' if zip_info['status'] == 'SKIPPED_TOO_LARGE' else 'Extracted successfully'
                })
            
            zip_df = pd.DataFrame(zip_summary)
            zip_df.to_excel(writer, sheet_name='ZIP_Analysis', index=False)
            
            # Extracted ZIP contents only
            zip_contents = df[df['source_type'] == 'ZIP_CONTENT']
            if not zip_contents.empty:
                zip_contents.to_excel(writer, sheet_name='ZIP_Contents', index=False)
            
            # Summary
            summary_data = [
                {'Metric': 'Total SharePoint Files', 'Count': len(df[df['in_sharepoint'] == True])},
                {'Metric': 'ZIP Files Found', 'Count': len(zip_analysis)},
                {'Metric': 'Large ZIPs Skipped', 'Count': len([z for z in zip_analysis.values() if z['status'] == 'SKIPPED_TOO_LARGE'])},
                {'Metric': 'Small ZIPs Extracted', 'Count': len([z for z in zip_analysis.values() if z['status'] == 'EXTRACTED'])},
                {'Metric': 'ZIP Contents Extracted', 'Count': len(df[df['source_type'] == 'ZIP_CONTENT'])},
                {'Metric': 'Total Qdrant Files', 'Count': len(df[df['in_qdrant'] == True])},
                {'Metric': 'Files Ingested', 'Count': len(df[df['status'].str.contains('Ingested')])},
                {'Metric': 'Files Not Ingested', 'Count': len(df[df['status'] == 'Not Ingested'])}
            ]
            
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        return report_path
    
    def run_smart_analysis(self):
        """Run smart ZIP-aware analysis"""
        logger.info(f"Starting smart ZIP analysis (max ZIP size: {self.max_zip_size/(1024*1024):.0f} MB)...")
        
        try:
            # Get files with smart ZIP handling
            sp_files, zip_analysis = self.get_sharepoint_files_smart_zip()
            
            # Get Qdrant files
            qdrant_files, qdrant_details = self.get_unique_files_from_qdrant()
            
            # Compare
            tracking_data = self.compare_files_smart(sp_files, qdrant_files, qdrant_details)
            
            # Generate report
            report_path = self.generate_smart_excel_report(tracking_data, zip_analysis)
            
            # Print summary
            df = pd.DataFrame(tracking_data)
            large_zips = len([z for z in zip_analysis.values() if z['status'] == 'SKIPPED_TOO_LARGE'])
            extracted_zips = len([z for z in zip_analysis.values() if z['status'] == 'EXTRACTED'])
            
            print("\n" + "="*70)
            print("📊 SMART ZIP-AWARE KROGER ANALYSIS SUMMARY")
            print("="*70)
            print(f"📁 Total SharePoint Files: {len(df[df['in_sharepoint'] == True])}")
            print(f"📦 ZIP Files Found: {len(zip_analysis)}")
            print(f"   ├── Large ZIPs Skipped: {large_zips}")
            print(f"   └── Small ZIPs Extracted: {extracted_zips}")
            print(f"📄 ZIP Contents Found: {len(df[df['source_type'] == 'ZIP_CONTENT'])}")
            print(f"🗄️  Qdrant Files: {len(df[df['in_qdrant'] == True])}")
            print(f"✅ Files Ingested: {len(df[df['status'].str.contains('Ingested')])}")
            print(f"❌ Files Not Ingested: {len(df[df['status'] == 'Not Ingested'])}")
            print(f"📄 Report: {report_path}")
            print("="*70)
            
            # Show ZIP details
            print("\n📦 ZIP FILE ANALYSIS:")
            for zip_name, zip_info in zip_analysis.items():
                status_icon = "🚫" if zip_info['status'] == 'SKIPPED_TOO_LARGE' else "✅"
                print(f"{status_icon} {zip_name}: {zip_info['size_mb']:.1f} MB - {zip_info['status']}")
            
            return report_path
            
        except Exception as e:
            logger.error(f"Error in smart analysis: {e}")
            raise


if __name__ == "__main__":
    try:
        # Set max ZIP size to 100MB (adjust as needed)
        tracker = SmartZipTracker(max_zip_size_mb=100)
        report_path = tracker.run_smart_analysis()
        print(f"\n🎉 Smart analysis complete! Check: {report_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Failed to run smart analysis: {e}")