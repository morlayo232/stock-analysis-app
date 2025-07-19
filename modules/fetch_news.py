def fetch_google_news(query, max_items=5):
    import feedparser
    try:
        url = f"https://news.google.com/rss/search?q={query}+주식&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        results = [entry.title for entry in feed.entries[:max_items]]
        return results
    except Exception:
        return []
