# modules/score_utils.pyTypeError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).

Traceback:

File "/mount/src/stock-analysis-app/app.py", line 32, in <module> scored_df = finalize_scores(raw_df)

File "/mount/src/stock-analysis-app/modules/score_utils.py", line 14, in finalize_scores s = pd.Series([default]*N, index=df.index) ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/generic.py", line 2190, in __array_ufunc__ return arraylike.array_ufunc(self, ufunc, method, *inputs, **kwargs) ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/arraylike.py", line 399, in array_ufunc result = getattr(ufunc, method)(*inputs, **kwargs)



import numpy as np
import pandas as pd

def finalize_scores(df, style="aggressive"):
    df = df.copy()
    N = len(df)

    def safe_numeric(col, default=0):
        if col in df.columns:
            s = df[col]
        else:
            s = pd.Series([default]*N, index=df.index)
        # None 또는 list인 경우도 Series로 강제
        if s is None or isinstance(s, list):
            s = pd.Series([default]*N, index=df.index)
        # 문자/NaN 모두 0으로
        s = pd.to_numeric(s, errors="coerce").fillna(default)
        s = s.astype(float)
        s[s < 0] = 0
        return s

    PER = safe_numeric("PER")
    PBR = safe_numeric("PBR")
    EPS = safe_numeric("EPS")
    BPS = safe_numeric("BPS", 1)
    배당률 = safe_numeric("배당률")
    거래량 = safe_numeric("거래량")

    거래량_log = np.log1p(거래량)

    df["score"] = (
        -0.1 * PER
        -0.2 * PBR
        +0.2 * (EPS / (BPS + 1))
        +0.05 * 배당률
        +0.1 * 거래량_log
    )

    return df

def assess_reliability(row):
    vals = [row.get(x, np.nan) for x in ["PER", "PBR", "EPS", "BPS", "배당률"]]
    missing = sum(pd.isna(vals))
    if missing == 0:
        return "A"
    elif missing <= 1:
        return "B"
    else:
        return "C"
