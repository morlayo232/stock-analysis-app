import pandas as pd
import numpy as np
import time
from modules.score_utils import finalize_scores

def update_database():
    stocks = pd.read_csv("initial_stock_list.csv")
    all_data = []
    N = len(stocks)
    for i, row in stocks.iterrows():
        # 아래는 실제 크롤러/수집코드 대체
        time.sleep(0.1)
        data = {
            "종목명": row["종목명"],
            "종목코드": row["종목코드"],
            "현재가": np.random.randint(1000,50000),
            "PER": np.random.uniform(5,20),
            "PBR": np.random.uniform(0.5,3),
            "EPS": np.random.randint(100,50000),
            "BPS": np.random.randint(1000,50000),
            "배당률": np.random.uniform(0,5),
            "거래량": np.random.randint(1000,100000),
            "거래량평균20": np.random.randint(1000,100000),
            "고가": np.random.randint(2000,60000),
            "저가": np.random.randint(500,30000),
            "갱신일": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
        }
        all_data.append(data)
        print(f"{i+1}/{N}개 ({(i+1)/N*100:.1f}%) 갱신 중...", end="\r")
    df = pd.DataFrame(all_data)
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False)

def update_single_stock(code):
    # 실제로는 해당 code만 다시 수집
    df = pd.read_csv("filtered_stocks.csv")
    idx = df[df["종목코드"]==int(code)].index
    if len(idx):
        # 예시용 랜덤 갱신
        df.loc[idx, "PER"] = np.random.uniform(5,20)
        df.loc[idx, "PBR"] = np.random.uniform(0.5,3)
        df.loc[idx, "EPS"] = np.random.randint(100,50000)
        df.loc[idx, "BPS"] = np.random.randint(1000,50000)
        df.loc[idx, "배당률"] = np.random.uniform(0,5
