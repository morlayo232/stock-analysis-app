# update_stock_database.py

import os
import time
from datetime import datetime, timedelta

import pandas as pd
from pykrx import stock

from modules.score_utils import finalize_scores

# ─────────────────────────────────────────────────────────────────────────────
# 1) KRX 일별 시세(OHLCV) 히스토리 저장 함수
def save_price_history(code: str, days: int = 60):
    """
    지정 종목코드에 대해 최근 `days` 거래일의 OHLCV를 
    price_{code}.csv 로 저장합니다.
    """
    code = code.zfill(6)
    today = datetime.today()
    start = (today - timedelta(days=days * 2)).strftime("%Y%m%d")  # 여유 있게 범위 지정
    end = today.strftime("%Y%m%d")
    try:
        df = stock.get_market_ohlcv_by_date(start, end, code)
        if not df.empty:
            filename = f"price_{code}.csv"
            df.to_csv(filename, index=True)
            print(f"[PRICE] Saved {filename} ({len(df)} rows)")
        else:
            print(f"[PRICE] No price data for {code}")
    except Exception as e:
        print(f"[PRICE] Error fetching {code}: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# 2) 전체 종목 데이터 갱신
def update_database():
    """
    initial_krx_list_test.csv 에 있는 모든 종목에 대해
    1) 실시간 스냅샷(현재가·PER·PBR·EPS·BPS·배당률 등) 수집
    2) finalize_scores 로 점수 계산
    3) filtered_stocks.csv 로 저장
    4) price_{code}.csv 히스토리 저장
    """
    # 1) 초기 종목 리스트 로드
    if not os.path.exists("initial_krx_list_test.csv"):
        print("[ERROR] initial_krx_list_test.csv not found.")
        return

    df_list = pd.read_csv("initial_krx_list_test.csv", dtype=str)
    df_list["종목코드"] = df_list["종목코드"].str.zfill(6)

    all_records = []
    for idx, row in df_list.iterrows():
        code = row["종목코드"]
        name = row["종목명"]

        # 2) 일별 스냅샷(시세·재무) 예시: pykrx 로딩
        try:
            today = datetime.today().strftime("%Y%m%d")
            ohlcv = stock.get_market_ohlcv_by_date(today, today, code).iloc[-1]
            fund = stock.get_market_fundamental_by_date(today, today, code).iloc[-1]
            record = {
                "종목명": name,
                "종목코드": code,
                "갱신일": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "현재가": int(ohlcv["종가"]),
                "PER": float(fund["PER"]),
                "PBR": float(fund["PBR"]),
                "EPS": float(fund.get("EPS", float("nan"))),      # 일부 항목은 NaN
                "BPS": float(fund.get("BPS", float("nan"))),
                "배당률": float(fund.get("DIV", float("nan"))),
                "거래량": int(ohlcv["거래량"]),
            }
        except Exception as e:
            print(f"[SKIP] {code} 데이터 수집 실패: {e}")
            continue

        all_records.append(record)
        print(f"[FETCH] {idx+1}/{len(df_list)} {code} snapshot collected.", end="\r")
        time.sleep(0.1)

    if not all_records:
        print("\n[ERROR] 유효한 데이터가 하나도 없습니다. 종료.")
        return

    # 3) DataFrame 생성 → 점수 계산 → CSV 저장
    df = pd.DataFrame(all_records)
    df = finalize_scores(df)  # modules/score_utils.py
    df.to_csv("filtered_stocks.csv", index=False)
    print("\n[SAVE] filtered_stocks.csv saved.")

    # 4) 각 종목별 히스토리 저장
    for rec in all_records:
        save_price_history(rec["종목코드"])
        time.sleep(0.1)

    print("[DONE] update_database completed.")


# ─────────────────────────────────────────────────────────────────────────────
# 3) 개별 종목 데이터 갱신
def update_single_stock(code: str):
    """
    filtered_stocks.csv 에 이미 들어있는 종목에 대해
    1) 스냅샷 재수집 → 레코드 갱신
    2) 점수 재계산 → CSV 덮어쓰기
    3) price_{code}.csv 재저장
    """
    code = str(code).zfill(6)
    if not os.path.exists("filtered_stocks.csv"):
        print("[ERROR] filtered_stocks.csv not found.")
        return

    df = pd.read_csv("filtered_stocks.csv", dtype=str)
    df["종목코드"] = df["종목코드"].str.zfill(6)
    mask = df["종목코드"] == code
    if not mask.any():
        print(f"[ERROR] {code} not in filtered_stocks.csv")
        return

    # 재수집
    try:
        today = datetime.today().strftime("%Y%m%d")
        ohlcv = stock.get_market_ohlcv_by_date(today, today, code).iloc[-1]
        fund = stock.get_market_fundamental_by_date(today, today, code).iloc[-1]
        updates = {
            "갱신일": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "현재가": int(ohlcv["종가"]),
            "PER": float(fund["PER"]),
            "PBR": float(fund["PBR"]),
            "EPS": float(fund.get("EPS", float("nan"))),
            "BPS": float(fund.get("BPS", float("nan"))),
            "배당률": float(fund.get("DIV", float("nan"))),
            "거래량": int(ohlcv["거래량"]),
        }
    except Exception as e:
        print(f"[ERROR] {code} snapshot fetch failed: {e}")
        return

    for k, v in updates.items():
        df.loc[mask, k] = v

    # 점수 재계산
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    print(f"[SAVE] filtered_stocks.csv updated for {code}")

    # 히스토리 재저장
    save_price_history(code)
    print(f"[SAVE] price_{code}.csv refreshed.")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    update_database()
