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
        if per is not None and not np.isnan(per):
            if per < 7:
                eval_lines.append("✔️ [PER] PER이 7 미만: 이익 대비 주가가 낮아 저평가 가능성이 있습니다. 단, 업종별 평균 PER과 비교해보세요.")
            elif per > 20:
                eval_lines.append("⚠️ [PER] PER이 20 초과: 미래 성장 기대 반영이나 과대평가일 수 있어 신중한 접근 필요합니다.")

        # PBR 평가 및 보완 설명
        if pbr is not None and not np.isnan(pbr):
            if pbr < 1:
                eval_lines.append("✔️ [PBR] PBR 1 미만: 자산가치보다 주가가 낮아 안전마진이 큽니다. 하지만 재무구조 악화, 자산 감가상각 등 이슈도 확인하세요.")
                eval_lines.append("   예) 부채비율, 자산유동성, 자산 평가 방법 변동 여부 점검 권장")
            elif pbr > 2:
                eval_lines.append("⚠️ [PBR] PBR 2 초과: 고평가 우려 있습니다. 성장 동력, 이익 지속 가능성, 업계 비교 분석 필요합니다.")

        # 배당률 평가
        if div is not None and not np.isnan(div):
            if div > 3:
                eval_lines.append("💰 [배당] 배당률 3% 이상: 안정적 현금흐름과 장기투자에 적합합니다.")
            elif div < 1:
                eval_lines.append("💡 [배당] 배당률 1% 미만: 성장주일 가능성 크므로 주가 상승 잠재력 중심 분석이 필요합니다.")

        # EPS 평가
        if eps is not None and not np.isnan(eps):
            if eps > 0:
                eval_lines.append("🟢 [EPS] 최근 분기 흑자: 기업 수익성 안정적임을 의미합니다.")
            else:
                eval_lines.append("🔴 [EPS] 최근 분기 적자: 재무 악화 원인 분석과 지속 가능성 점검이 필수입니다.")

        # BPS 평가
        if bps is not None and not np.isnan(bps):
            if bps > 0:
                eval_lines.append("🟢 [BPS] 자산가치 양호: 투자 안정성을 뒷받침합니다.")
            else:
                eval_lines.append("🔴 [BPS] 자산가치 낮음: 감가상각, 부채 과다 가능성 검토 필요합니다.")

        # RSI 평가
        if "RSI_14" in df_price.columns and not np.isnan(df_price['RSI_14'].iloc[-1]):
            rsi_now = df_price['RSI_14'].iloc[-1]
            if rsi_now < 30:
                eval_lines.append("📉 [RSI] RSI 30 이하 과매도: 기술적 반등 가능, 펀더멘털과 병행 판단 권장")
            elif rsi_now > 70:
                eval_lines.append("📈 [RSI] RSI 70 이상 과매수: 단기 조정 가능성, 매수 타이밍 신중히")

        # 종합 점수 평가 및 유형별 추가 설명
        if score > q80:
            eval_lines.append("✅ [종합 진단] 투자 매력도 매우 높음: 분할 매수 및 적극 매수 고려")
        elif score < q20:
            eval_lines.append("❌ [종합 진단] 투자 매력도 낮음: 보수적 접근 및 타 종목 검토 권장")
        else:
            eval_lines.append("☑️ [종합 진단] 평균 수준: 가격 조정 시 분할 매수 등 장기 전략 추천")

        # 추가 유형 예시 (100개 내외는 별도 문서로 별도 제공 권장)
        # 예: 급등 가능성, 위험 신호, 업종 성장성, 시장 변동성 반영 등
        # 이후 단계에서 확장 가능

        return eval_lines

    except Exception:
        return ["종목 평가 및 투자 전략 정보를 불러올 수 없습니다."]
