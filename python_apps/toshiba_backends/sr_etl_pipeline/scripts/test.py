import json
import sys

# Add the connectors directory to path if needed
sys.path.append('connectors')

try:
    from connectors.qdrant_connector import QdrantConnector
except ImportError:
    # If the import fails, try importing from current directory
    from qdrant_connector import QdrantConnector

def test_qdrant_connection():
    """Test Qdrant connection and examine metadata structure"""
    
    # Load config
    try:
        with open('config/settings.json', 'r') as f:
            config = json.load(f)
        print("✅ Config loaded successfully")
        print(f"Qdrant URL: {config.get('qdrant_url', 'Not found')}")
        print(f"Collection: {config.get('collection_name', 'Not found')}")
    except FileNotFoundError:
        print("❌ Config file not found at config/settings.json")
        return
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return

    # Test Qdrant connection
    try:
        qdrant = QdrantConnector(config)
        print("✅ Qdrant connector initialized")
        
        # Get collection info
        collection_info = qdrant.client.get_collection(config['collection_name'])
        print(f"✅ Collection found: {collection_info.points_count} documents")
        
        # Get sample documents
        print("\n📋 Sample documents from Qdrant:")
        print("="*50)
        
        sample_docs = qdrant.client.scroll(
            config['collection_name'], 
            limit=3, 
            with_payload=True,
            with_vectors=False
        )
        
        for i, doc in enumerate(sample_docs[0], 1):
            print(f"\n📄 Document {i}:")
            print(f"   ID: {doc.id}")
            print(f"   Payload keys: {list(doc.payload.keys()) if doc.payload else 'No payload'}")
            
            if doc.payload:
                # Look for file-related fields
                for key, value in doc.payload.items():
                    if any(term in key.lower() for term in ['file', 'path', 'name', 'source', 'document']):
                        print(f"   🗂️  {key}: {value}")
                    elif any(term in key.lower() for term in ['date', 'time', 'created', 'modified']):
                        print(f"   📅 {key}: {value}")
                        
            print("-" * 30)
            
        # Summary of all unique payload keys
        all_keys = set()
        sample_docs_large = qdrant.client.scroll(
            config['collection_name'], 
            limit=50, 
            with_payload=True,
            with_vectors=False
        )
        
        for doc in sample_docs_large[0]:
            if doc.payload:
                all_keys.update(doc.payload.keys())
                
        print(f"\n🔍 All unique metadata fields found (from {len(sample_docs_large[0])} documents):")
        for key in sorted(all_keys):
            print(f"   - {key}")
            
    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")
        print(f"   Make sure Qdrant is running at {config.get('qdrant_url')}:{config.get('qdrant_port')}")

if __name__ == "__main__":
    print("🔬 Testing Qdrant Connection")
    print("="*40)
    test_qdrant_connection()