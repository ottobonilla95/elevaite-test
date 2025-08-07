import sys
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# print(base_dir)
sys.path.append(base_dir)

from tools.standard_tools.markitdown import MarkitdownTool
from tools.standard_tools.docling import DoclingTool

class XlsxParser:
    def __init__(self, tool="markitdown"):
        if tool == "markitdown":
            self.tool = MarkitdownTool()
        elif tool == "docling":
            self.tool = DoclingTool()
        else:
            raise ValueError(f"Unsupported tool: {tool}")

    def parse(self, file_path):
        try:
            result = self.tool.process_file(file_path)
            return {"content": result}
        except Exception as e:
            raise Exception(f"Failed to parse XLSX file: {file_path}. Error: {e}")



# if __name__ == "__main__":
#     file_path = "Data sheet for Co pilot - CES'25_v1 (3).xlsx"

#     try:
#         parser = XlsxParser(tool="markitdown")
#         parsed_data = parser.parse(file_path)
#         print("Parsed Content (Markitdown):", parsed_data)

#         # parser = XlsxParser(tool="docling")
#         # parsed_data = parser.parse(file_path)
#         # print("Parsed Content (Docling):", parsed_data)
#     except Exception as e:
#         print(f"Error: {e}")
