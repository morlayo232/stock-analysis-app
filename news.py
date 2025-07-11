import requests
from bs4 import BeautifulSoup
from collections import Counter
import re

# 간단한 불용어 리스트
STOPWORDS = ['관련', '보도', '기자', '속보', '위해', '대해', '및', '때문', '부터', '까지', '현재', '오늘', '내일']

def fetch_news_headlines(keyword):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://search.naver.com/search.naver?where=news&query={keyword}&sm=tab_opt"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    items = soup.select("ul.list_news div.news_wrap.api_ani_send")

    headlines = []
    for item in items[:5]:
        title_tag = item.select_one("a.news_tit")
        if title_tag:
            headlines.append(title_tag.text.strip())
    return headlines

def clean_korean_text(text):
    # 한글/숫자만 남기기
    text = re.sub(r"[^가-힣0-9\s]", "", text)
    return text

def extract_keywords(headlines):
    words = []
    for title in headlines:
        clean = clean_korean_text(title)
        for word in clean.split():
            if len(word) > 1 and word not in STOPWORDS:
                words.append(word)
    counter = Counter(words)
    return [w for w, _ in counter.most_common(5)]

def fetch_news_keywords(keyword):
    try:
        headlines = fetch_news_headlines(keyword)
        if not headlines:
            return []
        keywords = extract_keywords(headlines)
        return keywords
    except:
        return []
