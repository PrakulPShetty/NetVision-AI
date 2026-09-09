"""
NetVision AI - Runtime Feature Transformer Test
"""

import json
from pathlib import Path

import numpy as np

from src.features.runtime_transformer import RuntimeFeatureTransformer


ROOT = Path(__file__).resolve().parents[1]


def main():
    print("=" * 70)
    print("PHASE 9.2 — RUNTIME FEATURE TRANSFORMER TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Load authoritative feature schema
    # ---------------------------------------------------------

    feature_path = ROOT / "models" / "trained" / "feature_names.json"

    assert feature_path.exists(), (
        f"Missing feature schema: {feature_path}"
    )

    with open(feature_path, "r", encoding="utf-8") as f:
        feature_names = json.load(f)

    assert len(feature_names) == 138

    print(f"\nFeature schema: {len(feature_names)} features")
    print("Feature schema: PASS")

    # ---------------------------------------------------------
    # 2. Create transformer
    # ---------------------------------------------------------

    transformer = RuntimeFeatureTransformer(feature_names)

    print("Transformer initialization: PASS")

    # ---------------------------------------------------------
    # 3. Representative 5-minute traffic input
    # ---------------------------------------------------------

    traffic = {
        "flow_count": 100,
        "unique_dst_ports": 20,
        "unique_protocols": 2,

        "forward_packets": 500,
        "backward_packets": 350,

        "forward_bytes": 50000,
        "backward_bytes": 35000,

        "flow_duration": 120000,

        "flow_bytes_per_sec": 708.33,
        "flow_packets_per_sec": 7.08,
        "backward_packets_per_sec": 2.92,

        "down_up_ratio": 0.70,

        "syn_flag_cnt": 10,
        "ack_flag_cnt": 50,
        "rst_flag_cnt": 2,
        "fin_flag_cnt": 5,
        "psh_flag_cnt": 8,
        "urg_flag_cnt": 1,

        "fwd_psh_flags": 3,
        "fwd_urg_flags": 1,

        "cwe_flag_count": 0,
        "ece_flag_cnt": 0,

        "fwd_header_len": 4000,
        "bwd_header_len": 2800,
        "init_fwd_win_byts": 64240,
        "init_bwd_win_byts": 65535,
        "fwd_seg_size_min": 20,

        "fwd_pkt_len_max": 1500,
        "fwd_pkt_len_min": 40,
        "fwd_pkt_len_mean": 100,
        "fwd_pkt_len_std": 50,

        "bwd_pkt_len_max": 1500,
        "bwd_pkt_len_min": 40,
        "bwd_pkt_len_mean": 100,
        "bwd_pkt_len_std": 50,

        "pkt_len_min": 40,
        "pkt_len_max": 1500,
        "pkt_len_mean": 100,
        "pkt_len_std": 50,
        "pkt_len_var": 2500,
        "pkt_size_avg": 100,

        "flow_iat_mean": 1000,
        "flow_iat_std": 200,
        "flow_iat_max": 5000,

        "fwd_iat_tot": 50000,
        "fwd_iat_mean": 1000,
        "fwd_iat_std": 200,
        "fwd_iat_max": 5000,

        "bwd_iat_tot": 40000,
        "bwd_iat_mean": 1000,
        "bwd_iat_std": 200,
        "bwd_iat_max": 5000,
        "bwd_iat_min": 100,

        "active_mean": 500,
        "active_std": 100,
        "active_max": 1000,
        "active_min": 100,

        "idle_mean": 1000,
        "idle_std": 200,
        "idle_max": 2000,
        "idle_min": 200,
    }

    # ---------------------------------------------------------
    # 4. Transform
    # ---------------------------------------------------------

    result = transformer.transform(traffic)

    print("\nTransformation executed: PASS")

    # ---------------------------------------------------------
    # 5. Validate shape
    # ---------------------------------------------------------

    assert result.shape == (1, 138), (
        f"Expected (1, 138), got {result.shape}"
    )

    print("Output shape (1, 138): PASS")

    # ---------------------------------------------------------
    # 6. Validate exact feature order
    # ---------------------------------------------------------

    assert result.columns.tolist() == feature_names

    print("Exact feature order: PASS")

    # ---------------------------------------------------------
    # 7. Validate numeric values
    # ---------------------------------------------------------

    assert result.dtypes.apply(
        lambda dtype: np.issubdtype(dtype, np.number)
    ).all()

    print("Numeric feature types: PASS")

    # ---------------------------------------------------------
    # 8. Validate NaN / Inf
    # ---------------------------------------------------------

    assert not result.isna().any().any()

    assert not np.isinf(
        result.to_numpy(dtype=float)
    ).any()

    print("NaN / Inf validation: PASS")

    # ---------------------------------------------------------
    # 9. Validate important derived features
    # ---------------------------------------------------------

    assert result.loc[0, "flow_count"] == 100
    assert result.loc[0, "total_flow_count"] == 100
    assert result.loc[0, "unique_dst_ports"] == 20
    assert result.loc[0, "unique_protocols"] == 2

    print("Derived network features: PASS")

    # ---------------------------------------------------------
    # 10. Final status
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("PHASE 9.2 RUNTIME TRANSFORMER TEST: PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()
    