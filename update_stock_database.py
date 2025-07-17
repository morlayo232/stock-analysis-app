import pandas as pd
import numpy as np
import datetime
from modules.score_utils import calc_score, calc_boom_prob
from modules.calculate_indicators import fetch_krx_fundamental

def update_database(initial_file="initial_stock_list_test.csv", filtered_file="filtered_stocks.csv"):
    initial_df = pd.read_csv(initial_file)
    result_rows = []
    for _, row in initial_df.iterrows():
        종목명 = row.get("종목명")
        종목코드 = row.get("종목코드")
        # KRX 등에서 실제로 값 수집
        fund = fetch_krx_fundamental(종목코드)
        PER = fund.get("PER", 0)
        PBR = fund.get("PBR", 0)
        EPS = fund.get("EPS", 0)
        BPS = fund.get("BPS", 0)
        배당률 = fund.get("배당률", 0)
        score = calc_score(PER, PBR, EPS, BPS, 배당률)
        boom_prob = calc_boom_prob(fund)
        갱신일 = datetime.datetime.today().strftime("%Y-%m-%d")
        result_rows.append({
            "종목명": 종목명, "종목코드": 종목코드, "PER": PER, "PBR": PBR, "EPS": EPS, "BPS": BPS, 
            "배당률": 배당률, "score": score, "급등확률": boom_prob, "갱신일": 갱신일
        })
    filtered_df = pd.DataFrame(result_rows)
    filtered_df.to_csv(filtered_file, index=False, encoding="utf-8-sig")
    print("filtered_stocks.csv 갱신 완료")

if __name__ == "__main__":
    update_database()
