# update_stock_database.py

import pandas as pd
from modules.fetch_price import fetch_price
from modules.calculate_indicators import add_tech_indicators

def update_database():
    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    for i, row in df.iterrows():
        code = str(row['종목코드']).zfill(6)
        try:
            price_df = fetch_price(code)
            if price_df is None or price_df.empty:
                print(f"[전체 갱신][{code}] fetch_price 결과 없음/빈 데이터. 건너뜀.")
                continue
            price_df = add_tech_indicators(price_df)
            for col in ['현재가', '거래량', '거래량평균20', 'PER', 'PBR', 'EPS', 'BPS', '배당률']:
                if col in price_df.columns:
                    df.at[i, col] = price_df[col].iloc[-1]
            # 추가: 등락률, 거래량급증, 최고가갱신 컬럼 생성
            if "거래량평균20" in price_df.columns and "거래량" in price_df.columns:
                df.at[i, "거래량급증"] = float(price_df["거래량"].iloc[-1]) / float(price_df["거래량평균20"].iloc[-1]) if float(price_df["거래량평균20"].iloc[-1]) > 0 else 0
            if "현재가" in price_df.columns:
                price = price_df["현재가"].iloc[-1]
                price_yesterday = price_df["현재가"].iloc[-2] if len(price_df) > 1 else price
                df.at[i, "등락률"] = (float(price) - float(price_yesterday)) / float(price_yesterday) * 100 if price_yesterday else 0
                df.at[i, "최고가갱신"] = 1 if price >= price_df["현재가"].rolling(60, min_periods=1).max().iloc[-1] else 0
        except Exception as e:
            print(f"[전체 갱신][{code}] 오류: {e}")
    df.to_csv("filtered_stocks.csv", index=False)
