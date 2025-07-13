import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# 1차 시도: Yahoo Finance
def fetch_from_yahoo(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        df.reset_index(inplace=True)
        if df.empty or len(df) < 10:
            raise ValueError("Yahoo 데이터 부족")
        return df
    except Exception as e:
        print(f"Yahoo 데이터 오류: {e}")
        return pd.DataFrame()

# 2차 시도: Naver Finance
def fetch_from_naver(ticker):
    url = f"https://finance.naver.com/item/sise_day.nhn?code={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    dfs = []

    for page in range(1, 6):
        try:
            res = requests.get(url + f"&page={page}", headers=headers, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', class_='type2')
            df = pd.read_html(str(table))[0]
            dfs.append(df)
            time.sleep(0.3)
        except Exception as e:
            print(f"Naver 크롤링 오류 (p{page}): {e}")
            continue

    try:
        df_all = pd.concat(dfs).dropna()
        df_all.columns = ['날짜', '종가', '전일비', '시가', '고가', '저가', '거래량']
        df_all['날짜'] = pd.to_datetime(df_all['날짜'])
        df_all = df_all.sort_values('날짜').reset_index(drop=True)
        df_all.rename(columns={'종가': 'Close', '거래량': 'Volume'}, inplace=True)
        return df_all
    except Exception as e:
        print(f"Naver 데이터 처리 실패: {e}")
        return pd.DataFrame()

# 3차 시도: 빈 DataFrame 반환
def fetch_fallback(ticker):
    print(f"⚠️ {ticker} 데이터 불러오기 실패. 빈 데이터 반환.")
    return pd.DataFrame()

# 통합 함수
def load_price(ticker, market):
    full_ticker = f"{ticker}.KS" if market == "KOSPI" else f"{ticker}.KQ"
    for loader in [fetch_from_yahoo, fetch_from_naver, fetch_fallback]:
        df = loader(ticker if loader == fetch_from_naver else full_ticker)
        if not df.empty:
            return df
<<<<<<< HEAD
    return pd.DataFrame()
=======
    return pd.DataFrame()
>>>>>>> 4a27f38146733656025b2d13e5b4cc219821c6cb
