# update_stock_database.py

import pandas as pd
from pykrx import stock
from datetime import datetime
from modules.score_utils import finalize_scores

def fetch_price(code):
    today = datetime.today().strftime("%Y%m%d")
    try:
        df = stock.get_market_ohlcv_by_date(today, today, code)
        if not df.empty:
            return int(df['종가'][-1]), int(df['거래량'][-1])
    except Exception:
        pass
    return None, None

def fetch_fundamental(code):
    today = datetime.today().strftime("%Y%m%d")
    try:
        df = stock.get_market_fundamental_by_date(today, today, code)
        if not df.empty:
            return {
                'PER': float(df['PER'][-1]),
                'PBR': float(df['PBR'][-1]),
                'EPS': float(df['EPS'][-1]),
                'BPS': float(df['BPS'][-1]),
                '배당률': float(df['DIV'][-1])
            }
    except Exception:
        pass
    return {'PER': None, 'PBR': None, 'EPS': None, 'BPS': None, '배당률': None}

def update_database():
    df_list = pd.read_csv("initial_krx_list.csv")
    n = len(df_list)
    data = []
    for i, row in df_list.iterrows():
        name = row['종목명']
        code = str(row['종목코드']).zfill(6)
        price, volume = fetch_price(code)
        fin = fetch_fundamental(code)
        data.append({
            "종목명": name,
            "종목코드": code,
            "현재가": price,
            "거래량": volume,
            "PER": fin["PER"],
            "PBR": fin["PBR"],
            "EPS": fin["EPS"],
            "BPS": fin["BPS"],
            "배당률": fin["배당률"]
        })
        # 진행률 표시
        if (i+1) % max(1, n//20) == 0 or (i+1) == n:
            progress = (i+1) / n * 100
            print(f"[DB Update] 진행률: {progress:.1f}% ({i+1}/{n})")
    df = pd.DataFrame(data)
    df = finalize_scores(df, style="aggressive")
    # 거래량평균/급등 등 컬럼 추가
    df["거래량평균20"] = df["거래량"].rolling(window=20).mean()
    df["거래량평균60"] = df["거래량"].rolling(window=60).mean()
    df["거래량급증"] = (df["거래량"] > 2.5 * df["거래량평균20"])
    # 등락률
    df["등락률"] = (df["현재가"] - df["현재가"].shift(1)) / df["현재가"].shift(1) * 100
    # 최고가20
    df["최고가20"] = df["현재가"].rolling(window=20).max()
    df["최고가갱신"] = (df["현재가"] >= df["최고가20"])
    # 급등점수(비중: 거래량급증 0.4, 신고가갱신 0.3, 등락률>7 0.2, score상위 0.1)
    df["급등점수"] = (
        df["거래량급증"].astype(int) * 0.4 +
        df["최고가갱신"].astype(int) * 0.3 +
        (df["등락률"] > 7).astype(int) * 0.2 +
        (df["score"] > df["score"].quantile(0.7)).astype(int) * 0.1
    )
    cols = ["종목명", "종목코드", "현재가", "거래량", "거래량평균20", "거래량평균60",
            "거래량급증", "최고가20", "최고가갱신", "등락률", "PER", "PBR", "EPS", "BPS", "배당률", "score", "급등점수"]
    df = df[cols]
    df.to_csv("filtered_stocks.csv", index=False)
    print("filtered_stocks.csv 저장 완료!")

if __name__ == "__main__":
    update_database()
