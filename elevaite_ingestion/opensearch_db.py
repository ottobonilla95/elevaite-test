from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3

region = 'us-east-2'
host = 'ymqp012rakuig1o6ir2h.us-east-2.aoss.amazonaws.com' 
index_name = 'toshiba-pdfs'

credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, region, "aoss")

client = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=60
)

embed_output = {
    "chunk_id": "036c23b3-4c2f-41ae-b6f8-246e6b508e76",
    "contextual_header": "sample header",
    "chunk_text": "a dummy chunk for testing.",
    "filename": "toshiba.pdf",
    "page_range": [34],
    "start_paragraph": 88,
    "end_paragraph": 90,
    "chunk_embedding": [0.0025, 0.0156, 0.0072, -0.0175, 0.0012, 0.0003]  
}

def upsert_chunk(doc):
    doc_id = doc["chunk_id"]
    body = {
        "chunk_text": doc["chunk_text"],
        "contextual_header": doc["contextual_header"],
        "filename": doc["filename"],
        "page_range": doc["page_range"],
        "start_paragraph": doc["start_paragraph"],
        "end_paragraph": doc["end_paragraph"],
        "chunk_embedding": doc["chunk_embedding"]
    }

    client.index(
        index=index_name,
        id=doc_id,
        body=body
    )

upsert_chunk(embed_output)
print("\nDocument upserted!")
