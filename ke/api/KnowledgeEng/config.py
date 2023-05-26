import os
from datetime import datetime

# directory names
input_dir = "input"
data_dir = "data"
output_dir = "output"
plain_dir = "plain"
scraped_dir = "scraped"
content_dir = "content"
log_dir = "log"
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
input_dir = os.path.join(current_dir, input_dir)
data_dir = os.path.join(current_dir, data_dir)
output_dir = os.path.join(current_dir, output_dir)
plain_dir = os.path.join(output_dir, plain_dir)
scraped_dir = os.path.join(output_dir, scraped_dir)
content_dir = os.path.join(output_dir, content_dir)
log_dir = os.path.join(output_dir, log_dir)


# file names and path
input_file = "input.txt"
output_file = "output.html"
meta_file = "meta.json"
chunk_ref_file = "chunk_ref.txt"
ref_file = "ref.txt"
log_file = "log" + "_" + datetime.now().strftime("%Y%m%d%H%M") + ".txt"
input_path = os.path.join(output_dir, input_file)
output_path = os.path.join(output_dir, output_file)
meta_path = os.path.join(output_dir, meta_file)
chunk_ref_path = os.path.join(output_dir, chunk_ref_file)
ref_path = os.path.join(output_dir, ref_file)
log_path = os.path.join(log_dir, log_file)


# data files and path
title_filter_file = "title_filter.txt"
chunk_filter_file = "chunk_filter.txt"
filter_file = "filter.txt"
urls_file = "urls.txt"
incidents_file = "incidents.txt"
temp_file = "temp.txt"
title_filter_path = os.path.join(data_dir, title_filter_file)
chunk_filter_path = os.path.join(data_dir, chunk_filter_file)
filtered_path = os.path.join(data_dir, filter_file)
urls_path = os.path.join(data_dir, urls_file)
incidents_path = os.path.join(data_dir, incidents_file)
temp_path = os.path.join(data_dir, temp_file)
clsfy_prdct_file = "clsfy_prdct.txt"
clsfy_prdct_path = os.path.join(data_dir, clsfy_prdct_file)

filter_tags = [
    "aside",
    "footer",
    "header",
    "nav",
    "script",
    "style",
    "title",
    "button",
    "input"
]
filter_links = ["#", "prev", "next", "previous", "next"]

# file extensions
html_extn = ".html"
json_extn = ".json"
text_extn = ".txt"
pdf_extn = ".pdf"

# constants used in the program
anchor_tag = ["a"]
heading_tags = ["title","h1", "h2", "h3", "h4", "h5", "h6", "u"]
filter_pattern = r"[^a-zA-Z0-9\s\'\\\.\:\-\_]"
title_split = [":", "-"]
href_attr = "href"

# filter class tags
filter_class_tags = [
    "banner",
    "breadcrumb",
    "language",
    "toolbar",
    "nav",
    "footer",
    "feedback",
]

#Qdrant and chunking configurations
openai_api_key = "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"
collection_name="kbDocs_KnowledgeEng_test"
embedding_model = "text-embedding-ada-002"
qdrant_url="https://a29a4a5f-b731-4ffa-befd-5c3f702c66f3.us-east-1-0.aws.cloud.qdrant.io:6333" 
qdrant_api_key="bD7Kx0EQ3hPe2FJjzjNpXr7E4mZatk9MAhqwNHi4EBOPdNqKcRW7HA"
chunksize=600
chunk_overlap=0

#json keys configurations
summary_key = "Summary"
doctype_key = "DocumentType"
docid_key = "DocumentId"
product_key = "Product"
version_key = "Version"
topic_key = "Topic"
subtopic_key = "Sub-Topic"
url_key = "url"
source_key = "source"
text_key = "Text"
size_key = "Size"
chunk_key = "Chunk"
totaltok_key = "TotalTokens"
chunks_key = "Chunks"