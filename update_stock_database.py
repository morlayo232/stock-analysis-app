import pandas as pd
from pykrx import stock
from datetime import datetime
from modules.score_utils import finalize_scores

def fetch_price(code):
    today = datetime.today().strftime("%Y%m%d")
    try:
        df = stock.get_market_ohlcv_by_date(today, today, code)
        if df is not None and not df.empty:
            return int(df['종가'][-1])
    except Exception:
        pass
    return None

def fetch_fundamental(code):
    today = datetime.today().strftime("%Y%m%d")
    try:
        df = stock.get_market_fundamental_by_date(today, today, code)
        if df is not None and not df.empty:
            return {
                'PER': float(df['PER'][-1]) if not pd.isna(df['PER'][-1]) else None,
                'PBR': float(df['PBR'][-1]) if not pd.isna(df['PBR'][-1]) else None,
                'EPS': float(df['EPS'][-1]) if not pd.isna(df['EPS'][-1]) else None,
                'BPS': float(df['BPS'][-1]) if not pd.isna(df['BPS'][-1]) else None,
                '배당률': float(df['DIV'][-1]) if not pd.isna(df['DIV'][-1]) else None
            }
    except Exception:
        pass
    return {'PER': None, 'PBR': None, 'EPS': None, 'BPS': None, '배당률': None}

def update_database():
    df_list = pd.read_csv("initial_krx_list.csv", dtype={'종목코드': str})
    codes = dict(zip(df_list['종목명'], df_list['종목코드']))
    data = []
    for name, code in codes.items():
        price = fetch_price(code)
        fin = fetch_fundamental(code)
        data.append({
            "종목명": name, "종목코드": code, "현재가": price,
            "PER": fin["PER"], "PBR": fin["PBR"], "EPS": fin["EPS"], "BPS": fin["BPS"], "배당률": fin["배당률"]
        })
    df = pd.DataFrame(data)
    df = finalize_scores(df, style="aggressive")
    df.to_csv("filtered_stocks.csv", index=False)
    print("filtered_stocks.csv로 저장 완료!")

if __name__ == "__main__":
    update_database()
