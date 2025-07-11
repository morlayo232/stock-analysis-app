import pandas as pd

# ✅ filtered_stocks.csv 로드
def load_filtered_data():
    return pd.read_csv("filtered_stocks.csv")

# ✅ 한국 주식 종목코드를 yfinance 형식으로 변환
def get_yf_ticker(code, market):
    """
    code: 종목코드 (예: "005930")
    market: "코스피" 또는 "코스닥"
    return: "005930.KS" or "035420.KQ"
    """
    if market == "코스피":
        return f"{code}.KS"
    elif market == "코스닥":
        return f"{code}.KQ"
    return code

# ✅ 투자 매력 점수 계산 함수
def calculate_investment_score(row):
    score = 0
    try:
        score += (max(0, 100 - float(row["PER"]) * 4)) * 0.2     # 낮을수록 유리
        score += (max(0, 100 - float(row["PBR"]) * 20)) * 0.2
        score += float(row.get("ROE", 0)) * 0.3
        score += float(row.get("배당률", 0)) * 1.5
        score += float(row.get("기술점수", 0)) * 0.2
        score += float(row.get("세력점수", 0)) * 0.1
    except:
        pass
    return round(score, 2)

# ✅ 투자 판단 요약 생성
def get_advice(info, score):
    advice = []

    try:
        if float(info.get('RSI', 0)) > 70:
            advice.append("⚠️ RSI 과매수 → 단기 조정 주의")
        if float(info.get('MACD', 0)) > float(info.get('Signal', 0)):
            advice.append("📈 MACD 상승 전환")
        if float(info.get('세력점수', 0)) > 70:
            advice.append("🧲 세력 매집 흔적 강함")
        if score > 80:
            advice.append("✅ 중장기 투자 매력 우수")
        elif score > 60:
            advice.append("📊 단기 접근 가능")
        else:
            advice.append("🔎 보류 또는 추가 분석 권장")
    except:
        advice.append("지표 부족으로 분석 제한")

    return " / ".join(advice)
