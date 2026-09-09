"""
NetVision AI
FastAPI Backend

Unified Network Attack Forecasting API

Pipeline:
    Practical Traffic Input / Model Features
        ↓
    Runtime Input Transformation (if practical traffic)
        ↓
    138 Model Features
        ↓
    ML Ensemble (XGBoost + Random Forest-SMOTE)
        ↓
    World Model (2-state Markov model: 10/20/30/45/60 min)
        ↓
    Probability-Space SHAP Explainability
        ↓
    MITRE ATT&CK Mapping
        ↓
    Unified Forecast Response
"""

from pathlib import Path
from typing import Any, Dict

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.schemas.forecast import ForecastRequest
from src.forecasting.attack_forecast import AttackForecastPipeline


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = PROJECT_ROOT / "models" / "trained"
WORLD_MODEL_DIR = PROJECT_ROOT / "models" / "forecasting"
XAI_BACKGROUND_PATH = PROJECT_ROOT / "models" / "xai" / "shap_background.csv"


# ============================================================
# LOAD SHAP BACKGROUND
# ============================================================

if not XAI_BACKGROUND_PATH.exists():
    raise FileNotFoundError(
        f"SHAP background dataset not found: {XAI_BACKGROUND_PATH}"
    )

shap_background = pd.read_csv(XAI_BACKGROUND_PATH)


# ============================================================
# VALIDATE SHAP BACKGROUND
# ============================================================

if shap_background.shape != (50, 138):
    raise ValueError(
        f"Invalid SHAP background shape. Expected (50, 138), received {shap_background.shape}."
    )

if shap_background.isna().any().any():
    raise ValueError("SHAP background contains NaN values.")


# ============================================================
# INITIALIZE FORECASTING PIPELINE
# ============================================================

pipeline = AttackForecastPipeline(
    xgb_model_path=(MODEL_DIR / "xgb_model.json"),
    rf_model_path=(MODEL_DIR / "rf_smote_model.pkl"),
    feature_names_path=(MODEL_DIR / "feature_names.json"),
    ensemble_config_path=(MODEL_DIR / "ensemble_config.json"),
    transition_model_path=(WORLD_MODEL_DIR / "state_transition_model.json"),
    shap_background_data=shap_background,
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="NetVision AI",
    description="AI-based Network Attack Forecasting from Network Traffic Data",
    version="1.0.0",
)

# Enable CORS for local/frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "project": "NetVision AI",
        "status": "running",
        "service": "Network Attack Forecasting",
        "version": "1.0.0",
    }


# ============================================================
# HEALTH ENDPOINT
# ============================================================

@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "ml_model": "loaded",
        "world_model": "loaded",
        "xai": "loaded",
        "mitre_attack": "loaded",
    }


# ============================================================
# FORECAST ENDPOINT
# ============================================================

@app.post("/forecast")
def forecast(request: ForecastRequest) -> Dict[str, Any]:
    try:
        # 1. If 138 model-ready features dictionary is provided directly
        if request.features is not None and len(request.features) == 138:
            return pipeline.forecast(request.features)

        # 2. Extract practical traffic input dictionary
        traffic_data: Dict[str, Any] = {}

        if request.traffic is not None:
            traffic_data.update(request.traffic)

        req_dict = request.model_dump(exclude_none=True)
        for k, v in req_dict.items():
            if k not in ("features", "traffic") and isinstance(v, (int, float, str)):
                traffic_data[k] = v

        # If no traffic data was explicitly supplied, fallback to empty dict
        # RuntimeFeatureTransformer applies sensible defaults for demo/test inputs
        return pipeline.forecast_from_traffic(traffic_data)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Forecast processing failed: {str(exc)}",
        )