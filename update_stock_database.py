import pandas as pd
from pykrx import stock
from datetime import datetime
from modules.score_utils import finalize_scores

def fetch_krx_data(code: str) -> dict:
    """KRX에서 당일 시가/종가/고가/저가/거래량 & 재무(Per/Pbr/Div) 수집"""
    today = datetime.today().strftime("%Y%m%d")
    ohlcv = stock.get_market_ohlcv_by_date(today, today, code)
    fund  = stock.get_market_fundamental_by_date(today, today, code)
    if ohlcv.empty or fund.empty:
        return None
    row_ohlc = ohlcv.iloc[-1]
    row_fund = fund.iloc[-1]
    return {
        "현재가":    int(row_ohlc['종가']),
        "고가":      int(row_ohlc['고가']),
        "저가":      int(row_ohlc['저가']),
        "거래량":    int(row_ohlc['거래량']),
        "거래량평균20": int(ohlcv['거래량'].rolling(20).mean().iloc[-1]),
        "PER":      float(row_fund['PER']),
        "PBR":      float(row_fund['PBR']),
        "배당수익률": float(row_fund['DIV'])
    }

def update_database():
    init = pd.read_csv("initial_krx_list.csv", dtype=str)
    records = []
    for _, r in init.iterrows():
        data = fetch_krx_data(r['종목코드'])
        if not data:
            continue
        records.append({
            "종목명": r['종목명'],
            "종목코드": r['종목코드'].zfill(6),
            "갱신일": datetime.now().strftime("%Y-%m-%d %H:%M"),
            **data
        })
    df = pd.DataFrame(records)
    df = finalize_scores(df)  # default style=aggressive
    df.to_csv("filtered_stocks.csv", index=False)
    print("filtered_stocks.csv 생성 완료!")

def update_single_stock(code: str):
    df = pd.read_csv("filtered_stocks.csv", dtype=str)
    idx = df[df["종목코드"] == code].index
    if idx.empty:
        print("해당 종목 없음")
        return
    data = fetch_krx_data(code)
    if not data:
        print("수집 실패")
        return
    for k, v in data.items():
        df.loc[idx, k] = v
    df.loc[idx, '갱신일'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    print("단일 종목 갱신 완료!")
