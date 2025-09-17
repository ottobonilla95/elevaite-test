from elevaite_ingestion.tools.standard_tools.markitdown import MarkitdownTool
from elevaite_ingestion.tools.standard_tools.docling import DoclingTool


class DocxParser:
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
            raise Exception(f"Failed to parse Docx file: {file_path}. Error: {e}")


# if __name__ == "__main__":
#     file_path = "Ethics of Autonomous Vehicles - Spring 2023.docx"

#     try:
#         # parser = DocxParser(tool="markitdown")
#         # parsed_data = parser.parse(file_path)
#         # print("Parsed Content (Markitdown):", parsed_data)
#         parser = DocxParser(tool="docling")
#         parsed_data = parser.parse(file_path)
#         print("Parsed Content (Docling):", parsed_data)
#     except Exception as e:
#         print(f"Error: {e}")
