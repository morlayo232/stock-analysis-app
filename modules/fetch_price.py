import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

def fetch_stock_price(code):
    # 1. 야후 파이낸스
    market_code = ".KS" if code.startswith("0") or code.startswith("1") else ".KQ"
    ticker = f"{code}{market_code}"
    try:
        df = yf.Ticker(ticker).history(period="6mo")
        if not df.empty:
            df = df.reset_index()
            if 'Date' not in df.columns: df.rename(columns={'index':'Date'}, inplace=True)
            print(f"[YF 성공] {ticker} 데이터 {len(df)}건")
            return df[['Date','Close','Open','High','Low','Volume']]
    except Exception as e:
        print(f"[YF 실패] {code}: {e}")

    # 2. 네이버 금융
    url = f"https://finance.naver.com/item/sise_day.nhn?code={code}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    dfs = []
    for page in range(1, 7):
        try:
            res = requests.get(url + f"&page={page}", headers=headers)
            df_naver = pd.read_html(res.text)[0]
            dfs.append(df_naver)
            time.sleep(0.2)
        except Exception as e:
            print(f"[NAVER 실패] {code} page {page}: {e}")
    try:
        df = pd.concat(dfs)
        df = df.dropna()
        df.columns = ['날짜','Close','전일비','Open','High','Low','Volume']
        df['Date'] = pd.to_datetime(df['날짜'])
        df = df.sort_values('Date').reset_index(drop=True)
        for col in ['Close','Open','High','Low','Volume']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',',''), errors='coerce')
        print(f"[NAVER 성공] {code} 데이터 {len(df)}건")
        return df[['Date','Close','Open','High','Low','Volume']]
    except Exception as e:
        print(f"[NAVER 전체실패] {code}: {e}")

    # 3. 다음 금융
    try:
        url = f"https://finance.daum.net/api/quotes/{code}/days?perPage=100&page=1"
        headers = {"User-Agent": "Mozilla/5.0", "referer": f"https://finance.daum.net/quotes/{code}"}
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
        print(f"[DAUM 성공] {code} 데이터 {len(df)}건")
        return df[["Date", "Close", "Open", "High", "Low", "Volume"]]
    except Exception as e:
        print(f"[DAUM 실패] {code}: {e}")

    print(f"[ALL FAIL] {code} 모든 주가 소스 실패")
    return pd.DataFrame()
