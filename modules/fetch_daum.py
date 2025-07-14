import requests
from bs4 import BeautifulSoup

def get_daum_financials(code):
    # 1. API JSON 시도 (키 다양화)
    try:
        url = f"https://finance.daum.net/api/financials/{code}?periodType=annual"
        headers = {"User-Agent": "Mozilla/5.0", "referer": f"https://finance.daum.net/quotes/{code}"}
        res = requests.get(url, headers=headers)
        data = res.json()
        per = data.get("per") or data.get("PER")
        pbr = data.get("pbr") or data.get("PBR")
        roe = data.get("roe") or data.get("ROE")
        dividend = data.get("dividend") or data.get("DividendYield") or data.get("dividendYield")
        if any([per, pbr, roe, dividend]):
            print(f"[DAUM FIN API] {code}: PER={per}, PBR={pbr}, ROE={roe}, 배당률={dividend}")
            return per, pbr, roe, dividend
    except Exception as e:
        print(f"[DAUM FIN API 실패] {code}: {e}")

    # 2. HTML 백업 파싱
    try:
        url = f"https://finance.daum.net/quotes/{code}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        per, pbr, roe, dividend = None, None, None, None
        for span in soup.find_all("span"):
            txt = span.get_text(strip=True)
            if "PER" in txt and not per:
                per = txt.split("PER")[-1].replace("배", "").strip()
            if "PBR" in txt and not pbr:
                pbr = txt.split("PBR")[-1].replace("배", "").strip()
            if "ROE" in txt and not roe:
                roe = txt.split("ROE")[-1].replace("%", "").strip()
            if "배당" in txt and not dividend:
                dividend = txt.split("배당")[-1].replace("%", "").strip()
        print(f"[DAUM FIN HTML] {code}: PER={per}, PBR={pbr}, ROE={roe}, 배당률={dividend}")
        return per, pbr, roe, dividend
    except Exception as e:
        print(f"[DAUM FIN HTML 실패] {code}: {e}")
        return None, None, None, None
