import requests

def get_daum_financials(code):
    try:
        url = f"https://finance.daum.net/api/financials/{code}?periodType=annual"
        headers = {"User-Agent": "Mozilla/5.0", "referer": f"https://finance.daum.net/quotes/{code}"}
        res = requests.get(url, headers=headers)
        data = res.json()
        # 실 응답구조 확인 필요, 없는 경우 None 처리
        per = data.get("per", None)
        pbr = data.get("pbr", None)
        roe = data.get("roe", None)
        dividend = data.get("dividend", None)
        print(f"[DAUM FIN] {code}: PER={per}, PBR={pbr}, ROE={roe}, 배당률={dividend}")
        return per, pbr, roe, dividend
    except Exception as e:
        print(f"[DAUM FIN 실패] {code}: {e}")
        return None, None, None, None
