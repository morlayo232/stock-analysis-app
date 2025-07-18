import pandas as pd
from pykrx import stock
from datetime import datetime
from modules.score_utils import finalize_scores

# 기본 초기 종목 리스트: initial_krx_list.csv
INIT_CSV = "initial_krx_list.csv"
OUT_CSV  = "filtered_stocks.csv"

def fetch_fundamental(code:str):
    today = datetime.today().strftime("%Y%m%d")
    dff = stock.get_market_fundamental_by_date(today, today, code)
    if dff.empty: return {}
    row = dff.iloc[-1]
    return {
        "PER": row["PER"],
        "PBR": row["PBR"],
        "EPS": None,  # KRX API 제공 안 함
        "BPS": None,
        "배당수익률": row["DIV"]
    }

def fetch_price_and_volumes(code:str):
    # 최근 20영업일 OHLCV
    today = datetime.today().strftime("%Y%m%d")
    dfh = stock.get_market_ohlcv_by_date((pd.Timestamp.today()-pd.Timedelta(days=30)).strftime("%Y%m%d"),
                                         today, code)
    if dfh.empty: return {}
    latest = dfh.iloc[-1]
    return {
        "현재가": latest["종가"],
        "거래량": latest["거래량"],
        "거래량평균20": dfh["거래량"].rolling(20).mean().iloc[-1],
        "고가": latest["고가"],
        "저가": latest["저가"]
    }

def update_database():
    df0 = pd.read_csv(INIT_CSV, dtype=str)
    records = []
    for _, r in df0.iterrows():
        code = r["종목코드"].zfill(6)
        fund = fetch_fundamental(code)
        pr   = fetch_price_and_volumes(code)
        if not fund or not pr: continue
        rec = {
            "종목명": r["종목명"],
            "종목코드": code,
            "갱신일": datetime.now().strftime("%Y-%m-%d %H:%M"),
            **fund, **pr
        }
        records.append(rec)
    if not records: return
    df = pd.DataFrame(records)
    df = finalize_scores(df, style="aggressive")
    df.to_csv(OUT_CSV, index=False)

def update_single_stock(code:str):
    try:
        df = pd.read_csv(OUT_CSV, dtype=str)
    except FileNotFoundError:
        update_database()
        df = pd.read_csv(OUT_CSV, dtype=str)
    df = df.set_index("종목코드")
    fund = fetch_fundamental(code)
    pr   = fetch_price_and_volumes(code)
    if fund and pr:
        df.loc[code, list(fund.keys())] = fund.values()
        df.loc[code, list(pr.keys())]   = pr.values()
        df.loc[code, "갱신일"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        df = df.reset_index()
        df = finalize_scores(df, style="aggressive")
        df.to_csv(OUT_CSV, index=False)
