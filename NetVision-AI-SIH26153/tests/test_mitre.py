"""
NetVision AI
Phase 8 — MITRE ATT&CK Module Test

Tests the finalized behavioral MITRE mapping implementation.

Techniques:
    T1046      Network Service Discovery
    T1498      Network Denial of Service
    T1498.001  Direct Network Flood
"""

from pathlib import Path
import sys
import json

import numpy as np
import pandas as pd


# ============================================================
# Add project root to Python import path
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from src.mitre import MITREAttackMapper


# ============================================================
# Header
# ============================================================

print("=" * 70)
print("NetVision AI — Phase 8 MITRE ATT&CK Module Test")
print("=" * 70)


# ============================================================
# 1. Load finalized feature schema
# ============================================================

print("\nLoading feature schema...")

feature_path = (
    ROOT
    / "models"
    / "trained"
    / "feature_names.json"
)

if not feature_path.exists():
    raise FileNotFoundError(
        f"Feature schema not found: {feature_path}"
    )


with open(
    feature_path,
    "r",
    encoding="utf-8",
) as file:

    feature_names = json.load(file)


print(
    f"Feature count       : {len(feature_names)}"
)

assert len(feature_names) == 138

print(
    "Feature schema      : VALID"
)


# ============================================================
# 2. Initialize MITRE mapper
# ============================================================

print("\n" + "=" * 70)
print("Initializing MITRE Mapper")
print("=" * 70)

mapper = MITREAttackMapper(
    feature_names=feature_names
)

print(
    "MITRE mapper        : INITIALIZED"
)


# ============================================================
# 3. Helper function
# ============================================================

def create_input():
    """
    Create a single 138-feature temporal input row
    initialized to zero.
    """

    return pd.DataFrame(
        np.zeros(
            (1, len(feature_names)),
            dtype=float,
        ),
        columns=feature_names,
    )


# ============================================================
# TEST 1 — Full behavioral evidence
# ============================================================

print("\n" + "=" * 70)
print("TEST 1 — Full Behavioral Evidence")
print("=" * 70)

X_full = create_input()


# Destination diversity
X_full.loc[
    0,
    "unique_dst_ports"
] = 20

X_full.loc[
    0,
    "unique_protocols"
] = 3


# Traffic volume
X_full.loc[
    0,
    "flow_count"
] = 100

X_full.loc[
    0,
    "total_flow_count"
] = 100

X_full.loc[
    0,
    "Tot Fwd Pkts_sum"
] = 1000

X_full.loc[
    0,
    "TotLen Fwd Pkts_sum"
] = 50000


# Packet rate
X_full.loc[
    0,
    "Bwd Pkts/s_mean"
] = 500


# Temporal concentration
X_full.loc[
    0,
    "Flow Duration_max"
] = 1000000


result_full = mapper.map(
    X_full
)


technique_ids = {
    technique["technique_id"]
    for technique in result_full[
        "techniques"
    ]
}


print(
    "Mapping status     :",
    result_full[
        "mapping_status"
    ]
)

print(
    "Techniques detected:",
    sorted(technique_ids)
)


expected_techniques = {
    "T1046",
    "T1498",
    "T1498.001",
}

assert technique_ids == expected_techniques

print(
    "Technique mapping  : PASS"
)


# Validate confidence levels

confidence_map = {
    technique["technique_id"]:
    technique["confidence"]
    for technique in result_full[
        "techniques"
    ]
}


assert (
    confidence_map["T1046"]
    == "Medium"
)

assert (
    confidence_map["T1498"]
    == "Medium"
)

assert (
    confidence_map["T1498.001"]
    == "Low-Medium"
)


print(
    "Confidence levels  : PASS"
)


# ============================================================
# TEST 2 — Insufficient evidence
# ============================================================

print("\n" + "=" * 70)
print("TEST 2 — Insufficient Evidence")
print("=" * 70)

X_zero = create_input()

result_zero = mapper.map(
    X_zero
)


print(
    "Mapping status     :",
    result_zero[
        "mapping_status"
    ]
)

print(
    "Technique count    :",
    len(
        result_zero[
            "techniques"
        ]
    )
)


assert (
    result_zero[
        "mapping_status"
    ]
    == "No confident MITRE mapping identified"
)

assert (
    len(
        result_zero[
            "techniques"
        ]
    )
    == 0
)


print(
    "Insufficient evidence handling : PASS"
)


# ============================================================
# TEST 3 — Partial evidence
# ============================================================

print("\n" + "=" * 70)
print("TEST 3 — Partial Evidence")
print("=" * 70)

X_partial = create_input()

X_partial.loc[
    0,
    "flow_count"
] = 100

X_partial.loc[
    0,
    "total_flow_count"
] = 100


result_partial = mapper.map(
    X_partial
)


print(
    "Mapping status     :",
    result_partial[
        "mapping_status"
    ]
)

print(
    "Technique count    :",
    len(
        result_partial[
            "techniques"
        ]
    )
)


assert (
    result_partial[
        "mapping_status"
    ]
    == "No confident MITRE mapping identified"
)

assert (
    len(
        result_partial[
            "techniques"
        ]
    )
    == 0
)


print(
    "Partial evidence handling      : PASS"
)


# ============================================================
# TEST 4 — Output structure
# ============================================================

print("\n" + "=" * 70)
print("TEST 4 — MITRE Output Structure")
print("=" * 70)

assert "mapping_status" in result_full
assert "techniques" in result_full
assert "signal_groups" in result_full


required_technique_fields = {
    "technique_id",
    "technique_name",
    "tactic",
    "confidence",
    "evidence",
    "supporting_features",
    "interpretation",
    "limitation",
}


for technique in result_full[
    "techniques"
]:

    assert (
        required_technique_fields
        .issubset(
            technique.keys()
        )
    )


print(
    "MITRE output fields : PASS"
)


# ============================================================
# TEST 5 — Signal group structure
# ============================================================

print("\n" + "=" * 70)
print("TEST 5 — Behavioral Signal Groups")
print("=" * 70)

expected_groups = {
    "destination_diversity",
    "traffic_volume",
    "packet_rate",
    "temporal_concentration",
}


actual_groups = set(
    result_full[
        "signal_groups"
    ].keys()
)


print(
    "Signal groups      :",
    sorted(actual_groups)
)


assert (
    actual_groups
    == expected_groups
)


print(
    "Signal group structure : PASS"
)


# ============================================================
# Final summary
# ============================================================

print("\n" + "=" * 70)
print("PHASE 8 VS CODE MITRE TEST SUMMARY")
print("=" * 70)

print(
    "138-feature schema          : PASS"
)

print(
    "MITRE mapper initialization : PASS"
)

print(
    "Full evidence mapping       : PASS"
)

print(
    "Confidence validation       : PASS"
)

print(
    "Insufficient evidence       : PASS"
)

print(
    "Partial evidence handling   : PASS"
)

print(
    "Output structure            : PASS"
)

print(
    "Signal groups               : PASS"
)

print(
    "\nOVERALL MITRE MODULE TEST   : PASS"
)

print("=" * 70)