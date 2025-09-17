from typing import Dict, List, Tuple, TypedDict

from langchain_core.documents import Document


class LineType(TypedDict):
    content: str
    metadata: Dict[str, str]


class HeaderType(TypedDict):
    level: int
    name: str
    data: str


class MarkdownHeaderTextSplitter:
    """Splitting markdown files based on specified headers."""

    def __init__(
        self,
        headers_to_split_on: List[Tuple[str, str]],
        return_each_line: bool = False,
        strip_headers: bool = True,
    ):
        self.return_each_line = return_each_line
        self.headers_to_split_on = sorted(headers_to_split_on, key=lambda split: len(split[0]), reverse=True)
        self.strip_headers = strip_headers

    def split_text(self, text: str) -> List[Document]:
        lines = text.split("\n")
        lines_with_metadata: List[LineType] = []
        current_content: List[str] = []
        current_metadata: Dict[str, str] = {}
        header_stack: List[HeaderType] = []
        initial_metadata: Dict[str, str] = {}

        in_code_block = False
        opening_fence = ""

        for line in lines:
            stripped_line = line.strip()
            stripped_line = "".join(filter(str.isprintable, stripped_line))

            if not in_code_block:
                if stripped_line.startswith("```") and stripped_line.count("```") == 1:
                    in_code_block = True
                    opening_fence = "```"
                elif stripped_line.startswith("~~~"):
                    in_code_block = True
                    opening_fence = "~~~"
            else:
                if stripped_line.startswith(opening_fence):
                    in_code_block = False
                    opening_fence = ""

            if in_code_block:
                current_content.append(stripped_line)
                continue

            for sep, name in self.headers_to_split_on:
                if stripped_line.startswith(sep) and (len(stripped_line) == len(sep) or stripped_line[len(sep)] == " "):
                    if name is not None:
                        current_header_level = sep.count("#")
                        while header_stack and header_stack[-1]["level"] >= current_header_level:
                            popped_header = header_stack.pop()
                            if popped_header["name"] in initial_metadata:
                                initial_metadata.pop(popped_header["name"])

                        header: HeaderType = {
                            "level": current_header_level,
                            "name": name,
                            "data": stripped_line[len(sep) :].strip(),
                        }
                        header_stack.append(header)
                        initial_metadata[name] = header["data"]

                    if current_content:
                        lines_with_metadata.append(
                            {
                                "content": "\n".join(current_content),
                                "metadata": current_metadata.copy(),
                            }
                        )
                        current_content.clear()

                    if not self.strip_headers:
                        current_content.append(stripped_line)

                    break
            else:
                if stripped_line:
                    current_content.append(stripped_line)
                elif current_content:
                    lines_with_metadata.append(
                        {
                            "content": "\n".join(current_content),
                            "metadata": current_metadata.copy(),
                        }
                    )
                    current_content.clear()

            current_metadata = initial_metadata.copy()

        if current_content:
            lines_with_metadata.append(
                {
                    "content": "\n".join(current_content),
                    "metadata": current_metadata,
                }
            )

        return (
            self.aggregate_lines_to_chunks(lines_with_metadata)
            if not self.return_each_line
            else [Document(page_content=chunk["content"], metadata=chunk["metadata"]) for chunk in lines_with_metadata]
        )

    def aggregate_lines_to_chunks(self, lines: List[LineType]) -> List[Document]:
        aggregated_chunks: List[LineType] = []

        for line in lines:
            if aggregated_chunks and aggregated_chunks[-1]["metadata"] == line["metadata"]:
                aggregated_chunks[-1]["content"] += "  \n" + line["content"]
            else:
                aggregated_chunks.append(line)

        return [Document(page_content=chunk["content"], metadata=chunk["metadata"]) for chunk in aggregated_chunks]
