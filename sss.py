# 예를 들어, get_naver_financials 함수가 PER, PBR, ROE, 배당률을 받아온다고 가정
from modules.fetch_naver import get_naver_financials

stock_codes = ["005930", "035720", "000660"]  # 삼성전자, 카카오, SK하이닉스 예시

for code in stock_codes:
    per, pbr, roe, dividend = get_naver_financials("005930")
    print(f"종목코드: {code} | PER: {per} | PBR: {pbr} | ROE: {roe} | 배당률: {dividend}")
