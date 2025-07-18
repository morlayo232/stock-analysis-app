from pykrx import stock
from datetime import datetime
import pandas as pd
def fetch_price(code):
today = datetime.today().strftime("%Y%m%d")
try:
df = stock.get_market_ohlcv_by_date(today, today, code)
fund = stock.get_market_fundamental_by_date(today, today, code)
if not df.empty and not fund.empty:
result = pd.DataFrame({
"현재가": [int(df['종가'][-1])],
"PER": [float(fund['PER'][-1]) if not pd.isna(fund['PER'][-1]) else None],
"PBR": [float(fund['PBR'][-1]) if not pd.isna(fund['PBR'][-1]) else None],
"EPS": [float(fund['EPS'][-1]) if not pd.isna(fund['EPS'][-1]) else None],
"BPS": [float(fund['BPS'][-1]) if not pd.isna(fund['BPS'][-1]) else None],
"배당률": [float(fund['DIV'][-1]) if not pd.isna(fund['DIV'][-1]) else None],
})
return result
except Exception as e:
print("fetch_price 오류:", e)
return pd.DataFrame()
