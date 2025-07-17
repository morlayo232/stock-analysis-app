import pandas as pd
import numpy as np
import os
import time
from modules.score_utils import finalize_scores

# 실전에서는 KRX/네이버/다음 등 실수집 함수 사용 필요 (예시는 더미)
def fetch_krx_data(code):
    # TODO: 실제 수집 로직으로 교체
    try:
        # 여기는 더미 (실제는 웹크롤링/OPEN API 등으로 교체)
        return {
            "현재가": np.random.randint(1000, 50000),
            "PER": np.random.uniform(5, 20),
            "PBR": np.random.uniform(0.5, 3),
            "EPS": np.random.randint(100, 50000),
            "BPS": np.random.randint(1000, 50000),
            "배당률": np.random.uniform(0, 5),
            "거래량": np.random.randint(1000, 100000),
            "거래량평균20": np.random.randint(1000, 100000),
            "고가": np.random.randint(2000, 60000),
            "저가": np.random.randint(500, 30000),
        }
    except Exception as e:
        print("수집오류:", e)
        return None

def update_database():
    stocks = pd.read_csv("initial_krx_list_test.csv")  # 파일명 맞게!
    all_data = []
    N = len(stocks)
    for i, row in stocks.iterrows():
        # 실데이터 수집
        stock_data = fetch_krx_data(row["종목코드"])
        if stock_data is None:
            print(f"{row['종목명']}({row['종목코드']}): 데이터 수집 실패, 건너뜀")
            continue
        data = {
            "종목명": row["종목명"],
            "종목코드": str(row["종목코드"]),
            "갱신일": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            **stock_data
        }
        all_data.append(data)
        print(f"{i+1}/{N}개 ({(i+1)/N*100:.1f}%) 갱신 중...", end="\r")
    if not all_data:
        print("수집된 데이터가 없습니다. 파일 저장 건너뜀.")
        return
    df = pd.DataFrame(all_data)
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    time.sleep(0.5)  # 저장 안정화
    print("After save, directory list:", os.listdir())
    assert os.path.exists("filtered_stocks.csv"), "filtered_stocks.csv 파일 생성 실패"
    print("filtered_stocks.csv 최종 생성/확인 완료!")

def update_single_stock(code):
    df = pd.read_csv("filtered_stocks.csv")
    idx = df[df["종목코드"] == str(code)].index
    if not len(idx):
        print("해당 종목 없음")
        return
    # 실데이터 수집
    stock_data = fetch_krx_data(code)
    if stock_data is None:
        print(f"{code}: 개별 수집 실패")
        return
    for k, v in stock_data.items():
        df.loc[idx, k] = v
    df.loc[idx, "갱신일"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)
    time.sleep(0.2)
    print("개별종목 filtered_stocks.csv 저장/확인:", os.path.exists("filtered_stocks.csv"))
