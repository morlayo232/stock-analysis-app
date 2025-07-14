import requests
from bs4 import BeautifulSoup

def get_naver_financials(code):
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        per, pbr, roe, dividend = None, None, None, None

        # <th> 텍스트 기반 모든 표에서 탐색
        for th in soup.find_all("th"):
            txt = th.get_text(strip=True)
            td = th.find_next_sibling("td")
            if not td: continue
            value = td.get_text(strip=True).replace(",", "").replace("%", "").replace("배", "")
            if "PER" in txt and "추정" not in txt:
                per = value if value not in ["", "-", "N/A"] else per
            elif "PBR" in txt:
                pbr = value if value not in ["", "-", "N/A"] else pbr
            elif "ROE" in txt:
                roe = value if value not in ["", "-", "N/A"] else roe
            elif "배당" in txt:
                dividend = value if value not in ["", "-", "N/A"] else dividend

        # 그래도 없는 경우 모든 <td>에서 키워드 직접 검색
        if not all([per, pbr, roe, dividend]):
            for td in soup.find_all("td"):
                txt = td.get_text(strip=True)
                if ("PER" in txt and not per) and "추정" not in txt:
                    per = txt.split("PER")[-1].replace("배", "").strip()
                if ("PBR" in txt and not pbr):
                    pbr = txt.split("PBR")[-1].replace("배", "").strip()
                if ("ROE" in txt and not roe):
                    roe = txt.split("ROE")[-1].replace("%", "").strip()
                if ("배당" in txt and not dividend):
                    dividend = txt.split("배당")[-1].replace("%", "").strip()
        print(f"[NAVER FIN] {code}: PER={per}, PBR={pbr}, ROE={roe}, 배당률={dividend}")
        return per, pbr, roe, dividend
    except Exception as e:
        print(f"[NAVER FIN 실패] {code}: {e}")
        return None, None, None, None
