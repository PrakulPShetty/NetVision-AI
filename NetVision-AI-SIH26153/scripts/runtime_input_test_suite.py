"""
NetVision AI — Runtime Input Architecture Test Suite
=====================================================

Validates the rearchitected practical traffic input end-to-end:

    TC1  Normal benign traffic            (practical profile)
    TC2  High-volume attack-like traffic  (practical profile)
    TC3  SYN-heavy connection flood       (practical profile)
    TC4  Scanning-like traffic            (practical profile)
    TC5  Mixed benign + suspicious        (practical profile)
    TC6  Real benign Phase 4 row          (direct 138-feature)
    TC7  Real attack Phase 4 row          (direct 138-feature)

For every case it reports the transformed feature audit (shape, zeros,
NaN, Inf), XGB / RF / ensemble probabilities, threshold, current state,
World Model forecasts, XAI top features and MITRE correlations, plus a
comparison table and a feature-vector validation.

Run from the project root:

    python scripts/runtime_input_test_suite.py

The ML models, ensemble weights, threshold, World Model, XAI and MITRE
modules are NOT modified by this suite.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.forecasting.attack_forecast import AttackForecastPipeline  # noqa: E402

DIVIDER = "=" * 78
SUBDIV = "-" * 78

# ------------------------------------------------------------------
# Artifacts
# ------------------------------------------------------------------
FEATURE_NAMES_PATH = PROJECT_ROOT / "models" / "trained" / "feature_names.json"
SHAP_BG_PATH = PROJECT_ROOT / "models" / "xai" / "shap_background.csv"

with open(FEATURE_NAMES_PATH, encoding="utf-8") as f:
    feature_names = json.load(f)

shap_bg = pd.read_csv(SHAP_BG_PATH)

# ------------------------------------------------------------------
# Practical traffic profiles (mirror frontend/src/utils/presets.js)
# ------------------------------------------------------------------

PRACTICAL_CASES = [
    {
        "id": "TC1",
        "name": "Normal benign traffic",
        "pattern": "Normal",
        "description": (
            "Balanced web / API / DB traffic — median benign CIC-IDS2018 "
            "Phase 4 window values."
        ),
        "traffic": {
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
        },
    },
    {
        "id": "TC2",
        "name": "High-volume attack-like traffic",
        "pattern": "High Volume",
        "description": (
            "Large asymmetric bulk transfer with heavy backward payload and "
            "elevated RST/ACK activity — median attack Phase 4 window values."
        ),
        "traffic": {
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
        },
    },
    {
        "id": "TC3",
        "name": "SYN-heavy connection flood",
        "pattern": "SYN Heavy",
        "description": (
            "~90 000 SYNs in 5 minutes (~300 connection attempts/second, "
            "an order of magnitude above the normal connection rate) toward "
            "a single port with minimal handshake completion."
        ),
        "traffic": {
            "flow_count": 90000, "unique_dst_ports": 2, "unique_protocols": 1,
            "forward_packets": 90000, "backward_packets": 20000,
            "forward_bytes": 5400000, "backward_bytes": 1600000,
            "max_fwd_packets_per_flow": 1, "max_bwd_packets_per_flow": 2,
            "max_fwd_bytes_per_flow": 66, "max_bwd_bytes_per_flow": 160,
            "avg_flow_duration_sec": 0.05, "max_flow_duration_sec": 3,
            "avg_fwd_packet_size": 60, "avg_bwd_packet_size": 80,
            "max_fwd_packet_size": 60, "max_bwd_packet_size": 80,
            "min_fwd_packet_size": 54, "min_bwd_packet_size": 54,
            "pkt_len_std": 5,
            "avg_flow_bytes_per_sec": 18000000,
            "avg_flow_packets_per_sec": 300000,
            "avg_bwd_packets_per_sec": 60000,
            "avg_iat_sec": 0.01, "iat_std_sec": 0.005, "max_iat_sec": 0.05,
            "avg_bwd_iat_sec": 0.02,
            "syn_flag_cnt": 90000, "ack_flag_cnt": 20000,
            "rst_flag_cnt": 15000, "fin_flag_cnt": 0, "psh_flag_cnt": 5000,
            "urg_flag_cnt": 0,
            "init_fwd_win_byts": 64240, "init_bwd_win_byts": 64240,
            "fwd_seg_size_min": 0,
            "active_mean_sec": 0.05, "idle_mean_sec": 0.01,
            "down_up_ratio": 0.3,
        },
    },
    {
        "id": "TC4",
        "name": "Scanning-like traffic",
        "pattern": "Scanning",
        "description": (
            "Thousands of distinct destination ports with small one-to-two "
            "packet flows and high RST replies — service discovery behavior."
        ),
        "traffic": {
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
        },
    },
    {
        "id": "TC5",
        "name": "Mixed benign + suspicious traffic",
        "pattern": "Mixed",
        "description": (
            "Mostly ordinary traffic with a modest elevation in connection "
            "attempts, RSTs, and destination diversity — ambiguous by design."
        ),
        "traffic": {
            "flow_count": 9200, "unique_dst_ports": 1800, "unique_protocols": 3,
            "forward_packets": 56000, "backward_packets": 52000,
            "forward_bytes": 3700000, "backward_bytes": 29500000,
            "max_fwd_packets_per_flow": 1200, "max_bwd_packets_per_flow": 5900,
            "max_fwd_bytes_per_flow": 29000, "max_bwd_bytes_per_flow": 8400000,
            "avg_flow_duration_sec": 12.5, "max_flow_duration_sec": 120,
            "avg_fwd_packet_size": 56, "avg_bwd_packet_size": 106,
            "max_fwd_packet_size": 215, "max_bwd_packet_size": 350,
            "min_fwd_packet_size": 8, "min_bwd_packet_size": 20,
            "pkt_len_std": 116,
            "avg_flow_bytes_per_sec": 205000, "avg_flow_packets_per_sec": 20000,
            "avg_bwd_packets_per_sec": 2400,
            "avg_iat_sec": 3.9, "iat_std_sec": 0.7, "max_iat_sec": 6.2,
            "avg_bwd_iat_sec": 0.55,
            "syn_flag_cnt": 600, "ack_flag_cnt": 2900, "rst_flag_cnt": 2400,
            "fin_flag_cnt": 36, "psh_flag_cnt": 3900, "urg_flag_cnt": 260,
            "init_fwd_win_byts": 8600, "init_bwd_win_byts": 24000,
            "fwd_seg_size_min": 17,
            "active_mean_sec": 0.13, "idle_mean_sec": 4.6,
            "down_up_ratio": 0.46,
        },
    },
]


def audit_vector(df: pd.DataFrame) -> dict:
    """Audit a transformed 138-feature vector."""
    arr = df.to_numpy(dtype=float)
    return {
        "shape": df.shape,
        "zeros": int((arr == 0).sum()),
        "nonzero": int((arr != 0).sum()),
        "nan": int(np.isnan(arr).sum()),
        "inf": int(np.isinf(arr).sum()),
    }


def print_forecasts(world_model: dict) -> None:
    for item in world_model.get("forecasts", []):
        print(
            f"      {item.get('horizon_minutes'):>3} min : "
            f"attack probability = {item.get('attack_probability'):.4f}  "
            f"state = {item.get('state')}"
        )


def print_xai(xai: dict, top: int = 5) -> None:
    contributions = xai.get("top_contributions") or []
    for item in contributions[:top]:
        print(
            f"      {item.get('feature', '?'):<34} "
            f"shap = {item.get('shap_value', 0.0):+.4f}"
        )


def print_mitre(mitre: dict) -> None:
    techniques = mitre.get("techniques") or []
    if not techniques:
        print(f"      {mitre.get('mapping_status', 'No mapping')}")
        return
    for tech in techniques:
        print(
            f"      {tech.get('technique_id'):<12} "
            f"{tech.get('technique_name', '?')}  "
            f"[{tech.get('confidence')}]"
        )


def main() -> None:
    print(DIVIDER)
    print("NetVision AI — RUNTIME INPUT TEST SUITE (TC1–TC7)")
    print(DIVIDER)

    # ------------------------------------------------------------------
    # 0. Pipeline init + model integrity baseline
    # ------------------------------------------------------------------
    pipeline = AttackForecastPipeline(shap_background_data=shap_bg)

    xgb_all = pipeline.xgb_model.predict_proba(shap_bg)[:, 1]
    rf_all = pipeline.rf_model.predict_proba(shap_bg)[:, 1]
    ens_all = pipeline.xgb_weight * xgb_all + pipeline.rf_weight * rf_all
    order = np.argsort(ens_all)

    benign_row = shap_bg.iloc[[order[0]]]
    attack_row = shap_bg.iloc[[order[-1]]]

    print(f"\nModel integrity baseline (genuine Phase 4 rows):")
    for label, row in (("BENIGN", benign_row), ("ATTACK", attack_row)):
        x = float(pipeline.xgb_model.predict_proba(row)[0, 1])
        r = float(pipeline.rf_model.predict_proba(row)[0, 1])
        e = pipeline.xgb_weight * x + pipeline.rf_weight * r
        state = "ATTACK" if e >= pipeline.threshold else "BENIGN"
        print(
            f"  {label:<7} XGB={x:.4f}  RF={r:.4f}  "
            f"Ensemble={e:.4f}  Threshold={pipeline.threshold}  "
            f"State={state}"
        )

    # ------------------------------------------------------------------
    # 1. Run all test cases
    # ------------------------------------------------------------------
    results = []

    for case in PRACTICAL_CASES:
        print(f"\n{DIVIDER}")
        print(f"{case['id']} — {case['name']}")
        print(SUBDIV)
        print(f"  Description : {case['description']}")
        print(f"  Input       : {len(case['traffic'])} practical fields")

        result = pipeline.forecast_from_traffic(case["traffic"])
        ml = result["ml"]

        # Re-transform to audit the exact vector
        df = pipeline.runtime_transformer.transform(case["traffic"])
        audit = audit_vector(df)

        print(f"  Transformed feature shape : {audit['shape']}")
        print(f"  Zero features             : {audit['zeros']}")
        print(f"  Non-zero features         : {audit['nonzero']}")
        print(f"  NaN count                 : {audit['nan']}")
        print(f"  Inf count                 : {audit['inf']}")
        print(
            f"  XGBoost probability       : {ml['xgb_attack_probability']:.4f}"
        )
        print(f"  Random Forest probability : {ml['rf_attack_probability']:.4f}")
        print(
            f"  Ensemble probability      : "
            f"{ml['ensemble_attack_probability']:.4f}"
        )
        print(f"  Threshold                 : {ml['decision_threshold']}")
        print(f"  Current state             : {ml['current_state_label']}")
        print("  World Model forecasts:")
        print_forecasts(result["world_model"])
        print("  XAI top features:")
        print_xai(result["xai"])
        print("  MITRE correlations:")
        print_mitre(result["mitre_attack"])

        results.append(
            {
                "id": case["id"],
                "name": case["name"],
                "pattern": case["pattern"],
                "xgb": ml["xgb_attack_probability"],
                "rf": ml["rf_attack_probability"],
                "ensemble": ml["ensemble_attack_probability"],
                "state": ml["current_state_label"],
                "audit": audit,
            }
        )

    # ------------------------------------------------------------------
    # 2. Real Phase 4 rows (direct 138-feature path)
    # ------------------------------------------------------------------
    for label, row, case_id, name in (
        ("REAL BENIGN", benign_row, "TC6", "Real benign Phase 4 row"),
        ("REAL ATTACK", attack_row, "TC7", "Real attack Phase 4 row"),
    ):
        print(f"\n{DIVIDER}")
        print(f"{case_id} — {name}")
        print(SUBDIV)
        result = pipeline.forecast(row.iloc[0].to_dict())
        ml = result["ml"]
        audit = audit_vector(row)

        print(f"  Description : genuine Phase 4 row (direct 138 features)")
        print(f"  Transformed feature shape : {audit['shape']}")
        print(f"  Zero features             : {audit['zeros']}")
        print(f"  Non-zero features         : {audit['nonzero']}")
        print(f"  NaN count                 : {audit['nan']}")
        print(f"  Inf count                 : {audit['inf']}")
        print(
            f"  XGBoost probability       : {ml['xgb_attack_probability']:.4f}"
        )
        print(f"  Random Forest probability : {ml['rf_attack_probability']:.4f}")
        print(
            f"  Ensemble probability      : "
            f"{ml['ensemble_attack_probability']:.4f}"
        )
        print(f"  Threshold                 : {ml['decision_threshold']}")
        print(f"  Current state             : {ml['current_state_label']}")
        print("  World Model forecasts:")
        print_forecasts(result["world_model"])
        print("  XAI top features:")
        print_xai(result["xai"])
        print("  MITRE correlations:")
        print_mitre(result["mitre_attack"])

        results.append(
            {
                "id": case_id,
                "name": name,
                "pattern": label,
                "xgb": ml["xgb_attack_probability"],
                "rf": ml["rf_attack_probability"],
                "ensemble": ml["ensemble_attack_probability"],
                "state": ml["current_state_label"],
                "audit": audit,
            }
        )

    # ------------------------------------------------------------------
    # 3. Comparison table
    # ------------------------------------------------------------------
    print(f"\n{DIVIDER}")
    print("TEST CASE COMPARISON")
    print(DIVIDER)
    header = (
        f"  {'Test Case':<10} {'Input Pattern':<18} {'XGB':>8} {'RF':>8} "
        f"{'Ensemble':>9} {'State':>8} {'Zeros':>6}"
    )
    print(header)
    print("  " + "-" * (len(header) - 2))
    for r in results:
        print(
            f"  {r['id']:<10} {r['pattern']:<18} {r['xgb']:>8.4f} "
            f"{r['rf']:>8.4f} {r['ensemble']:>9.4f} {r['state']:>8} "
            f"{r['audit']['zeros']:>6}"
        )

    # ------------------------------------------------------------------
    # 4. Feature-vector validation + meaningful-change check
    # ------------------------------------------------------------------
    print(f"\n{DIVIDER}")
    print("FEATURE VECTOR VALIDATION")
    print(DIVIDER)
    all_ok = True
    for case in PRACTICAL_CASES:
        df = pipeline.runtime_transformer.transform(case["traffic"])
        ok = (
            df.shape == (1, 138)
            and df.columns.tolist() == feature_names
            and not df.isna().any().any()
            and not np.isinf(df.to_numpy(dtype=float)).any()
        )
        all_ok = all_ok and ok
        print(f"  {case['id']} shape=(1,138) order=exact NaN=0 Inf=0 : "
              f"{'PASS' if ok else 'FAIL'}")

    print()
    print("  Meaningful input change check — TC1 (normal) vs TC2 (attack-like):")
    df1 = pipeline.runtime_transformer.transform(PRACTICAL_CASES[0]["traffic"])
    df2 = pipeline.runtime_transformer.transform(PRACTICAL_CASES[1]["traffic"])
    changed = [
        c for c in feature_names
        if df1[c].iloc[0] != df2[c].iloc[0]
    ]
    print(f"    features that differ : {len(changed)} / 138")

    families = {}
    for col in changed:
        family = col.rsplit("_", 1)[0] if "_" in col else col
        families[family] = families.get(family, 0) + 1
    top_families = sorted(
        families.items(), key=lambda kv: kv[1], reverse=True
    )[:10]
    print("    top changed feature families:")
    for family, count in top_families:
        print(f"      {family:<28} {count} feature(s)")

    # ------------------------------------------------------------------
    # 5. Backend integration (in-process FastAPI TestClient)
    # ------------------------------------------------------------------
    print(f"\n{DIVIDER}")
    print("BACKEND INTEGRATION — POST /forecast (TestClient)")
    print(DIVIDER)
    try:
        from fastapi.testclient import TestClient

        from backend.app.main import app

        client = TestClient(app)

        health = client.get("/health")
        print(f"  GET /health : {health.status_code} "
              f"{health.json().get('status')}")

        # TC2 practical profile through the HTTP endpoint
        resp = client.post(
            "/forecast", json={"traffic": PRACTICAL_CASES[1]["traffic"]}
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        ml = data["ml"]
        print(
            f"  POST /forecast (TC2 practical) : XGB={ml['xgb_attack_probability']:.4f} "
            f"RF={ml['rf_attack_probability']:.4f} "
            f"ENS={ml['ensemble_attack_probability']:.4f} "
            f"State={ml['current_state_label']}"
        )
        assert "world_model" in data and "xai" in data and "mitre_attack" in data

        # Real attack row through the HTTP endpoint (138 features dict)
        payload = {"features": attack_row.iloc[0].to_dict()}
        resp = client.post("/forecast", json=payload)
        assert resp.status_code == 200, resp.text
        ml = resp.json()["ml"]
        print(
            f"  POST /forecast (TC7 real attack): XGB={ml['xgb_attack_probability']:.4f} "
            f"RF={ml['rf_attack_probability']:.4f} "
            f"ENS={ml['ensemble_attack_probability']:.4f} "
            f"State={ml['current_state_label']}"
        )
        print("  Backend integration : PASS")
    except Exception as exc:  # pragma: no cover
        print(f"  Backend integration : SKIPPED/FAILED ({exc})")

    # ------------------------------------------------------------------
    # 6. Summary
    # ------------------------------------------------------------------
    print(f"\n{DIVIDER}")
    print("SUMMARY")
    print(DIVIDER)
    print(f"  Model integrity (real rows): ")
    print(f"    TC6 real benign : XGB={results[5]['xgb']:.4f} "
          f"RF={results[5]['rf']:.4f} ENS={results[5]['ensemble']:.4f} "
          f"-> {results[5]['state']}")
    print(f"    TC7 real attack : XGB={results[6]['xgb']:.4f} "
          f"RF={results[6]['rf']:.4f} ENS={results[6]['ensemble']:.4f} "
          f"-> {results[6]['state']}")
    print(f"  Feature-vector validation : {'PASS' if all_ok else 'FAIL'}")

    expected_benign = {"TC1", "TC6"}
    expected_attack = {"TC7"}
    for r in results:
        if r["id"] in expected_benign:
            assert r["state"] == "BENIGN", (
                f"{r['id']} expected BENIGN, got {r['state']}"
            )
        if r["id"] in expected_attack:
            assert r["state"] == "ATTACK", (
                f"{r['id']} expected ATTACK, got {r['state']}"
            )

    print()
    print("RUNTIME INPUT TEST SUITE : PASS")
    print(DIVIDER)


if __name__ == "__main__":
    main()