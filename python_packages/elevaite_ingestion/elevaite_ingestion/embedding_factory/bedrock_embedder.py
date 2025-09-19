import os
import json
from typing import List

try:
    import boto3
except Exception:
    boto3 = None  # type: ignore


def get_embedding(text: str, model: str | None = None, region: str | None = None) -> List[float]:
    """Generate an embedding via AWS Bedrock runtime.

    - Requires boto3 and AWS credentials
    - model defaults to "amazon.titan-embed-text-v1" if not provided
    - region defaults to AWS_REGION or us-east-1
    """
    if boto3 is None:
        raise ImportError("boto3 is not installed. Install boto3 to use bedrock embeddings.")

    model_id = model or os.getenv("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v1")
    aws_region = region or os.getenv("AWS_REGION", "us-east-1")

    client = boto3.client("bedrock-runtime", region_name=aws_region)

    body = {"inputText": text}
    resp = client.invoke_model(modelId=model_id, body=json.dumps(body))
    payload = json.loads(resp["body"].read())

    # Common Titan embedding response shape: {"embedding": [..]}
    if "embedding" in payload:
        return list(payload["embedding"])  # type: ignore
    # Some providers might nest results; attempt best-effort extraction
    if "vector" in payload:
        return list(payload["vector"])  # type: ignore

    raise RuntimeError("Unexpected Bedrock embedding response shape")

