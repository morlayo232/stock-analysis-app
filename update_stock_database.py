import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
from modules.score_utils import finalize_scores

def fetch_price(code):
    today = datetime.today().strftime("%Y%m%d")
    try:
        df = stock.get_market_ohlcv_by_date(today, today, code)
        if df is not None and not df.empty:
            return int(df['종가'][-1])
    except Exception:
        pass
    return None

def fetch_fundamental(code):
    today = datetime.today().strftime("%Y%m%d")
    try:
        df = stock.get_market_fundamental_by_date(today, today, code)
        if df is not None and not df.empty:
            return {
                'PER': float(df['PER'][-1]) if not pd.isna(df['PER'][-1]) else None,
                'PBR': float(df['PBR'][-1]) if not pd.isna(df['PBR'][-1]) else None,
                'ROE': float('nan'),
                '배당률': float(df['DIV'][-1]) if not pd.isna(df['DIV'][-1]) else None
            }
    except Exception:
        pass
    return {'PER': None, 'PBR': None, 'ROE': None, '배당률': None}

def update_database():
    df_list = pd.read_csv("initial_krx_list_test.csv", dtype={'종목코드': str})
    codes = dict(zip(df_list['종목명'], df_list['종목코드']))
    data = []
    for name, code in codes.items():
        price = fetch_price(code)
        fin = fetch_fundamental(code)
        data.append({
            "종목명": name, "종목코드": code, "현재가": price,
            "PER": fin["PER"], "PBR": fin["PBR"], "ROE": fin["ROE"], "배당률": fin["배당률"]
        })
    df = pd.DataFrame(data)
    df = finalize_scores(df, style="aggressive")
    df.to_csv("filtered_stocks.csv", index=False)
    print("filtered_stocks.csv로 저장 완료!")

def update_single_stock(code):
    import streamlit as st
    import pandas as pd
    from pykrx import stock
    from datetime import datetime, timedelta
    from modules.calculate_indicators import add_tech_indicators

    st.write("===== [갱신 시작] =====")
    st.write("입력 code:", code)
    df = pd.read_csv("filtered_stocks.csv", dtype={'종목코드': str})
    code = str(code).zfill(6)
    row_idx = df[df['종목코드'] == code].index
    if len(row_idx) == 0:
        st.error(f"[개별 갱신][{code}] filtered_stocks.csv에 해당 종목코드 없음")
        raise Exception(f"종목코드({code}) 없음")
    idx = int(row_idx[0])
    try:
        today = datetime.today()
        start = (today - timedelta(days=365)).strftime("%Y%m%d")
        end = today.strftime("%Y%m%d")
        df_price = stock.get_market_ohlcv_by_date(start, end, code)
        if df_price is None or df_price.empty:
            st.error(f"[개별 갱신][{code}] 가격 데이터 없음")
            raise Exception("가격 데이터 없음")

        df_price = add_tech_indicators(df_price)
        fund = stock.get_market_fundamental_by_date(end, end, code)

        df.at[idx, '현재가'] = int(df_price['종가'].iloc[-1])
        if not fund.empty:
            for col in ['PER', 'PBR', 'EPS', 'BPS', 'DIV']:
                if col in fund.columns:
                    val = fund[col].iloc[-1]
                    if col == "DIV":
                        df.at[idx, '배당률'] = val
                    else:
                        df.at[idx, col] = val

        for col in ['RSI_14', 'MACD', 'MACD_SIGNAL', 'EMA_20']:
            if col in df_price.columns:
                df.at[idx, col] = df_price[col].iloc[-1]

        df.to_csv("filtered_stocks.csv", index=False)
        st.success(f"[개별 갱신][{code}] 최신 데이터 및 기술지표 반영됨")
        return True
    except Exception as e:
        st.error(f"[개별 갱신][{code}] 오류: {e}")
        raise
``
