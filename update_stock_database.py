import pandas as pd from pykrx import stock from datetime import datetime from modules.score_utils import finalize_scores

def fetch_price(code): today = datetime.today().strftime("%Y%m%d") try: df = stock.get_market_ohlcv_by_date(today, today, code) if not df.empty: return int(df['종가'][-1]) except: return None

def fetch_fundamental(code): today = datetime.today().strftime("%Y%m%d") try: df = stock.get_market_fundamental_by_date(today, today, code) if not df.empty: return { 'PER': float(df['PER'][-1]), 'PBR': float(df['PBR'][-1]), 'ROE': float('nan'), # 복정: fetch_naver 또는 daum에서 복치 '배당수익률': float(df['DIV'][-1]) } except: return {'PER': None, 'PBR': None, 'ROE': None, '배당수익률': None}

def update_database(): df_list = pd.read_csv("initial_krx_list.csv") codes = dict(zip(df_list['종목명'], df_list['종목코드'])) data = [] for name, code in codes.items(): price = fetch_price(code) fin = fetch_fundamental(code) data.append({ "종목명": name, "종목코드": code, "현재가": price, "PER": fin['PER'], "PBR": fin['PBR'], "ROE": fin['ROE'], "배당수익률": fin['배당수익률'] })

df = pd.DataFrame(data) df = finalize_scores(df, style="aggressive") df.to_csv("filtered_stocks.csv", index=False) print("filtered_stocks.csv 저장 완료!") 

if name == "main": update_database()

