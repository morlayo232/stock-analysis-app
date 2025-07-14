import pandas as pd
import time
from modules.fetch_price import fetch_stock_price
from modules.calculate_indicators import calculate_indicators
from modules.score_utils import safe_float, finalize_scores, DEFAULT_FIN
from modules.fetch_naver import get_naver_financials
from modules.fetch_daum import get_daum_financials

def get_financials_full_backup(code):
    per, pbr, roe, dividend = get_naver_financials(code)
    if not all([per, pbr, roe, dividend]):
        per2, pbr2, roe2, dividend2 = get_daum_financials(code)
        per = per or per2
        pbr = pbr or pbr2
        roe = roe or roe2
        dividend = dividend or dividend2
    return per, pbr, roe, dividend

def get_krx_list():
    return pd.read_csv("initial_krx_list.csv", dtype=str)[["종목코드", "종목명", "시장구분"]]

def main():
    krx = get_krx_list()
    results = []
    missed_list = []

    for _, row in krx.iterrows():
        code, name, market = row["종목코드"], row["종목명"], row["시장구분"]
        try:
            df = fetch_stock_price(code)
            if df.empty or len(df) < 20:
                print(f"⚠️ 주가 데이터 부족: {code} {name}")
                continue
            df = calculate_indicators(df)
            latest = df.iloc[-1]
            result = {
                "종목코드": code,
                "종목명": name,
                "시장구분": market,
                "현재가": latest["Close"],
                "거래량": latest["Volume"],
                "RSI": round(latest["RSI"], 2),
                "MACD": round(latest["MACD"], 2),
                "Signal": round(latest["Signal"], 2),
                "수익률(3M)": round((df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100, 2)
            }
            per, pbr, roe, dividend = get_financials_full_backup(code)
            per = safe_float(per, None)
            pbr = safe_float(pbr, None)
            roe = safe_float(roe, None)
            dividend = safe_float(dividend, None)
            result["PER"] = per
            result["PBR"] = pbr
            result["ROE"] = roe
            result["배당률"] = dividend

            if not all([per, pbr, roe, dividend]):
                missed_list.append({"code": code, "name": name})

            results.append(result)
            print(f"✅ {code} {name} 처리 완료")
            time.sleep(0.2)
        except Exception as e:
            print(f"❌ {code} {name} 오류: {e}")
            continue

    df_result = pd.DataFrame(results)
    if not df_result.empty:
        df_result = finalize_scores(df_result, style="안정형")
        df_result.to_csv("filtered_stocks.csv", index=False, encoding="utf-8-sig")
        print("✅ filtered_stocks.csv 저장 완료")
    else:
        print("⚠️ 저장할 데이터가 없습니다.")

    if missed_list:
        pd.DataFrame(missed_list).to_csv("missed_financials.csv", index=False, encoding="utf-8-sig")
        print(f"⚠️ 미취득 종목 {len(missed_list)}건: missed_financials.csv로 저장")

if __name__ == "__main__":
    main()
