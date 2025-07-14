import numpy as np import pandas as pd

DEFAULT_FIN = ['PER', 'PBR', 'ROE', '배당수익률']

def safe_float(val): try: return float(str(val).replace(",", "").replace("%", "")) except: return np.nan

def safe_zscore(arr): arr = np.array(arr, dtype=np.float64) mean = np.nanmean(arr) std = np.nanstd(arr) if std == 0 or np.isnan(std): return np.zeros_like(arr) return (arr - mean) / std

def assess_reliability(row): count = sum(~np.isnan([row.get(c, np.nan) for c in DEFAULT_FIN])) if count >= 4: return 'A' elif count == 3: return 'B' else: return 'C'

def finalize_scores(df, style="aggressive"): for col in DEFAULT_FIN: if col in df.columns: df[col] = df[col].apply(safe_float) else: df[col] = np.nan

for col in DEFAULT_FIN: df[f'z_{col}'] = safe_zscore(df[col]) if col in df else np.zeros(len(df)) scores = [] for _, row in df.iterrows(): z = {k: row.get(f'z_{k}', np.nan) for k in DEFAULT_FIN} weights = { "aggressive": {"PER": -0.25, "PBR": -0.25, "ROE": 0.35, "배당수익률": 0.15}, "stable": {"PER": -0.3, "PBR": -0.4, "ROE": 0.2, "배당수익률": 0.1}, "dividend": {"PER": -0.1, "PBR": -0.2, "ROE": 0.0, "배당수익률": 0.7}, }[style] valid = {k: w for k, w in weights.items() if not np.isnan(z[k])} if not valid: scores.append(0) continue total_w = sum(abs(w) for w in valid.values()) score = sum(z[k] * w for k, w in valid.items()) / total_w scores.append(score) df['score'] = scores return df 
