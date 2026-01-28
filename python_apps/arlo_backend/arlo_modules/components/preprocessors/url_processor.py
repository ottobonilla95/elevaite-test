import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class QueryBasedURLTextExtractor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        self.stop_words = set(stopwords.words('english'))

    def fetch_url(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching the URL: {e}")
            return None

    def extract_text(self, html):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            p_tags = soup.find_all('p')
            article_tags = soup.find_all('div', class_ = 'article-content')
            # community_tags = soup.find_all('div', class_ = 'lia-accepted-solution')
            community_tags = soup.find_all('div', class_ = 'lia-message-body-content')
            # community_tags = soup.find_all('div', class_ = 'lia-quilt-row-forum-message-main')
            p_text = ' '.join([tag.get_text(strip=True) for tag in p_tags])
            community_tags_text = ' '.join([tag.get_text(strip=True, separator=' | ').replace('\xa0', ' ') for tag in community_tags])
            article_text = ' '.join([tag.get_text(strip=True, separator=' | ').replace('\xa0', ' ') for tag in article_tags])
            text = community_tags_text + article_text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            text = text.replace("|", '\n')
            return text
        except Exception:
            return "None found"

    def preprocess_text(self, text):
        sentences = sent_tokenize(text)
        return [' '.join([word.lower() for word in word_tokenize(sentence)
                          if word.isalnum() and word.lower() not in self.stop_words])
                for sentence in sentences]

    def get_relevant_sentences(self, sentences, query, top_n=5):
        vectorizer = TfidfVectorizer()
        sentence_vectors = vectorizer.fit_transform(sentences + [query])
        query_vector = sentence_vectors[-1]
        sentence_vectors = sentence_vectors[:-1]

        similarities = cosine_similarity(sentence_vectors, query_vector)
        top_indices = similarities.argsort(axis=0)[-top_n:][::-1]
        return [sentences[i[0]] for i in top_indices]

    def get_text_from_url(self, url,max_chars=10000):
        html = self.fetch_url(url)
        if not html:
            return None

        full_text = self.extract_text(html)
        return f"Link: {url}\n\n+{full_text}"