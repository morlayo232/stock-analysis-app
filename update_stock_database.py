import pandas as pd
import sys
import os

# modules 폴더가 현재 파일과 같은 경로에 있을 때만 작동 (권장 구조)
MODULE_DIR = os.path.join(os.path.dirname(__file__), "modules")
if MODULE_DIR not in sys.path:
    sys.path.append(MODULE_DIR)

from fetch_price import fetch_price
from fetch_naver import fetch_naver_fundamentals
from calculate_indicators import add_tech_indicators

def update_database():
    """
    전체 종목 데이터 일괄 갱신 (filtered_stocks.csv 전체)
    """
    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    for i, row in df.iterrows():
        code = str(row['종목코드'])
        try:
            price_df = fetch_price(code)
            if price_df is not None and not price_df.empty:
                price_df = add_tech_indicators(price_df)
                fin = fetch_naver_fundamentals(code)
                for col in ['현재가', 'PER', 'PBR', 'EPS', 'BPS', '배당률']:
                    if col in fin:
                        df.at[i, col] = fin[col]
                    elif col in price_df.columns:
                        df.at[i, col] = price_df[col].iloc[-1]
        except Exception as e:
            print(f"{code} 갱신 실패: {e}")
    df.to_csv("filtered_stocks.csv", index=False)

def update_single_stock(code):
    """
    특정 종목코드(code)만 최신 데이터로 갱신
    """
    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    row_idx = df[df['종목코드'] == str(code)].index
    if len(row_idx) == 0:
        raise Exception("종목코드 없음")
    try:
        price_df = fetch_price(str(code))
        if price_df is not None and not price_df.empty:
            price_df = add_tech_indicators(price_df)
            fin = fetch_naver_fundamentals(str(code))
            for col in ['현재가', 'PER', 'PBR', 'EPS', 'BPS', '배당률']:
                if col in fin:
                    df.at[row_idx[0], col] = fin[col]
                elif col in price_df.columns:
                    df.at[row_idx[0], col] = price_df[col].iloc[-1]
        df.to_csv("filtered_stocks.csv", index=False)
        return True
    except Exception as e:
        print(f"{code} 단일 갱신 실패: {e}")
        raise
