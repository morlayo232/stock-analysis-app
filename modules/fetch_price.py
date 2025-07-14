import pandas as pd
import yfinance as yf
from modules.fetch_naver import get_naver_price
from modules.fetch_daum import get_daum_price

def fetch_stock_price(code):
    try:
        df = yf.download(f"{code}.KS", period="6mo", progress=False)
        if not df.empty:
            df = df.reset_index()
            df = df.rename(columns={"Date": "Date", "Close": "Close", "Open": "Open", "High": "High", "Low": "Low", "Volume": "Volume"})
            return df[["Date", "Close", "Open", "High", "Low", "Volume"]]
    except Exception:
        pass
    try:
        df = get_naver_price(code)
        if not df.empty:
            return df
    except Exception:
        pass
    try:
        df = get_daum_price(code)
        if not df.empty:
            return df
    except Exception:
        pass
    return pd.DataFrame()
