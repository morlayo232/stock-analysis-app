# update_stock_database.py
import os
import time
import pandas as pd
from datetime import datetime
from modules.score_utils import finalize_scores

# (테스트용 예시 fetch, 실서비스에선 KRX/API 크롤러로 교체)
def fetch_krx_data(code: str):
    # TODO: 실제 크롤링 or API 호출 로직
    # 이 예시에선 항상 성공하도록 임의의 더미 리턴
    return {
        "현재가": 18000,
        "PER": 10.3,
        "PBR": 0.88,
        "EPS": 1500,
        "BPS": 13000,
        "배당률": 1.3,
        "거래량": 51200,
        "거래량평균20": 41500,
        "고가": 18300,
        "저가": 17500,
    }

def update_database():
    # 1) 초기 종목 리스트
    csv_in = "initial_krx_list_test.csv"
    if not os.path.exists(csv_in):
        print(f"{csv_in}이 없습니다.")
        # 헤더만 있는 빈 DataFrame 작성
        pd.DataFrame().to_csv("filtered_stocks.csv", index=False)
        return

    stocks = pd.read_csv(csv_in, dtype=str)
    all_data = []
    N = len(stocks)

    for i, row in stocks.iterrows():
        code = row["종목코드"].zfill(6)
        data = fetch_krx_data(code)  # 절대 None 반환하지 않도록 더미 구현
        # 2) 공통 필드 병합
        rec = {
            "종목명": row["종목명"],
            "종목코드": code,
            "갱신일": datetime.now().strftime("%Y-%m-%d %H:%M"),
            **data
        }
        all_data.append(rec)
        print(f"{i+1}/{N} 업데이트 중...", end="\r")

    # 3) DataFrame으로 변환 → 점수, 급등확률 계산
    df = pd.DataFrame(all_data)
    df = finalize_scores(df)

    # 4) 항상 파일 생성
    df.to_csv("filtered_stocks.csv", index=False, encoding="utf-8-sig")
    time.sleep(0.2)
    print("\n✅ filtered_stocks.csv 생성 완료:", os.path.exists("filtered_stocks.csv"))

def update_single_stock(code: str):
    code = code.zfill(6)
    if not os.path.exists("filtered_stocks.csv"):
        print("filtered_stocks.csv가 없습니다. 전체 업데이트 먼저 해주세요.")
        return

    df = pd.read_csv("filtered_stocks.csv", dtype=str)
    idx = df.index[df["종목코드"] == code]
    if len(idx) == 0:
        print(f"{code} 종목을 찾을 수 없습니다.")
        return

    # 1) 개별 데이터 가져오기
    data = fetch_krx_data(code)
    # 2) 갱신
    for k, v in data.items():
        df.loc[idx, k] = v
    df.loc[idx, "갱신일"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 3) 점수 재계산 및 저장
    df = finalize_scores(df)
    df.to_csv("filtered_stocks.csv", index=False, encoding="utf-8-sig")
    time.sleep(0.1)
    print("✅ 개별종목 갱신 완료:", os.path.exists("filtered_stocks.csv"))
