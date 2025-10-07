from typing import List, Dict, Optional, Union, Any
import re
import os
import boto3
from botocore.exceptions import ClientError
from data_classes import SourceReference


async def get_image_url(image_filename: str) -> Optional[str]:
    """
    Generate a signed URL for an image in S3.

    Args:
        image_filename: The filename of the image to get a URL for
    Returns:
        A signed URL for the image or None if the image doesn't exist
    """
    try:
        # Get S3 configuration from environment variables
        bucket_name = os.getenv("AWS_BUCKET_NAME")
        region = os.getenv("AWS_REGION", "us-east-2")

        # Create S3 client
        s3_client = boto3.client('s3', region_name=region,
            aws_access_key_id=os.getenv("AWS_AKID"),
            aws_secret_access_key=os.getenv("AWS_SAK")
        )

        # Generate a presigned URL for the S3 object
        expiration = 3600  # URL expiration time in seconds (1 hour)
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': "toshiba_6800_6200/"+image_filename},
            ExpiresIn=expiration
        )

        return response
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None


async def process_sources(extracted_sources: List[SourceReference]) -> List[SourceReference]:
    """
    Process source references to add URLs for images.

    Args:
        extracted_sources: List of SourceReference objects to process
    Returns:
        List of processed SourceReference objects with URLs added
    """
    if not extracted_sources:
        return []

    processed_sources = []

    for source in extracted_sources:
        if not source.url:
            try:
                image_filename = None
                if source.awsLink:
                    image_filename = f"{source.awsLink}.png"
                else:
                    # Extract the first page number from the pages string
                    page_num = None
                    if source.pages:
                        parts = source.pages.split(",")
                        if parts:
                            first_part = parts[0].split("-")[0].strip()
                            if first_part.isdigit():
                                page_num = first_part

                    if page_num and source.filename:
                        base_filename = source.filename.replace(".pdf", "")
                        image_filename = f"{base_filename}_page_{page_num}.png"

                if image_filename:
                    image_url = await get_image_url(image_filename)
                    if image_url:
                        source.url = image_url
            except Exception as e:
                print(f"Error getting image URL: {e}")

        processed_sources.append(source)

    return processed_sources


async def extract_sources_from_text(text: str) -> Optional[List[SourceReference]]:
    """
    Extracts source information from the accumulated text
    Looks for patterns like:
    - Source: 6800 Hardware Service Guide (2).pdf, Page 41
    - Sources: 6800 Hardware Service Guide (2).pdf, Page [41,54]
    - Source: 6800 Parts Manual (3).pdf, Pages: 40-45
    - Source: [6800 Hardware Service Guide (2).pdf](https://example.com/file.pdf), Page 41
    - 6800 Hardware Service Guide (2).pdf, Page 213 [aws_link: 6800_Hardware_Service_Guide_(2).pdf_page_213]
    - 6800 Parts Manual (3) page 91 [aws_id: 6800 Parts Manual (3)_page_91]

    Args:
        text: The accumulated text to extract sources from
    Returns:
        List of SourceReference objects or None if no sources found
    """
    if not text:
        return None

    # Look for source information at the end of the text after <Answer> tag or "**Sources:**"
    text_after_answer_tag = text

    # First try to find the <Answer> tag
    answer_tag_index = text.rfind("<Answer>")
    if answer_tag_index != -1:
        text_after_answer_tag = text[answer_tag_index:]
    else:
        # If no <Answer> tag, look for "**Sources:**"
        sources_header_index = text.rfind("**Sources:**")
        if sources_header_index != -1:
            text_after_answer_tag = text[sources_header_index:]
        else:
            # If neither is found, try to find any source pattern directly
            source_index = text.rfind("Source:")
            if source_index == -1:
                # If no source indicators are found, return None
                return None
            text_after_answer_tag = text[source_index:]

    # Different patterns to match
    patterns = [
        # Source: filename.pdf, Page XX
        r"Source:\s+(.*?\.pdf)(?:,|\s+)(?:Page|Pages?):?\s+(\d+)",

        # Source: filename.pdf, Page [X,Y]
        r"Source(?:s)?:\s+(.*?\.pdf)(?:,|\s+)(?:Page|Pages?):?\s+\[(\d+,\d+)\]",

        # Source: filename.pdf, Pages: X-Y
        r"Source(?:s)?:\s+(.*?\.pdf)(?:,|\s+)(?:Page|Pages?):?\s+(\d+-\d+)",

        # - filename.pdf, Pages: XX [aws_link: filename_page_XX]
        r"-\s+(.*?\.pdf)(?:,|\s+)(?:Page|Pages?):?\s+(\d+|\[.*?\])\s+\[aws_link:\s+(.*?)\]"
    ]

    # Pattern for markdown-style links: [filename](url)
    markdown_link_pattern = r"\[(.*?\.pdf)\]\((https?:\/\/[^\s)]+)\)"

    # Pattern for aws_links: [aws_link: filename_page_XX]
    aws_link_pattern = r"\[aws_link:\s+(.*?)\]"

    # Pattern for aws_id: [aws_id: filename_page_XX]
    aws_id_pattern = r"\[aws_id:\s+(.*?)\]"

    sources = []

    # First, extract any markdown-style links and store them in a map
    link_map = {}
    for match in re.finditer(markdown_link_pattern, text_after_answer_tag, re.IGNORECASE):
        if len(match.groups()) >= 2:
            link_map[match.group(1).strip()] = match.group(2).strip()

    # Extract aws_links and store them in a map
    aws_link_map = {}
    for match in re.finditer(aws_link_pattern, text_after_answer_tag, re.IGNORECASE):
        if len(match.groups()) >= 1:
            aws_link = match.group(1).strip()
            # Store the aws_link to be used later when matching with filenames
            aws_link_map[aws_link] = aws_link

    # Extract aws_ids and store them in the same map as aws_links
    for match in re.finditer(aws_id_pattern, text_after_answer_tag, re.IGNORECASE):
        if len(match.groups()) >= 1:
            aws_id = match.group(1).strip()
            # Store the aws_id to be used later
            aws_link_map[aws_id] = aws_id

    # Add sources from aws_link_map
    for key in aws_link_map:
        source_object = SourceReference(filename="Source", pages="", awsLink=key)
        sources.append(source_object)

    # Look for direct aws_id pattern: "6800 Parts Manual (3) page 91 [aws_id: 6800 Parts Manual (3)_page_91]"
    direct_aws_id_pattern = r"(.*?)\s+page\s+(\d+)\s+\[aws_id:\s+(.*?)\]"
    for match in re.finditer(direct_aws_id_pattern, text_after_answer_tag, re.IGNORECASE):
        if len(match.groups()) >= 3:
            filename = match.group(1).strip()
            page_num = match.group(2).strip()
            aws_id = match.group(3).strip()

            # Create a source reference object
            source = SourceReference(
                filename=f"{filename}.pdf",  # Add .pdf extension for consistency
                pages=page_num,
                awsLink=aws_id  # Use awsLink field for the aws_id
            )

            # Store the full match text to help with replacement later
            source.fullMatchText = match.group(0)

            sources.append(source)

    # Try each pattern
    for pattern in patterns:
        matches = re.search(pattern, text_after_answer_tag, re.IGNORECASE)
        if matches and len(matches.groups()) >= 2:
            filename = matches.group(1).strip()
            pages = matches.group(2).strip()
            source = SourceReference(
                filename=filename,
                pages=pages
            )

            # Check if we have a URL for this filename
            if filename in link_map:
                source.url = link_map[filename]

            # Check if this is the aws_link pattern (which has 3 capture groups)
            if len(matches.groups()) >= 3 and matches.group(3):
                # Use the aws_link as the URL
                aws_link = matches.group(3).strip()
                source.awsLink = aws_link
            else:
                # Check if we have an aws_link that matches this filename and page
                base_filename = filename.replace(".pdf", "")

                # Handle different page formats: single number, range, or array
                page_num = ""
                if pages.startswith("[") and pages.endswith("]"):
                    # Handle array format like [135, 136, 334, 337, 338]
                    page_array = pages[1:-1].split(",")
                    if page_array:
                        page_num = page_array[0].strip()
                elif "-" in pages:
                    # Handle range format like 40-45
                    page_num = pages.split("-")[0].strip()
                else:
                    # Handle single number format
                    page_num = pages.split(",")[0].strip()

                possible_aws_link = f"{base_filename.replace(' ', '_')}_page_{page_num}"

                if possible_aws_link in aws_link_map:
                    source.awsLink = possible_aws_link

            sources.append(source)

    # If we found any sources, return them
    sources = sources if sources else None
    if sources:
        return await process_sources(sources)
    return sources
    # return sources if sources else None


async def extract_only_aws_links(text: str) -> List[str]:
    """
    Extracts only aws_links from the accumulated text
    Looks for patterns like:
    - [aws_link: 6800_Hardware_Service_Guide_(2).pdf_page_213]

    Args:
        text: The accumulated text to extract aws_links from
    Returns:
        List of aws_links or empty list if none found
    """
    if not text:
        return []

    aws_link_pattern = r"\[aws_id:\s+(.*?)\]"
    aws_links = []
    for match in re.finditer(aws_link_pattern, text, re.IGNORECASE):
        if len(match.groups()) >= 1:
            aws_links.append(match.group(1).strip())

    return list(set(aws_links))

async def remove_prefix(text: str) -> str:
    # Regex to remove 2 numbers followed by _ For eg. 22_6800 Self Checkout System 7 Parts Manual Models 1x0, 2xx, 3xx, and 4xx_page_38
    # will become 6800 Self Checkout System 7 Parts Manual Models 1x0, 2xx, 3xx, and 4xx_page_38
    pattern = r"^\d{2}_"
    return re.sub(pattern, "", text)

async def reconstruct_source(text: str, aws_status: bool = True) -> str:
    s = text.split("_page_")
    if not aws_status:
        return f"- {s[0]} page {s[1]} [aws_id: None_{text}]"
    elif "excel" in s[0] or ".csv" in s[0] or ".xls" in s[0] or ".xlsx" in s[0]:
        return f"- {s[0]} page 0 [aws_id: None]"
    else:
        return f"- {s[0]} page {s[1]} [aws_id: {text}]"

# test_response = """
# The part number for the Loader module is 80Y1564.
#
# **Sources:**
#
# - 6800 Self Checkout System 7 Parts Manual Models 1x0, 2xx, 3xx, and 4xx page 38 [aws_id: 22_6800 Self Checkout System 7 Parts Manual Models 1x0, 2xx, 3xx, and 4xx_page_38]
# - 6800 Parts Manual (3) page 37 [aws_id: 6800 Parts Manual (3)_page_37]
# - Modular eXpansion Platform 6800 KDU page 198 [aws_id: 20_Modular eXpansion Platform 6800 KDU_page_198]
# - 4888-ExxBW4 Parts Manual (3) page 35 [aws_id: 4888-ExxBW4 Parts Manual (3)_page_35]
# """
# import asyncio
# print(asyncio.run(extract_only_aws_links(test_response)))
