# ✅ /modules/score_utils.py
import numpy as np

# 투자 점수 계산 함수
# 스타일별 가중치를 다르게 적용하며, 스코어 누락 방지 및 안정성 보강

def calculate_final_score(row, style):
    try:
        per = float(row['PER'])
        pbr = float(row['PBR'])
        roe = float(row['ROE'])
        dividend = float(row['배당률'])
        rsi = float(row['RSI'])
        macd = float(row['MACD'])
        signal = float(row['Signal'])
        volume = float(row['거래량'])
        price = float(row['현재가'])
        return_3m = float(row['3개월수익률'])
    except:
        return np.nan

    # 기본 정량 점수 (재무 지표 기반)
    base_score = 0
    if per > 0: base_score += max(0, 20 - per) * 0.5
    if pbr > 0: base_score += max(0, 5 - pbr) * 1.0
    base_score += roe * 0.8
    base_score += dividend * 0.5

    # 기술적 점수
    tech_score = 0
    if rsi < 30: tech_score += 10
    if macd > signal: tech_score += 10
    if volume > 0 and price > 0:  # 거래대금
        trade_amount = volume * price
        if trade_amount > 1e9: tech_score += 5

    # 수익률
    momentum_score = return_3m * 0.3 if return_3m > 0 else 0

    # 스타일별 가중치
    if style == '공격적':
        total = base_score * 0.4 + tech_score * 0.4 + momentum_score * 0.2
    elif style == '안정적':
        total = base_score * 0.6 + tech_score * 0.2 + momentum_score * 0.2
    elif style == '배당형':
        total = base_score * 0.5 + dividend * 1.5 + tech_score * 0.2
    else:
        total = base_score + tech_score + momentum_score

    return round(total, 2)
