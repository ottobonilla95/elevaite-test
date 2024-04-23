from typing import Any, Dict, List
import docx
from pydantic import BaseModel
from unstructured.partition.html import partition_html
from unstructured.partition.docx import partition_docx
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from unstructured.documents.elements import Element
from pprint import pprint
import sys, glob, os
import json


class ChunkAsJson(BaseModel):
    metadata: Dict[str, Any]
    page_content: str


def get_file_elements(filepath=None, filedir=None):
    elements = partition_html(filename=filepath)
    print("Total elements = " + str(len(elements)))
    """ for idx, element in enumerate(elements):
        print("Element Index : " + str(idx) + " Element Category :" + element.category + "\n")
        element_attrs = element.to_dict()
        print("Element Type :" + str(element_attrs['type']) + "\n")
        metadata = element.metadata.to_dict()
        print("Metadata " + str(metadata.keys()))
        for k, v in metadata.items():
            print(k,v)
        print('Text : ' + str(element.text)) """
    source = get_filename(filepath)
    print(source)
    chunks = chunk_by_title(elements=elements, max_characters=2000)
    chunks_as_json = []
    for idx, chunk in enumerate(chunks):
        chunk_as_json = get_chunk_as_json(source=source, chunk=chunk)
        chunks_as_json.append(chunk_as_json)
    return chunks_as_json
    # for k, v in element.to_dict().items():
    # print(k, v)


def get_file_elements_internal(
    file, filepath, content_type: str | None = None
) -> List[ChunkAsJson]:
    elements = partition_html(file=file, content_type=content_type)
    # elements = partition(file=file, content_type=content_type)
    source = get_filename(filepath)
    chunks = chunk_by_title(elements=elements, max_characters=2000)
    chunks_as_json: List[ChunkAsJson] = []
    for idx, chunk in enumerate(chunks):
        chunk_as_json = get_chunk_as_json(source=source, chunk=chunk)
        chunks_as_json.append(chunk_as_json)
    return chunks_as_json


def get_file_elements_from_url(
    filepath, content_type: str | None = None, physical_address: str | None = None
):
    elements = partition(url=physical_address, content_type=content_type)
    source = get_filename(filepath)
    chunks = chunk_by_title(elements=elements, max_characters=2000)
    chunks_as_json = []
    for idx, chunk in enumerate(chunks):
        chunk_as_json = get_chunk_as_json(source=source, chunk=chunk)
        chunks_as_json.append(chunk_as_json)
    return chunks_as_json


def get_docx_elements(filepath=None, filedir=None):
    elements = partition_docx(filepath)
    print("Total elements = " + str(len(elements)))
    source = get_filename(filepath=filepath)
    document_title = ""
    current_chunks = []
    current_chunk_charaters = 0
    documnet_chunks = []
    for idx, element in enumerate(elements):
        # TODO: Figure this one out
        if element.category == "Title" and idx == 0:  # type: ignore
            document_title = element.text
        current_chunks.append(element.text)
        current_chunk_charaters += len(element.text)
        if current_chunk_charaters >= 1500:
            documnet_chunks.append(document_title + "\n" + " ".join(current_chunks))
            current_chunks.clear()
            current_chunk_charaters = 0
    chunks_as_json = []
    for idx, document in enumerate(documnet_chunks):
        print("Index : ", idx)
        print("Document Chunk: ", document)
        chunk_as_json = get_chunk_as_json(source=source, chunk=document)
        print(chunk_as_json)
        chunks_as_json.append(chunk_as_json)
    print("Total Chunks: ", len(documnet_chunks))
    output_directory = "/home/binu/elevaite/ingest/data/msa/output"
    write_page_chunks_to_file(
        chunks_as_json, chunk_dir_full_path=output_directory, findex=1
    )


def write_chunks_to_file(chunks_as_json, chunk_dir_full_path: str, findex: int):
    chunk_index = 0
    if chunk_dir_full_path:
        for pidx, page_chunks in enumerate(chunks_as_json):
            for sidx, page_chunk in enumerate(page_chunks):
                chunk_index = chunk_index + 1
                filepath = (
                    chunk_dir_full_path
                    + "/"
                    + "chunk_"
                    + str(findex)
                    + "_"
                    + str(pidx)
                    + "_"
                    + str(sidx)
                    + ".json"
                )
                print("Writing File" + filepath)
                with open(filepath, "w") as f:
                    f.write(json.dumps(page_chunk))


def write_page_chunks_to_file(chunks_as_json, chunk_dir_full_path: str, findex: int):
    chunk_index = 0
    if chunk_dir_full_path:
        for pidx, page_chunk in enumerate(chunks_as_json):
            chunk_index = chunk_index + 1
            filepath = (
                chunk_dir_full_path
                + "/"
                + "chunk_"
                + str(findex)
                + "_"
                + str(pidx)
                + ".json"
            )
            print("Writing File" + filepath)
            print(page_chunk)
            with open(filepath, "w") as f:
                f.write(json.dumps(page_chunk))


def get_filename(filepath):
    return filepath.split("/")[-1]


def get_document_title(source):
    return source.split(".")[0]


def process_file_dir(directory=None, output_directory=None):
    chunks_as_json = []
    page_as_json = []
    findex = 0
    print(f"Output Directory {output_directory}")
    for filename in glob.glob(f"{directory}/*.html"):
        print("Filename :" + filename)
        chunks_as_json.append(get_file_elements(filename))
        print("Number of chunks " + str(len(chunks_as_json)))
        if output_directory:
            findex = findex + 1
            write_chunks_to_file(
                chunks_as_json, chunk_dir_full_path=output_directory, findex=findex
            )
            chunks_as_json.clear()


def get_chunk_as_json(source: str, chunk: Element) -> ChunkAsJson:
    chunk_with_no_tabs = str(chunk).replace("\t", "")
    page_metadata = ChunkAsJson(metadata={}, page_content="")
    page_metadata.metadata["source"] = source
    page_metadata.metadata["document_title"] = get_document_title(source)
    page_metadata.metadata["page_title"] = page_metadata.metadata["document_title"]

    page_content_title = []
    if page_metadata.metadata["document_title"]:
        page_content_title.append(str(page_metadata.metadata["document_title"]))
    if page_metadata.metadata["page_title"]:
        page_content_title.append(str(page_metadata.metadata["page_title"]))
    content_title = " ".join(page_content_title)
    page_metadata.page_content = content_title + " " + str(chunk_with_no_tabs)
    return page_metadata


if __name__ == "__main__":
    print(sys.argv[1])
    if len(sys.argv) > 1:
        if os.path.exists(sys.argv[1]) and os.path.isdir(sys.argv[1]):
            if len(sys.argv) > 2:
                process_file_dir(sys.argv[1], sys.argv[2])
            else:
                process_file_dir(sys.argv[1])
        else:
            get_docx_elements(sys.argv[1])
