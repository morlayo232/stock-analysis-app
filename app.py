# app.py

import sys
import os
sys.path.append(os.path.abspath("modules"))  # 이 라인은 반드시 import문 전에!

import streamlit as st
import pandas as pd
import numpy as np

from fetch_news import fetch_google_news
from score_utils import finalize_scores, assess_reliability
from chart_utils import plot_price_rsi_macd
from calculate_indicators import add_tech_indicators
# ...

# 1. 전체 종목리스트 불러오기 (예: initial_krx_list.csv)
df_list = pd.read_csv("initial_krx_list.csv")  # 컬럼: 종목코드, 종목명, 시장구분 등
codes = dict(zip(df_list['종목명'], df_list['종목코드']))

# 2. 개별 종목별 재무/주가/뉴스 일괄 수집
def fetch_price(code):
    today = datetime.today().strftime("%Y%m%d")
    try:
        df = stock.get_market_ohlcv_by_date(today, today, code)
        if not df.empty:
            return int(df['종가'][-1])
    except Exception:
        pass
    return None

def fetch_fundamental(code):
    today = datetime.today().strftime("%Y%m%d")
    try:
        df = stock.get_market_fundamental_by_date(today, today, code)
        if not df.empty:
            return {
                'PER': float(df['PER'][-1]),
                'PBR': float(df['PBR'][-1]),
                'ROE': float('nan'),  # 필요시 fetch_naver 등에서 보조 추출
                '배당수익률': float(df['DIV'][-1])
            }
    except Exception:
        pass
    return {'PER': None, 'PBR': None, 'ROE': None, '배당수익률': None}

st.set_page_config(page_title="투자 매니저", layout="wide")
st.title("투자 매니저")

style = st.sidebar.radio("투자 성향", ["aggressive", "stable", "dividend"], horizontal=True)

data = []
# 전체 종목 반복 (많으니 속도/트래픽 고려해 1회만 실행 또는 DB 저장 추천)
for name, code in codes.items():
    price = fetch_price(code)
    fin = fetch_fundamental(code)
    data.append({
        "종목명": name, "종목코드": code, "현재가": price,
        "PER": fin["PER"], "PBR": fin["PBR"], "ROE": fin["ROE"], "배당수익률": fin["배당수익률"]
    })

df = pd.DataFrame(data)
df = finalize_scores(df, style=style)

st.subheader("투자 성향별 TOP 10")
st.dataframe(df.sort_values("score", ascending=False).head(10)[["종목명", "종목코드", "현재가", "PER", "PBR", "ROE", "배당수익률", "score"]])

st.subheader("종목별 최신 뉴스 (구글 뉴스)")
for _, row in df.sort_values("score", ascending=False).head(10).iterrows():
    st.markdown(f"**{row['종목명']} ({row['종목코드']})**")
    news_list = fetch_google_news(row['종목명'])
    if news_list:
        for n in news_list:
            st.markdown(f"- {n}")
    else:
        st.write("뉴스 없음")
