import config as config
import html_util as hu
import html_title as ht


# get all links in the url
def getLinks(url):
    links = {}
    soup = hu.getbs(url)
    if not soup:
        return links
    link_tags = soup.find_all(config.anchor_tag)
    for link_tag in link_tags:
        link_dtl = _getLinkDtl(link_tag)
        links.update(link_dtl)
    return links


# get link details from link
def _getLinkDtl(link_tag):
    link_dtl = {}
    url = link_tag.attrs.get(config.href_attr)
    title = link_tag.text.strip()
    if not title:
        title = ht.getFirstTitle(url)
    if url and title and "#" not in url:
        link_dtl[title] = url.strip()
    return link_dtl
