import pandas as pd
import requests
from bs4 import BeautifulSoup

def fetch_from_daum(code):
    try:
        url = f"https://finance.daum.net/api/quotes/{code}/days?perPage=100&page=1"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "referer": f"https://finance.daum.net/quotes/{code}"
        }
        res = requests.get(url, headers=headers)
        json_data = res.json()["data"]

        df = pd.DataFrame(json_data)
        df.rename(columns={
            "tradeDate": "Date",
            "tradePrice": "Close",
            "openPrice": "Open",
            "highPrice": "High",
            "lowPrice": "Low",
            "candleAccTradeVolume": "Volume"
        }, inplace=True)

        df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d")
        df = df.sort_values("Date").reset_index(drop=True)
        return df[["Date", "Close", "Open", "High", "Low", "Volume"]]

    except Exception as e:
        print(f"다음 크롤링 오류: {e}")
        return pd.DataFrame()
