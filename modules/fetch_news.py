import feedparser
def fetch_google_news(query, max_items=5):
url = f"https://news.google.com/rss/search?q={query}+주식&hl=ko&gl=KR&ceid=KR:ko"
feed = feedparser.parse(url)
results = []
for entry in feed.entries[:max_items]:
results.append(entry.title)
return results
