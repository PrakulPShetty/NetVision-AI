"""
NetVision AI backend application.

Provides the API entry point for the network attack
forecasting system.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException

from backend.app.schemas.forecast import ForecastRequest
from src.forecasting.attack_forecast import AttackForecastPipeline


# ============================================================
# Project Root
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# Model Paths
# ============================================================

XGB_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "trained"
    / "xgb_model.json"
)

RF_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "trained"
    / "rf_smote_model.pkl"
)

FEATURE_NAMES_PATH = (
    PROJECT_ROOT
    / "models"
    / "trained"
    / "feature_names.json"
)

ENSEMBLE_CONFIG_PATH = (
    PROJECT_ROOT
    / "models"
    / "trained"
    / "ensemble_config.json"
)

TRANSITION_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "forecasting"
    / "state_transition_model.json"
)


# ============================================================
# Forecasting Pipeline
# ============================================================

forecasting_pipeline = AttackForecastPipeline(
    xgb_model_path=XGB_MODEL_PATH,
    rf_model_path=RF_MODEL_PATH,
    feature_names_path=FEATURE_NAMES_PATH,
    ensemble_config_path=ENSEMBLE_CONFIG_PATH,
    transition_model_path=TRANSITION_MODEL_PATH,
)


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="NetVision AI",
    description="AI-based Network Attack Forecasting API",
    version="1.0.0",
)


# ============================================================
# Root Endpoint
# ============================================================

@app.get("/")
def root():
    """Basic API health check."""

    return {
        "project": "NetVision AI",
        "status": "running",
        "service": "Network Attack Forecasting",
    }


# ============================================================
# Health Endpoint
# ============================================================

@app.get("/health")
def health():
    """Backend health check."""

    return {
        "status": "healthy",
        "ml_model": "loaded",
        "world_model": "loaded",
    }


# ============================================================
# Forecast Endpoint
# ============================================================

@app.post("/forecast")
def forecast(request: ForecastRequest):
    """
    Generate a network attack forecast.

    The request contains the 138 model-ready features.
    """

    try:
        result = forecasting_pipeline.forecast(
            request.features
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        ) from exc