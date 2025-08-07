import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SUPPORTED_FORMATS = ["docx", "xlsx", "html", "pdf"]

DEFAULT_TOOL = "markitdown"
TOOL_CHOICES = ["markitdown", "docling", "llamaparse"]
