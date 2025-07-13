<<<<<<< HEAD
import requests
from bs4 import BeautifulSoup

def get_naver_financials(code):
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="per_table")
        per, pbr, roe, dividend = None, None, None, None
        if table:
            rows = table.find_all("tr")
            for row in rows:
                ths = row.find_all("th")
                for th in ths:
                    txt = th.text.strip()
                    td = th.find_next_sibling("td")
                    if not td:
                        continue
                    val = td.text.strip().replace(",", "").replace("%", "")
                    if "PER" in txt and "배" not in txt:
                        per = val if val and val != '-' else None
                    elif "PBR" in txt:
                        pbr = val if val and val != '-' else None
                    elif "ROE" in txt:
                        roe = val if val and val != '-' else None
                    elif "배당" in txt:
                        dividend = val if val and val != '-' else None
        print(f"[FIN 성공] {code}: PER={per}, PBR={pbr}, ROE={roe}, 배당률={dividend}")
        return per, pbr, roe, dividend
    except Exception as e:
        print(f"[FIN 실패] {code}: {e}")
        return None, None, None, None
=======
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

def fetch_from_naver(code):
    headers = {"User-Agent": "Mozilla/5.0"}
    dfs = []

    try:
        for page in range(1, 6):
            url = f"https://finance.naver.com/item/sise_day.nhn?code={code}&page={page}"
            res = requests.get(url, headers=headers)
            table = BeautifulSoup(res.text, "html.parser").find("table", class_="type2")
            df = pd.read_html(str(table))[0]
            dfs.append(df)
            time.sleep(0.2)

        df_all = pd.concat(dfs).dropna()
        df_all.columns = ['Date', 'Close', 'Diff', 'Open', 'High', 'Low', 'Volume']
        df_all["Date"] = pd.to_datetime(df_all["Date"])
        df_all = df_all.sort_values("Date").reset_index(drop=True)
        return df_all

    except:
        return pd.DataFrame()
>>>>>>> 4a27f38146733656025b2d13e5b4cc219821c6cb
