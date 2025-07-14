import pandas as pd
import requests
from bs4 import BeautifulSoup

def get_naver_price(code):
    url = f"https://finance.naver.com/item/sise_day.nhn?code={code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    dfs = []
    for page in range(1, 5):  # 4페이지(약 80일)
        page_url = url + f"&page={page}"
        res = requests.get(page_url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table", {"class": "type2"})
        if table is not None:
            df = pd.read_html(str(table), header=0)[0]
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs)
    df = df.rename(columns={"날짜": "Date", "종가": "Close", "시가": "Open", "고가": "High", "저가": "Low", "거래량": "Volume"})
    df = df[["Date", "Close", "Open", "High", "Low", "Volume"]]
    df = df.dropna()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.sort_values("Date").reset_index(drop=True)
    for col in ["Close", "Open", "High", "Low", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna()
    return df
