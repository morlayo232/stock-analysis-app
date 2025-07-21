# modules/evaluate_stock.py

import numpy as np

def evaluate_stock(scored_df, selected, df_price):
    eval_lines = []

    try:
        per = scored_df.loc[scored_df["종목명"] == selected, "PER"].values[0]
        pbr = scored_df.loc[scored_df["종목명"] == selected, "PBR"].values[0]
        div = scored_df.loc[scored_df["종목명"] == selected, "배당률"].values[0]
        eps = scored_df.loc[scored_df["종목명"] == selected, "EPS"].values[0]
        bps = scored_df.loc[scored_df["종목명"] == selected, "BPS"].values[0]
        score = scored_df.loc[scored_df["종목명"] == selected, "score"].values[0]
        q80 = scored_df["score"].quantile(0.8)
        q20 = scored_df["score"].quantile(0.2)

        # PER 평가
        if per < 7:
            eval_lines.append("✔️ [PER] 현재 PER이 7 미만입니다. 기업 이익 대비 주가가 낮아 저평가 가능성이 큽니다. 단, 업종별 평균과 비교 필수.")
        elif per > 20:
            eval_lines.append("⚠️ [PER] 현재 PER이 20 이상입니다. 성장 기대감 반영이나 단기 과대평가 구간일 수 있어 신중히 판단하세요.")

        # PBR 평가
        if pbr < 1:
            eval_lines.append("✔️ [PBR] PBR이 1 미만으로 순자산 대비 저평가. 다만 자산 구성과 부채비율도 검토 권장.")
        elif pbr > 2:
            eval_lines.append("⚠️ [PBR] PBR이 2 이상일 경우 자산 대비 고평가 가능성 있으니 투자 주의.")

        # 배당률 평가
        if div > 3:
            eval_lines.append("💰 [배당] 배당률 3% 이상으로 안정적 현금흐름 기대 가능, 배당 투자자에 적합.")
        elif div < 1:
            eval_lines.append("💡 [배당] 배당률이 낮아 성장주 가능성 있으나, 배당수익 기대는 낮음.")

        # EPS 평가
        if eps > 0:
            eval_lines.append("🟢 [EPS] 최근 분기 흑자로 수익성 안정 확인.")
        else:
            eval_lines.append("🔴 [EPS] 적자 상태로 재무 악화 우려, 원인 분석 필요.")

        # BPS 평가
        if bps > 0:
            eval_lines.append("🟢 [BPS] 순자산 가치 양호, 투자 안정성 지지.")
        else:
            eval_lines.append("🔴 [BPS] 낮거나 마이너스인 경우 재무 건전성 재확인 필요.")

        # RSI 평가
        if "RSI_14" in df_price.columns and not np.isnan(df_price['RSI_14'].iloc[-1]):
            rsi_now = df_price['RSI_14'].iloc[-1]
            if rsi_now < 30:
                eval_lines.append("📉 [RSI] RSI 30 이하 과매도 상태. 단기 반등 가능성 있으나 펀더멘털도 함께 검토해야 합니다.")
            elif rsi_now > 70:
                eval_lines.append("📈 [RSI] RSI 70 이상 과매수 상태. 조정 가능성 있으니 매수 시기 신중히 판단.")

        # 종합 점수 평가
        if score > q80:
            eval_lines.append("✅ [종합 점수] 투자 매력도가 매우 높아 분할 매수 권장.")
        elif score < q20:
            eval_lines.append("❌ [종합 점수] 투자 매력도가 낮으니 보류 또는 관망 필요.")
        else:
            eval_lines.append("☑️ [종합 점수] 평균 수준. 가격 조정 시 분할 매수 고려.")

    except Exception as e:
        eval_lines.append("평가 중 오류 발생, 데이터 점검 필요.")

    return eval_lines
