from pykrx import stock
from datetime import datetime

def fetch_price(code):
    today = datetime.today().strftime("%Y%m%d")
    try:
        df = stock.get_market_ohlcv_by_date(today, today, code)
        if not df.empty:
            return int(df['종가'][-1])
    except Exception:
        pass
    return None
