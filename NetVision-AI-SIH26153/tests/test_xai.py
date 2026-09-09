"""
NetVision AI
Phase 8 — XAI Module Test

Tests the finalized probability-space SHAP implementation
against the existing Phase 7 model artifacts.
"""

# ============================================================
# Imports
# ============================================================

from pathlib import Path
import sys
import json

import numpy as np
import pandas as pd
import joblib
import xgboost as xgb


# ============================================================
# Add project root to Python import path
# ============================================================

# tests/test_xai.py
# parents[0] = tests
# parents[1] = project root

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Now the project source can be imported
from src.xai import SHAPExplainer


# ============================================================
# NetVision AI — Phase 8 XAI Module Test
# ============================================================

print("=" * 70)
print("NetVision AI — Phase 8 XAI Module Test")
print("=" * 70)


# ============================================================
# 1. Define model directory
# ============================================================

MODEL_DIR = ROOT / "models" / "trained"

print("\nProject root:")
print(ROOT)

print("\nModel directory:")
print(MODEL_DIR)


# ============================================================
# 2. Verify required model artifacts
# ============================================================

print("\n" + "=" * 70)
print("Checking Model Artifacts")
print("=" * 70)

required_files = [
    "xgb_model.json",
    "rf_smote_model.pkl",
    "feature_names.json",
    "ensemble_config.json",
]

for filename in required_files:

    file_path = MODEL_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required model artifact not found: {file_path}"
        )

    print(
        f"{filename:30s}: FOUND"
    )


# ============================================================
# 3. Load XGBoost model
# ============================================================

print("\nLoading XGBoost model...")

xgb_model = xgb.XGBClassifier()

xgb_model.load_model(
    str(MODEL_DIR / "xgb_model.json")
)

print("XGBoost model       : LOADED")


# ============================================================
# 4. Load Random Forest model
# ============================================================

print("Loading Random Forest model...")

rf_model = joblib.load(
    MODEL_DIR / "rf_smote_model.pkl"
)

print("Random Forest model : LOADED")


# ============================================================
# 5. Load feature schema
# ============================================================

print("Loading feature schema...")

with open(
    MODEL_DIR / "feature_names.json",
    "r",
    encoding="utf-8",
) as file:

    feature_names = json.load(file)


print(
    f"Feature count       : {len(feature_names)}"
)


# ============================================================
# 6. Validate feature count
# ============================================================

assert len(feature_names) == 138, (
    f"Expected 138 features, "
    f"found {len(feature_names)}"
)

print(
    "Feature schema      : VALID"
)


# ============================================================
# 7. Load ensemble configuration
# ============================================================

print("Loading ensemble configuration...")

with open(
    MODEL_DIR / "ensemble_config.json",
    "r",
    encoding="utf-8",
) as file:

    ensemble_config = json.load(file)


weights = ensemble_config[
    "ensemble"
]["weights"]

xgb_weight = float(weights[0])
rf_weight = float(weights[1])

threshold = float(
    ensemble_config["threshold"]
)


print(
    f"XGBoost weight      : {xgb_weight}"
)

print(
    f"Random Forest weight: {rf_weight}"
)

print(
    f"Threshold           : {threshold}"
)


# ============================================================
# 8. Validate ensemble configuration
# ============================================================

assert np.isclose(
    xgb_weight + rf_weight,
    1.0,
)

assert np.isclose(
    xgb_weight,
    0.5,
)

assert np.isclose(
    rf_weight,
    0.5,
)

print(
    "Ensemble configuration: VALID"
)


# ============================================================
# 9. Create test input
# ============================================================

print("\n" + "=" * 70)
print("Creating Test Input")
print("=" * 70)

# One synthetic model-ready input containing
# exactly the 138 expected features.

X_test = pd.DataFrame(
    np.zeros(
        (1, len(feature_names)),
        dtype=float,
    ),
    columns=feature_names,
)


print(
    "Input shape         :",
    X_test.shape,
)

assert X_test.shape == (
    1,
    138,
)

print(
    "Input schema        : VALID"
)


# ============================================================
# 10. Create SHAP background data
# ============================================================

print("\nCreating SHAP background data...")

# This background is used only to test the VS Code module.
#
# During Phase 8 research, real Phase 4 traffic windows
# were used as the background dataset.

X_background = pd.DataFrame(
    np.zeros(
        (50, len(feature_names)),
        dtype=float,
    ),
    columns=feature_names,
)


print(
    "Background shape    :",
    X_background.shape,
)

assert X_background.shape == (
    50,
    138,
)


# ============================================================
# 11. Initialize SHAP explainer
# ============================================================

print("\n" + "=" * 70)
print("Initializing SHAP Explainer")
print("=" * 70)

explainer = SHAPExplainer(
    xgb_model=xgb_model,
    rf_model=rf_model,
    feature_names=feature_names,
    xgb_weight=xgb_weight,
    rf_weight=rf_weight,
    background_data=X_background,
)

print(
    "SHAP explainer      : INITIALIZED"
)


# ============================================================
# 12. Generate explanation
# ============================================================

print("\n" + "=" * 70)
print("Generating SHAP Explanation")
print("=" * 70)

result = explainer.explain(
    X_test,
    top_n=10,
)


print(
    "Explanation         : GENERATED"
)


# ============================================================
# 13. Validate probability output
# ============================================================

xgb_probability = result[
    "ensemble"
]["xgb_attack_probability"]

rf_probability = result[
    "ensemble"
]["rf_attack_probability"]

ensemble_probability = result[
    "ensemble"
]["ensemble_attack_probability"]


assert (
    0.0
    <= xgb_probability
    <= 1.0
)

assert (
    0.0
    <= rf_probability
    <= 1.0
)

assert (
    0.0
    <= ensemble_probability
    <= 1.0
)


print(
    "XGB probability    :",
    xgb_probability,
)

print(
    "RF probability     :",
    rf_probability,
)

print(
    "Ensemble probability:",
    ensemble_probability,
)

print(
    "Probability range  : PASS"
)


# ============================================================
# 14. Validate SHAP reconstruction
# ============================================================

reconstruction_error = result[
    "reconstruction_error"
]

validation_passed = result[
    "validation_passed"
]


print(
    "\nSHAP reconstruction error:",
    reconstruction_error,
)

assert (
    reconstruction_error < 1e-5
)

assert (
    validation_passed is True
)

print(
    "SHAP reconstruction : PASS"
)


# ============================================================
# 15. Validate feature contributions
# ============================================================

top_contributions = result[
    "top_contributions"
]

assert len(
    top_contributions
) == 10


for item in top_contributions:

    assert "feature" in item
    assert "shap_value" in item
    assert "absolute_shap" in item


print(
    "Top feature extraction: PASS"
)


# ============================================================
# 16. Display top feature contributions
# ============================================================

print("\n" + "=" * 70)
print("Top 10 SHAP Feature Contributions")
print("=" * 70)

for index, item in enumerate(
    top_contributions,
    start=1,
):

    feature = item[
        "feature"
    ]

    shap_value = item[
        "shap_value"
    ]

    print(
        f"{index:2d}. "
        f"{feature:35s} "
        f"{shap_value:+.8f}"
    )


# ============================================================
# 17. Final validation summary
# ============================================================

print("\n" + "=" * 70)
print("PHASE 8 VS CODE XAI TEST SUMMARY")
print("=" * 70)

print(
    "Model artifacts loading      : PASS"
)

print(
    "138-feature schema           : PASS"
)

print(
    "Ensemble configuration       : PASS"
)

print(
    "SHAP initialization          : PASS"
)

print(
    "Probability-space SHAP      : PASS"
)

print(
    "SHAP reconstruction         : PASS"
)

print(
    "Feature contribution output : PASS"
)

print(
    "\nOVERALL XAI MODULE TEST     : PASS"
)

print("=" * 70)