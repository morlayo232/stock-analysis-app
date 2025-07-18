# update_stock_database.py

import pandas as pd
import numpy as np
from datetime import datetime
from modules.score_utils import finalize_scores

# 실제 KRX/API 수집 로직으로 교체하세요
def fetch_krx_data(code):
    try:
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
        return None

def update_single_stock(df_all: pd.DataFrame, code: str) -> pd.DataFrame:
    """
    df_all: 현재 세션에 로드된 전체 DataFrame
    code: 6자리 문자열 종목코드
    반환값: 해당 코드 행만 갱신된 새로운 DataFrame
    """
    # 실데이터 수집
    stock_data = fetch_krx_data(code)
    if stock_data is None:
        raise RuntimeError(f"{code} 데이터 수집 실패")
    # 갱신일 기록
    stock_data["갱신일"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    # 해당 행 인덱스 찾기
    idx = df_all.index[df_all["종목코드"] == code]
    if len(idx) == 0:
        raise KeyError(f"{code} 종목이 존재하지 않습니다.")
    i = idx[0]
    # 필드 덮어쓰기
    for k, v in stock_data.items():
        df_all.at[i, k] = v
    # 전체 DataFrame에 score/급등확률 재계산
    df_all = finalize_scores(df_all)
    return df_all
