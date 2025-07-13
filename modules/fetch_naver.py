import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

def fetch_from_naver(code):
    headers = {"User-Agent": "Mozilla/5.0"}
    dfs = []

    try:
        for page in range(1, 6):
            url = f"https://finance.naver.com/item/sise_day.nhn?code={code}&page={page}"
            res = requests.get(url, headers=headers)
            table = BeautifulSoup(res.text, "html.parser").find("table", class_="type2")
            df = pd.read_html(str(table))[0]
            dfs.append(df)
            time.sleep(0.2)

        df_all = pd.concat(dfs).dropna()
        df_all.columns = ['Date', 'Close', 'Diff', 'Open', 'High', 'Low', 'Volume']
        df_all["Date"] = pd.to_datetime(df_all["Date"])
        df_all = df_all.sort_values("Date").reset_index(drop=True)
        return df_all

    except:
        return pd.DataFrame()
