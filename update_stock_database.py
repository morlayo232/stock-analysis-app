import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
from modules.score_utils import finalize_scores

def fetch_price(code, max_retry=10):
    today = datetime.today()
    for i in range(max_retry):
        day = today - timedelta(days=i)
        if day.weekday() >= 5:  # 주말 제외
            continue
        date = day.strftime("%Y%m%d")
        try:
            df = stock.get_market_ohlcv_by_date(date, date, code)
            if df is not None and not df.empty:
                return {
                    "현재가": int(df['종가'].iloc[-1]),
                    "거래대금": int(df['거래대금'].iloc[-1])
                }
        except Exception:
            continue
    return {"현재가": None, "거래대금": None}

def fetch_fundamental(code, max_retry=10):
    today = datetime.today()
    for i in range(max_retry):
        day = today - timedelta(days=i)
        if day.weekday() >= 5:
            continue
        date = day.strftime("%Y%m%d")
        try:
            df = stock.get_market_fundamental_by_date(date, date, code)
            if df is not None and not df.empty:
                return {
                    'PER': float(df['PER'].iloc[-1]) if not pd.isna(df['PER'].iloc[-1]) else None,
                    'PBR': float(df['PBR'].iloc[-1]) if not pd.isna(df['PBR'].iloc[-1]) else None,
                    'EPS': float(df['EPS'].iloc[-1]) if not pd.isna(df['EPS'].iloc[-1]) else None,
                    'BPS': float(df['BPS'].iloc[-1]) if not pd.isna(df['BPS'].iloc[-1]) else None,
                    '배당률': float(df['DIV'].iloc[-1]) if not pd.isna(df['DIV'].iloc[-1]) else None
                }
        except Exception:
            continue
    return {'PER': None, 'PBR': None, 'EPS': None, 'BPS': None, '배당률': None}

def update_database():
    import sys
    df_list = pd.read_csv("initial_krx_list.csv", dtype={'종목코드': str})
    codes = dict(zip(df_list['종목명'], df_list['종목코드']))
    data = []
    for name, code in codes.items():
        price_info = fetch_price(code)
        fin = fetch_fundamental(code)
        data.append({
            "종목명": name,
            "종목코드": code,
            "현재가": price_info["현재가"],
            "거래대금": price_info["거래대금"],
            "PER": fin["PER"],
            "PBR": fin["PBR"],
            "EPS": fin.get("EPS"),
            "BPS": fin.get("BPS"),
            "배당률": fin["배당률"]
        })
    df = pd.DataFrame(data)
    print(f"[update_database] 수집 데이터 건수: {len(df)}", file=sys.stderr)
    print(df.head(), file=sys.stderr)
    print(df.info(), file=sys.stderr)
    if not df.empty:
        df = finalize_scores(df, style="aggressive")
        try:
            df.to_csv("filtered_stocks.csv", index=False, encoding='utf-8-sig')
            print("filtered_stocks.csv로 저장 완료!", file=sys.stderr)
        except Exception as e:
            print(f"CSV 저장 실패: {e}", file=sys.stderr)
    else:
        print("빈 데이터프레임, CSV 저장하지 않음", file=sys.stderr)

if __name__ == "__main__":
    update_database()
