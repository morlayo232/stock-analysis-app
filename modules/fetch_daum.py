import pandas as pd
import requests

def get_daum_price(code):
    url = f"https://finance.daum.net/quotes/A{code}#chart"
    headers = {"User-Agent": "Mozilla/5.0", "referer": url}
    dfs = []
    for page in range(1, 5):
        api_url = f"https://finance.daum.net/api/quotes/A{code}/days?symbolCode=A{code}&page={page}&perPage=20&fieldName=closePrice&order=desc"
        res = requests.get(api_url, headers=headers)
        if res.status_code != 200:
            continue
        try:
            data = res.json().get("data", [])
        except Exception:
            continue
        if not data:
            continue
        df = pd.DataFrame(data)
        if not df.empty and {"date", "closePrice", "openPrice", "highPrice", "lowPrice", "tradeVolume"} <= set(df.columns):
            df = df.rename(columns={
                "date": "Date", "closePrice": "Close", "openPrice": "Open",
                "highPrice": "High", "lowPrice": "Low", "tradeVolume": "Volume"
            })
            dfs.append(df[["Date", "Close", "Open", "High", "Low", "Volume"]])
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for col in ["Close", "Open", "High", "Low", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.sort_values("Date").reset_index(drop=True)
    df = df.dropna()
    return df

def get_daum_financials(code):
    try:
        url = f"https://finance.daum.net/quotes/A{code}"
        headers = {"User-Agent": "Mozilla/5.0", "referer": url}
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            return None, None, None, None
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res.text, "html.parser")
        per, pbr, roe, dividend = None, None, None, None

        for item in soup.select(".list_info li"):
            label = item.select_one(".label")
            value = item.select_one(".emph")
            if not label or not value:
                continue
            txt = label.text.strip()
            val = value.text.strip().replace(",", "").replace("%", "").replace("배", "")
            if "PER" in txt and not per:
                per = val
            elif "PBR" in txt and not pbr:
                pbr = val
            elif "ROE" in txt and not roe:
                roe = val
            elif "배당수익률" in txt and not dividend:
                dividend = val
        return per, pbr, roe, dividend
    except Exception as e:
        print(f"[DAUM FIN 실패] {code}: {e}")
        return None, None, None, None
