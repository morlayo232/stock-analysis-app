# app.py

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import json

sys.path.append(os.path.abspath("modules"))

from score_utils import finalize_scores, assess_reliability
from fetch_news import fetch_google_news
from chart_utils import plot_price_rsi_macd
from calculate_indicators import add_tech_indicators
from datetime import datetime
from pykrx import stock

st.set_page_config(page_title="투자 매니저", layout="wide")
st.title("투자 매니저")

# 즐겨찾기 파일명
FAV_FILE = "favorites.json"

def load_favorites():
    if os.path.exists(FAV_FILE):
        with open(FAV_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_favorites(fav_list):
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump(fav_list, f, ensure_ascii=False)

@st.cache_data
def load_filtered_data():
    try:
        df = pd.read_csv("filtered_stocks.csv")
        expected = [
            "종목명", "종목코드", "현재가",
            "PER", "PBR", "EPS", "BPS", "배당률"
        ]
        for col in expected:
            if col not in df.columns:
                df[col] = np.nan
        return df
    except Exception:
        from update_stock_database import update_database
        try:
            update_database()
            df = pd.read_csv("filtered_stocks.csv")
            for col in expected:
                if col not in df.columns:
                    df[col] = np.nan
            return df
        except Exception:
            return pd.DataFrame()

style = st.sidebar.radio(
    "투자 성향", ["aggressive", "stable", "dividend"], horizontal=True
)

# -------------------------------
# 사이드바 즐겨찾기 기능/등록/해제/선택
fav_list = load_favorites()

raw_df = load_filtered_data()
if not isinstance(raw_df, pd.DataFrame):
    st.error("데이터가 DataFrame 형식이 아닙니다.")
    st.stop()

if raw_df.empty:
    st.error("데이터프레임이 비어 있습니다.")
    st.stop()

scored_df = finalize_scores(raw_df, style=style)
scored_df["신뢰등급"] = scored_df.apply(assess_reliability, axis=1)
top10 = scored_df.sort_values("score", ascending=False).head(10)

st.sidebar.markdown("#### ⭐ 즐겨찾기")
# 즐겨찾기 등록/해제 대상: 선택 종목과 동일하게 드롭다운에 반영
sidebar_fav_selected = None
if fav_list:
    sidebar_fav_selected = st.sidebar.selectbox(
        "즐겨찾기 목록", fav_list, key="fav_selectbox"
    )
else:
    sidebar_fav_selected = None

# 본문 종목 기본 선택 처리: 즐겨찾기 선택 > TOP10 > 전체
if sidebar_fav_selected:
    selected = sidebar_fav_selected
    code = scored_df[scored_df["종목명"] == selected]["종목
