import pandas as pd
from datetime import datetime
import os
from sharepoint_connector import SharePointConnector
from qdrant_connector import QdrantConnector
import logging

logger = logging.getLogger(__name__)

class FileTracker:
    def __init__(self, config):
        self.sp_connector = SharePointConnector(config)
        self.qdrant_connector = QdrantConnector(config)
        
    def create_tracking_report(self):
        """Create comprehensive tracking report"""
        logger.info("Starting file tracking analysis...")
        
        # Get SharePoint files
        sp_files = self.sp_connector.list_files_recursive()
        logger.info(f"Found {len(sp_files)} files in SharePoint")
        
        # Get Qdrant documents  
        qdrant_docs = self.qdrant_connector.get_all_documents()
        logger.info(f"Found {len(qdrant_docs)} documents in Qdrant")
        
        # Process and compare
        tracking_data = self.compare_files(sp_files, qdrant_docs)
        
        # Create Excel report
        report_path = self.generate_excel_report(tracking_data)
        
        return report_path
        
    def compare_files(self, sp_files, qdrant_docs):
        """Compare SharePoint files with Qdrant documents"""
        # You'll need to examine the qdrant_docs first to see 
        # how file paths are stored in the metadata
        
        tracking_records = []
        
        for sp_file in sp_files:
            record = {
                'file_name': sp_file['name'],
                'sharepoint_path': sp_file.get('relative_path', ''),
                'file_size': sp_file.get('size', 0),
                'modified_date': sp_file.get('lastModifiedDateTime', ''),
                'file_type': os.path.splitext(sp_file['name'])[1],
                'in_sharepoint': True,
                'in_qdrant': False,  # Will update this
                'status': 'Not Ingested'
            }
            tracking_records.append(record)
            
        return tracking_records
        
    def generate_excel_report(self, tracking_data):
        """Generate Excel tracking report"""
        df = pd.DataFrame(tracking_data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"file_tracking_report_{timestamp}.xlsx"
        
        with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
            # Main tracking sheet
            df.to_excel(writer, sheet_name='File_Tracking', index=False)
            
            # Summary sheet
            summary = df.groupby('status').size().reset_index(name='count')
            summary.to_excel(writer, sheet_name='Summary', index=False)
            
        logger.info(f"Report saved as: {report_path}")
        return report_path