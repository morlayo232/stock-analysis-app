# news.py
import requests
from bs4 import BeautifulSoup

def fetch_news_headlines(query, max_count=5):
    """
    종목명 또는 키워드(query)를 받아 네이버 뉴스 헤드라인을 추출
    """
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://search.naver.com/search.naver?where=news&query={query}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    headlines = []
    for item in soup.select(".news_area")[:max_count]:
        title_tag = item.select_one("a.news_tit")
        if title_tag:
            title = title_tag.text.strip()
            link = title_tag['href']
            headlines.append((title, link))

    return headlines
