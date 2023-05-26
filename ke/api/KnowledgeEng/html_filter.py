import re
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
import config as config
import nlp_util as nu


# filter title
def filterTitle(title_tag):
    title = title_tag.text.strip()
    path = config.title_filter_path
    title = _filterTitleWords(path, title)
    return title


# remove filter words from title
def _filterTitleWords(path, title, ratio=0.8):
    if not title:
        return ""
    texts = open(path, "r", encoding="utf-8").read()
    lines = texts.splitlines()
    ntitle = title
    ltitle = title.lower()
    for line in lines:
        score = SequenceMatcher(None, ltitle, line).ratio()
        if score >= ratio:
            ntitle = ""
            break
    return ntitle


# filter tags in html
def filterHTMLTags(html):
    html = _filterClass(html)
    html = _filterTags(html)
    html = _filterLinks(html)
    #html = _filterSpaces(html)
    html = _filterHTMLText(html)
    return html


# filter class tags in html
def _filterClass(html):
    soup = BeautifulSoup(html, features="html.parser")
    if not soup:
        return html
    filter_class_tags = config.filter_class_tags
    for filter_class_tag in filter_class_tags:
        tags = soup.find_all("div", {"class": filter_class_tag})
        for tag in tags:
            tag.decompose()
    return soup.prettify()


# filter class tags in html
def _filterTags(html):
    soup = BeautifulSoup(html, features="html.parser")
    if not soup:
        return html
    filter_tags = config.filter_tags
    for filter_tag in filter_tags:
        tags = soup.find_all(filter_tag)
        for tag in tags:
            tag.decompose()
    return soup.prettify()


# filter links in html
def _filterLinks(html):
    soup = BeautifulSoup(html, features="html.parser")
    if not soup:
        return html
    filter_links = config.filter_links
    tags = soup.find_all("a")
    for tag in tags:
        tag_text = tag.get_text().lower().strip()
        if tag_text in filter_links:
            tag.decompose()
    return soup.prettify()


# filter text in html (remove unnecessary newlines/whitespaces)
def _filterSpaces(html):
    soup = BeautifulSoup(html, features="html.parser")
    if not soup:
        return html
    text = soup.get_text().strip()
    contents = re.sub(r"\n\s*+", "\n", text).strip().splitlines()
    if contents and len(contents) > 1 and contents[0] == contents[1]:
        html = html.replace(contents[0], "", 1).strip()
    return html


# filter html text based on chunk filter
def _filterHTMLText(html):
    filter_path = config.chunk_filter_path
    lines = open(filter_path, "r", encoding="utf-8").readlines()
    for line in lines:
        line = line.strip()
        if line:
            html = re.sub(line, "", html, flags=re.IGNORECASE)
    return html


# filter titles that are hyperlinks
def _filterLinkedTitle(title_tag):
    if not title_tag:
        return ""
    title = title_tag.text.strip()
    if title_tag.name == "a":
        title = ""
    return title


# filter stop words using nlp utlity
def filterStopWords(text):
    return nu.filterStopWords(text)
