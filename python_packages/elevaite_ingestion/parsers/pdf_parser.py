import sys
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from tools.standard_tools.markitdown import MarkitdownTool
from tools.standard_tools.docling import DoclingTool
from tools.standard_tools.pypdf import PyPDFTool


class PdfParser:
    def __init__(self, tool="pypdf"):
        if tool == "markitdown":
            self.tool = MarkitdownTool()
        elif tool == "docling":
            self.tool = DoclingTool()
        elif tool == "pypdf":
            self.tool = PyPDFTool()
        else:
            raise ValueError(f"Unsupported tool: {tool}")

    def parse(self, file_path):
        try:
            result = self.tool.parse(file_path)
            return {"content": result}
        except Exception as e:
            raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")


# Example usage (commented out)
# if __name__ == "__main__":
#     file_path = "path/to/your/test.pdf"
#     try:
#         parser = PdfParser(tool="pypdf")
#         parsed_data = parser.parse(file_path)
#         print("Parsed Content:", parsed_data)
#     except Exception as e:
#         print(f"Error: {e}")
