import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from scipy.stats import zscore
from modules import calculate_indicators
from news import fetch_news_keywords
import warnings
warnings.filterwarnings("ignore")

# --- 종목 리스트 로드 ---
def get_krx_list():
    df = pd.read_csv("initial_krx_list.csv", dtype=str)
    return df[['종목코드', '종목명', '시장구분']]

# --- yfinance용 코드 변환 ---
def get_yf_ticker(code, market):
    if market == '코스피':
        return f"{code}.KS"
    elif market == '코스닥':
        return f"{code}.KQ"
    else:
        return code  # fallback

# --- 네이버 주가 크롤링 ---
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
        time.sleep(0.3)
    df_all = pd.concat(dfs)
    df_all = df_all.dropna()
    df_all.columns = ['날짜', '종가', '전일비', '시가', '고가', '저가', '거래량']
    df_all['날짜'] = pd.to_datetime(df_all['날짜'])
    df_all = df_all.sort_values('날짜')
    df_all.reset_index(drop=True, inplace=True)
    df_all['Close'] = df_all['종가'].astype(str).str.replace(",", "").astype(float)
    df_all['Volume'] = df_all['거래량'].astype(str).str.replace(",", "").astype(float)
    return df_all

# --- 투자 점수 계산 ---
def calc_score(fin_df):
    fin_df['PER_z'] = zscore(fin_df['PER'].astype(float))
    fin_df['PBR_z'] = zscore(fin_df['PBR'].astype(float))
    fin_df['score'] = (-fin_df['PER_z'] - fin_df['PBR_z']) + (fin_df['3개월수익률'] / 10)
    return fin_df

# --- 메인 함수 ---
def main():
    krx_list = get_krx_list()
    records = []

    for idx, row in krx_list.iterrows():
        code = row['종목코드']
        name = row['종목명']
        market = row['시장구분']
        yf_code = get_yf_ticker(code, market)

        try:
            stock = yf.Ticker(yf_code)
            hist = stock.history(period="6mo")
            if hist.empty or len(hist) < 30:
                hist = fetch_naver_stock_data(code)
                if hist.empty or len(hist) < 30:
                    print(f"❌ 데이터 부족: {code} {name}")
                    continue
            hist.reset_index(inplace=True)
            df_ind = calculate_indicators(hist)

            # 지표 및 기본 재무 데이터 예시
            per = round(5 + 20 * abs(zscore(df_ind['Close']))[-1], 2)
            pbr = round(0.8 + 1.5 * abs(zscore(df_ind['Close']))[-1], 2)
            dividend = round(2 + (df_ind['RSI'].iloc[-1] % 3), 2)
            volume = hist['Volume'].iloc[-1]
            return_3mo = (df_ind['Close'].iloc[-1] / df_ind['Close'].iloc[0] - 1) * 100

            # 뉴스 키워드
            keywords = fetch_news_keywords(name)
            keyword_str = ", ".join(keywords[:3]) if keywords else ""

            records.append({
                '종목코드': code,
                '종목명': name,
                '시장구분': market,
                'PER': per,
                'PBR': pbr,
                '배당률': dividend,
                '거래량': volume,
                '3개월수익률': round(return_3mo, 2),
                '뉴스키워드': keyword_str
            })

            print(f"✅ 완료: {code} {name}")
            time.sleep(0.2)

        except Exception as e:
            print(f"⚠️ 오류 발생: {code} {name} | {e}")
            continue

    df = pd.DataFrame(records)
    df = calc_score(df)
    df.to_csv("filtered_stocks.csv", index=False, encoding='utf-8-sig')
    print("✅ filtered_stocks.csv 저장 완료")

if __name__ == "__main__":
    main()
