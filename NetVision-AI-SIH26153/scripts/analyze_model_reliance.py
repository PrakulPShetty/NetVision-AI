"""
NetVision AI — Model reliance + derivation-identity analysis (READ-ONLY).

1. Frozen-model feature reliance:
   - XGBoost gain importance
   - RandomForest gini importance
   - aggregated by feature FAMILY (e.g. "SYN Flag Cnt", "Flow IAT", ...)

2. Identity validation on the 50 genuine Phase 4 rows (shap_background.csv):
   tests whether practical aggregates can legitimately reconstruct
   temporal features (bytes/packet, IAT ≈ duration/packets, header ≈ 20×pkts).

Nothing here modifies project code or artifacts.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.forecasting.attack_forecast import AttackForecastPipeline  # noqa: E402

shap_bg = pd.read_csv(PROJECT_ROOT / "models" / "xai" / "shap_background.csv")
pipeline = AttackForecastPipeline(shap_background_data=shap_bg)

with open(PROJECT_ROOT / "models" / "trained" / "feature_names.json", encoding="utf-8") as f:
    feature_names = json.load(f)

# ------------------------------------------------------------------
# 1. Feature reliance
# ------------------------------------------------------------------
xgb_imp = pd.Series(pipeline.xgb_model.feature_importances_, index=feature_names)
rf_imp = pd.Series(pipeline.rf_model.feature_importances_, index=feature_names)
combined = 0.5 * xgb_imp / xgb_imp.sum() + 0.5 * rf_imp / rf_imp.sum()

print("=" * 78)
print("TOP 30 FEATURES — combined normalized importance (50/50 XGB+RF)")
top = combined.sort_values(ascending=False).head(30)
for feat, imp in top.items():
    print(f"  {feat:<32} xgb={xgb_imp[feat]:.4f}  rf={rf_imp[feat]:.4f}  comb={imp:.4f}")

def family(feat: str) -> str:
    for suffix in ("_sum", "_mean", "_max", "_min"):
        if feat.endswith(suffix):
            return feat[: -len(suffix)]
    return feat

fam = combined.groupby(combined.index.map(family)).sum().sort_values(ascending=False)
print("\nTOP 25 FAMILIES — combined importance")
for feat, imp in fam.head(25).items():
    print(f"  {feat:<32} {imp:.4f}")

print("\nFAMILY IMPORTANCE SPLIT by representation class:")
derived_from_totals = ["Tot Fwd Pkts", "Tot Bwd Pkts", "TotLen Fwd Pkts", "TotLen Bwd Pkts",
                       "SYN Flag Cnt", "ACK Flag Cnt", "RST Flag Cnt", "FIN Flag Cnt",
                       "PSH Flag Cnt", "URG Flag Cnt", "Fwd PSH Flags", "Fwd URG Flags",
                       "flow_count", "unique_dst_ports", "unique_protocols", "total_flow_count"]
tot_imp = float(fam.reindex(derived_from_totals).fillna(0).sum())
print(f"  derivable-from-current-form families : {tot_imp:.4f} ({tot_imp:.1%})")
print(f"  NOT derivable from current form      : {1 - tot_imp:.4f} ({1 - tot_imp:.1%})")

# ------------------------------------------------------------------
# 2. Identity validation on genuine rows
# ------------------------------------------------------------------
print("\n" + "=" * 78)
print("IDENTITY CHECKS on 50 genuine Phase 4 rows")

def rel_err(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    denom = np.maximum(np.abs(b), 1e-9)
    return float(np.median(np.abs(a - b) / denom)), float(np.mean(np.abs(a - b) / denom < 0.10))

checks = []

# A. Pkt Size Avg_mean  ≈  (TotLen Fwd + TotLen Bwd)_sum / (Tot Fwd + Tot Bwd)_sum
a = shap_bg["Pkt Size Avg_mean"]
b = (shap_bg["TotLen Fwd Pkts_sum"] + shap_bg["TotLen Bwd Pkts_sum"]) / \
    (shap_bg["Tot Fwd Pkts_sum"] + shap_bg["Tot Bwd Pkts_sum"]).replace(0, np.nan)
checks.append(("Pkt Size Avg_mean ≈ totBytes/totPkts", a, b))

# B. Flow IAT Mean_mean ≈ Flow Duration_mean / (total pkts per flow)
tot_pkts_flow = shap_bg["Tot Fwd Pkts_mean"] + shap_bg["Tot Bwd Pkts_mean"]
b = shap_bg["Flow Duration_mean"] / tot_pkts_flow.replace(0, np.nan)
checks.append(("Flow IAT Mean_mean ≈ Duration_mean / pkts_per_flow", shap_bg["Flow IAT Mean_mean"], b))

# C. Fwd Header Len_mean ≈ 20 × Tot Fwd Pkts_mean (TCP header, no options)
checks.append(("Fwd Header Len_mean ≈ 20 × FwdPkts_mean", shap_bg["Fwd Header Len_mean"], 20 * shap_bg["Tot Fwd Pkts_mean"]))
checks.append(("Bwd Header Len_mean ≈ 20 × BwdPkts_mean", shap_bg["Bwd Header Len_mean"], 20 * shap_bg["Tot Bwd Pkts_mean"]))

# D. Bwd Pkts/s_mean ≈ BwdPkts_mean / (Duration_mean / 1e6)
b = shap_bg["Tot Bwd Pkts_mean"] / (shap_bg["Flow Duration_mean"] / 1e6).replace(0, np.nan)
checks.append(("Bwd Pkts/s_mean ≈ BwdPkts_mean / dur_s", shap_bg["Bwd Pkts/s_mean"], b))

# E. Fwd PSH Flags == PSH Flag Cnt ?  and Fwd URG vs URG
checks.append(("Fwd PSH Flags_sum == PSH Flag Cnt_sum", shap_bg["Fwd PSH Flags_sum"], shap_bg["PSH Flag Cnt_sum"]))
checks.append(("Fwd URG Flags_sum == URG Flag Cnt_sum", shap_bg["Fwd URG Flags_sum"], shap_bg["URG Flag Cnt_sum"]))

# F. Flow Byts/s_mean ≈ (TotLen sums per flow)/flow/duration  (rough)
b = (shap_bg["TotLen Fwd Pkts_mean"] + shap_bg["TotLen Bwd Pkts_mean"]) / \
    (shap_bg["Flow Duration_mean"] / 1e6).replace(0, np.nan)
checks.append(("Flow Byts/s_mean ≈ bytes_per_flow/dur_s", shap_bg["Flow Byts/s_mean"], b))

for name, a, b in checks:
    med, within10 = rel_err(a, b)
    print(f"  {name:<52} medianRelErr={med:8.3f}  within10%={within10:.0%}")

# G. Distribution of hard-to-know fields by state
print("\nDistributions by predicted state (0.40 threshold):")
X = shap_bg[feature_names]
xgb_p = pipeline.xgb_model.predict_proba(X)[:, 1]
rf_p = pipeline.rf_model.predict_proba(X)[:, 1]
state = (0.5 * xgb_p + 0.5 * rf_p) >= pipeline.threshold
shap_bg2 = shap_bg.copy()
shap_bg2["_state"] = np.where(state, "ATTACK", "BENIGN")

for feat in ["Init Fwd Win Byts_mean", "Init Bwd Win Byts_mean",
             "Active Mean_mean", "Idle Mean_mean",
             "Down/Up Ratio_mean", "Flow Duration_mean",
             "Flow IAT Mean_mean", "Pkt Len Std_mean",
             "Fwd Seg Size Min_mean", "Bwd Pkts/s_mean"]:
    g = shap_bg2.groupby("_state")[feat]
    print(f"  {feat:<26} BENIGN med={g.median().get('BENIGN', float('nan')):>14.2f}"
          f"  ATTACK med={g.median().get('ATTACK', float('nan')):>14.2f}")

print("\nAnalysis complete (read-only).")
