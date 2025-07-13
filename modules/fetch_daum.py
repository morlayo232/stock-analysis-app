import pandas as pd
import requests

def fetch_from_daum(code):
    # 주가(기존 그대로, 필요시 유지)
    try:
        url = f"https://finance.daum.net/api/quotes/{code}/days?perPage=100&page=1"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "referer": f"https://finance.daum.net/quotes/{code}"
        }
        res = requests.get(url, headers=headers)
        json_data = res.json()["data"]

        df = pd.DataFrame(json_data)
        df.rename(columns={
            "tradeDate": "Date",
            "tradePrice": "Close",
            "openPrice": "Open",
            "highPrice": "High",
            "lowPrice": "Low",
            "candleAccTradeVolume": "Volume"
        }, inplace=True)

        df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d")
        df = df.sort_values("Date").reset_index(drop=True)
        return df[["Date", "Close", "Open", "High", "Low", "Volume"]]
    except Exception as e:
        print(f"다음 크롤링 오류: {e}")
        return pd.DataFrame()

def get_daum_financials(code):
    try:
        url = f"https://finance.daum.net/api/financials/{code}?periodType=annual"
        headers = {"User-Agent": "Mozilla/5.0", "referer": f"https://finance.daum.net/quotes/{code}"}
        res = requests.get(url, headers=headers)
        data = res.json()

        # 실제 데이터 키/구조에 따라 보정 필요 (아래는 예시, 실데이터 구조 확인 필수)
        # 만약 API 응답에서 per, pbr, roe, dividend 키가 없으면 None 반환
        per = data.get("per", None)
        pbr = data.get("pbr", None)
        roe = data.get("roe", None)
        dividend = data.get("dividend", None)
        print(f"[DAUM FIN] {code}: PER={per}, PBR={pbr}, ROE={roe}, 배당률={dividend}")
        return per, pbr, roe, dividend
    except Exception as e:
        print(f"[DAUM FIN 실패] {code}: {e}")
        return None, None, None, None
