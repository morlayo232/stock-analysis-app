import pandas as pd
from modules.fetch_price import fetch_price  # KRX API에서만 가져옴
from modules.calculate_indicators import add_tech_indicators

# 필요시만(예: KRX에서 못가져온 항목) 아래 임포트 활성화
# from modules.fetch_naver import fetch_naver_fundamentals

def update_database():
    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    for i, row in df.iterrows():
        code = str(row['종목코드'])
        try:
            price_df = fetch_price(code)  # KRX에서 모든 지표/재무 가져옴
            if price_df is not None and not price_df.empty:
                price_df = add_tech_indicators(price_df)
                # KRX에서 PER, PBR, EPS, BPS, 배당률 등 필수 재무 데이터 추출(여기서 fill)
                for col in ['현재가', 'PER', 'PBR', 'EPS', 'BPS', '배당률']:
                    if col in price_df.columns:
                        df.at[i, col] = price_df[col].iloc[-1]
                # 누락/예외시만 네이버 크롤러 보완(선택적)
                # if any(pd.isna(df.at[i, col]) for col in ['PER', 'PBR', 'EPS', 'BPS', '배당률']):
                #     try:
                #         from modules.fetch_naver import fetch_naver_fundamentals
                #         fin = fetch_naver_fundamentals(code)
                #         for col in ['PER', 'PBR', 'EPS', 'BPS', '배당률']:
                #             if col in fin:
                #                 df.at[i, col] = fin[col]
                #     except: pass
        except Exception as e:
            print(f"{code} 갱신 실패: {e}")
    df.to_csv("filtered_stocks.csv", index=False)

def update_single_stock(code):
    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    row_idx = df[df['종목코드'] == str(code)].index
    if len(row_idx) == 0:
        raise Exception("종목코드 없음")
    try:
        price_df = fetch_price(str(code))
        if price_df is not None and not price_df.empty:
            price_df = add_tech_indicators(price_df)
            for col in ['현재가', 'PER', 'PBR', 'EPS', 'BPS', '배당률']:
                if col in price_df.columns:
                    df.at[row_idx[0], col] = price_df[col].iloc[-1]
            # # 누락시만 네이버 크롤러 호출
            # if any(pd.isna(df.at[row_idx[0], col]) for col in ['PER', 'PBR', 'EPS', 'BPS', '배당률']):
            #     try:
            #         from modules.fetch_naver import fetch_naver_fundamentals
            #         fin = fetch_naver_fundamentals(str(code))
            #         for col in ['PER', 'PBR', 'EPS', 'BPS', '배당률']:
            #             if col in fin:
            #                 df.at[row_idx[0], col] = fin[col]
            #     except: pass
        df.to_csv("filtered_stocks.csv", index=False)
        return True
    except Exception as e:
        print(f"{code} 단일 갱신 실패: {e}")
        raise
