import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
from modules.score_utils import finalize_scores

def get_recent_business_day(n_days=10):
    today = datetime.today()
    for i in range(n_days):
        day = today - timedelta(days=i)
        if day.weekday() < 5:  # 평일 체크
            try:
                df = stock.get_market_ohlcv_by_date(day.strftime("%Y%m%d"), day.strftime("%Y%m%d"), "005930")
                if df is not None and not df.empty:
                    return day.strftime("%Y%m%d")
            except:
                continue
    return today.strftime("%Y%m%d")

def fetch_price(code):
    date = get_recent_business_day()
    try:
        df = stock.get_market_ohlcv_by_date(date, date, code)
        if df is not None and not df.empty:
            return int(df['종가'][-1])
    except Exception:
        pass
    return None

def fetch_fundamental(code):
    date = get_recent_business_day()
    try:
        df = stock.get_market_fundamental_by_date(date, date, code)
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
    import sys
    df_list = pd.read_csv("initial_krx_list.csv", dtype={'종목코드': str})
    codes = dict(zip(df_list['종목명'], df_list['종목코드']))
    data = []
    for name, code in codes.items():
        price = fetch_price(code)
        fin = fetch_fundamental(code)
        data.append({
            "종목명": name,
            "종목코드": code,
            "현재가": price,
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
