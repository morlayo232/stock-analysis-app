import requests
from bs4 import BeautifulSoup

def fetch_news_headlines(stock_name, max_news=3):
    url = f"https://search.naver.com/search.naver?where=news&query={stock_name}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    news_list = []
    for a in soup.select(".news_area .news_tit")[:max_news]:
        title = a.get_text(strip=True)
        link = a['href']
        news_list.append({"title": title, "link": link})
    return news_list
