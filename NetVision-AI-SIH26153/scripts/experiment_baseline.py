"""
NetVision AI — Baseline experiment harness (READ-ONLY, no code changes).

Runs:
  TEST 1 — genuine benign Phase 4 row through frozen pipeline
  TEST 2 — genuine attack Phase 4 row through frozen pipeline
  TEST 3 — practical benign input through runtime transformer
  TEST 4 — practical attack input through runtime transformer
  FEATURE COMPARISON — real attack vector vs practical attack vector
  PROVENANCE AUDIT — count populated / derived / defaulted features

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

FEATURE_NAMES_PATH = PROJECT_ROOT / "models" / "trained" / "feature_names.json"
SHAP_BG_PATH = PROJECT_ROOT / "models" / "xai" / "shap_background.csv"

with open(FEATURE_NAMES_PATH, encoding="utf-8") as f:
    feature_names = json.load(f)
shap_bg = pd.read_csv(SHAP_BG_PATH)

pipeline = AttackForecastPipeline(shap_background_data=shap_bg)

# ------------------------------------------------------------------
# Select genuine Phase 4 rows: strongest-attack and most-benign by
# ensemble score across the 50 real background rows.
# ------------------------------------------------------------------
probs = []
for i in range(len(shap_bg)):
    row = shap_bg.iloc[[i]]
    xgb_p = float(pipeline.xgb_model.predict_proba(row)[0, 1])
    rf_p = float(pipeline.rf_model.predict_proba(row)[0, 1])
    probs.append((i, xgb_p, rf_p, 0.5 * xgb_p + 0.5 * rf_p))
probs.sort(key=lambda t: t[3])

b_idx, b_xgb, b_rf, b_ens = probs[0]
a_idx, a_xgb, a_rf, a_ens = probs[-1]
benign_row = shap_bg.iloc[[b_idx]]
attack_row = shap_bg.iloc[[a_idx]]

print("=" * 78)
print("TEST 1 — REAL BENIGN (SHAP background idx", b_idx, ")")
print(f"  XGB={b_xgb:.4f}  RF={b_rf:.4f}  Ensemble={b_ens:.4f}  "
      f"State={'ATTACK' if b_ens >= pipeline.threshold else 'BENIGN'}")

print("=" * 78)
print("TEST 2 — REAL ATTACK (SHAP background idx", a_idx, ")")
print(f"  XGB={a_xgb:.4f}  RF={a_rf:.4f}  Ensemble={a_ens:.4f}  "
      f"State={'ATTACK' if a_ens >= pipeline.threshold else 'BENIGN'}")

# ------------------------------------------------------------------
# Practical inputs (current form fields only)
# ------------------------------------------------------------------
practical_benign = {
    "flow_count": 50, "unique_dst_ports": 4, "unique_protocols": 2,
    "forward_packets": 320, "backward_packets": 480,
    "forward_bytes": 48000, "backward_bytes": 210000,
    "flow_duration": 120000, "flow_bytes_per_sec": 2150.0,
    "flow_packets_per_sec": 6.67, "backward_packets_per_sec": 4.0,
    "down_up_ratio": 1.5,
    "syn_flag_cnt": 8, "ack_flag_cnt": 780, "rst_flag_cnt": 0,
    "fin_flag_cnt": 12, "psh_flag_cnt": 45, "urg_flag_cnt": 0,
}

practical_attack = {
    "flow_count": 2450, "unique_dst_ports": 2, "unique_protocols": 1,
    "forward_packets": 18500, "backward_packets": 240,
    "forward_bytes": 1180000, "backward_bytes": 12000,
    "flow_duration": 300000, "flow_bytes_per_sec": 3973.33,
    "flow_packets_per_sec": 62.47, "backward_packets_per_sec": 0.8,
    "down_up_ratio": 0.01,
    "syn_flag_cnt": 18200, "ack_flag_cnt": 120, "rst_flag_cnt": 40,
    "fin_flag_cnt": 0, "psh_flag_cnt": 0, "urg_flag_cnt": 0,
}

tf = pipeline.runtime_transformer

def score_df(df, label):
    xgb_p = float(pipeline.xgb_model.predict_proba(df)[0, 1])
    rf_p = float(pipeline.rf_model.predict_proba(df)[0, 1])
    ens = pipeline.xgb_weight * xgb_p + pipeline.rf_weight * rf_p
    state = "ATTACK" if ens >= pipeline.threshold else "BENIGN"
    print("=" * 78)
    print(label)
    print(f"  XGB={xgb_p:.4f}  RF={rf_p:.4f}  Ensemble={ens:.4f}  "
          f"Threshold={pipeline.threshold}  State={state}")
    return xgb_p, rf_p, ens

benign_df = tf.transform(practical_benign)
attack_df = tf.transform(practical_attack)

print("=" * 78)
print("TEST 3 — PRACTICAL BENIGN (current transformer)")
t3 = score_df(benign_df, "  Results:")

print("=" * 78)
print("TEST 4 — PRACTICAL ATTACK (current transformer)")
t4 = score_df(attack_df, "  Results:")

# ------------------------------------------------------------------
# Feature comparison: real attack vs practical attack
# ------------------------------------------------------------------
print("=" * 78)
print("FEATURE VECTOR COMPARISON — REAL ATTACK vs PRACTICAL ATTACK")

real_vec = attack_row.iloc[0]
prac_vec = attack_df.iloc[0]

def audit(vec, name):
    arr = vec.to_numpy(dtype=float)
    print(f"\n  {name}:")
    print(f"    shape={len(arr)}  zeros={int((arr == 0).sum())}  "
          f"nonzero={int((arr != 0).sum())}  NaN={int(np.isnan(arr).sum())}  "
          f"Inf={int(np.isinf(arr).sum())}")
    print(f"    min={np.min(arr):.6g}  max={np.max(arr):.6g}  "
          f"mean={np.mean(arr):.6g}")
    return set(vec.index[(vec == 0)])

real_zero = audit(real_vec, "REAL ATTACK")
prac_zero = audit(prac_vec, "PRACTICAL ATTACK (current transformer)")

both_zero = real_zero & prac_zero
only_prac_zero = prac_zero - real_zero

print(f"\n  zero in BOTH vectors: {len(both_zero)}")
print(f"  zero ONLY in practical vector (missing info): {len(only_prac_zero)}")
print("\n  Zero-only-in-practical features (model-relevant gaps):")
for feat in sorted(only_prac_zero):
    print(f"    {feat}")

# Key feature-by-feature comparison
KEY = [
    "Tot Fwd Pkts_sum", "Tot Fwd Pkts_mean", "Tot Fwd Pkts_max",
    "Tot Bwd Pkts_sum", "Tot Bwd Pkts_mean",
    "TotLen Fwd Pkts_sum", "TotLen Fwd Pkts_mean", "TotLen Fwd Pkts_max",
    "TotLen Bwd Pkts_sum", "TotLen Bwd Pkts_mean",
    "Flow Duration_mean", "Flow Duration_min", "Flow Duration_max",
    "Flow IAT Mean_mean", "Flow IAT Std_mean", "Flow IAT Max_mean",
    "Fwd IAT Tot_mean", "Fwd IAT Mean_mean",
    "Bwd IAT Tot_mean", "Bwd IAT Mean_mean",
    "Fwd Pkt Len Max_mean", "Fwd Pkt Len Min_mean", "Fwd Pkt Len Mean_mean",
    "Bwd Pkt Len Max_mean", "Bwd Pkt Len Min_mean", "Bwd Pkt Len Mean_mean",
    "Pkt Len Min_mean", "Pkt Len Max_mean", "Pkt Len Mean_mean", "Pkt Len Var_mean",
    "Flow Byts/s_mean", "Flow Byts/s_max", "Flow Pkts/s_mean", "Flow Pkts/s_max",
    "Bwd Pkts/s_mean",
    "SYN Flag Cnt_sum", "SYN Flag Cnt_max", "ACK Flag Cnt_sum",
    "RST Flag Cnt_sum", "FIN Flag Cnt_sum", "PSH Flag Cnt_sum",
    "Fwd Header Len_mean", "Bwd Header Len_mean",
    "Init Fwd Win Byts_mean", "Init Bwd Win Byts_mean",
    "Active Mean_mean", "Idle Mean_mean",
    "flow_count", "unique_dst_ports", "unique_protocols", "total_flow_count",
    "Down/Up Ratio_mean",
]

print("\n  Key features (real vs practical attack):")
print(f"  {'FEATURE':<30} {'REAL':>16} {'PRACTICAL':>16}")
for feat in KEY:
    if feat in feature_names:
        print(f"  {feat:<30} {real_vec[feat]:>16.4f} {prac_vec[feat]:>16.4f}")

print("\nBaseline harness complete (read-only).")
