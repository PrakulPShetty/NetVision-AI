"""
NetVision AI - Runtime Feature Transformer Test
===============================================

Validates the Phase-4-compatible derivation engine:
    - shape / order / NaN / Inf guarantees
    - exact per-flow mean = window sum / flow_count identity
    - window _sum features are populated
    - documented constants (flag max = 1, MTU cap 1460, window field 65535)
    - seconds -> microseconds conversion
    - legacy key backward compatibility
"""

import json
from pathlib import Path

import numpy as np

from src.features.runtime_transformer import RuntimeFeatureTransformer


ROOT = Path(__file__).resolve().parents[1]


def load_schema():
    feature_path = ROOT / "models" / "trained" / "feature_names.json"
    with open(feature_path, "r", encoding="utf-8") as f:
        feature_names = json.load(f)
    assert len(feature_names) == 138
    return feature_names


# ------------------------------------------------------------------
# Pytest-style tests
# ------------------------------------------------------------------

def test_schema_validation():
    feature_names = load_schema()
    transformer = RuntimeFeatureTransformer(feature_names)
    assert transformer.feature_names == feature_names


def test_legacy_input_contract():
    """The previous 17-field practical input still transforms cleanly."""
    feature_names = load_schema()
    transformer = RuntimeFeatureTransformer(feature_names)

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
    }

    result = transformer.transform(traffic)

    assert result.shape == (1, 138)
    assert result.columns.tolist() == feature_names
    assert not result.isna().any().any()
    assert not np.isinf(result.to_numpy(dtype=float)).any()

    # Legacy semantics preserved: flow_duration is microseconds.
    assert result.loc[0, "Flow Duration_mean"] == 120000.0
    assert result.loc[0, "flow_count"] == 100
    assert result.loc[0, "total_flow_count"] == 100


def test_mean_is_sum_over_flow_count():
    """Phase 4 identity: per-flow mean == window sum / flow_count."""
    feature_names = load_schema()
    transformer = RuntimeFeatureTransformer(feature_names)

    traffic = {
        "flow_count": 8570,
        "unique_dst_ports": 950,
        "unique_protocols": 3,
        "forward_packets": 50500,
        "backward_packets": 50300,
        "forward_bytes": 3555000,
        "backward_bytes": 28700000,
    }

    result = transformer.transform(traffic)

    assert result.loc[0, "Tot Fwd Pkts_sum"] == 50500
    assert np.isclose(result.loc[0, "Tot Fwd Pkts_mean"], 50500 / 8570)
    assert result.loc[0, "TotLen Bwd Pkts_sum"] == 28700000
    assert np.isclose(result.loc[0, "TotLen Bwd Pkts_mean"], 28700000 / 8570)


def test_sum_features_populated():
    """Window _sum features must not be zero when totals are provided."""
    feature_names = load_schema()
    transformer = RuntimeFeatureTransformer(feature_names)

    traffic = {
        "flow_count": 1000,
        "forward_packets": 10000,
        "backward_packets": 9000,
        "forward_bytes": 1000000,
        "backward_bytes": 900000,
    }

    result = transformer.transform(traffic)
    # Volume _sum features must be populated from window totals.
    volume_sums = [
        "Tot Fwd Pkts_sum",
        "Tot Bwd Pkts_sum",
        "TotLen Fwd Pkts_sum",
        "TotLen Bwd Pkts_sum",
    ]
    for feat in volume_sums:
        assert feat in feature_names
        assert result.loc[0, feat] > 0, f"{feat} should be populated"


def test_documented_constants():
    """Verified constants: flag max = 1, MTU 1460, window field 65535."""
    feature_names = load_schema()
    transformer = RuntimeFeatureTransformer(feature_names)

    traffic = {
        "flow_count": 1000,
        "forward_packets": 5000,
        "backward_packets": 5000,
        "forward_bytes": 300000,
        "backward_bytes": 500000,
        "syn_flag_cnt": 300,
        "ack_flag_cnt": 400,
        "rst_flag_cnt": 100,
        "init_fwd_win_byts": 8733,
        "init_bwd_win_byts": 24352,
    }

    result = transformer.transform(traffic)

    assert result.loc[0, "SYN Flag Cnt_sum"] == 300
    assert result.loc[0, "SYN Flag Cnt_max"] == 1.0
    assert result.loc[0, "ACK Flag Cnt_max"] == 1.0
    assert result.loc[0, "RST Flag Cnt_max"] == 1.0
    assert result.loc[0, "Pkt Len Max_max"] == 1460.0
    assert result.loc[0, "Bwd Pkt Len Max_max"] == 1460.0
    assert result.loc[0, "Init Fwd Win Byts_mean"] == 8733.0
    assert result.loc[0, "Init Fwd Win Byts_min"] == 0.0
    assert result.loc[0, "Init Fwd Win Byts_max"] == 65535.0
    assert result.loc[0, "Init Bwd Win Byts_max"] == 65535.0


def test_seconds_to_microseconds_conversion():
    """Duration / IAT / activity fields are entered in seconds."""
    feature_names = load_schema()
    transformer = RuntimeFeatureTransformer(feature_names)

    traffic = {
        "flow_count": 1000,
        "forward_packets": 5000,
        "backward_packets": 5000,
        "forward_bytes": 300000,
        "backward_bytes": 500000,
        "avg_flow_duration_sec": 12.9,
        "max_flow_duration_sec": 120.0,
        "avg_iat_sec": 4.05,
        "iat_std_sec": 0.74,
        "max_iat_sec": 6.6,
        "avg_bwd_iat_sec": 0.57,
        "active_mean_sec": 0.14,
        "idle_mean_sec": 4.85,
    }

    result = transformer.transform(traffic)

    assert np.isclose(result.loc[0, "Flow Duration_mean"], 12.9e6)
    assert np.isclose(result.loc[0, "Flow Duration_max"], 120.0e6)
    assert np.isclose(result.loc[0, "Flow IAT Mean_mean"], 4.05e6)
    assert np.isclose(result.loc[0, "Flow IAT Std_mean"], 0.74e6)
    assert np.isclose(result.loc[0, "Flow IAT Max_mean"], 6.6e6)
    assert np.isclose(result.loc[0, "Bwd IAT Mean_mean"], 0.57e6)
    assert np.isclose(result.loc[0, "Active Mean_mean"], 0.14e6)
    assert np.isclose(result.loc[0, "Idle Mean_mean"], 4.85e6)


def test_legacy_extended_keys_still_work():
    """Extended legacy keys (IAT / packet / active / idle) still map."""
    feature_names = load_schema()
    transformer = RuntimeFeatureTransformer(feature_names)

    traffic = {
        "flow_count": 100,
        "forward_packets": 500,
        "backward_packets": 350,
        "forward_bytes": 50000,
        "backward_bytes": 35000,
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
        "active_mean": 500,
        "active_std": 100,
        "active_max": 1000,
        "active_min": 100,
        "idle_mean": 1000,
        "idle_std": 200,
        "idle_max": 2000,
        "idle_min": 200,
        "fwd_header_len": 4000,
        "bwd_header_len": 2800,
    }

    result = transformer.transform(traffic)

    assert result.shape == (1, 138)
    assert not result.isna().any().any()
    assert result.loc[0, "Flow IAT Mean_mean"] == 1000.0
    assert result.loc[0, "Fwd Pkt Len Mean_mean"] == 100.0
    assert result.loc[0, "Pkt Len Std_mean"] == 50.0
    assert result.loc[0, "Active Mean_mean"] == 500.0
    assert result.loc[0, "Idle Mean_mean"] == 1000.0
    assert result.loc[0, "Fwd Header Len_mean"] == 4000.0


def test_empty_input_defaults_to_zero():
    feature_names = load_schema()
    transformer = RuntimeFeatureTransformer(feature_names)

    result = transformer.transform({})

    assert result.shape == (1, 138)
    assert not result.isna().any().any()
    assert not np.isinf(result.to_numpy(dtype=float)).any()
    assert (result.to_numpy(dtype=float) == 0).all()


def test_flow_count_zero_no_division_error():
    feature_names = load_schema()
    transformer = RuntimeFeatureTransformer(feature_names)

    result = transformer.transform({"flow_count": 0, "forward_packets": 100})

    assert result.shape == (1, 138)
    assert not result.isna().any().any()
    assert result.loc[0, "Tot Fwd Pkts_mean"] == 0.0


def test_non_finite_input_rejected():
    feature_names = load_schema()
    transformer = RuntimeFeatureTransformer(feature_names)

    import pytest

    with pytest.raises(ValueError):
        transformer.transform({"forward_packets": float("nan")})

    with pytest.raises(ValueError):
        transformer.transform({"forward_packets": float("inf")})


# ------------------------------------------------------------------
# Script-style entry point (kept for backward compatibility)
# ------------------------------------------------------------------

def main():
    print("=" * 70)
    print("PHASE 9.2 — RUNTIME FEATURE TRANSFORMER TEST")
    print("=" * 70)

    feature_names = load_schema()
    print(f"\nFeature schema: {len(feature_names)} features")

    transformer = RuntimeFeatureTransformer(feature_names)

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

    result = transformer.transform(traffic)

    assert result.shape == (1, 138)
    assert result.columns.tolist() == feature_names
    assert result.dtypes.apply(
        lambda dtype: np.issubdtype(dtype, np.number)
    ).all()
    assert not result.isna().any().any()
    assert not np.isinf(result.to_numpy(dtype=float)).any()
    assert result.loc[0, "flow_count"] == 100
    assert result.loc[0, "total_flow_count"] == 100
    assert result.loc[0, "unique_dst_ports"] == 20
    assert result.loc[0, "unique_protocols"] == 2

    # New derivation checks
    assert np.isclose(result.loc[0, "Tot Fwd Pkts_mean"], 500 / 100)
    assert result.loc[0, "Tot Fwd Pkts_sum"] == 500
    assert result.loc[0, "SYN Flag Cnt_sum"] == 10
    assert result.loc[0, "SYN Flag Cnt_max"] == 1.0

    print("\nTransformation executed: PASS")
    print("Output shape (1, 138): PASS")
    print("Exact feature order: PASS")
    print("Numeric feature types: PASS")
    print("NaN / Inf validation: PASS")
    print("Derived network features: PASS")
    print("Phase 4 derivation checks: PASS")
    print("\n" + "=" * 70)
    print("PHASE 9.2 RUNTIME TRANSFORMER TEST: PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()