from pykrx import stock
from datetime import datetime
import pandas as pd

def fetch_price(code):
    today = datetime.today().strftime("%Y%m%d")
    try:
        df = stock.get_market_ohlcv_by_date(today, today, code)
        if not df.empty:
            result = pd.DataFrame({
                "현재가": [int(df['종가'][-1])],
                "PER": [None],
                "PBR": [None],
                "EPS": [None],
                "BPS": [None],
                "배당률": [None]
            })
            return result
    except Exception as e:
        print("fetch_price 오류:", e)
    return pd.DataFrame()
