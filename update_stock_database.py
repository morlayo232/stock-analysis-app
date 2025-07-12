import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from scipy.stats import zscore

# --- KRX 종목 리스트 불러오기 ---
def get_krx_list():
    df = pd.read_csv('initial_krx_list.csv', dtype=str)
    return df[['종목코드', '종목명']]

# --- 네이버 금융 백업용 주가 크롤러 ---
def fetch_naver_stock_data(ticker):
    url = f"https://finance.naver.com/item/sise_day.nhn?code={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    dfs = []

    for page in range(1, 6):  # 최근 5페이지
        res = requests.get(url + f"&page={page}", headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', class_='type2')
        df = pd.read_html(str(table))[0]
        dfs.append(df)
        time.sleep(0.5)

    df_all = pd.concat(dfs)
    df_all = df_all.dropna()
    df_all.columns = ['날짜', '종가', '전일비', '시가', '고가', '저가', '거래량']
    df_all['날짜'] = pd.to_datetime(df_all['날짜'])
    df_all = df_all.sort_values('날짜')
    df_all.reset_index(drop=True, inplace=True)
    return df_all

# --- 투자 매력 점수 계산 (PER, PBR 기준 Z-Score 활용) ---
def calc_score(fin_df):
    fin_df['PER_z'] = zscore(fin_df['PER'].astype(float))
    fin_df['PBR_z'] = zscore(fin_df['PBR'].astype(float))
    fin_df['score'] = -fin_df['PER_z'] - fin_df['PBR_z']
    return fin_df

# --- 메인 실행 함수 ---
def main():
    krx_list = get_krx_list()
    records = []

    for idx, row in krx_list.iterrows():
        code = row['종목코드']
        name = row['종목명']
        try:
            stock = yf.Ticker(code)
            hist = stock.history(period="6mo")

            if hist.empty or len(hist) < 10:
                hist = fetch_naver_stock_data(code)
                if hist.empty:
                    print(f"📭 주가 데이터 없음: {code} {name}")
                    continue

            # 예시 재무데이터 (실제는 크롤링 또는 API 연동 필요)
            per = 10.0
            pbr = 1.2
            dividend = 2.5
            market = "코스피" if code.startswith("0") else "코스닥"

            records.append({
                '종목코드': code,
                '종목명': name,
                '시장구분': market,
                'PER': per,
                'PBR': pbr,
                'ROE': 8.0,
                '배당률': dividend,
                '현재가': hist['Close'].iloc[-1],
                '거래량': hist['Volume'].iloc[-1],
                '3개월수익률': round((hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100, 2),
                '기술점수': 0,
                '세력점수': 0,
                'RSI': 0,
                'MACD': 0,
                'Signal': 0
            })
            print(f"✅ 수집 완료: {code} {name}")
            time.sleep(0.2)
        except Exception as e:
            print(f"⚠️ 오류 {code} {name}: {e}")

    df = pd.DataFrame(records)
    df = calc_score(df)
    df.to_csv('filtered_stocks.csv', index=False, encoding='utf-8-sig')
    print("📁 filtered_stocks.csv 저장 완료")

# Streamlit 앱에서 직접 호출될 수 있도록 구성
if __name__ == "__main__":
    main()

