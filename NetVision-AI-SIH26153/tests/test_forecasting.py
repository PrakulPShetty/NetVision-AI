# ============================================================
# TEST — UNIFIED FORECAST PIPELINE
# ML + World Model + XAI + MITRE ATT&CK
# ============================================================

import sys
from pathlib import Path

import pandas as pd


# ------------------------------------------------------------
# 1. Add project root to Python path
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ------------------------------------------------------------
# 2. Import unified forecasting pipeline
# ------------------------------------------------------------

from src.forecasting.attack_forecast import AttackForecastPipeline


# ------------------------------------------------------------
# 3. Define artifact paths
# ------------------------------------------------------------

MODEL_DIR = PROJECT_ROOT / "models" / "trained"

WORLD_MODEL_DIR = PROJECT_ROOT / "models" / "forecasting"

XAI_BACKGROUND_PATH = (
    PROJECT_ROOT
    / "models"
    / "xai"
    / "shap_background.csv"
)


# ============================================================
# 4. TEST HEADER
# ============================================================

print("=" * 70)
print("UNIFIED FORECAST PIPELINE TEST")
print("=" * 70)


# ============================================================
# 5. VERIFY REQUIRED ARTIFACTS
# ============================================================

required_files = [
    MODEL_DIR / "xgb_model.json",
    MODEL_DIR / "rf_smote_model.pkl",
    MODEL_DIR / "feature_names.json",
    MODEL_DIR / "ensemble_config.json",
    WORLD_MODEL_DIR / "state_transition_model.json",
    XAI_BACKGROUND_PATH,
]

for path in required_files:

    assert path.exists(), (
        f"Required artifact not found: {path}"
    )

    print(
        f"{path.name:<40} : FOUND"
    )


# ============================================================
# 6. LOAD AND VALIDATE SHAP BACKGROUND
# ============================================================

shap_background = pd.read_csv(
    XAI_BACKGROUND_PATH
)

assert shap_background.shape == (
    50,
    138
), (
    "Expected SHAP background shape "
    "(50, 138), got "
    f"{shap_background.shape}"
)

assert (
    shap_background.isna()
    .sum()
    .sum()
    == 0
), (
    "SHAP background contains NaN values."
)

numeric_background = (
    shap_background
    .select_dtypes(include="number")
)

assert not numeric_background.isin(
    [float("inf"), float("-inf")]
).any().any(), (
    "SHAP background contains infinite values."
)

print()
print(
    f"SHAP background shape : "
    f"{shap_background.shape}"
)

print(
    "SHAP background       : VALID"
)


# ============================================================
# 7. INITIALIZE UNIFIED PIPELINE
# ============================================================

pipeline = AttackForecastPipeline(
    xgb_model_path=(
        MODEL_DIR / "xgb_model.json"
    ),

    rf_model_path=(
        MODEL_DIR / "rf_smote_model.pkl"
    ),

    feature_names_path=(
        MODEL_DIR / "feature_names.json"
    ),

    ensemble_config_path=(
        MODEL_DIR / "ensemble_config.json"
    ),

    transition_model_path=(
        WORLD_MODEL_DIR
        / "state_transition_model.json"
    ),

    shap_background_data=(
        shap_background
    ),
)

print()
print(
    "Pipeline initialization : PASS"
)


# ============================================================
# 8. VALIDATE FEATURE SCHEMA
# ============================================================

feature_names = (
    pipeline.feature_names
)

assert len(feature_names) == 138, (
    f"Expected 138 features, "
    f"found {len(feature_names)}"
)

assert list(
    shap_background.columns
) == feature_names, (
    "SHAP background feature order "
    "does not match model feature schema."
)

print(
    "138-feature schema      : PASS"
)


# ============================================================
# 9. CREATE CONTROLLED TEST INPUT
# ============================================================

# A zero vector is used only as a controlled
# integration test input.
#
# It is NOT a real attack sample.

test_features = {
    feature: 0.0
    for feature in feature_names
}

assert len(
    test_features
) == 138

print(
    "Test input             : 138 features"
)


# ============================================================
# 10. RUN COMPLETE FORECAST
# ============================================================

result = pipeline.forecast(
    test_features
)

assert isinstance(
    result,
    dict
)

print()
print(
    "Forecast execution      : PASS"
)


# ============================================================
# 11. ML FORECASTING VALIDATION
# ============================================================

assert "ml" in result

ml = result["ml"]

required_ml_fields = {
    "xgb_attack_probability",
    "rf_attack_probability",
    "ensemble_attack_probability",
    "current_state",
    "current_state_label",
}

assert required_ml_fields.issubset(
    ml.keys()
), (
    "ML output is missing "
    "required fields."
)

assert 0.0 <= (
    ml["xgb_attack_probability"]
) <= 1.0

assert 0.0 <= (
    ml["rf_attack_probability"]
) <= 1.0

assert 0.0 <= (
    ml["ensemble_attack_probability"]
) <= 1.0

assert ml[
    "current_state_label"
] in {
    "BENIGN",
    "ATTACK",
}

print()
print(
    "ML forecasting          : PASS"
)

print(
    f"XGB probability         : "
    f"{ml['xgb_attack_probability']:.6f}"
)

print(
    f"RF probability          : "
    f"{ml['rf_attack_probability']:.6f}"
)

print(
    f"Ensemble probability    : "
    f"{ml['ensemble_attack_probability']:.6f}"
)

print(
    f"Current state           : "
    f"{ml['current_state_label']}"
)


# ============================================================
# 12. WORLD MODEL VALIDATION
# ============================================================

assert "world_model" in result

world_model = result[
    "world_model"
]

assert "current_state" in world_model

assert "forecasts" in world_model

forecasts = world_model[
    "forecasts"
]

assert isinstance(
    forecasts,
    list
)

expected_horizons = [
    10,
    20,
    30,
    45,
    60,
]

actual_horizons = [
    item["horizon_minutes"]
    for item in forecasts
]

assert actual_horizons == (
    expected_horizons
), (
    "Unexpected forecast horizons: "
    f"{actual_horizons}"
)

for forecast in forecasts:

    attack_probability = (
        forecast[
            "future_attack_probability"
        ]
    )

    benign_probability = (
        forecast[
            "future_benign_probability"
        ]
    )

    assert (
        0.0
        <= attack_probability
        <= 1.0
    )

    assert (
        0.0
        <= benign_probability
        <= 1.0
    )

    assert abs(
        attack_probability
        + benign_probability
        - 1.0
    ) < 1e-10


print()
print(
    "World Model forecasting : PASS"
)

for forecast in forecasts:

    print(
        f"{forecast['horizon_minutes']:>2} min"
        f"  attack probability = "
        f"{forecast['future_attack_probability']:.6f}"
    )


# ============================================================
# 13. XAI / SHAP VALIDATION
# ============================================================

assert "xai" in result

xai = result["xai"]

assert isinstance(
    xai,
    dict
), (
    "XAI output must be a dictionary."
)


# ------------------------------------------------------------
# Verify XAI availability
# ------------------------------------------------------------

assert xai.get(
    "status"
) != "XAI unavailable", (
    "XAI is unavailable even though "
    "a real SHAP background was supplied."
)


# ------------------------------------------------------------
# Verify selected XAI method
# ------------------------------------------------------------

assert xai.get(
    "method"
) == "Probability-space SHAP", (
    "Unexpected XAI method."
)


# ------------------------------------------------------------
# Verify ensemble section
# ------------------------------------------------------------

assert "ensemble" in xai, (
    "XAI output does not contain "
    "the ensemble section."
)

xai_ensemble = xai[
    "ensemble"
]

required_xai_fields = {
    "xgb_weight",
    "rf_weight",
    "xgb_attack_probability",
    "rf_attack_probability",
    "ensemble_attack_probability",
}

assert required_xai_fields.issubset(
    xai_ensemble.keys()
), (
    "XAI ensemble output is missing "
    "required fields."
)


# ------------------------------------------------------------
# Verify XAI probabilities
# ------------------------------------------------------------

xai_xgb_probability = (
    xai_ensemble[
        "xgb_attack_probability"
    ]
)

xai_rf_probability = (
    xai_ensemble[
        "rf_attack_probability"
    ]
)

xai_ensemble_probability = (
    xai_ensemble[
        "ensemble_attack_probability"
    ]
)

assert 0.0 <= (
    xai_xgb_probability
) <= 1.0

assert 0.0 <= (
    xai_rf_probability
) <= 1.0

assert 0.0 <= (
    xai_ensemble_probability
) <= 1.0


# ------------------------------------------------------------
# Verify ensemble weights
# ------------------------------------------------------------

assert abs(
    xai_ensemble[
        "xgb_weight"
    ] - 0.5
) < 1e-10

assert abs(
    xai_ensemble[
        "rf_weight"
    ] - 0.5
) < 1e-10


# ------------------------------------------------------------
# Verify SHAP reconstruction
# ------------------------------------------------------------

assert (
    "base_probability"
    in xai
)

assert (
    "reconstructed_probability"
    in xai
)

assert (
    "reconstruction_error"
    in xai
)

assert (
    "validation_passed"
    in xai
)

reconstruction_error = (
    xai[
        "reconstruction_error"
    ]
)

assert reconstruction_error < 1e-5, (
    "SHAP reconstruction error "
    "is too large."
)

assert (
    xai["validation_passed"]
    is True
), (
    "SHAP reconstruction "
    "validation did not PASS."
)


# ------------------------------------------------------------
# Verify feature contributions
# ------------------------------------------------------------

assert (
    "top_contributions"
    in xai
)

assert isinstance(
    xai["top_contributions"],
    list
)

assert len(
    xai["top_contributions"]
) > 0, (
    "No SHAP feature "
    "contributions returned."
)


print()
print(
    "XAI / SHAP              : PASS"
)

print(
    f"SHAP method             : "
    f"{xai['method']}"
)

print(
    f"XAI ensemble probability: "
    f"{xai_ensemble_probability:.6f}"
)

print(
    f"Reconstruction error    : "
    f"{reconstruction_error:.12e}"
)


# ============================================================
# 14. MITRE ATT&CK VALIDATION
# ============================================================

assert "mitre_attack" in result

mitre = result[
    "mitre_attack"
]

assert isinstance(
    mitre,
    dict
), (
    "MITRE output must be a dictionary."
)


# ------------------------------------------------------------
# The actual MITRE mapper uses "mapping_status",
# not "status".
# ------------------------------------------------------------

assert "mapping_status" in mitre, (
    "MITRE output does not contain "
    "'mapping_status'."
)

assert "techniques" in mitre, (
    "MITRE output does not contain "
    "'techniques'."
)

assert "signal_groups" in mitre, (
    "MITRE output does not contain "
    "'signal_groups'."
)

assert isinstance(
    mitre["techniques"],
    list
)

assert isinstance(
    mitre["signal_groups"],
    dict
)


# ------------------------------------------------------------
# Validate mapping status
# ------------------------------------------------------------

assert isinstance(
    mitre["mapping_status"],
    str
)

# If no techniques are returned, the mapper must provide
# the configured no-mapping status and reason.

if len(
    mitre["techniques"]
) == 0:

    assert (
        mitre["mapping_status"]
        == "No confident MITRE mapping identified"
    )

    assert "reason" in mitre


# ------------------------------------------------------------
# If techniques are returned, validate each technique.
# ------------------------------------------------------------

allowed_techniques = {
    "T1046",
    "T1498",
    "T1498.001",
}

allowed_confidence = {
    "High",
    "Medium",
    "Low-Medium",
    "Low",
}

for technique in mitre[
    "techniques"
]:

    assert (
        technique["technique_id"]
        in allowed_techniques
    )

    assert (
        technique["confidence"]
        in allowed_confidence
    )

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

    assert required_technique_fields.issubset(
        technique.keys()
    ), (
        "MITRE technique output "
        "is missing required fields."
    )


print()
print(
    "MITRE ATT&CK mapping     : PASS"
)

print(
    f"Mapping status           : "
    f"{mitre['mapping_status']}"
)

print(
    f"Techniques identified    : "
    f"{len(mitre['techniques'])}"
)


# ============================================================
# 15. UNIFIED OUTPUT VALIDATION
# ============================================================

required_sections = {
    "ml",
    "world_model",
    "xai",
    "mitre_attack",
}

assert required_sections.issubset(
    result.keys()
), (
    "Unified output is missing "
    "one or more required sections."
)

print()
print(
    "Unified output structure : PASS"
)


# ============================================================
# 16. ML ↔ XAI PROBABILITY CONSISTENCY
# ============================================================

ml_probability = (
    ml[
        "ensemble_attack_probability"
    ]
)

assert abs(
    ml_probability
    - xai_ensemble_probability
) < 1e-5, (
    "ML and XAI ensemble "
    "probabilities do not match."
)

print(
    "ML ↔ XAI probability    : PASS"
)


# ============================================================
# 17. DISPLAY TOP XAI CONTRIBUTIONS
# ============================================================

print()
print(
    "Top XAI contributions:"
)

for contribution in (
    xai[
        "top_contributions"
    ][:5]
):

    feature = contribution.get(
        "feature",
        "unknown"
    )

    shap_value = contribution.get(
        "shap_value",
        "N/A"
    )

    print(
        f"  {feature}: "
        f"{shap_value}"
    )


# ============================================================
# 18. FINAL RESULT
# ============================================================

print()
print("=" * 70)
print("UNIFIED PIPELINE VALIDATION")
print("=" * 70)

print(
    "ML forecasting          : PASS"
)

print(
    "World Model             : PASS"
)

print(
    "Probability-Space SHAP  : PASS"
)

print(
    "MITRE ATT&CK mapping    : PASS"
)

print(
    "Unified output          : PASS"
)

print(
    "ML ↔ XAI consistency    : PASS"
)

print()
print(
    "OVERALL FORECAST PIPELINE TEST : PASS"
)

print("=" * 70)