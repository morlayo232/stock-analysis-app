import os
import pandas as pd
from modules.score_utils import finalize_scores
from modules.fetch_price import fetch_price
from modules.fetch_naver import fetch_naver_financials
from datetime import datetime

# 1) 작업 디렉터리 강제 이동 (이 파일이 있는 폴더가 루트라고 가정)
os.chdir(os.path.dirname(__file__))

INITIAL_CSV = "initial_krx_list_test.csv"  # 실제 사용하는 파일명
OUTPUT_CSV  = "filtered_stocks.csv"

def fetch_fundamental(code):
    fin = fetch_naver_financials(code) or {}
    return {
        "PER": fin.get("PER"),
        "PBR": fin.get("PBR"),
        "EPS": fin.get("EPS"),
        "BPS": fin.get("BPS"),
        "배당률": fin.get("배당수익률")
    }

def update_database():
    df_list = pd.read_csv(INITIAL_CSV, dtype=str)
    records = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    for idx, row in df_list.iterrows():
        code = row["종목코드"]
        price = fetch_price(code)
        fin   = fetch_fundamental(code)
        if price is None or any(v is None for v in fin.values()):
            print(f"> {row['종목명']}({code}) 수집 불완전, 스킵")
            continue
        rec = {
            "종목명": row["종목명"],
            "종목코드": code,
            "현재가": price,
            **fin,
            "갱신일": now
        }
        records.append(rec)
        print(f"\r{idx+1}/{len(df_list)} 갱신 중…", end="")

    if not records:
        print("\n▶ 수집된 데이터가 없습니다. 저장하지 않습니다.")
        return

    df = pd.DataFrame(records)
    df = finalize_scores(df)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n▶ {OUTPUT_CSV} 생성 완료 (총 {len(df)}개)")

if __name__ == "__main__":
    update_database()
