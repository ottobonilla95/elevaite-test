import requests
import config as config
import html_util as hu
import html_title as ht
import html_link as hl


# get html content from url
def getHTML(url, reget=False):
    filter_tags = True
    html = hu.getHTML(url, reget, filter_tags)
    return html


# download html content from url
def downloadHTML(url, sub_dir=None, reget=False):
    filter_tags = True
    html = hu.saveHTML(url, sub_dir, reget, filter_tags)
    return html


# get text content from url
def getTextContent(url, reget=False):
    filter_tags = True
    stop_words = False
    text = hu.getContent(url, reget, filter_tags, stop_words)
    return text


# download text content from url
def downloadURLText(url, sub_dir=None, reget=False):
    filter_tags = True
    stop_words = False
    file_path = hu.saveContent(url, sub_dir, reget, filter_tags, stop_words)
    return file_path


# get binary content from url
def getBinaryContent(url, out_path):
    response = requests.get(url, stream=True, verify=False)
    out_file = open(out_path, "wb")
    for data in response.iter_content():
        out_file.write(data)
    out_file.close()


# download sublinks
def downloadLinks(url):
    links = hl.getLinks(url).values()
    paths = []
    for link in links:
        path = downloadURLText(link, sub_dir=None, reget=False)
        paths.append(path)
    return paths
