import pandas as pd
import yfinance as yf
from modules.fetch_naver import get_naver_price
from modules.fetch_daum import get_daum_price

def fetch_stock_price(code):
    try:
        df = yf.download(f"{code}.KS", period="6mo", progress=False)
        if not df.empty:
            df = df.reset_index()
