DEFAULT_FIN = {
    "PER": 10.0,
    "PBR": 1.0,
    "ROE": 8.0,
    "배당률": 2.0
}

def safe_float(val, default):
    try:
        sval = str(val).replace(',', '').replace('%', '').replace('N/A', '').replace('-', '').replace('\n', '').replace('l', '').strip().upper()
        if sval in ['', 'NONE', 'NAN']:
            return default
        return float(sval)
    except Exception:
        return default

def apply_score_model(record):
    per = safe_float(record.get("PER", DEFAULT_FIN["PER"]), DEFAULT_FIN["PER"])
    pbr = safe_float(record.get("PBR", DEFAULT_FIN["PBR"]), DEFAULT_FIN["PBR"])
    roe = safe_float(record.get("ROE", DEFAULT_FIN["ROE"]), DEFAULT_FIN["ROE"])
    div = safe_float(record.get("배당률", DEFAULT_FIN["배당률"]), DEFAULT_FIN["배당률"])

    # 실무형 단순 합산 점수 (원하면 가중치/z-score 방식으로 추가 확장 가능)
    per_score = -per
    pbr_score = -pbr
    roe_score = roe
    div_score = div

    total_score = per_score + pbr_score + roe_score + div_score
    record["score"] = round(total_score, 2)
    return record
