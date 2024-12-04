from langchain_openai import OpenAIEmbeddings
import trafilatura
import re
import os
from langchain_community.agent_toolkits.load_tools import load_tools
from dotenv import load_dotenv

# Load environment variables
# env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), '.env')
env_file_path = os.path.abspath(os.path.join(__file__, '../../../../.env'))

load_dotenv(dotenv_path=env_file_path)

tools = load_tools(["searx-search-results-json"],
                     # searx_host=os.getenv("SEARX_HOST"),
                   searx_host = os.getenv("SEARX_HOST"),
                   num_results=50)
searx_tool = tools[0]

def extract_links(query_result):
    """
    Extract URLs from the search query result JSON.
    Args:
        query_result (str): The JSON response from the SearxNG search.
    Returns:
        list: A list of extracted URLs.
    """
    urls = re.findall(r'https?://[^\s,\'"]+', query_result)
    # print("#############")
    # print("urls:::::::::::::::::::::", urls)
    return urls

embedding_model = OpenAIEmbeddings()

def perform_web_search(query, sites=None):
    print("Web Search Query: ", query)
    if sites:
        cleaned_sites = [site.replace("https://", "").replace("http://", "").replace("www.", "").strip("/") for site in sites]
        site_specific_query = " OR ".join([f"site:{site}" for site in cleaned_sites]) + f" {query}"
    else:
        site_specific_query = query

    # Run the query with SearxNG and get links
    query_result = searx_tool.run(site_specific_query)
    # print("Query result: ", query_result)
    links = extract_links(query_result)
    # print("Original Links: ", links)
    filtered_links = []
    documents = ["-"]
    for link in links:
        if "community.arlo.com" in link or "kb.arlo.com" in link:
            filtered_links.append(link)
        elif "www.arlo.com" in link:
            pass
            downloaded = trafilatura.fetch_url(link)
            if downloaded:
                page_content = trafilatura.extract(downloaded)
                if page_content:
                    documents.append(page_content)
            else:
                documents.append("-")

    if len(documents) > 0:
        url_contents = "\n".join(documents)
    else:
        url_contents = ""


    links = filtered_links
    # print("Filtered Links: ", links)

    # Extract content from each link using trafilatura
    # documents = []
    # for url in links:
    #     downloaded = trafilatura.fetch_url(url)
    #     if downloaded:
    #         page_content = trafilatura.extract(downloaded)
    #         documents.append(page_content)
    #         # if page_content:
    #         #     documents.append(Document(page_content))
    #     # else:
    #     #     print(f"Content extraction failed for {url}")
    #     else:
    #         print(f"Failed to download {url}")
    #
    # url_contents = "\n".join(documents)

    return url_contents, links

# Example usage:
# web_text, urls_fetched = perform_web_search("Arlo mic issue",)
# print("Web text: ", web_text)
# print("Urls fetched: ", urls_fetched)

