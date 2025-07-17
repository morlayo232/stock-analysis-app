import pandas as pd
import numpy as np
import time
from modules.score_utils import finalize_scores

def update_database():
    stocks = pd.read_csv("initial_stock_list.csv")
    all_data = []
    N = len(stocks)
    for i, row in stocks.iterrows():
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
    df = finalize_scores(df)   # 점수/급등확률 등 자동 산출
    df.to_csv("filtered_stocks.csv", index=False)

def update_single_stock(code):
    df = pd.read_csv("filtered_stocks.csv")
    idx = df[df["종목코드"]==str(code)].index  # 코드가 str일 가능성 있으니 str로
    if len(idx):
        i = idx[0]
        df.loc[i, "PER"] = np.random.uniform(5,20)
        df.loc[i, "PBR"] = np.random.uniform(0.5,3)
        df.loc[i, "EPS"] = np.random.randint(100,50000)
        df.loc[i, "BPS"] = np.random.randint(1000,50000)
        df.loc[i, "배당률"] = np.random.uniform(0,5)
        df.loc[i, "거래량"] = np.random.randint(1000,100000)
        df.loc[i, "거래량평균20"] = np.random.randint(1000,100000)
        df.loc[i, "고가"] = np.random.randint(2000,60000)
        df.loc[i, "저가"] = np.random.randint(500,30000)
        df.loc[i, "갱신일"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
        df = finalize_scores(df)  # 반드시 점수/급등확률 보정
        df.to_csv("filtered_stocks.csv", index=False)
