import pandas as pd
import requests
from bs4 import BeautifulSoup

def get_daum_price(code):
    url = f"https://finance.daum.net/quotes/A{code}#chart"
    headers = {"User-Agent": "Mozilla/5.0", "referer": url}
    dfs = []
    for page in range(1, 5):  # 4페이지(약 80일)
        api_url = f"https://finance.daum.net/api/quotes/A{code}/days?symbolCode=A{code}&page={page}&perPage=20&fieldName=closePrice&order=desc"
        res = requests.get(api_url, headers=headers)
        if res.status_code != 200:
            continue
        try:
            data = res.json().get("data", [])
        except Exception:
            continue
        if not data:
            continue
        df = pd.DataFrame(data)
        if not df.empty and {"date", "closePrice", "openPrice", "highPrice", "lowPrice", "tradeVolume"} <= set(df.columns):
            df = df.rename(columns={
                "date": "Date", "closePrice": "Close", "openPrice": "Open",
                "highPrice": "High", "lowPrice": "Low", "tradeVolume": "Volume"
            })
            dfs.append(df[["Date", "Close", "Open", "High", "Low", "Volume"]])
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for col in ["Close", "Open", "High", "Low", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.sort_values("Date").reset_index(drop=True)
    df = df.dropna()
    return df
