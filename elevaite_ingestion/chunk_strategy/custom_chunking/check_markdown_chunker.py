from markdown_chunker import MarkdownHeaderTextSplitter
from markitdown import MarkItDown
import os


from markitdown import MarkItDown

md = MarkItDown() 
result = md.convert("/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/Ethics of Autonomous Vehicles - Spring 2023.docx")
# print(result.text_content)

splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")]
)

chunks = splitter.split_text(result.text_content)
for chunk in chunks:
    print(chunk.page_content + "\n#############\n")

