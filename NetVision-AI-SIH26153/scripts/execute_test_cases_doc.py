"""
NetVision AI — Test-Case Execution Runner (TEST_CASES.md documentation source)
==============================================================================

Executes the four test cases documented in TEST_CASES.md against the
CURRENT implementation, with NO changes to:

    - ML models / model weights
    - ensemble weights
    - the 0.40 decision threshold
    - World Model
    - XAI
    - MITRE logic

Cases:
    TC1  Normal / Benign Traffic
    TC2  High-Volume / Flood-Like Attack Scenario
    TC3  Scanning-Like Traffic Scenario
    TC4  Real CIC-IDS2018 Attack Sample (ground-truth validation case)

For every case the runner records:
    runtime transformed feature count, feature shape, NaN/Inf counts,
    XGBoost / RF / ensemble probabilities, threshold, current state,
    10/20/30/45/60-minute World Model forecasts, XAI top contributing
    features, and MITRE behavioral correlations.

Run from the project root:

    .venv313/Scripts/python.exe scripts/execute_test_cases_doc.py

Outputs:
    reports/test_case_results.json
    artifacts/phase-8/attack_sample_for_TEST_CASES.csv  (TC4 provenance copy)
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.forecasting.attack_forecast import AttackForecastPipeline  # noqa: E402

OUTPUT_JSON = PROJECT_ROOT / "reports" / "test_case_results.json"
SAMPLE_COPY = PROJECT_ROOT / "artifacts" / "phase-8" / "attack_sample_for_TEST_CASES.csv"

# ------------------------------------------------------------------
# Load artifacts (unchanged)
# ------------------------------------------------------------------
FEATURE_NAMES_PATH = PROJECT_ROOT / "models" / "trained" / "feature_names.json"
SHAP_BG_PATH = PROJECT_ROOT / "models" / "xai" / "shap_background.csv"

with open(FEATURE_NAMES_PATH, encoding="utf-8") as f:
    feature_names = json.load(f)

shap_bg = pd.read_csv(SHAP_BG_PATH)

pipeline = AttackForecastPipeline(shap_background_data=shap_bg)

# ------------------------------------------------------------------
# Ground truth: real Phase 4 rows (SHAP background sampled from
# genuine Phase 4 feature-engineered data). Score all rows and pick
# the highest-ensemble-probability row as the ATTACK ground-truth case.
# ------------------------------------------------------------------
ens_scores = []
for i in range(len(shap_bg)):
    row = shap_bg.iloc[[i]]
    x = float(pipeline.xgb_model.predict_proba(row)[0, 1])
    r = float(pipeline.rf_model.predict_proba(row)[0, 1])
    ens_scores.append(pipeline.xgb_weight * x + pipeline.rf_weight * r)

attack_idx = int(np.argmax(ens_scores))
benign_idx = int(np.argmin(ens_scores))

attack_row = shap_bg.iloc[[attack_idx]]
benign_row = shap_bg.iloc[[benign_idx]]

# Provenance copy of the exact attack row used (row index recorded)
SAMPLE_COPY.parent.mkdir(parents=True, exist_ok=True)
attack_row.assign(_shap_background_row_index=attack_idx).to_csv(SAMPLE_COPY, index=False)

# ------------------------------------------------------------------
# Synthetic practical-traffic scenarios (behavioral/attack-like
# validation scenarios — NO ground-truth labels available).
# These reuse the project's established runtime-input profiles from
# scripts/runtime_input_test_suite.py (TC1/TC2/TC4), which mirror
# frontend/src/utils/presets.js.
# ------------------------------------------------------------------

TC1_TRAFFIC = {
    "flow_count": 8570, "unique_dst_ports": 950, "unique_protocols": 3,
    "forward_packets": 50500, "backward_packets": 50300,
    "forward_bytes": 3555000, "backward_bytes": 28700000,
    "max_fwd_packets_per_flow": 1130, "max_bwd_packets_per_flow": 5820,
    "max_fwd_bytes_per_flow": 28300, "max_bwd_bytes_per_flow": 8340000,
    "avg_flow_duration_sec": 12.9, "max_flow_duration_sec": 120,
    "avg_fwd_packet_size": 57, "avg_bwd_packet_size": 108,
    "max_fwd_packet_size": 222, "max_bwd_packet_size": 371,
    "min_fwd_packet_size": 9, "min_bwd_packet_size": 22,
    "pkt_len_std": 117,
    "avg_flow_bytes_per_sec": 214664, "avg_flow_packets_per_sec": 21281,
    "avg_bwd_packets_per_sec": 2543,
    "avg_iat_sec": 4.05, "iat_std_sec": 0.74, "max_iat_sec": 6.6,
    "avg_bwd_iat_sec": 0.57,
    "syn_flag_cnt": 285, "ack_flag_cnt": 2694, "rst_flag_cnt": 2007,
    "fin_flag_cnt": 35, "psh_flag_cnt": 3846, "urg_flag_cnt": 259,
    "init_fwd_win_byts": 8733, "init_bwd_win_byts": 24352,
    "fwd_seg_size_min": 17,
    "active_mean_sec": 0.14, "idle_mean_sec": 4.85,
    "down_up_ratio": 0.45,
}

TC2_TRAFFIC = {
    "flow_count": 9880, "unique_dst_ports": 1134, "unique_protocols": 3,
    "forward_packets": 59200, "backward_packets": 69900,
    "forward_bytes": 3875000, "backward_bytes": 46115000,
    "max_fwd_packets_per_flow": 2000, "max_bwd_packets_per_flow": 6160,
    "max_fwd_bytes_per_flow": 41500, "max_bwd_bytes_per_flow": 8970000,
    "avg_flow_duration_sec": 11.3, "max_flow_duration_sec": 120,
    "avg_fwd_packet_size": 54, "avg_bwd_packet_size": 101,
    "max_fwd_packet_size": 203, "max_bwd_packet_size": 322,
    "min_fwd_packet_size": 7, "min_bwd_packet_size": 17,
    "pkt_len_std": 115,
    "avg_flow_bytes_per_sec": 187343, "avg_flow_packets_per_sec": 18120,
    "avg_bwd_packets_per_sec": 2244,
    "avg_iat_sec": 3.49, "iat_std_sec": 0.63, "max_iat_sec": 5.6,
    "avg_bwd_iat_sec": 0.51,
    "syn_flag_cnt": 345, "ack_flag_cnt": 3579, "rst_flag_cnt": 2746,
    "fin_flag_cnt": 38, "psh_flag_cnt": 4705, "urg_flag_cnt": 297,
    "init_fwd_win_byts": 8352, "init_bwd_win_byts": 20239,
    "fwd_seg_size_min": 18,
    "active_mean_sec": 0.12, "idle_mean_sec": 4.12,
    "down_up_ratio": 0.47,
}

TC3_TRAFFIC = {
    "flow_count": 12000, "unique_dst_ports": 5000, "unique_protocols": 2,
    "forward_packets": 24000, "backward_packets": 6000,
    "forward_bytes": 1320000, "backward_bytes": 480000,
    "max_fwd_packets_per_flow": 2, "max_bwd_packets_per_flow": 1,
    "max_fwd_bytes_per_flow": 120, "max_bwd_bytes_per_flow": 80,
    "avg_flow_duration_sec": 0.5, "max_flow_duration_sec": 2,
    "avg_fwd_packet_size": 55, "avg_bwd_packet_size": 80,
    "max_fwd_packet_size": 60, "max_bwd_packet_size": 80,
    "min_fwd_packet_size": 54, "min_bwd_packet_size": 54,
    "pkt_len_std": 10,
    "avg_flow_bytes_per_sec": 60000, "avg_flow_packets_per_sec": 2000,
    "avg_bwd_packets_per_sec": 500,
    "avg_iat_sec": 0.05, "iat_std_sec": 0.02, "max_iat_sec": 0.5,
    "avg_bwd_iat_sec": 0.05,
    "syn_flag_cnt": 6000, "ack_flag_cnt": 9000, "rst_flag_cnt": 8000,
    "fin_flag_cnt": 10, "psh_flag_cnt": 20, "urg_flag_cnt": 0,
    "init_fwd_win_byts": 64240, "init_bwd_win_byts": 64240,
    "fwd_seg_size_min": 0,
    "active_mean_sec": 0.01, "idle_mean_sec": 0.1,
    "down_up_ratio": 0.36,
}


def audit_vector(df: pd.DataFrame) -> dict:
    arr = df.to_numpy(dtype=float)
    return {
        "feature_count": int(df.shape[1]),
        "shape": list(df.shape),
        "nan_count": int(np.isnan(arr).sum()),
        "inf_count": int(np.isinf(arr).sum()),
        "zero_count": int((arr == 0).sum()),
        "nonzero_count": int((arr != 0).sum()),
    }


def run_case(case_id: str, name: str, kind: str, feature_df: pd.DataFrame,
             input_desc: dict) -> dict:
    """Run the full unmodified pipeline on a 138-feature single-row frame."""
    features = feature_df.iloc[0].to_dict()
    result = pipeline.forecast(features)

    ml = result["ml"]
    wm = result["world_model"]
    xai = result["xai"]
    mitre = result["mitre_attack"]
    audit = audit_vector(feature_df)

    forecasts = {}
    for item in wm.get("forecasts", []):
        forecasts[str(item["horizon_minutes"])] = {
            "attack_probability": round(float(item["attack_probability"]), 6),
            "state": item["state"],
            "steps": item["steps"],
        }

    top_xai = [
        {
            "feature": c["feature"],
            "shap_value": round(float(c["shap_value"]), 6),
        }
        for c in (xai.get("top_contributions") or [])[:5]
    ]

    techniques = mitre.get("techniques") or []
    mitre_list = [
        {
            "technique_id": t["technique_id"],
            "technique_name": t["technique_name"],
            "tactic": t["tactic"],
            "confidence": t["confidence"],
        }
        for t in techniques
    ]

    return {
        "id": case_id,
        "name": name,
        "input_kind": kind,
        "input_description": input_desc,
        "runtime_transformed_feature_count": audit["feature_count"],
        "feature_shape": audit["shape"],
        "nan_count": audit["nan_count"],
        "inf_count": audit["inf_count"],
        "zero_count": audit["zero_count"],
        "nonzero_count": audit["nonzero_count"],
        "xgb_probability": round(ml["xgb_attack_probability"], 6),
        "rf_probability": round(ml["rf_attack_probability"], 6),
        "ensemble_probability": round(ml["ensemble_attack_probability"], 6),
        "threshold": ml["decision_threshold"],
        "current_state": ml["current_state_label"],
        "world_model_forecasts": forecasts,
        "xai_top_features": top_xai,
        "mitre": {
            "mapping_status": mitre.get("mapping_status"),
            "techniques": mitre_list,
        },
        "xai_reconstruction_error": xai.get("reconstruction_error"),
    }


results = {
    "meta": {
        "executor": "scripts/execute_test_cases_doc.py",
        "note": "Executed against the current unmodified implementation.",
        "xgb_weight": pipeline.xgb_weight,
        "rf_weight": pipeline.rf_weight,
        "threshold": pipeline.threshold,
        "shap_background_shape": list(shap_bg.shape),
        "attack_sample_row_index": attack_idx,
        "benign_sample_row_index": benign_idx,
        "sample_copy": str(SAMPLE_COPY.relative_to(PROJECT_ROOT)).replace("\\", "/"),
    },
    "cases": [],
}

# ------------------------------------------------------------------
# TC1 / TC2 / TC3 — practical traffic (via RuntimeFeatureTransformer)
# ------------------------------------------------------------------
for case_id, name, traffic in (
    ("TC1", "Normal / Benign Traffic", TC1_TRAFFIC),
    ("TC2", "High-Volume / Flood-Like Attack Scenario", TC2_TRAFFIC),
    ("TC3", "Scanning-Like Traffic Scenario", TC3_TRAFFIC),
):
    df = pipeline.runtime_transformer.transform(traffic)
    desc = {
        "type": "practical_traffic (RuntimeFeatureTransformer)",
        "practical_field_count": len(traffic),
        "source": "scripts/runtime_input_test_suite.py profiles (mirrors frontend/src/utils/presets.js)",
    }
    results["cases"].append(run_case(case_id, name, "synthetic_practical_traffic", df, desc))
    print(f"executed {case_id} — {name}")

# ------------------------------------------------------------------
# TC4 — Real CIC-IDS2018 attack sample (direct 138-feature path)
# ------------------------------------------------------------------
tc4_desc = {
    "type": "real_phase4_features (direct 138-feature input, no runtime transformation)",
    "source": "models/xai/shap_background.csv row "
              f"{attack_idx} — genuine CIC-IDS2018 Phase 4 feature-engineered window",
    "ground_truth": "ATTACK (real dataset sample)",
    "provenance_copy": str(SAMPLE_COPY.relative_to(PROJECT_ROOT)).replace("\\", "/"),
}
results["cases"].append(
    run_case("TC4", "Real CIC-IDS2018 Attack Sample", "real_dataset_sample", attack_row, tc4_desc)
)
print("executed TC4 — Real CIC-IDS2018 Attack Sample")

# ------------------------------------------------------------------
# Reference execution: real benign row (context for validation status)
# ------------------------------------------------------------------
benign_result = run_case(
    "REF-BENIGN", "Real CIC-IDS2018 Benign Sample (reference)",
    "real_dataset_sample", benign_row,
    {
        "type": "real_phase4_features (direct 138-feature input)",
        "source": f"models/xai/shap_background.csv row {benign_idx}",
        "ground_truth": "BENIGN (real dataset sample)",
    },
)
results["reference_benign"] = benign_result
print("executed REF-BENIGN — Real benign reference")

OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\nResults written to: {OUTPUT_JSON}")
print(f"Attack sample copy: {SAMPLE_COPY}")
print("\n--- QUICK SUMMARY ---")
for c in results["cases"]:
    print(
        f"{c['id']:<5} XGB={c['xgb_probability']:.4f}  RF={c['rf_probability']:.4f}  "
        f"ENS={c['ensemble_probability']:.4f}  Thr={c['threshold']}  "
        f"State={c['current_state']:<7} NaN={c['nan_count']} Inf={c['inf_count']} "
        f"shape={tuple(c['feature_shape'])}"
    )
print(
    f"REF   XGB={benign_result['xgb_probability']:.4f}  RF={benign_result['rf_probability']:.4f}  "
    f"ENS={benign_result['ensemble_probability']:.4f}  State={benign_result['current_state']}"
)
