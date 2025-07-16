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
            for col in ['현재가', 'PER', 'PBR', 'EPS', 'BPS', '배당률']:
                if col in price_df.columns:
                    df.at[i, col] = price_df[col].iloc[-1]
                else:
                    print(f"[전체 갱신][{code}] 컬럼 {col} 없음")
        except Exception as e:
            print(f"[전체 갱신][{code}] 오류: {e}")
    df.to_csv("filtered_stocks.csv", index=False)

def update_single_stock(code):
    import pandas as pd
    from modules.fetch_price import fetch_price
    from modules.calculate_indicators import add_tech_indicators

    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    code = str(code).zfill(6)
    row_idx = df[df['종목코드'] == code].index
    if len(row_idx) == 0:
        print(f"[개별 갱신][{code}] filtered_stocks.csv에 해당 종목코드 없음")
        return
    idx = int(row_idx[0])
    try:
        price_df = fetch_price(code)
        if price_df is None or price_df.empty:
            print(f"[개별 갱신][{code}] 가격 데이터 없음")
            return
        price_df = add_tech_indicators(price_df)
        for col in ['현재가', 'PER', 'PBR', 'EPS', 'BPS', '배당률']:
            if col in price_df.columns:
                df.at[idx, col] = price_df[col].iloc[-1]
        df.to_csv("filtered_stocks.csv", index=False)
        print(f"[개별 갱신][{code}] 최신 데이터 반영 완료")
    except Exception as e:
        print(f"[개별 갱신][{code}] 오류: {e}")
        return
