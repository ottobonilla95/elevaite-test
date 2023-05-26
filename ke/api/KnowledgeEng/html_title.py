import config as config
import html_util as hu
import html_filter as hf


# get title from url
def getTitles(url, tags=config.heading_tags):
    titles = []
    soup = hu.getbs(url)
    if not soup:
        return titles
    for tag in tags:
        title_tags = soup.find_all(tag)
        for title_tag in title_tags:
            title = hf.filterTitle(title_tag)
            if title and title not in titles:
                titles.append(title)
    return titles


# get first title from url
def getFirstTitle(url):
    title = None
    titles = getTitles(url)
    if titles:
        title = titles[0]
    return title


# check if heading tag is present in the line
def isTagPresent(line, tags=config.heading_tags):
    isPresent = False
    for tag in tags:
        if tag in line:
            isPresent = True
            break
    return isPresent
