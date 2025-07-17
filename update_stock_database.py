import pandas as pd
import numpy as np
import datetime
from modules.score_utils import calc_score, calc_boom_prob

# 초기 종목리스트 읽기
initial_df = pd.read_csv("initial_stock_list.csv")

result_rows = []
for idx, row in initial_df.iterrows():
    # 필요한 값들 수집 (실제 구현시 크롤링/데이터수집 대체)
    종목명 = row.get("종목명")
    종목코드 = row.get("종목코드")
    # 아래는 예시값, 실제 데이터는 크롤링/DB에서 추출
    PER = row.get("PER", 0)
    PBR = row.get("PBR", 0)
    EPS = row.get("EPS", 0)
    BPS = row.get("BPS", 0)
    배당률 = row.get("배당률", 0)

    # 점수/급등확률 계산
    score = calc_score(PER, PBR, EPS, BPS, 배당률)
    boom_prob = calc_boom_prob(row)

    # 오늘 날짜
    갱신일 = datetime.datetime.today().strftime("%Y-%m-%d")

    result_rows.append({
        "종목명": 종목명,
        "종목코드": 종목코드,
        "PER": PER,
        "PBR": PBR,
        "EPS": EPS,
        "BPS": BPS,
        "배당률": 배당률,
        "score": score,
        "급등확률": boom_prob,
        "갱신일": 갱신일
    })

filtered_df = pd.DataFrame(result_rows)
filtered_df.to_csv("filtered_stocks.csv", index=False, encoding="utf-8-sig")
print("filtered_stocks.csv 갱신 완료")
