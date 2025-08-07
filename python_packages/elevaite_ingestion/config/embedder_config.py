import os
import json
import boto3
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

# from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import BedrockEmbeddings

load_dotenv()

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "config.json"
)


def load_config():
    """Load config.json dynamically."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}


config = load_config()

DEFAULT_PROVIDER = config["embedding"]["default_provider"]
DEFAULT_MODEL = config["embedding"]["default_model"]


def get_bedrock_client():
    """Initialize AWS Bedrock client."""
    try:
        return boto3.client(service_name="bedrock-runtime")
    except Exception as e:
        print(f"❌ Failed to initialize AWS Bedrock client: {e}")
        return None


def get_embedder():
    """Returns the correct embedding model based on the provider."""
    if DEFAULT_PROVIDER == "openai":
        return OpenAIEmbeddings(model=DEFAULT_MODEL)
    # elif DEFAULT_PROVIDER == "sentence_transformers":
    #     # return SentenceTransformer(DEFAULT_MODEL)
    elif DEFAULT_PROVIDER == "amazon_bedrock":
        bedrock_client = get_bedrock_client()
        if not bedrock_client:
            raise ValueError("❌ Bedrock client initialization failed.")
        return BedrockEmbeddings(model_id=DEFAULT_MODEL, client=bedrock_client)
    else:
        raise ValueError(f"❌ Unsupported embedding provider: {DEFAULT_PROVIDER}")


EMBEDDER_CONFIG = {
    "provider": DEFAULT_PROVIDER,
    "model": DEFAULT_MODEL,
    "models": config["embedding"]["providers"]
    .get(DEFAULT_PROVIDER, {})
    .get("models", {}),
}

print("🔍 Loaded EMBEDDER_CONFIG:", json.dumps(EMBEDDER_CONFIG, indent=4))
