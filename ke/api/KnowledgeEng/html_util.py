import os
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import validators
import file_util as fu
import config as config
import html_filter as hf


# get BeautifulSoup object from url
def getbs(url):
    if not url:
        print("URL is empty")
        return None
    if not validators.url(url):
        print("Invalid URL: " + url)
        return None
    response = requests.get(url, verify=False)
    html = response.text
    soup = BeautifulSoup(html, features="html.parser")
    return soup


# prettify html
def prettify(html):
    soup = BeautifulSoup(html, features="html.parser")
    prety_html = ""
    if not soup:
        return prety_html
    prety_html = soup.prettify()
    return prety_html


# get text from html
def getHTMLContent(html):
    soup = BeautifulSoup(html, features="html.parser")
    text = ""
    if not soup:
        return text
    text = soup.get_text().strip()
    return text


# get html from url
def getHTML(url, reget=False, filter_tags=False):
    search_path = config.scraped_dir
    html = ""
    files = fu.searchFile(search_path, name=config.ref_file, text=url)
    if files and not reget:
        file_path = files[0]
        html = fu.readTextFile(file_path)
    else:
        soup = getbs(url)
        if soup:
            html = soup.prettify()
        if filter_tags:
            html = hf.filterHTMLTags(html)
            html = prettify(html)
    return html


# get html text list based urls
def getHTMLs(urls, filter_tags=False, reget=False):
    html_text_list = []
    for url in urls:
        html_text = getHTML(url, reget, filter_tags)
        html_text_list.append(html_text)
    return html_text_list


# save html scrapped from url
def saveHTML(url, sub_dir=None, reget=False, filter_tags=False):
    file_path = ""
    if not url:
        return file_path
    file_name = getFileNameFromURL(url) + config.html_extn
    path = config.output_dir
    if sub_dir:
        path = os.path.join(path, sub_dir)
    file_path = os.path.join(path, file_name)
    if reget or not os.path.isfile(file_path):
        html_text = getHTML(url, reget, filter_tags)
        fu.saveTextFile(file_path, html_text)
        ref = url + " = " + file_path
        ref_path = os.path.join(path, config.ref_file)
        ref_text = fu.readTextFile(ref_path)
        if html_text and ref not in ref_text:
            fu.saveTextFile(ref_path, ref, append=True)
        if not html_text:
            fu.saveTextFile(config.log_path, url, append=True)
    return file_path


# save html list based urls
def saveHTMLs(urls, sub_dir=None, reget=False, filter_tags=False):
    file_paths = []
    for url in urls:
        file_path = saveHTML(url, sub_dir, reget, filter_tags)
        file_paths.append(file_path)
    return file_paths


# get text content of a url
def getContent(url, reget=False, filter_tags=True, stop_words=False):
    if not url:
        return ""
    html = getHTML(url, reget, filter_tags)
    text = getHTMLContent(html)
    if stop_words:
        text = hf.filterStopWords(text)
    text = re.sub(r"\s+", " ", text)
    return text


# get text content of urls
def getContents(urls, reget=False, filter_tags=True, stop_words=False):
    contents = []
    for url in urls:
        content = getContent(url, reget, filter_tags, stop_words)
        contents.append(content)
    return contents


# save content of a url
def saveContent(url, sub_dir=None, reget=False, filter_tags=True, stop_words=False):
    text = getContent(url, reget, filter_tags, stop_words)
    path = ""
    if text:
        path = config.content_dir
        path = os.path.join(path, sub_dir) if sub_dir else path
        fu.saveTextFile(path, text)
    return path


# save contents of urls
def saveContents(urls, sub_dir=None, reget=False, filter_tags=True, stop_words=False):
    paths = []
    for url in urls:
        path = saveContent(url, reget, sub_dir, filter_tags, stop_words)
        paths.append(path)
    return paths


# convert html to text
def html2txt(url, path):
    text = getContent(url, filter_tags=True, stop_words=False)
    fu.saveTextFile(path, text)


# get path from url
def getFileNameFromURL(url, append_timestamp=False):
    path = re.findall(r"https?://[^\s]+", url, re.IGNORECASE)
    path = path[0].rsplit("/", 1)[1]
    if "=" in path:
        path = path.split("=")[1]
    if append_timestamp:
        path += "_" + datetime.now().strftime("%Y%m%d%H%M%S%f")
    return path
