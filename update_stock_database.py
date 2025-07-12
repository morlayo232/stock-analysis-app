import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from scipy.stats import zscore

# KRX 종목 리스트 불러오기
def get_krx_list():
    df = pd.read_csv('initial_krx_list.csv', dtype=str)
    return df[['종목코드', '종목명', '시장구분']]

# 네이버 금융 크롤링 (백업용)
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
    df_all['Close'] = pd.to_numeric(df_all['종가'].str.replace(',', ''))
    df_all['Volume'] = pd.to_numeric(df_all['거래량'].astype(str).str.replace(',', ''), errors='coerce')
    df_all.reset_index(drop=True, inplace=True)
    return df_all[['날짜', 'Close', 'Volume']]

# 투자 매력도 스코어 계산
def calc_score(df):
    df['PER_z'] = zscore(df['PER'].astype(float))
    df['PBR_z'] = zscore(df['PBR'].astype(float))
    df['score'] = -df['PER_z'] - df['PBR_z']  # 낮을수록 매력 있음
    return df

def main():
    krx = get_krx_list()
    records = []

    for idx, row in krx.iterrows():
        code = row['종목코드']
        name = row['종목명']
        market = row['시장구분']
        ticker = code + (".KS" if market == "코스피" else ".KQ")

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6mo")
            if hist.empty or len(hist) < 10:
                hist = fetch_naver_stock_data(code)
                if hist.empty:
                    print(f"❌ {name}({code}) 데이터 없음")
                    continue
            else:
                hist = hist.reset_index()
                hist = hist[['Date', 'Close', 'Volume']]

            per = 8.5   # 예시 값
            pbr = 0.9   # 예시 값
            dividend = 3.0  # 예시 값

            close_now = hist['Close'].iloc[-1]
            close_past = hist['Close'].iloc[0]
            rate_3m = (close_now / close_past - 1) * 100

            volume_now = hist['Volume'].iloc[-1]
            volume_past = hist['Volume'].rolling(window=20).mean().iloc[-1]
            smart_money_ratio = volume_now / volume_past if volume_past else 0

            records.append({
                '종목코드': code,
                '종목명': name,
                '시장구분': market,
                'PER': per,
                'PBR': pbr,
                '배당률': dividend,
                '거래량': volume_now,
                '3개월수익률': round(rate_3m, 2),
                '세력지표': round(smart_money_ratio, 2)
            })
            print(f"✅ {name} ({code}) 처리 완료")
            time.sleep(0.1)
        except Exception as e:
            print(f"❗ 오류 - {name}({code}): {e}")

    df = pd.DataFrame(records)
    df = calc_score(df)
    df.to_csv("filtered_stocks.csv", index=False, encoding='utf-8-sig')
    print("✅ filtered_stocks.csv 저장 완료")

if __name__ == "__main__":
    main()
