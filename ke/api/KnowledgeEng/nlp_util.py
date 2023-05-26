import os
from difflib import SequenceMatcher
import config as config


# remove stop words from text
def filterStopWords(text):
    if not text:
        return ""
    filter_words = open(config.filtered_path).read().splitlines()
    text_words = text.split()
    literals = []
    for text_word in text_words:
        if text_word.lower() not in filter_words:
            literals.append(text_word)
    return " ".join(literals)


# get ngrams from text
def getNGrams(text, grams):
    ngrams = []
    words = text.split()
    length = len(words)
    for index in range(length - grams + 1):
        ngram = " ".join(words[index : index + grams])
        ngrams.append(ngram.strip())
    return ngrams


# get tag based on the tag list file
def getBestMatch(text, tags=[], tags_path=""):
    if tags_path:
        tags = open(tags_path, "r").readlines()
    scores = {}
    for tag in tags:
        tag_len = len(tag.split())
        count = 0
        l_tag = tag.lower().strip()
        words = getNGrams(text, tag_len)
        for word in words:
            l_word = word.lower().strip()
            score = SequenceMatcher(None, l_tag, l_word).ratio()
            if score > 0.8:
                count += 1
        scores[tag] = count
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    tag_name = sorted_scores[0][0] if sorted_scores[0][1] > 0 else ""
    return tag_name
