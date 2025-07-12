# update_stock_database.py
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from scipy.stats import zscore

# --- 기본 종목 리스트 가져오기 ---
def get_krx_list():
    df = pd.read_csv('initial_krx_list.csv', dtype=str)
    return df[['종목코드', '종목명', '시장구분']]

# --- 네이버 금융 주가 데이터 크롤링 (fallback) ---
def fetch_naver_stock_data(ticker):
    url = f"https://finance.naver.com/item/sise_day.nhn?code={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    dfs = []
    for page in range(1, 6):
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

# --- 투자 매력도 계산 ---
def calc_score(df):
    df['PER'] = pd.to_numeric(df['PER'], errors='coerce')
    df['PBR'] = pd.to_numeric(df['PBR'], errors='coerce')
    df['ROE'] = pd.to_numeric(df['ROE'], errors='coerce')
    df['기술점수'] = pd.to_numeric(df['기술점수'], errors='coerce').fillna(0)
    df['세력점수'] = pd.to_numeric(df['세력점수'], errors='coerce').fillna(0)

    df['PER_z'] = zscore(df['PER'].fillna(df['PER'].mean()))
    df['PBR_z'] = zscore(df['PBR'].fillna(df['PBR'].mean()))
    df['score'] = -df['PER_z'] - df['PBR_z'] + df['기술점수'] + df['세력점수']
    return df

# --- 메인 실행 함수 ---
def main():
    krx_list = get_krx_list()
    records = []

    for idx, row in krx_list.iterrows():
        code = row['종목코드']
        name = row['종목명']
        market = row['시장구분']

        try:
            stock = yf.Ticker(code)
            hist = stock.history(period="3mo")
            if hist.empty or len(hist) < 10:
                hist = fetch_naver_stock_data(code)
                if hist.empty:
                    print(f"[X] 주가 없음: {code} {name}")
                    continue

            per = 10.0  # 예시 placeholder
            pbr = 1.2
            roe = 8.5
            dividend = 2.0

            r3m = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
            tech_score = 1.0  # 향후 기술적 분석 기반 점수 반영 가능
            power_score = 1.0  # 세력 점수: 추세/거래량 분석 기반 반영 가능

            last_rsi = 50
            last_macd = 0
            last_signal = 0

            records.append({
                '종목코드': code,
                '종목명': name,
                '시장구분': market,
                'PER': per,
                'PBR': pbr,
                'ROE': roe,
                '배당률': dividend,
                '현재가': hist['Close'].iloc[-1],
                '거래량': hist['Volume'].iloc[-1],
                '3개월수익률': round(r3m, 2),
                '기술점수': tech_score,
                '세력점수': power_score,
                'RSI': last_rsi,
                'MACD': last_macd,
                'Signal': last_signal
            })
            print(f"[O] 수집 완료: {code} {name}")
            time.sleep(0.2)

        except Exception as e:
            print(f"[!] 오류 발생: {code} {name} → {e}")

    df = pd.DataFrame(records)
    df = calc_score(df)
    df.to_csv('filtered_stocks.csv', index=False, encoding='utf-8-sig')
    print("✅ filtered_stocks.csv 갱신 완료")

if __name__ == "__main__":
    main()
