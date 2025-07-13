import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from modules import calculate_indicators
from scipy.stats import zscore

# --- KRX 리스트 불러오기 ---
def get_krx_list():
    return pd.read_csv('initial_krx_list_test.csv', dtype=str)[['종목코드', '종목명', '시장구분']]

# --- Naver 주가 크롤링 fallback ---
def fetch_naver_stock_data(ticker):
    url = f"https://finance.naver.com/item/sise_day.nhn?code={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    dfs = []
    for page in range(1, 6):
        res = requests.get(url + f"&page={page}", headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', class_='type2')
        try:
            df = pd.read_html(str(table))[0]
            dfs.append(df)
        except:
            continue
        time.sleep(0.5)
    df_all = pd.concat(dfs).dropna()
    df_all.columns = ['날짜', '종가', '전일비', '시가', '고가', '저가', '거래량']
    df_all['날짜'] = pd.to_datetime(df_all['날짜'])
    df_all = df_all.sort_values('날짜').reset_index(drop=True)
    return df_all

# --- score 계산 함수 ---
def calc_score(fin_df):
    fin_df[['PER', 'PBR', 'ROE']] = fin_df[['PER', 'PBR', 'ROE']].astype(float)
    fin_df['PER_z'] = zscore(fin_df['PER'])
    fin_df['PBR_z'] = zscore(fin_df['PBR'])
    fin_df['ROE_z'] = zscore(fin_df['ROE'])
    fin_df['score'] = -fin_df['PER_z'] - fin_df['PBR_z'] + fin_df['ROE_z']
    return fin_df

# --- 메인 ---
def main():
    krx_list = get_krx_list()
    records = []

    for idx, row in krx_list.iterrows():
        code, name, market = row['종목코드'], row['종목명'], row['시장구분']
        ticker = f"{code}.KS" if market == 'KOSPI' else f"{code}.KQ"

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6mo")
            if hist.empty or len(hist) < 10:
                hist = fetch_naver_stock_data(code)
                if hist.empty:
                    print(f"⚠️ 데이터 부족: {code} {name}")
                    continue
                hist.rename(columns={'종가': 'Close', '거래량': 'Volume'}, inplace=True)

            # 기술 지표 계산
            hist = hist.reset_index()
            hist = calculate_indicators(hist)

            # 예시 수치 (실제 API 연동 필요)
            per, pbr, roe, dividend = 10.0, 1.2, 8.0, 2.5
            current_price = hist['Close'].iloc[-1]
            volume = hist['Volume'].iloc[-1]
            rsi = hist['RSI'].iloc[-1]
            macd = hist['MACD'].iloc[-1]
            signal = hist['Signal'].iloc[-1]
            ret_3m = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100

            # 기술/세력 점수 계산
            tech_score = 0
            if rsi < 30: tech_score += 10
            if macd > signal: tech_score += 10
            force_score = 10 if volume > hist['Volume'].mean() else 0

            records.append({
                '종목코드': code,
                '종목명': name,
                '시장구분': market,
                'PER': per,
                'PBR': pbr,
                'ROE': roe,
                '배당률': dividend,
                '현재가': current_price,
                '거래량': volume,
                '3개월수익률': round(ret_3m, 2),
                '기술점수': tech_score,
                '세력점수': force_score,
                'RSI': round(rsi, 2),
                'MACD': round(macd, 2),
                'Signal': round(signal, 2),
            })

            print(f"✓ 수집 완료: {code} {name}")
            time.sleep(0.3)

        except Exception as e:
            print(f"❌ 오류: {code} {name} - {e}")
            continue

    df = pd.DataFrame(records)
    df = calc_score(df)
    df.to_csv('filtered_stocks.csv', index=False, encoding='utf-8-sig')
    print("✅ filtered_stocks.csv 저장 완료")

if __name__ == "__main__":
    main()
