import pandas as pd
import json
import sys
import os
import logging

sys.path.append('connectors')

from sharepoint_connector import SharePointConnector
from qdrant_connector import QdrantConnector

logging.basicConfig(level=logging.WARNING)


DOCUMENT_EXTENSIONS = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt']


def extract_zip_contents(sp_connector, zip_file_info):
    filename = zip_file_info['name']
    size_mb = zip_file_info.get('size', 0) / (1024 * 1024)
    contents = []

    try:
        import zipfile
        import requests
        from io import BytesIO
        import tempfile

        site_id, drive_id = sp_connector.get_site_and_drive_ids()
        download_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{zip_file_info['id']}/content"

        if size_mb > 100:
            print(f"  Downloading large ZIP ({size_mb:.1f}MB): {filename}")
            response = requests.get(download_url, headers=sp_connector.headers, verify=False, stream=True)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tempf:
                for chunk in response.iter_content(chunk_size=10*1024*1024):
                    tempf.write(chunk)
            zip_path = tempf.name
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for info in zf.infolist():
                    if not info.is_dir():
                        name = os.path.basename(info.filename)
                        if any(name.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS):
                            contents.append(name)
            os.unlink(zip_path)
        else:
            response = requests.get(download_url, headers=sp_connector.headers, verify=False)
            response.raise_for_status()
            with zipfile.ZipFile(BytesIO(response.content), 'r') as zf:
                for info in zf.infolist():
                    if not info.is_dir():
                        name = os.path.basename(info.filename)
                        if any(name.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS):
                            contents.append(name)
    except Exception as e:
        print(f"    Error extracting {filename}: {e}")
    return contents


def get_all_sharepoint_files(sp_connector):
    all_files = sp_connector.list_files_recursive()
    file_set = set()
    for file in all_files:
        name = file['name']
        if any(name.lower().endswith(ext) for ext in DOCUMENT_EXTENSIONS):
            file_set.add(name)
        elif name.lower().endswith('.zip'):
            print(f"Extracting ZIP: {name}")
            for zipped in extract_zip_contents(sp_connector, file):
                file_set.add(zipped)
    return file_set


def get_all_qdrant_files(qdrant_connector, collection_name):
    client = qdrant_connector.client
    all_docs = []
    offset = None
    while True:
        points, next_offset = client.scroll(
            collection_name=collection_name,
            limit=1000,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        all_docs.extend(points)
        if next_offset is None:
            break
        offset = next_offset

    qdrant_files = set()
    for doc in all_docs:
        payload = doc.payload or {}
        if payload.get('filename'):
            qdrant_files.add(payload['filename'].strip())
        if payload.get('table_filename'):
            tf = payload['table_filename'].strip()
            if '_page_' in tf:
                tf_clean = tf.split('_page_')[0] + '.pdf'
                qdrant_files.add(tf_clean)
            else:
                qdrant_files.add(tf)
    return qdrant_files


def main():
    print("="*60)
    print("KROGER — SHAREPOINT/QDRANT MISSING FILES REPORT")
    print("="*60)

    config_path = 'config/settings.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    sp_connector = SharePointConnector(config)
    qdrant_connector = QdrantConnector(config)

    print(">>> Scanning all SharePoint files (including ZIPs)...")
    sp_files = get_all_sharepoint_files(sp_connector)
    print(f"  {len(sp_files)} documents (.pdf, .docx, .xlsx, etc) found in SharePoint.")

    print(">>> Scanning Qdrant collection for ingested document files...")
    qdrant_files = get_all_qdrant_files(qdrant_connector, config['collection_name'])
    print(f"  {len(qdrant_files)} unique document files found in Qdrant.")

    matched = sp_files & qdrant_files
    missing = sorted(list(sp_files - qdrant_files))

    print(f"\n== SUMMARY ==")
    print(f"Total SharePoint docs: {len(sp_files)}")
    print(f"Total Qdrant docs    : {len(qdrant_files)}")
    print(f"Matched files        : {len(matched)}")
    print(f"Missing files        : {len(missing)}")
    match_percent = (len(matched) / len(sp_files)) * 100 if sp_files else 0
    print(f"Coverage            : {match_percent:.1f}%")

    # Excel report
    now = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    out_name = f'kroger_sharepoint_qdrant_missing_{now}.xlsx'
    with pd.ExcelWriter(out_name, engine='openpyxl') as writer:
        df_missing = pd.DataFrame({'MissingFile': missing})
        df_missing.to_excel(writer, sheet_name="Missing_Files", index=False)

        summary = pd.DataFrame({
            'Metric': [
                'Total SharePoint Files',
                'Total Qdrant Files',
                'Matched Files',
                'Missing Files',
                'Coverage Percent'
            ],
            'Value': [
                len(sp_files),
                len(qdrant_files),
                len(matched),
                len(missing),
                f"{match_percent:.1f}%"
            ]
        })
        summary.to_excel(writer, sheet_name="Summary", index=False)
    print(f"\nExcel report saved: {out_name}")


if __name__ == "__main__":
    main()
