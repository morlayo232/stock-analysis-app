from scipy.stats import zscore

# 추정값 사용 시 기본 입력
DEFAULT_FIN = {
    "PER": 10.0,
    "PBR": 1.0,
    "ROE": 8.0,
    "배당률": 2.0
}

def apply_score_model(record):
    record["PER"] = DEFAULT_FIN["PER"]
    record["PBR"] = DEFAULT_FIN["PBR"]
    record["ROE"] = DEFAULT_FIN["ROE"]
    record["배당률"] = DEFAULT_FIN["배당률"]

    # 정규화 점수 (zscore는 전체 DataFrame에서 일괄 계산이 더 적합함 → 여기선 간이 점수)
    per_score = -record["PER"]
    pbr_score = -record["PBR"]
    roe_score = record["ROE"]
    div_score = record["배당률"]

    total_score = per_score + pbr_score + roe_score + div_score
    record["score"] = round(total_score, 2)

    return record
