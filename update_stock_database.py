# update_stock_database.py
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from modules.calculate_indicators import calculate_indicators
from modules.score_utils import calculate_score

# --- KRX 리스트 불러오기 ---
def get_krx_list():
    return pd.read_csv('initial_krx_list.csv', dtype=str)[['종목코드', '종목명', '시장구분']]

# --- 2차: Naver 주가 크롤링 fallback ---
def fetch_naver_stock_data(ticker):
    url = f"https://finance.naver.com/item/sise_day.nhn?code={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    dfs = []
    for page in range(1, 6):
        try:
            res = requests.get(url + f"&page={page}", headers=headers)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', class_='type2')
            df = pd.read_html(str(table))[0]
            dfs.append(df)
            time.sleep(0.5)
        except Exception as e:
            print(f"네이버 주가 크롤링 오류 (p{page}): {e}")
            continue
    try:
        df_all = pd.concat(dfs).dropna()
        df_all.columns = ['날짜', '종가', '전일비', '시가', '고가', '저가', '거래량']
        df_all['날짜'] = pd.to_datetime(df_all['날짜'])
        df_all = df_all.sort_values('날짜').reset_index(drop=True)
        df_all.rename(columns={'종가': 'Close', '거래량': 'Volume'}, inplace=True)
        return df_all
    except Exception as e:
        print(f"네이버 주가 데이터 처리 실패: {e}")
        return pd.DataFrame()

# --- 메인 ---
def main():
    krx_list = get_krx_list()
    records = []

    for idx, row in krx_list.iterrows():
        code, name, market = row['종목코드'], row['종목명'], row['시장구분']
        ticker = f"{code}.KS" if market == 'KOSPI' else f"{code}.KQ"
        df = pd.DataFrame()

        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="6mo")
            df.reset_index(inplace=True)
            if df.empty or len(df) < 10:
                df = fetch_naver_stock_data(code)
            if df.empty or len(df) < 10:
                print(f"⚠️ 데이터 부족: {code} {name}")
                continue

            df = calculate_indicators(df)
            current_price = df['Close'].iloc[-1]
            volume = df['Volume'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            macd = df['MACD'].iloc[-1]
            signal = df['Signal'].iloc[-1]
            ret_3m = (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100

            # 실제 재무 데이터가 없을 경우 기본값 대입
            per, pbr, roe, dividend = 10.0, 1.2, 8.0, 2.5

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
                'RSI': round(rsi, 2),
                'MACD': round(macd, 2),
                'Signal': round(signal, 2)
            })

            print(f"✓ 수집 완료: {code} {name}")
            time.sleep(0.2)

        except Exception as e:
            print(f"❌ 오류: {code} {name} - {e}")
            continue

    df = pd.DataFrame(records)
    if df.empty:
        print("❗ 데이터프레임이 비어있습니다.")
        return

    df = calculate_score(df)

    try:
        df.to_csv('filtered_stocks.csv', index=False, encoding='utf-8-sig')
        print("✅ filtered_stocks.csv 저장 완료")
    except Exception as e:
        print(f"❌ CSV 저장 실패: {e}")

if __name__ == "__main__":
    main()
