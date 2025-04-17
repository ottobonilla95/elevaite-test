import sys
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# print(base_dir)
sys.path.append(base_dir)


from tools.standard_tools.crawl4ai import Crawl4aiTool
from tools.standard_tools.markitdown import MarkitdownTool

class HtmlParser:
    def __init__(self, tool="markitdown"):
        if tool == "markitdown":
            self.tool = MarkitdownTool()
        elif tool == "crawl4ai":
            self.tool = Crawl4aiTool()
        else:
            raise ValueError(f"Unsupported tool: {tool}")

    def parse(self, file_path):
        try:
            result = self.tool.process_file(file_path)
            return {"content": result}
        except Exception as e:
            raise Exception(f"Failed to parse html file: {file_path}. Error: {e}")
