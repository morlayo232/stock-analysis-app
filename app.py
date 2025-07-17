import streamlit as st
import pandas as pd
import os
from modules.score_utils import finalize_scores, assess_reliability, FIELD_EXPLAIN
from update_stock_database import update_database, update_single_stock

st.set_page_config(page_title="투자 매니저", layout="wide")

@st.cache_data
def load_all_stocklist():
    if os.path.exists("initial_krx_list_test.csv"):
        df = pd.read_csv("initial_krx_list_test.csv")
        names = df["종목명"].astype(str).tolist()
        codes = df["종목코드"].astype(str).tolist()
        options = [f"{n} ({c})" for n, c in zip(names, codes)]
        code_map = dict(zip(options, codes))
        return options, code_map, names
    return [], {}, []

options, code_map, names = load_all_stocklist()

st.title("투자 매니저")
st.markdown("### 🔍 종목 검색")
selected = st.text_input("종목명 또는 코드 입력", "", key="searchbox", help="종목명 일부 입력 시 연관 검색 지원")
autocomplete = [o for o in options if selected in o or selected in o.replace(" ", "")] if selected else options
if autocomplete:
    selected_option = st.selectbox("", autocomplete, key="autofill")
    code = code_map[selected_option]
    name = selected_option.split(" (")[0]
else:
    code, name = "", ""

if code:
    st.markdown(f"**조회 중인 종목:** <span style='color:#1166bb;font-weight:bold'>{name} ({code})</span>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("🔄 개별갱신"):
            update_single_stock(code)
            st.success("개별 종목 데이터 갱신 완료!")
    with col_btn2:
        if st.button("🌐 전체갱신"):
            with st.spinner("전체 데이터 갱신중..."):
                update_database()
                st.success("전체 데이터 갱신 완료!")

df_all = pd.read_csv("filtered_stocks.csv") if os.path.exists("filtered_stocks.csv") else pd.DataFrame()
row = df_all[df_all["종목코드"] == str(code)].iloc[0] if (code and not df_all.empty and (df_all["종목코드"] == str(code)).any()) else None

st.markdown("### 📊 최신 재무 정보")
fields = ["PER", "PBR", "EPS", "BPS", "배당률", "score", "급등확률"]
if row is not None:
    cols = st.columns(2)
    for i, f in enumerate(fields):
        with cols[i%2]:
            st.metric(
                f"{f}  ", f"{row[f]:,.2f}" if pd.notna(row[f]) else "-",
                help=FIELD_EXPLAIN.get(f, "")
            )
    st.caption(f"⏰ 갱신일: {row['갱신일']} / 신뢰등급: {row.get('신뢰등급','-')}")
else:
    st.info("조회된 재무 데이터가 없습니다.")

# 이하 차트, 점수/급등 top10 등은 동일하게 구현
