import pandas as pd
import numpy as np
import os
import time
from modules.score_utils import finalize_scores

def fetch_krx_data(code):
    """
    실제 KRX/네이버/다음 등에서 해당 종목의 데이터를 수집하는 함수.
    구현 예시로, 반드시 실수집 코드로 교체 필요.
    """
    try:
        # 실제 수집코드로 교체 필요!
        # 아래는 더미값, 데이터 없으면 None 반환
        data = {
            "현재가": 18000 + int(code)%1000,
            "PER": 10 + int(code)%5,
            "PBR": 0.7 + int(code)%3*0.3,
            "EPS": 1200 + int(code)%100,
            "BPS": 15000 + int(code)%1000,
            "배당률": 1.0 + int(code)%2,
            "거래량": 10000 + int(code)%5000,
            "거래량평균20": 9000 + int(code)%5000,
            "고가": 18500 + int(code)%1000,
            "저가": 17500 + int(code)%800,
        }
        return data
    except Exception as e:
        print("수집오류:", e)
        return None

def update_database():
    stocks = pd.read_csv("initial_krx_list_test.csv")  # 파일명 주의
    all_data = []
    N = len(stocks)
    for i, row in stocks.iterrows():
        time.sleep(0.1)
        code = str(row["종목코드"]).zfill(6)
        krx_data = fetch_krx_data(code)
        if krx_data is None:
            print(f"[경고] {row['종목명']}({code}) 데이터 수집 실패!")
            continue
        data = {
            "종목명": row["종목명"],
            "종목코드": code,
            "현재가": krx_data.get("현재가"),
            "PER": krx_data.get("PER"),
            "PBR": krx_data.get("PBR"),
            "EPS": krx_data.get("EPS"),
            "BPS": krx_data.get("BPS"),
            "배당률": krx_data.get("배당률"),
            "거래량": krx_data.get("거래량"),
            "거래량평균20": krx_data.get("거래량평균20"),
            "고가": krx_data.get("고가"),
            "저가": krx_data.get("저가"),
            "갱신일": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        }
        all_data.append(data)
        print(f"{i+1}/{N}개 ({(i+1)/N*100:.1f}%) 갱신 중...", end="\r")
    df = pd.DataFrame(all_data)
    print("\n[DEBUG] 수집 DataFrame: \n", df.head())
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    print("filtered_stocks.csv 저장 위치:", os.path.abspath("filtered_stocks.csv"))
    print("현재 디렉토리 파일:", os.listdir())
    if os.path.exists("filtered_stocks.csv"):
        print("filtered_stocks.csv 생성 완료!")
    else:
        print("filtered_stocks.csv 생성 실패!")

def update_single_stock(code):
    code = str(code).zfill(6)
    df = pd.read_csv("filtered_stocks.csv")
    idx = df[df["종목코드"] == code].index
    if len(idx):
        krx_data = fetch_krx_data(code)
        if krx_data is None:
            print(f"[경고] {code} 데이터 수집 실패(개별)!")
            return
        for k in ["현재가", "PER", "PBR", "EPS", "BPS", "배당률", "거래량", "거래량평균20", "고가", "저가"]:
            df.loc[idx, k] = krx_data.get(k)
        df.loc[idx, "갱신일"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
        df = finalize_scores(df)
        df.to_csv("filtered_stocks.csv", index=False)
        print(f"{code} 개별 데이터 갱신 완료.")
    else:
        print(f"{code} 종목코드 찾을 수 없음.")
