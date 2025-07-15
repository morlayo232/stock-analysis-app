from pykrx import stock
from datetime import datetime
import pandas as pd

def fetch_price(code):
    today = datetime.today().strftime("%Y%m%d")
    try:
        df = stock.get_market_ohlcv_by_date(today, today, code)
        if not df.empty:
            # 여기에 '종가', 'PER', 'PBR', 'EPS', 'BPS', '배당률' 등도 같이 DataFrame에 추가해야 함
            result = pd.DataFrame({
                "현재가": [int(df['종가'][-1])],
                # "PER": [...],  # KRX에서 재무지표 추가 가능하면 여기도!
                # "PBR": [...],
                # "EPS": [...],
                # "BPS": [...],
                # "배당률": [...]
            })
            return result
    except Exception as e:
        print("fetch_price 오류:", e)
    return pd.DataFrame()  # 빈 DataFrame이라도 반환!

