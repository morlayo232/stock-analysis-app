# 📄 update_stock_database.py

import pandas as pd
from modules.fetch_price import fetch_price
from modules.calculate_indicators import add_tech_indicators

def update_database():
    """
    전체 종목 데이터 일괄 갱신 (filtered_stocks.csv 전체)
    """
    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    for i, row in df.iterrows():
        code = str(row['종목코드']).zfill(6)
        try:
            price_df = fetch_price(code)
            if price_df is None or price_df.empty:
                print(f"{code}: fetch_price 결과 없음/빈 데이터")
                continue
            price_df = add_tech_indicators(price_df)
            for col in ['현재가', 'PER', 'PBR', 'EPS', 'BPS', '배당률']:
                if col in price_df.columns:
                    df.at[i, col] = price_df[col].iloc[-1]
        except Exception as e:
            print(f"{code} 갱신 실패: {e}")
    df.to_csv("filtered_stocks.csv", index=False)

def update_single_stock(code):
    """
    특정 종목코드(code, str/숫자)만 최신 데이터로 갱신
    """
    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    code = str(code).zfill(6)
    row_idx = df[df['종목코드'] == code].index
    if len(row_idx) == 0:
        raise Exception(f"종목코드({code}) 없음. filtered_stocks.csv 내에 없음.")
    try:
        price_df = fetch_price(code)
        if price_df is None or price_df.empty:
            raise Exception(f"fetch_price({code}) 결과 없음/빈 데이터")
        price_df = add_tech_indicators(price_df)
        for col in ['현재가', 'PER', 'PBR', 'EPS', 'BPS', '배당률']:
            if col in price_df.columns:
                df.at[row_idx[0], col] = price_df[col].iloc[-1]
        df.to_csv("filtered_stocks.csv", index=False)
        return True
    except Exception as e:
        print(f"{code} 단일 갱신 실패: {e}")
        raise
