import numpy as np
import streamlit as st

def evaluate_stock_extended_1(scored_df, selected, df_price):
    eval_lines = []

    # 1. PER 평가
    per = scored_df.loc[scored_df["종목명"] == selected, "PER"].values[0]
    if per is not None and not np.isnan(per):
        if per < 7:
            eval_lines.append(
                "✔️ [PER] 현재 PER이 7 미만으로 이익 대비 주가가 낮아 저평가 가능성이 있습니다. "
                "단, 업종 평균과 비교 후 판단하세요."
            )
        elif per > 20:
            eval_lines.append(
                "⚠️ [PER] PER이 20 이상으로 성장 기대 반영이나 단기 과대평가 가능성 있어 신중히 접근하세요."
            )

    # 2. PBR 평가
    pbr = scored_df.loc[scored_df["종목명"] == selected, "PBR"].values[0]
    if pbr is not None and not np.isnan(pbr):
        if pbr < 1:
            eval_lines.append(
                "✔️ [PBR] PBR 1 미만으로 순자산 대비 주가가 낮아 안전마진이 큽니다. "
                "회계기준과 일시적 요인도 고려하세요."
            )
        elif pbr > 2:
            eval_lines.append(
                "⚠️ [PBR] PBR 2 초과 시 자산 대비 고평가 가능성으로 투자 신중 필요."
            )

    # 3. 배당률 평가
    div = scored_df.loc[scored_df["종목명"] == selected, "배당률"].values[0]
    if div is not None and not np.isnan(div):
        if div >= 3:
            eval_lines.append(
                "💰 [배당] 배당률 3% 이상으로 안정적 현금흐름 기대, 배당 투자자에 적합."
            )
        elif div < 1:
            eval_lines.append(
                "💡 [배당] 배당률 낮아 성장 중심 투자자에게 유리하며, 주가 상승 가능성 주목."
            )

    # 4. EPS 상태 평가
    eps = scored_df.loc[scored_df["종목명"] == selected, "EPS"].values[0]
    if eps is not None and not np.isnan(eps):
        if eps > 0:
            eval_lines.append(
                "🟢 [EPS] 최근 분기 순이익 흑자로 수익성 안정적입니다."
            )
        else:
            eval_lines.append(
                "🔴 [EPS] 적자 상태로 재무 악화 가능성, 원인 분석 필요."
            )

    # 5. BPS 상태 평가
    bps = scored_df.loc[scored_df["종목명"] == selected, "BPS"].values[0]
    if bps is not None and not np.isnan(bps):
        if bps > 0:
            eval_lines.append(
                "🟢 [BPS] 자산가치가 긍정적이며 투자 안정성에 기여합니다."
            )
        else:
            eval_lines.append(
                "🔴 [BPS] 낮거나 불안정한 자산가치는 투자 시 주의가 필요합니다."
            )

    # 6. RSI 상태 평가
    if "RSI_14" in df_price.columns and not np.isnan(df_price['RSI_14'].iloc[-1]):
        rsi_now = df_price['RSI_14'].iloc[-1]
        if rsi_now < 30:
            eval_lines.append(
                "📉 [RSI] 30 이하 과매도 구간으로 기술적 반등 가능성 있으나 펀더멘털 확인 필요."
            )
        elif rsi_now > 70:
            eval_lines.append(
                "📈 [RSI] 70 이상 과매수 구간, 단기 조정 가능성 있으니 신중히 대응하세요."
            )

    # 7. MACD와 Signal선 위치 평가
    if 'MACD' in df_price.columns and 'MACD_SIGNAL' in df_price.columns:
        macd_latest = df_price['MACD'].iloc[-1]
        signal_latest = df_price['MACD_SIGNAL'].iloc[-1]
        if macd_latest < signal_latest:
            eval_lines.append(
                "📉 [MACD] MACD가 Signal선 아래로 단기 하락 신호입니다."
            )
        else:
            eval_lines.append(
                "📈 [MACD] MACD가 Signal선을 상향 돌파해 단기 상승 모멘텀입니다."
            )

    # 8. EMA-20 대비 종가 상태
    if "EMA_20" in df_price.columns and "종가" in df_price.columns:
        ema_20 = df_price["EMA_20"].iloc[-1]
        close = df_price["종가"].iloc[-1]
        if close > ema_20:
            eval_lines.append(
                "📈 [EMA-20] 주가가 EMA-20 위에 있어 단기 상승추세입니다."
            )
        else:
            eval_lines.append(
                "📉 [EMA-20] 주가가 EMA-20 아래로 단기 조정 중일 수 있습니다."
            )

    # 9. 거래대금 및 유동성 평가
    trading_value = scored_df.loc[scored_df["종목명"] == selected, "거래대금"].values[0]
    if trading_value is not None and not np.isnan(trading_value):
        if trading_value < 1e7:
            eval_lines.append(
                "⚠️ [유동성] 거래대금이 낮아 매매 어려움과 변동성 확대 가능성이 있습니다."
            )

    # 10. 거래량 변화 관찰
    if '거래량' in df_price.columns:
        recent_volume = df_price['거래량'].iloc[-1]
        avg_volume = df_price['거래량'].rolling(window=20).mean().iloc[-1]
        if recent_volume > avg_volume * 1.5:
            eval_lines.append(
                "📊 [거래량] 거래량 급증으로 변동성 확대 가능성 있어 주의하세요."
            )
        elif recent_volume < avg_volume * 0.5:
            eval_lines.append(
                "📉 [거래량] 거래량 감소로 투자자 관심 저하 우려가 있습니다."
            )

    # 11. 복합 투자 매력도 평가
    score = scored_df.loc[scored_df["종목명"] == selected, "score"].values[0]
    q80 = scored_df["score"].quantile(0.8)
    q20 = scored_df["score"].quantile(0.2)
    if score > q80:
        eval_lines.append(
            "✅ [종합 진단] 투자 매력도가 매우 높아 분할 매수 및 장기투자 추천 종목입니다."
        )
    elif score < q20:
        eval_lines.append(
            "❌ [종합 진단] 투자 매력도가 낮아 위험 부담이 크므로 신중히 접근하세요."
        )
    else:
        eval_lines.append(
            "☑️ [종합 진단] 평균 수준 투자 매력도로 조정 시 매수 기회입니다."
        )

    # 12. 시장 및 업종 상황 고려
    eval_lines.append(
        "ℹ️ [시장상황] 시장 및 업종 동향을 고려해 투자 시기를 신중히 판단하세요."
    )

    # 13. PER, EPS, 배당 조합 심화 평가
    if per is not None and eps is not None and div is not None:
        if per < 10 and eps > 0 and div >= 2:
            eval_lines.append("📌 [강력 추천] 저PER·흑자·고배당 조합으로 안정적 수익 기대 가능.")
        elif per > 25 and eps < 0:
            eval_lines.append("📌 [위험 신호] 고PER·적자 조합으로 투자 신중 권장.")

    # 14. 거래량 및 주가 상승률 복합 분석
    if '거래량' in df_price.columns and "종가" in df_price.columns:
        recent_volume = df_price['거래량'].iloc[-1]
        avg_volume = df_price['거래량'].rolling(window=20).mean().iloc[-1]
        price_now = df_price['종가'].iloc[-1]
        price_prev = df_price['종가'].iloc[-2]
        if recent_volume > avg_volume * 1.5 and price_now > price_prev:
            eval_lines.append("📌 [모멘텀] 거래량 증가와 주가 상승 동반, 긍정 신호입니다.")
        elif recent_volume > avg_volume * 1.5 and price_now <= price_prev:
            eval_lines.append("📌 [주의] 거래량 급증에도 주가 하락, 변동성 위험 존재.")

    # 15. RSI + MACD 히스토그램 단기 모멘텀 판단
    if "RSI_14" in df_price.columns and 'MACD_HIST' in df_price.columns:
        rsi = df_price['RSI_14'].iloc[-1]
        macd_hist = df_price['MACD_HIST'].iloc[-1]
        if rsi < 30 and macd_hist > 0:
            eval_lines.append("📌 [반등 가능성] RSI 과매도 + MACD 양호, 반등 기대.")
        elif rsi > 70 and macd_hist < 0:
            eval_lines.append("📌 [조정 가능성] RSI 과매수 + MACD 하락, 단기 조정 유의.")

    # 16. 고배당 + 안정적 재무구조 투자 조언
    debt_ratio = scored_df.loc[scored_df["종목명"] == selected, "부채비율"].values[0] if "부채비율" in scored_df.columns else None
    if div is not None and div >= 4 and debt_ratio is not None and debt_ratio < 40:
        eval_lines.append("📌 [고배당 안정] 배당률 높고 부채비율 낮아 안정적 배당 성장주입니다.")

    # 17. EMA-20 하락 + 거래량 감소 단기 조정 경계
    if "EMA_20" in df_price.columns and '거래량' in df_price.columns:
        ema20 = df_price["EMA_20"].iloc[-1]
        close = df_price["종가"].iloc[-1]
        avg_vol = df_price['거래량'].rolling(window=20).mean().iloc[-1]
        recent_vol = df_price['거래량'].iloc[-1]
        if close < ema20 and recent_vol < avg_vol * 0.5:
            eval_lines.append("📌 [조정 신호] 주가 EMA-20 아래 및 거래량 감소, 추가 하락 가능성 주의.")

    return eval_lines

def evaluate_stock(scored_df, selected, df_price):
    return evaluate_stock_extended_1(scored_df, selected, df_price)
