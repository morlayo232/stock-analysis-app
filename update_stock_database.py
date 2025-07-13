# update_stock_database.py
import pandas as pd
import yfinance as yf
import time
import requests
from bs4 import BeautifulSoup
from modules.calculate_indicators import calculate_indicators
from modules.score_utils import calc_base_score, apply_style_weight

# --- KRX 종목 리스트 불러오기 ---
def get_krx_list():
    return pd.read_csv('initial_krx_list.csv', dtype=str)[['종목코드', '종목명', '시장구분']]

# --- Naver 주가 크롤링 ---
def fetch_naver_data(code):
    try:
        url = f"https://finance.naver.com/item/sise_day.nhn?code={code}"
        headers = {"User-Agent": "Mozilla/5.0"}
        dfs = []
        for page in range(1, 4):
            res = requests.get(f"{url}&page={page}", headers=headers, timeout=5)
            df = pd.read_html(res.text)[0]
            dfs.append(df)
            time.sleep(0.5)
        df = pd.concat(dfs).dropna()
        df.columns = ['날짜', '종가', '전일비', '시가', '고가', '저가', '거래량']
        df['날짜'] = pd.to_datetime(df['날짜'])
        df = df.sort_values('날짜')
        df.rename(columns={'종가': 'Close', '거래량': 'Volume'}, inplace=True)
        return df.reset_index(drop=True)
    except:
        return pd.DataFrame()

# --- 주가 수집 (yfinance → Naver) ---
def fetch_price_data(code, market):
    ticker = f"{code}.KS" if market == "KOSPI" else f"{code}.KQ"
    try:
        data = yf.Ticker(ticker).history(period="6mo")
        if data.empty or len(data) < 20:
            raise Exception("yfinance data 부족")
        data.reset_index(inplace=True)
        return data
    except:
        return fetch_naver_data(code)

# --- 재무 지표 크롤링 (기본값 대체 포함) ---
def fetch_financial_info(code):
    try:
        url = f"https://finance.naver.com/item/main.nhn?code={code}"
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        per = float(soup.select_one("em#_per").text.replace(",", ""))
        pbr = float(soup.select_one("em#_pbr").text.replace(",", ""))
        roe = float(soup.select_one("em#_roe").text.replace(",", ""))
        dividend = float(soup.select_one("table tbody tr:nth-child(10) td em").text.strip('%'))
        return per, pbr, roe, dividend
    except:
        return 10.0, 1.0, 8.0, 2.0

# --- 메인 함수 ---
def main():
    krx = get_krx_list()
    records = []

    for _, row in krx.iterrows():
        code, name, market = row['종목코드'], row['종목명'], row['시장구분']
        try:
            df = fetch_price_data(code, market)
            if df.empty or 'Close' not in df.columns:
                print(f"⚠️ 데이터 없음: {code} {name}")
                continue

            df = calculate_indicators(df)
            per, pbr, roe, dividend = fetch_financial_info(code)

            close = df['Close'].iloc[-1]
            volume = df['Volume'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            macd = df['MACD'].iloc[-1]
            signal = df['Signal'].iloc[-1]
            ret_3m = (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100

            tech_score = 0
            if rsi < 30: tech_score += 10
            if macd > signal: tech_score += 10
            force_score = 10 if volume > df['Volume'].mean() else 0

            records.append({
                '종목코드': code,
                '종목명': name,
                '시장구분': market,
                'PER': per,
                'PBR': pbr,
                'ROE': roe,
                '배당률': dividend,
                '현재가': close,
                '거래량': volume,
                '3개월수익률': round(ret_3m, 2),
                '기술점수': tech_score,
                '세력점수': force_score,
                'RSI': round(rsi, 2),
                'MACD': round(macd, 2),
                'Signal': round(signal, 2)
            })

            print(f"✓ 수집 완료: {code} {name}")
            time.sleep(0.3)

        except Exception as e:
            print(f"❌ 오류: {code} {name} - {e}")
            continue

    df = pd.DataFrame(records)
    if df.empty:
        print("❌ 저장 중단: 데이터 없음")
        return

    df = calc_base_score(df)
    df = apply_style_weight(df, "공격적")  # 기본 저장 기준

    try:
        df.to_csv("filtered_stocks.csv", index=False, encoding="utf-8-sig")
        print("✅ 저장 완료: filtered_stocks.csv")
    except Exception as e:
        print(f"❌ 저장 실패: {e}")

if __name__ == "__main__":
    main()
