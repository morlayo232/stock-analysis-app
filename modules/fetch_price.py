import pandas as pd
from modules.fetch_naver import fetch_from_naver
from modules.fetch_daum import fetch_from_daum
import yfinance as yf

def fetch_stock_price(code):
    market_code = ".KS" if code.startswith("0") or code.startswith("1") else ".KQ"
    ticker = f"{code}{market_code}"

    try:
        df = yf.Ticker(ticker).history(period="6mo")
        if not df.empty:
            df = df.reset_index()
            return df
    except:
        pass

    df = fetch_from_naver(code)
    if not df.empty:
        return df

    df = fetch_from_daum(code)
    return df
