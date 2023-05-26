import logging
from time import time
import html_dwnld as hd
import html_title as ht
import html_util as hu

import re

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)

#only for testing
urls = [
    "https://www.google.com/url?q=https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id%3DkA14u000000oMb4CAE%26lang%3Den_US%25E2%2580%25A9&source=gmail-imap&ust=1683570797000000&usg=AOvVaw20e7nk5mjAKfGWBbdf1u2Y"
]

def urlextract(url):
    time_start = gettime()
    logger.info(f'URL Content Extract Begins :: - {url} {int(time() * 1e+3) - time_start}ms')
    output = hd.getTextContent(url)    
    title = ht.getFirstTitle(url)
    documentId = hu.getFileNameFromURL(url)    
    logger.info(f'URL Content Extract Completed :: - {url} {int(time() * 1e+3) - time_start}ms')
    return output, url, title, documentId  

def gettime():
    time_start = int(time() * 1e+3)
    return time_start

# enable only for testing
#WEBExtract.urlextract("https://docs.paloaltonetworks.com/panorama/10-1/panorama-admin/troubleshooting/recover-managed-device-connectivity-to-panorama")