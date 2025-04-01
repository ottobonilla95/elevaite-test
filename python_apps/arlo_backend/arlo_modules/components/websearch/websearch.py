# from sentence_transformers import CrossEncoder
import requests
from urllib.parse import urlparse

class BingWebSearcher:
    def __init__(self, subscription_key):
        self.subscription_key = subscription_key
        self.search_url = "https://api.bing.microsoft.com/v7.0/search"
        self.headers = {"Ocp-Apim-Subscription-Key": self.subscription_key}

    def search(self, query, num_results=10):
        params = {
            "q": query,
            "count": 50,  # Request more results to ensure we get enough after filtering
            "textDecorations": True,
            "textFormat": "HTML"
        }
        response = requests.get(self.search_url, headers=self.headers, params=params)
        response.raise_for_status()
        search_results = response.json()
        return search_results

    def filter_articles(self, search_results, num_results=10, filter_domains=["community.arlo", "kb.arlo"]):
        filtered_articles = []
        if 'webPages' in search_results and 'value' in search_results['webPages']:
            for item in search_results['webPages']['value']:
                domain = urlparse(item['url']).netloc
                if any(filter_domain in domain for filter_domain in filter_domains):
                    filtered_articles.append({
                        'title': item['name'],
                        'link': item['url'],
                        'snippet': item.get('snippet', 'No snippet available'),
                        'domain': domain
                    })
                if len(filtered_articles) == num_results:
                    break

        return filtered_articles

    def print_articles(self, articles):
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article['title']}")
            print(f"   URL: {article['link']}")
            print(f"   Domain: {article['domain']}")
            print(f"   Snippet: {article['snippet']}")

    def urls_fetched(self, articles):
        urls = []
        for article in articles:
            urls.append(article['link'])
        return urls

