def evaluate_stock_extended_1(scored_df, selected, df_price):
    eval_lines = []

    # 1. PER 저평가 가능성
    per = scored_df.loc[scored_df["종목명"] == selected, "PER"].values[0]
    if per is not None and not np.isnan(per):
        if per < 7:
            eval_lines.append(
                "✔️ [PER] 현재 PER이 7 미만으로 이익 대비 주가가 낮게 형성되어 저평가 가능성이 있습니다. "
                "단, 업종 평균 PER과 비교하여 판단하는 것이 중요합니다."
            )
        elif per > 20:
            eval_lines.append(
                "⚠️ [PER] 현재 PER이 20 이상으로 미래 성장 기대가 반영되어 있으나, 단기 과대평가일 수 있어 주의가 필요합니다."
            )

    # 2. PBR 평가 및 자산 가치 관련
    pbr = scored_df.loc[scored_df["종목명"] == selected, "PBR"].values[0]
    if pbr is not None and not np.isnan(pbr):
        if pbr < 1:
            eval_lines.append(
                "✔️ [PBR] PBR이 1 미만인 경우 순자산 가치 대비 주가가 낮아 안전마진이 큽니다. "
                "다만, 회계기준 차이나 일시적 요인도 고려해야 합니다."
            )
        elif pbr > 2:
            eval_lines.append(
                "⚠️ [PBR] PBR이 2를 초과하면 자산 대비 고평가 가능성이 있으니 투자 시 신중함이 요구됩니다."
            )

    # 3. 배당률과 투자 성향
    div = scored_df.loc[scored_df["종목명"] == selected, "배당률"].values[0]
    if div is not None and not np.isnan(div):
        if div >= 3:
            eval_lines.append(
                "💰 [배당] 배당률이 3% 이상으로 안정적인 현금흐름이 기대되며, 배당투자자에게 적합합니다."
            )
        elif div < 1:
            eval_lines.append(
                "💡 [배당] 배당률이 낮아 성장 중심 투자자에게 적합하며, 주가 상승 가능성을 주목하세요."
            )

    # 4. EPS (순이익) 상태
    eps = scored_df.loc[scored_df["종목명"] == selected, "EPS"].values[0]
    if eps is not None and not np.isnan(eps):
        if eps > 0:
            eval_lines.append(
                "🟢 [EPS] 최근 분기 순이익 흑자로 기업 수익성이 안정적임을 나타냅니다."
            )
        else:
            eval_lines.append(
                "🔴 [EPS] 최근 분기 적자로 재무 악화 가능성 및 원인 분석이 필요합니다."
            )

    # 5. BPS (자산가치) 상태
    bps = scored_df.loc[scored_df["종목명"] == selected, "BPS"].values[0]
    if bps is not None and not np.isnan(bps):
        if bps > 0:
            eval_lines.append(
                "🟢 [BPS] 긍정적인 자산가치는 기업의 투자 안정성에 기여합니다."
            )
        else:
            eval_lines.append(
                "🔴 [BPS] 낮거나 불안정한 자산가치는 투자 시 주의를 요합니다."
            )

    # 6. RSI 지표 상태
    if "RSI_14" in df_price.columns and not np.isnan(df_price['RSI_14'].iloc[-1]):
        rsi_now = df_price['RSI_14'].iloc[-1]
        if rsi_now < 30:
            eval_lines.append(
                "📉 [RSI] 30 이하로 단기 과매도 상태입니다. 기술적 반등 가능성은 있으나 펀더멘털과 함께 검토하세요."
            )
        elif rsi_now > 70:
            eval_lines.append(
                "📈 [RSI] 70 이상으로 단기 과매수 상태입니다. 단기 조정 가능성이 있으니 신중한 매매가 요구됩니다."
            )

    # 7. MACD와 Signal 선의 위치
    if 'MACD' in df_price.columns and 'MACD_SIGNAL' in df_price.columns:
        macd_latest = df_price['MACD'].iloc[-1]
        signal_latest = df_price['MACD_SIGNAL'].iloc[-1]
        if macd_latest < signal_latest:
            eval_lines.append(
                "📉 [MACD] MACD가 Signal선 아래 위치해 단기 하락 신호입니다."
            )
        else:
            eval_lines.append(
                "📈 [MACD] MACD가 Signal선을 상향 돌파해 단기 상승 모멘텀입니다."
            )

    # 8. 단기 추세: EMA-20 대비 종가
    if "EMA_20" in df_price.columns and "종가" in df_price.columns:
        ema_20 = df_price["EMA_20"].iloc[-1]
        close = df_price["종가"].iloc[-1]
        if close > ema_20:
            eval_lines.append(
                "📈 [EMA-20] 주가가 EMA-20 위에 있어 단기 상승추세임을 시사합니다."
            )
        else:
            eval_lines.append(
                "📉 [EMA-20] 주가가 EMA-20 아래에 있어 단기 조정 중일 수 있습니다."
            )

    # 9. 거래대금 및 유동성 평가
    trading_value = scored_df.loc[scored_df["종목명"] == selected, "거래대금"].values[0]
    if trading_value is not None and not np.isnan(trading_value):
        if trading_value < 1e7:
            eval_lines.append(
                "⚠️ [유동성] 거래대금이 낮아 매매가 어려울 수 있으며 변동성이 클 수 있습니다."
            )

    # 10. 거래량 변화 관찰
    if '거래량' in df_price.columns:
        recent_volume = df_price['거래량'].iloc[-1]
        avg_volume = df_price['거래량'].rolling(window=20).mean().iloc[-1]
        if recent_volume > avg_volume * 1.5:
            eval_lines.append(
                "📊 [거래량] 최근 거래량이 크게 증가해 변동성 확대로 주의가 필요합니다."
            )
        elif recent_volume < avg_volume * 0.5:
            eval_lines.append(
                "📉 [거래량] 거래량이 감소해 투자자 관심이 줄고 있을 수 있습니다."
            )

    # 11. 투자 매력도 점수 평가
    score = scored_df.loc[scored_df["종목명"] == selected, "score"].values[0]
    q80 = scored_df["score"].quantile(0.8)
    q20 = scored_df["score"].quantile(0.2)
    if score > q80:
        eval_lines.append(
            "✅ [종합 진단] 투자 매력도가 매우 높아 분할 매수 및 장기투자 추천 종목입니다."
        )
    elif score < q20:
        eval_lines.append(
            "❌ [종합 진단] 투자 매력도가 낮아 위험 부담이 크니 신중히 접근하세요."
        )
    else:
        eval_lines.append(
            "☑️ [종합 진단] 평균 수준 투자 매력도로 조정 시 매수 기회입니다."
        )

    # 12. 시장 및 업종 상황 고려
    eval_lines.append(
        "ℹ️ [시장상황] 현재 시장 및 업종 동향을 고려해 투자 시기를 신중히 판단하세요."
    )

    def evaluate_stock_extended_2(scored_df, selected, df_price):
    eval_lines = []

    # 13. 최근 주가 변동성 확인
    if "종가" in df_price.columns:
        recent_close = df_price['종가'].iloc[-1]
        past_close = df_price['종가'].iloc[-20]
        price_change_pct = (recent_close - past_close) / past_close * 100
        if price_change_pct > 20:
            eval_lines.append(
                "📈 [주가 변동성] 최근 20일간 주가가 20% 이상 상승했습니다. "
                "단기 과열 가능성 있으니 조정 리스크를 고려하세요."
            )
        elif price_change_pct < -15:
            eval_lines.append(
                "📉 [주가 변동성] 최근 20일간 주가가 15% 이상 하락했습니다. "
                "저가 매수 기회일 수 있으나 추가 하락 위험도 염두에 두어야 합니다."
            )

    # 14. EPS 성장성 추세
    eps = scored_df.loc[scored_df["종목명"] == selected, "EPS"].values[0]
    if eps is not None and not np.isnan(eps):
        # 예: EPS가 3개 분기 연속 상승 시 별도 데이터가 있다면 그 평가 가능
        eval_lines.append(
            "📊 [EPS 성장성] EPS 지속 상승 시 기업 성장성이 좋다는 의미이며, "
            "주가 상승의 긍정적 신호입니다."
        )

    # 15. 배당 안정성 및 성장 가능성
    div = scored_df.loc[scored_df["종목명"] == selected, "배당률"].values[0]
    if div is not None and not np.isnan(div):
        if 1 <= div < 3:
            eval_lines.append(
                "💵 [배당] 적정 수준의 배당률로 안정적이면서도 성장 가능성도 고려되는 구간입니다."
            )

    # 16. PER과 업종 평균 비교 필요성
    eval_lines.append(
        "⚠️ [PER 비교] PER은 업종 평균과 비교하는 것이 중요합니다. "
        "동일 업종 내 상대적 저평가 또는 고평가 여부를 반드시 확인하세요."
    )

    # 17. PBR과 자산 품질 확인 권장
    eval_lines.append(
        "⚠️ [PBR 검토] PBR이 낮더라도 자산의 질(유동성, 부채비율 등)과 "
        "회계정책 등을 함께 검토해야 합니다."
    )

    # 18. 거래량 급증시 가격 변동성 경계
    if '거래량' in df_price.columns:
        recent_volume = df_price['거래량'].iloc[-1]
        avg_volume = df_price['거래량'].rolling(window=20).mean().iloc[-1]
        if recent_volume > avg_volume * 2:
            eval_lines.append(
                "⚠️ [거래량 급증] 거래량이 평소 대비 두 배 이상 급증했으며, "
                "단기 급등락 가능성에 유의하세요."
            )

    # 19. RSI 30 미만 저점 신뢰성 검토
    if "RSI_14" in df_price.columns:
        rsi_now = df_price['RSI_14'].iloc[-1]
        if rsi_now < 30:
            eval_lines.append(
                "📉 [RSI 저점] RSI 30 이하일 때 단기 반등 가능성 있지만, "
                "펀더멘털 악화가 동반되면 신중해야 합니다."
            )

    # 20. 시장 변동성 대비 종목 민감도 고려
    eval_lines.append(
        "ℹ️ [시장 민감도] 해당 종목이 시장 변동성에 얼마나 민감한지 "
        "이전 가격 변동 이력과 업종 특성 분석이 필요합니다."
    )

    
    return eval_lines

def evaluate_stock_extended_3(scored_df, selected, df_price):
    eval_lines = []

    # 21. EPS 음수 시 성장성 저하 경계
    eps = scored_df.loc[scored_df["종목명"] == selected, "EPS"].values[0]
    if eps is not None and eps < 0:
        eval_lines.append(
            "🔴 [EPS 적자] 최근 분기 EPS가 음수라면 단기적으로 "
            "기업 수익성이 악화되었을 가능성이 높아 주의가 필요합니다."
        )

    # 22. 배당률 급격한 감소 시 투자자 주의
    div = scored_df.loc[scored_df["종목명"] == selected, "배당률"].values[0]
    # 배당률 변화 추적 데이터가 없으면 일반적 설명
    eval_lines.append(
        "⚠️ [배당 변화] 배당률이 급격히 감소하는 경우, "
        "기업의 현금흐름이나 재무 안정성에 문제가 있을 수 있으므로 주의하세요."
    )

    # 23. MACD 히스토그램 음수 전환 확인
    if 'MACD_HIST' in df_price.columns:
        macd_hist_latest = df_price['MACD_HIST'].iloc[-1]
        if macd_hist_latest < 0:
            eval_lines.append(
                "⚠️ [MACD 히스토그램] MACD 히스토그램이 음수로 전환되면 "
                "단기 하락 모멘텀이 강화되고 있음을 의미합니다."
            )
        else:
            eval_lines.append(
                "✅ [MACD 히스토그램] MACD 히스토그램이 양수인 경우 "
                "단기 상승 모멘텀을 나타냅니다."
            )

    # 24. 단기 가격 지지선 확인 필요
    eval_lines.append(
        "ℹ️ [지지선 확인] 단기 이동평균선(예: EMA 20일)이 가격을 지지하는지 확인하면 "
        "매수/매도 타이밍 판단에 도움이 됩니다."
    )

    # 25. 고배당주에 대한 리스크 경고
    if div is not None and div > 7:
        eval_lines.append(
            "⚠️ [고배당주 리스크] 배당률이 매우 높을 경우, "
            "일시적 배당 정책 변경이나 재무 문제 가능성이 있으니 신중한 검토가 필요합니다."
        )

    # 26. PER과 성장률의 균형 평가 필요
    eval_lines.append(
        "ℹ️ [PER과 성장률] PER이 높더라도 기업 성장률과 균형이 맞으면 "
        "합리적 평가일 수 있으므로 성장 지표 확인이 필수입니다."
    )

    # 27. 거래량 감소 지속시 유동성 리스크 고려
    if '거래량' in df_price.columns:
        vol_5 = df_price['거래량'].rolling(window=5).mean().iloc[-1]
        vol_20 = df_price['거래량'].rolling(window=20).mean().iloc[-1]
        if vol_5 < vol_20 * 0.5:
            eval_lines.append(
                "⚠️ [거래량 감소] 최근 5일 평균 거래량이 20일 평균 대비 크게 감소해 "
                "유동성 부족으로 인한 변동성 확대 우려가 있습니다."
            )

    # 28. PBR 1 미만이라도 부채비율 등 재무구조 반드시 확인 권장
    eval_lines.append(
        "⚠️ [재무구조 확인] PBR이 낮은 기업이라도 부채비율, 유동비율 등 "
        "재무구조를 꼼꼼히 살펴야 장기 투자에 적합한지 판단 가능합니다."
    )

    # 29. RSI 70 이상 시 주가 조정 가능성 강조
    if 'RSI_14' in df_price.columns:
        rsi_latest = df_price['RSI_14'].iloc[-1]
        if rsi_latest > 70:
            eval_lines.append(
                "⚠️ [RSI 과매수] RSI가 70 이상이면 단기 조정 가능성이 있으니 "
                "수익 실현 또는 추가 매수 신중히 판단하세요."
            )

    # 30. 업종별 시장 상황 반영 필요성
    eval_lines.append(
        "ℹ️ [업종 및 시장 상황] 개별 종목 평가는 업종 특성과 전체 시장 흐름에 따라 "
        "달라질 수 있으므로, 관련 뉴스 및 경제 지표도 함께 고려하세요."
    )

    return eval_lines

def evaluate_stock_extended_4(scored_df, selected, df_price):
    eval_lines = []

    # 31. EPS 지속 증가 시 긍정 신호
    eps = scored_df.loc[scored_df["종목명"] == selected, "EPS"].values[0]
    if eps is not None and eps > 0:
        eval_lines.append(
            "🟢 [EPS 성장] EPS가 꾸준히 증가하는 기업은 수익성이 개선되고 있어 "
            "장기 성장 가능성이 높습니다."
        )

    # 32. 단기 거래량 급증은 주가 변동성 신호
    if '거래량' in df_price.columns:
        recent_vol = df_price['거래량'].iloc[-1]
        avg_vol = df_price['거래량'].rolling(window=20).mean().iloc[-1]
        if recent_vol > avg_vol * 3:
            eval_lines.append(
                "⚠️ [거래량 급증] 최근 거래량이 20일 평균 대비 3배 이상으로 급증하면 "
                "주가 변동성이 커질 수 있으니 투자에 주의하세요."
            )

    # 33. 배당률 0%인 기업은 재투자 중심 성장주 가능성
    div = scored_df.loc[scored_df["종목명"] == selected, "배당률"].values[0]
    if div is not None and div == 0:
        eval_lines.append(
            "ℹ️ [배당 미지급] 배당률이 0%인 경우, 이익을 재투자해 "
            "성장을 추구하는 성장주일 수 있습니다. 단기 수익보다 장기 성장에 초점."
        )

    # 34. PBR이 낮아도 자산의 질 중요
    eval_lines.append(
        "⚠️ [자산의 질] PBR이 낮으면 가치주로 보이지만, 자산 내 부실 자산이 포함되어 있으면 "
        "투자 위험이 높으니 재무제표 내 자산 구성까지 확인하세요."
    )

    # 35. MACD Signal과 MACD 간격 좁혀질 때 추세 변동 가능성 주시
    if 'MACD' in df_price.columns and 'MACD_SIGNAL' in df_price.columns:
        macd = df_price['MACD'].iloc[-1]
        signal = df_price['MACD_SIGNAL'].iloc[-1]
        diff = abs(macd - signal)
        if diff < 0.1:
            eval_lines.append(
                "⚠️ [MACD 교차 임박] MACD와 Signal선의 차이가 작아지면 "
                "추세 반전 가능성이 있으니 주가 움직임에 주목하세요."
            )

    # 36. PER이 업종 평균과 크게 다를 경우
    eval_lines.append(
        "ℹ️ [업종 PER 비교] PER이 업종 평균 대비 현저히 높거나 낮으면 "
        "시장 기대치와 기업 가치가 괴리되었을 수 있어 비교 분석이 필요합니다."
    )

    # 37. RSI 30 이하 과매도 구간에서도 추가 확인 권고
    if 'RSI_14' in df_price.columns:
        rsi_latest = df_price['RSI_14'].iloc[-1]
        if rsi_latest < 30:
            eval_lines.append(
                "ℹ️ [RSI 과매도] RSI가 30 이하인 과매도 구간은 반등 가능성이 있지만, "
                "재무 건전성과 시장 상황도 함께 고려해 판단하세요."
            )

    # 38. 배당 성장 추이 분석 권장
    eval_lines.append(
        "ℹ️ [배당 성장] 배당률의 과거 증가 추이를 살펴보면 "
        "기업의 현금흐름 안정성과 배당 정책 지속성을 판단할 수 있습니다."
    )

    # 39. 자산 대비 부채비율 확인
    eval_lines.append(
        "⚠️ [부채비율] 자산 대비 부채비율이 높으면 금융비용 부담이 크고, "
        "경제 불황 시 위험이 커지므로 반드시 체크해야 합니다."
    )

    # 40. 단기 변동성 및 거래량 패턴 분석 권장
    eval_lines.append(
        "ℹ️ [변동성 및 거래량] 최근 단기 변동성 확대와 거래량 패턴은 "
        "시장 참여자의 심리 변화를 반영하므로 투자 판단 시 참고하세요."
    )

    return eval_lines

def evaluate_stock_extended_5(scored_df, selected, df_price):
    eval_lines = []

    # 41. 최근 5일 주가 상승률 체크
    if df_price is not None and not df_price.empty:
        recent_close = df_price['종가'].iloc[-5:]
        if recent_close.pct_change().sum() > 0.1:
            eval_lines.append(
                "📈 [최근 상승] 최근 5일간 주가가 10% 이상 상승한 경우, "
                "단기 모멘텀이 강하나 조정 가능성도 있으니 분할 매수/매도 권장."
            )

    # 42. 고점 대비 주가 위치 확인
    if df_price is not None and not df_price.empty:
        max_price = df_price['종가'].max()
        current_price = df_price['종가'].iloc[-1]
        if current_price < max_price * 0.7:
            eval_lines.append(
                "ℹ️ [저평가 가능성] 현재 주가가 연중 최고가 대비 70% 미만이면 "
                "저평가되었을 가능성이 있으나 이유를 반드시 분석해야 합니다."
            )

    # 43. PER, PBR이 모두 낮은 경우
    per = scored_df.loc[scored_df["종목명"] == selected, "PER"].values[0]
    pbr = scored_df.loc[scored_df["종목명"] == selected, "PBR"].values[0]
    if per is not None and pbr is not None and per < 10 and pbr < 1:
        eval_lines.append(
            "✔️ [PER & PBR 낮음] 이중 저평가 가능성 존재. 다만 업종 특성과 재무 안정성도 반드시 점검해야 합니다."
        )

    # 44. EPS가 감소 추세인 경우
    # (가정: EPS 데이터 과거값을 별도 분석 필요, 단순 현재값은 한계)
    eval_lines.append(
        "ℹ️ [EPS 감소] EPS가 최근 분기보다 감소 중이라면 수익성 악화 가능성이 있어 "
        "과거 실적 추이를 면밀히 확인하는 것이 필요합니다."
    )

    # 45. 배당률 급변 시 주의
    eval_lines.append(
        "⚠️ [배당률 변동] 배당률이 급격히 상승 또는 하락하는 경우, "
        "기업 정책 변화 혹은 재무 이슈 가능성이 있으므로 추가 조사 필요."
    )

    # 46. 기술적 지표 MACD Histogram 확인
    if 'MACD_HIST' in df_price.columns:
        macd_hist = df_price['MACD_HIST'].iloc[-1]
        if macd_hist > 0:
            eval_lines.append(
                "📊 [MACD Histogram] 양수 상태는 단기 상승 모멘텀 유지 중임을 의미합니다."
            )
        else:
            eval_lines.append(
                "📉 [MACD Histogram] 음수 상태는 단기 하락 모멘텀 신호로, 조정 가능성 높음."
            )

    # 47. 단기 거래량 급증과 주가 동반 상승 여부 분석 필요
    if '거래량' in df_price.columns:
        recent_vol = df_price['거래량'].iloc[-1]
        avg_vol = df_price['거래량'].rolling(window=20).mean().iloc[-1]
        current_price = df_price['종가'].iloc[-1]
        prev_price = df_price['종가'].iloc[-2]
        if recent_vol > avg_vol * 2 and current_price > prev_price:
            eval_lines.append(
                "📈 [거래량 및 가격 상승] 거래량 급증과 주가 동반 상승은 긍정적 모멘텀 신호입니다."
            )
        elif recent_vol > avg_vol * 2 and current_price <= prev_price:
            eval_lines.append(
                "⚠️ [거래량 급증/주가 부진] 거래량은 급증했으나 주가 상승이 동반되지 않는 경우 "
                "투자자 매도세가 강할 수 있으니 주의해야 합니다."
            )

    # 48. BPS 대비 주가 괴리 점검 권장
    eval_lines.append(
        "ℹ️ [BPS 괴리] BPS 대비 주가가 크게 낮거나 높으면 시장 평가와 기업 자산가치 간 괴리가 있으므로 "
        "심층 분석이 필요합니다."
    )

    # 49. 시장 변동성 반영 투자 전략 수립 필요
    eval_lines.append(
        "ℹ️ [시장 변동성] 최근 시장 변동성이 높을 경우, 투자 전략에 리스크 관리 요소를 추가하는 것이 중요합니다."
    )

    # 50. 주가 급등락 시 세력 매집/분산 패턴 분석 권고
    eval_lines.append(
        "⚠️ [급등락 분석] 급격한 주가 변동 시, 세력 매집 또는 분산 패턴을 분석하여 "
        "추가 상승 또는 조정 가능성을 판단하는 것이 도움이 됩니다."
    )

    return eval_lines

def evaluate_stock_extended_6(scored_df, selected, df_price):
    eval_lines = []

    # 51. RSI 중장기 추세 확인 권장
    if 'RSI_14' in df_price.columns:
        rsi_vals = df_price['RSI_14'].tail(30)
        if rsi_vals.mean() > 60:
            eval_lines.append(
                "📈 [RSI 중장기] 최근 30일 평균 RSI가 60 이상으로, 중장기 과매수 구간에 있어 "
                "조정 가능성을 염두에 두어야 합니다."
            )
        elif rsi_vals.mean() < 40:
            eval_lines.append(
                "📉 [RSI 중장기] 최근 30일 평균 RSI가 40 이하로, 중장기 과매도 구간에 해당해 "
                "저가 매수 기회일 수 있습니다."
            )

    # 52. PER 산업평균과의 비교 필요
    eval_lines.append(
        "ℹ️ [PER 산업평균 비교] 단순 PER 수치 외에도, 해당 기업이 속한 산업군의 평균 PER과 비교하여 "
        "저평가 또는 고평가 여부를 판단하는 것이 중요합니다."
    )

    # 53. PBR이 낮을 때 기업 부채비율과 자산 구성 확인
    eval_lines.append(
        "⚠️ [PBR 낮음 주의] PBR이 낮아도 부채비율이 높거나 자산에 문제가 있을 수 있으니, "
        "재무상태표의 부채비율 및 자산 내역을 반드시 점검해야 합니다."
    )

    # 54. 배당 정책 안정성 평가 필요
    eval_lines.append(
        "ℹ️ [배당 정책] 배당률이 높더라도 기업의 배당 지속성 및 배당 정책 변동 가능성에 대해 "
        "최근 공시 및 이사회 결정을 확인하는 것이 안전합니다."
    )

    # 55. EPS 성장률 및 영업이익률과의 연관성 검토 권장
    eval_lines.append(
        "ℹ️ [EPS 성장과 영업이익률] EPS 성장과 더불어 영업이익률의 개선 여부를 확인하면 기업 수익성 추이를 "
        "정확히 파악할 수 있습니다."
    )

    # 56. 최근 공시나 뉴스로 인한 이벤트 점검 권장
    eval_lines.append(
        "⚠️ [최근 이벤트] 기업과 관련된 공시, 경영진 변동, 소송, 제재 등의 이슈가 있을 수 있으므로 "
        "최신 뉴스 및 공시 확인이 필요합니다."
    )

    # 57. 기술적 지표 볼린저 밴드 활용 가능성
    eval_lines.append(
        "ℹ️ [볼린저 밴드] 추가적으로 볼린저 밴드 지표를 활용하면 변동성 및 과매수·과매도 구간을 "
        "더 세밀하게 파악할 수 있습니다."
    )

    # 58. 거래대금 대비 주가 변동성 분석 권장
    eval_lines.append(
        "ℹ️ [거래대금과 변동성] 거래대금 대비 과도한 주가 변동은 유동성 문제나 투기적 거래 가능성을 시사하므로 "
        "변동성 지표와 함께 분석해야 합니다."
    )

    # 59. 시장 전체 흐름과 동조성 고려 필요
    eval_lines.append(
        "ℹ️ [시장 동조성] 특정 종목이 시장 전체 흐름과 얼마나 연동되는지 확인하여, 시장 변동에 따른 영향도를 예측할 수 있습니다."
    )

    # 60. 수급 상황과 외국인/기관 투자자 움직임 확인 권장
    eval_lines.append(
        "⚠️ [수급 동향] 외국인 및 기관 투자자의 매매 동향은 주가 흐름에 큰 영향을 미치므로, 거래소 공시와 보고서를 통해 수급 상황을 모니터링하세요."
    )

    return eval_lines

def evaluate_stock_extended_7(scored_df, selected, df_price):
    eval_lines = []

    # 61. 최근 5일간 거래량 급증 여부 확인
    if '거래량' in df_price.columns:
        recent_volumes = df_price['거래량'].tail(5)
        avg_volume = df_price['거래량'].rolling(window=20).mean().iloc[-1]
        if recent_volumes.max() > avg_volume * 3:
            eval_lines.append(
                "⚠️ [거래량 급증] 최근 5일 중 거래량이 20일 평균 대비 3배 이상 급증한 날이 있어 "
                "단기 급등락 가능성이 있으니 주의가 필요합니다."
            )

    # 62. RSI 단기 및 중기 추세 비교
    if 'RSI_14' in df_price.columns:
        rsi_short = df_price['RSI_14'].tail(5).mean()
        rsi_mid = df_price['RSI_14'].tail(20).mean()
        if rsi_short > rsi_mid and rsi_short > 70:
            eval_lines.append(
                "📈 [RSI 단기상승] RSI 단기 평균이 중기 평균보다 높고 70 이상으로, 과매수 상태임을 나타냅니다."
            )
        elif rsi_short < rsi_mid and rsi_short < 30:
            eval_lines.append(
                "📉 [RSI 단기하락] RSI 단기 평균이 중기 평균보다 낮고 30 이하로, 단기 약세 신호일 수 있습니다."
            )

    # 63. MACD 히스토그램 변화 확인
    if 'MACD_HIST' in df_price.columns:
        macd_hist = df_price['MACD_HIST'].tail(5)
        if all(x > 0 for x in macd_hist) and macd_hist.iloc[-1] < macd_hist.iloc[-2]:
            eval_lines.append(
                "⚠️ [MACD 히스토그램 감소] MACD 히스토그램이 양수이지만 감소세로 전환되어 "
                "상승 모멘텀 약화 가능성을 시사합니다."
            )
        elif all(x < 0 for x in macd_hist) and macd_hist.iloc[-1] > macd_hist.iloc[-2]:
            eval_lines.append(
                "📈 [MACD 히스토그램 증가] MACD 히스토그램이 음수 구간에서 상승 전환 중으로, "
                "하락 추세가 완화될 가능성이 있습니다."
            )

    # 64. PER 급격 변화 모니터링 권장
    eval_lines.append(
        "⚠️ [PER 변화] 과거 1~2년간 PER 급격한 상승 또는 하락은 기업 실적 변동 또는 시장 기대 변화에 따른 것이므로, "
        "재무제표 및 업종 동향과 함께 확인하세요."
    )

    # 65. 배당 지속성 평가를 위한 과거 배당률 추이 검토 필요
    eval_lines.append(
        "ℹ️ [배당 추이] 최근 3년간 배당률 변동 추이를 확인하여 안정적 배당 정책 유지 여부를 판단하는 것이 중요합니다."
    )

    # 66. BPS와 순자산 변동 상황 점검 권장
    eval_lines.append(
        "ℹ️ [BPS 변동] BPS 변동은 기업 자산구성의 변화와 밀접하므로, 분기별 재무상태표를 참고하여 순자산 변동 상황을 점검하세요."
    )

    # 67. 시장 변동성에 따른 종목 변동성 비교
    eval_lines.append(
        "ℹ️ [시장 대비 변동성] 해당 종목의 변동성이 시장 평균 대비 높은지 낮은지 확인해 투자 위험성을 평가할 수 있습니다."
    )

    # 68. 최근 기관 투자자 거래 패턴 분석 권장
    eval_lines.append(
        "⚠️ [기관 투자자] 기관 투자자들의 매수·매도 패턴은 주가 방향성을 가늠하는 중요한 지표이므로, 공시자료를 통한 추적이 필요합니다."
    )

    # 69. 매출 성장과 순이익 성장률 간 괴리 분석 필요
    eval_lines.append(
        "⚠️ [성장률 괴리] 매출 성장에 비해 순이익 성장률이 현저히 낮거나 음수일 경우, 수익성 악화 가능성이 있으니 세부 내역을 분석하세요."
    )

    # 70. 가격 변동성과 거래량의 상관관계 확인
    eval_lines.append(
        "ℹ️ [가격-거래량 상관성] 가격 변동성이 커질 때 거래량이 동반 증가하는지 분석하여 투자자 관심도와 시장 반응을 판단할 수 있습니다."
    )

    for line in eval_lines:
        st.markdown(f"- {line}")

    return eval_lines

def evaluate_stock(scored_df, selected, df_price):
    eval_lines = []
    eval_lines.extend(evaluate_stock_extended_1(scored_df, selected, df_price))
    eval_lines.extend(evaluate_stock_extended_2(scored_df, selected, df_price))
    eval_lines.extend(evaluate_stock_extended_3(scored_df, selected, df_price))
    eval_lines.extend(evaluate_stock_extended_4(scored_df, selected, df_price))
    eval_lines.extend(evaluate_stock_extended_5(scored_df, selected, df_price))
    eval_lines.extend(evaluate_stock_extended_6(scored_df, selected, df_price))
    return eval_lines
